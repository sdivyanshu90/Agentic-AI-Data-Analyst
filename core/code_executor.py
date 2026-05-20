"""Sandboxed code executor for real data analysis.

This is what turns the pipeline from *reasoning about* data into *computing on*
data. An agent emits Python; `DatasetCodeExecutor` runs it in a fresh
subprocess with the real dataset preloaded as `df` (pandas / numpy / scipy in
scope) and returns whatever the code printed.

Safety model — this is a *lightweight* sandbox, not a hardened one:
  * each run is a separate subprocess with a wall-clock timeout;
  * it runs in a throwaway temp directory;
  * an AST denylist rejects obviously dangerous code (process/network/file-
    system access, dynamic eval) *before* it is ever run.
For untrusted code in production you would add an OS container / seccomp; for
LLM-generated pandas against a known CSV the above is a reasonable bar. The
limitation is stated plainly in the benchmark report.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Modules whose import from *user* code signals intent beyond data analysis.
_BANNED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "shutil", "requests", "urllib",
    "http", "ftplib", "telnetlib", "ctypes", "multiprocessing", "threading",
    "importlib", "pickle", "marshal", "pty", "signal",
}
# Bare builtins that allow dynamic code / filesystem escape.
_BANNED_CALLS = {"eval", "exec", "compile", "__import__", "open", "input", "breakpoint"}

DEFAULT_TIMEOUT = 30
DEFAULT_MAX_OUTPUT = 14000


@dataclass
class ExecutionResult:
    ok: bool
    output: str          # what the code printed (truncated to max_output)
    error: str           # traceback / safety / timeout message, if any
    code: str            # the exact code that was run


def _safety_check(code: str) -> str | None:
    """Return an error string if the code is unsafe to run, else None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError: {exc}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _BANNED_IMPORTS:
                    return f"Disallowed import: {alias.name!r}"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _BANNED_IMPORTS:
                return f"Disallowed import: from {node.module!r}"
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _BANNED_CALLS:
                return f"Disallowed call: {func.id}()"
            # Block attribute-style escapes like os.system / subprocess.run
            if isinstance(func, ast.Attribute) and func.attr in {
                "system", "popen", "fork", "spawn", "spawnl", "execv", "execve",
            }:
                return f"Disallowed call: .{func.attr}()"
    return None


_HARNESS = """\
import sys
import pandas as pd
import numpy as np
try:
    from scipy import stats
except Exception:
    stats = None

pd.set_option("display.max_columns", 60)
pd.set_option("display.width", 200)

df = pd.read_csv(sys.argv[1])

# ====================== agent-supplied code below ======================
{user_code}
"""


class DatasetCodeExecutor:
    """Runs agent-supplied Python against one dataset, preloaded as `df`."""

    def __init__(
        self,
        dataset_path: str | Path,
        *,
        timeout: int = DEFAULT_TIMEOUT,
        max_output: int = DEFAULT_MAX_OUTPUT,
    ) -> None:
        self.dataset_path = Path(dataset_path).resolve()
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        self.timeout = timeout
        self.max_output = max_output
        self.run_count = 0

    def run(self, code: str) -> ExecutionResult:
        """Execute `code` in a fresh subprocess; capture what it prints."""
        self.run_count += 1
        code = (code or "").strip()
        if not code:
            return ExecutionResult(False, "", "Empty code block.", code)

        unsafe = _safety_check(code)
        if unsafe:
            return ExecutionResult(False, "", f"Rejected by sandbox: {unsafe}", code)

        script = _HARNESS.format(user_code=code)

        with tempfile.TemporaryDirectory(prefix="aida_exec_") as tmp:
            script_path = Path(tmp) / "_run.py"
            script_path.write_text(script, encoding="utf-8")
            try:
                proc = subprocess.run(
                    [sys.executable, str(script_path), str(self.dataset_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tmp,
                )
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    False, "", f"Execution timed out after {self.timeout}s.", code
                )

        stdout = self._truncate(proc.stdout or "")
        if proc.returncode != 0:
            err = (proc.stderr or "").strip() or "Non-zero exit, no stderr."
            return ExecutionResult(False, stdout, self._truncate(err), code)
        if not stdout.strip():
            return ExecutionResult(
                True,
                "",
                "Code ran but printed nothing — remember to print() your results.",
                code,
            )
        return ExecutionResult(True, stdout, "", code)

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_output:
            return text
        head = text[: self.max_output]
        return head + f"\n... [truncated {len(text) - self.max_output} chars]"
