"""The `run_python` tool exposed to code-capable phase agents.

IMPORTANT: this module deliberately does NOT use `from __future__ import
annotations`. The Gemini SDK introspects a tool function's *real* runtime type
annotations to build its schema for automatic function calling. Under PEP 563
(string annotations) that introspection fails with
``isinstance() arg 2 must be a type`` — so the tool function must be defined
in a module where annotations stay as real types.
"""
from core.code_executor import DatasetCodeExecutor


def make_run_python(dataset_path, transcript):
    """Build a `run_python` tool bound to one dataset.

    Returns ``(run_python, executor)``. Every executed snippet is appended to
    the caller-supplied `transcript` list as ``{code, output, error, ok}`` —
    the audit trail proving figures were computed, not guessed.
    """
    executor = DatasetCodeExecutor(dataset_path)

    def run_python(code: str) -> str:
        """Execute Python to analyse the dataset and return what it prints.

        pandas (pd), numpy (np) and scipy.stats (stats) are imported, and the
        dataset is already loaded as a DataFrame named `df`. You MUST print()
        every result you want to see — only what the code writes to stdout is
        returned to you.

        Args:
            code: Python source to run against the preloaded `df`.

        Returns:
            Whatever the code printed, or an error message if it failed.
        """
        result = executor.run(code)
        transcript.append({
            "code": result.code,
            "output": result.output,
            "error": result.error,
            "ok": result.ok,
        })
        if result.ok:
            return result.output or "(code ran but printed nothing)"
        return "EXECUTION FAILED — fix the code and try again:\n" + result.error

    # Belt-and-suspenders: pin real-type annotations so SDK introspection is
    # robust even if an importer re-exports this under PEP 563 semantics.
    run_python.__annotations__ = {"code": str, "return": str}
    return run_python, executor
