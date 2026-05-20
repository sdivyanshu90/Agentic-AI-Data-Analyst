"""Master Orchestrator.

Phase-1 scope: builds the mission brief from user inputs, runs Phase 1 with
retries against its quality gate, maintains the append-only pipeline state
log, and displays the Phase Transition Card. Other phases are wired through
the same path but will raise NotImplementedError until their agents land.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

# Make repo root importable when this file is run as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.context_packet import build_context_packet  # noqa: E402
from core.pipeline_state import PipelineStateLog  # noqa: E402
from core.quality_gates import GateResult, check_gate  # noqa: E402
from core.retry import build_retry_context  # noqa: E402

PHASE_AGENTS: dict[int, tuple[str, str]] = {
    1: ("agents.phase1_requirements", "Stakeholder Requirement Gathering"),
    2: ("agents.phase2_extraction", "Data Identification & Extraction"),
    3: ("agents.phase3_cleaning", "Data Quality & Cleaning"),
    4: ("agents.phase4_eda", "Exploratory Data Analysis"),
    5: ("agents.phase5_hypothesis", "Hypothesis Testing & Validation"),
    6: ("agents.phase6_advanced", "Advanced Analysis & Root Cause"),
    7: ("agents.phase7_visualisation", "Visualisation & Dashboard Design"),
    8: ("agents.phase8_reporting", "Storytelling, Reporting & Handoff"),
}


@dataclass
class OrchestratorResult:
    mission_brief: dict
    phase_outputs: dict[int, dict] = field(default_factory=dict)
    pipeline_state_log: dict = field(default_factory=dict)
    final_report: str | None = None
    blocked_phase: int | None = None


class DataAnalystOrchestrator:
    def __init__(
        self,
        *,
        max_retries_per_phase: int | None = None,
        log_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        verbose: bool = True,
    ) -> None:
        self.max_retries = max_retries_per_phase or int(
            os.environ.get("MAX_RETRIES_PER_PHASE", "3")
        )
        self.log_dir = Path(log_dir or os.environ.get("PIPELINE_LOG_DIR", "./logs"))
        self.output_dir = Path(
            output_dir or os.environ.get("PIPELINE_OUTPUT_DIR", "./outputs")
        )
        self.row_loss_alert_threshold = float(
            os.environ.get("ROW_LOSS_ALERT_THRESHOLD", "0.10")
        )
        # row_loss_pct is in percent (0–100); env value is a fraction.
        self.row_loss_alert_pct = self.row_loss_alert_threshold * 100
        self.verbose = verbose
        # Optional callback for user-interactive prompts (row-loss confirmation,
        # PARTIAL status acknowledgement). Defaults to interactive stdin/stdout.
        self.user_confirm = _default_user_confirm
        # Per-phase code-execution audit trail (populated for code-capable
        # phases when a real dataset path is supplied).
        self.execution_transcripts: dict[int, list] = {}

    # ---------- intake ----------

    def build_mission_brief(
        self,
        *,
        objective: str,
        data_source_description: str,
        stakeholder_type: str,
        business_domain: str = "",
        constraints: dict | None = None,
        success_looks_like: str = "",
        assumptions: list[str] | None = None,
        dataset_path: str = "",
    ) -> dict:
        brief = {
            "objective": objective.strip(),
            "business_domain": business_domain,
            "stakeholder_type": stakeholder_type,
            "data_source_description": data_source_description,
            "constraints": constraints or {},
            "success_looks_like": success_looks_like,
            "assumptions": assumptions or [],
        }
        # When a real dataset file is supplied, its path travels in the brief so
        # the analytical phases (3–6) can execute pandas against it directly.
        if dataset_path:
            brief["dataset_path"] = dataset_path
        return {"mission_brief": brief}

    # ---------- main pipeline driver ----------

    def run(
        self,
        *,
        objective: str,
        data_source_description: str,
        stakeholder_type: str,
        business_domain: str = "",
        constraints: dict | None = None,
        success_looks_like: str = "",
        assumptions: list[str] | None = None,
        phases_to_run: list[int] | None = None,
        dataset_path: str = "",
    ) -> OrchestratorResult:
        mission_brief = self.build_mission_brief(
            objective=objective,
            data_source_description=data_source_description,
            stakeholder_type=stakeholder_type,
            business_domain=business_domain,
            constraints=constraints,
            success_looks_like=success_looks_like,
            assumptions=assumptions,
            dataset_path=dataset_path,
        )

        state = PipelineStateLog()
        state.set_mission_brief(mission_brief["mission_brief"])

        phase_outputs: dict[int, dict] = {}
        result = OrchestratorResult(mission_brief=mission_brief)

        phases = phases_to_run or [1, 2, 3, 4, 5, 6, 7, 8]  # full 8-phase pipeline

        for phase_number in phases:
            try:
                output = self._run_phase(
                    phase_number=phase_number,
                    mission_brief=mission_brief,
                    phase_outputs=phase_outputs,
                    state=state,
                )
            except PhaseBlockedError as exc:
                state.mark_blocked()
                result.blocked_phase = phase_number
                result.pipeline_state_log = state.to_dict()
                self._log(f"\n⚠ PIPELINE BLOCKED at Phase {phase_number}: {exc}")
                self._persist(state, phase_outputs)
                return result

            phase_outputs[phase_number] = output
            result.phase_outputs[phase_number] = output

        # Phase 8's deliverable is the Markdown report — surface it on the result.
        if 8 in phase_outputs:
            result.final_report = phase_outputs[8].get("final_report")

        # Mark complete only when every requested phase has run.
        if all(p in phase_outputs for p in phases):
            state.mark_complete()
        result.pipeline_state_log = state.to_dict()
        self._persist(state, phase_outputs)
        return result

    # ---------- per-phase execution ----------

    def _run_phase(
        self,
        *,
        phase_number: int,
        mission_brief: dict,
        phase_outputs: dict[int, dict],
        state: PipelineStateLog,
    ) -> dict:
        module_name, phase_name = PHASE_AGENTS[phase_number]
        agent_module = import_module(module_name)

        self._log(
            f"\n▶ Phase {phase_number} — {phase_name} | invoking agent "
            f"(max retries: {self.max_retries})"
        )

        retry_context: dict | None = None
        last_output: dict | None = None
        last_gate: GateResult = GateResult(passed=False, failure_reason="not attempted")

        # `mission_brief` here is the wrapper {"mission_brief": {...}}; the
        # context packet stores just the inner brief at packet["mission_brief"]
        # so the agent sees a single layer of nesting.
        brief_inner = mission_brief.get("mission_brief", mission_brief)

        for attempt in range(1, self.max_retries + 1):
            packet = build_context_packet(
                mission_brief=brief_inner,
                prior_outputs=phase_outputs,
                pipeline_state=state.to_dict()["pipeline_state"],
                retry_context=retry_context,
            )

            try:
                phase_result = agent_module.run(packet)
            except NotImplementedError as exc:
                raise PhaseBlockedError(str(exc))
            output = phase_result.output if hasattr(phase_result, "output") else phase_result

            # Capture the executed-code audit trail, if this phase ran any.
            transcript = getattr(phase_result, "transcript", None)
            if transcript:
                self.execution_transcripts[phase_number] = transcript
                self._log(
                    f"  ⚙ Phase {phase_number} executed "
                    f"{getattr(phase_result, 'code_calls', len(transcript))} "
                    "code block(s) against the real dataset."
                )

            status = output.get("status", "COMPLETE")

            if status == "CLARIFICATION_NEEDED":
                clarification = output.get("clarification_needed") or "(no question provided)"
                state.append_phase(
                    phase_number=phase_number,
                    phase_name=phase_name,
                    status="FAILED",
                    key_decisions=[],
                    reasoning_summary="Agent requested clarification.",
                    output_summary=clarification,
                    quality_gate_passed=False,
                    failure_reason="CLARIFICATION_NEEDED",
                )
                raise PhaseBlockedError(
                    f"Phase {phase_number} needs user clarification: {clarification}"
                )

            if status == "BLOCKED":
                blocker = output.get("blocker") or "(no blocker reason given)"
                state.append_phase(
                    phase_number=phase_number,
                    phase_name=phase_name,
                    status="FAILED",
                    key_decisions=[],
                    reasoning_summary="Agent reported BLOCKED.",
                    output_summary=blocker,
                    quality_gate_passed=False,
                    failure_reason=f"BLOCKED: {blocker}",
                )
                raise PhaseBlockedError(f"Phase {phase_number} reported BLOCKED: {blocker}")

            gate = check_gate(phase_number, output, packet)
            last_output = output
            last_gate = gate

            if gate.passed and status != "NEEDS_RETRY":
                # Per CLAUDE.md Phase 3 note: row loss >20% would already fail
                # the gate, but any row loss above the alert threshold (default
                # 10%) deserves an explicit user confirmation before advancing,
                # even if the gate passes.
                if phase_number == 3:
                    suite = output.get("validation_suite") or {}
                    row_loss = float(suite.get("row_loss_pct") or 0.0)
                    if row_loss >= self.row_loss_alert_pct:
                        question = (
                            f"Phase 3 dropped {row_loss:.1f}% of rows "
                            f"({suite.get('row_count_original')} → "
                            f"{suite.get('row_count_clean')}). Proceed to Phase 4?"
                        )
                        if not self.user_confirm(question):
                            state.append_phase(
                                phase_number=phase_number,
                                phase_name=phase_name,
                                status="FAILED",
                                key_decisions=[],
                                reasoning_summary="User declined to proceed after row-loss alert.",
                                output_summary=question,
                                quality_gate_passed=False,
                                failure_reason="USER_ROW_LOSS_ABORT",
                            )
                            raise PhaseBlockedError(
                                f"Phase 3 halted by user: row loss {row_loss:.1f}%."
                            )

                # PARTIAL status is allowed for Phases 4, 5, and 6 (PROMPT.md
                # output_format lists PARTIAL for each); log it explicitly so
                # downstream phases can see the incomplete items.
                logged_status = "COMPLETE"
                if status == "PARTIAL" and phase_number in (4, 5, 6):
                    logged_status = "COMPLETE"  # advancement allowed
                    self._log(
                        f"  ⚠ Phase {phase_number} returned status=PARTIAL — "
                        "advancing per CLAUDE.md but downstream phases must "
                        "treat the output as incomplete."
                    )

                state.append_phase(
                    phase_number=phase_number,
                    phase_name=phase_name,
                    status=logged_status,
                    key_decisions=_extract_key_decisions(phase_number, output),
                    reasoning_summary=_extract_reasoning_summary(phase_number, output),
                    output_summary=_extract_output_summary(phase_number, output),
                    quality_gate_passed=True,
                )
                self._print_transition_card(
                    phase_number=phase_number,
                    phase_name=phase_name,
                    output=output,
                    gate=gate,
                )
                return output

            # Gate failed (or agent self-flagged): log the attempt and retry.
            reason = gate.failure_reason if not gate.passed else "Agent flagged NEEDS_RETRY"
            state.append_phase(
                phase_number=phase_number,
                phase_name=phase_name,
                status="RETRYING" if attempt < self.max_retries else "FAILED",
                key_decisions=[],
                reasoning_summary=f"Attempt {attempt} failed gate.",
                output_summary=reason,
                quality_gate_passed=False,
                failure_reason=reason,
            )
            self._log(f"  ✗ attempt {attempt} failed: {reason}")

            retry_context = build_retry_context(
                attempt=attempt + 1,
                previous_output=output,
                gate_result=gate,
            )

        # Exhausted retries.
        raise PhaseBlockedError(
            f"Phase {phase_number} failed after {self.max_retries} attempts. "
            f"Last failure: {last_gate.failure_reason}"
        )

    # ---------- presentation ----------

    def _print_transition_card(
        self,
        *,
        phase_number: int,
        phase_name: str,
        output: dict,
        gate: GateResult,
    ) -> None:
        if not self.verbose:
            return
        next_phase = phase_number + 1
        next_name = PHASE_AGENTS.get(next_phase, ("", "— END"))[1]
        decisions = _extract_key_decisions(phase_number, output)
        what = _extract_reasoning_summary(phase_number, output)
        out_summary = _extract_output_summary(phase_number, output)
        warnings = _extract_warnings(phase_number, output)

        bar = "━" * 47
        print(f"\n{bar}")
        print(f"▶ PHASE {phase_number} COMPLETE — {phase_name}")
        print(bar)
        print("WHAT THE AGENT DID:")
        print(f"  {what}")
        print("\nKEY DECISIONS MADE:")
        for d in decisions[:4]:
            print(f"  • {d}")
        if not decisions:
            print("  • (none recorded)")
        print("\nOUTPUT SUMMARY:")
        print(f"  {out_summary}")
        for w in warnings:
            print(f"\n{w}")
        print(f"\nQUALITY GATE: ✓ PASSED")
        if next_phase in PHASE_AGENTS:
            print(f"\nADVANCING TO: Phase {next_phase} — {next_name}")
        else:
            print("\nPIPELINE COMPLETE — no further phases.")
        print(bar)

    # ---------- persistence ----------

    def _persist(self, state: PipelineStateLog, phase_outputs: dict[int, dict]) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        state.save(self.log_dir / f"pipeline_state_{ts}.json")
        for phase, out in phase_outputs.items():
            path = self.output_dir / f"phase{phase}_output_{ts}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
            # Phase 8 also carries the final Markdown report — write it as .md
            # so the stakeholder deliverable is directly readable.
            if phase == 8 and isinstance(out, dict) and out.get("final_report"):
                md_path = self.output_dir / f"phase8_report_{ts}.md"
                md_path.write_text(str(out["final_report"]), encoding="utf-8")
        # Persist the executed-code audit trail for any code-capable phases.
        for phase, transcript in self.execution_transcripts.items():
            tpath = self.output_dir / f"phase{phase}_transcript_{ts}.json"
            tpath.parent.mkdir(parents=True, exist_ok=True)
            tpath.write_text(
                json.dumps(transcript, indent=2, default=str), encoding="utf-8"
            )

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)


# ---------- helpers ----------


class PhaseBlockedError(RuntimeError):
    """Raised when a phase cannot continue (clarification needed, retries exhausted, stub)."""


def _default_user_confirm(question: str) -> bool:
    """Prompt for a y/N answer on stdin. Returns False on non-interactive stdin."""
    print(f"\n⚠ USER CONFIRMATION REQUIRED: {question}")
    if not sys.stdin.isatty():
        print("  (non-interactive stdin — defaulting to NO)")
        return False
    try:
        answer = input("  Continue? [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def _extract_key_decisions(phase_number: int, output: dict) -> list[str]:
    if phase_number == 1:
        decisions: list[str] = []
        cls = output.get("analysis_classification") or {}
        if cls.get("types"):
            decisions.append(f"Classified analysis as: {', '.join(cls['types'])}")
        sq = output.get("sub_questions") or []
        p1 = [q for q in sq if q.get("priority") == "P1"]
        if p1:
            decisions.append(f"Identified {len(p1)} P1 sub-question(s) (of {len(sq)} total)")
        flags = output.get("scope_flags") or []
        if flags:
            decisions.append(
                f"Raised {len(flags)} scope flag(s): "
                + ", ".join(f.get("decision", "?") for f in flags)
            )
        return decisions
    if phase_number == 2:
        decisions = []
        sources = output.get("data_source_map") or []
        confirmed = sum(1 for s in sources if s.get("availability") == "CONFIRMED")
        decisions.append(
            f"Mapped {len(sources)} sub-question/source pair(s); {confirmed} CONFIRMED"
        )
        schemas = output.get("schema_reconnaissance") or []
        inferred = sum(1 for s in schemas if s.get("schema_status") == "INFERRED")
        if schemas:
            decisions.append(
                f"Reconnoitred {len(schemas)} schema(s); {inferred} INFERRED"
            )
        gov = output.get("governance_flags") or []
        pii = sum(1 for g in gov if g.get("flag_type") == "PII")
        if gov:
            decisions.append(
                f"Raised {len(gov)} governance flag(s) ({pii} PII)"
            )
        coverage = output.get("completeness_assessment") or []
        not_cov = sum(1 for c in coverage if c.get("coverage") == "NOT_COVERABLE")
        partial = sum(1 for c in coverage if c.get("coverage") == "PARTIALLY_COVERABLE")
        if coverage:
            decisions.append(
                f"KPI coverage: {len(coverage)} assessed, {partial} partial, {not_cov} not coverable"
            )
        return decisions
    if phase_number == 3:
        decisions = []
        anomalies = output.get("anomaly_taxonomy") or []
        critical = sum(1 for a in anomalies if a.get("severity") == "CRITICAL")
        warning = sum(1 for a in anomalies if a.get("severity") == "WARNING")
        if anomalies:
            decisions.append(
                f"Catalogued {len(anomalies)} anomaly(ies): {critical} CRITICAL, {warning} WARNING"
            )
        clean = output.get("cleaning_decisions") or []
        if clean:
            actions = {}
            for d in clean:
                actions[d.get("action", "?")] = actions.get(d.get("action", "?"), 0) + 1
            decisions.append(
                "Cleaning actions: "
                + ", ".join(f"{n}×{a}" for a, n in actions.items())
            )
        suite = output.get("validation_suite") or {}
        if "row_loss_pct" in suite:
            decisions.append(
                f"Validation row-loss: {suite.get('row_loss_pct', 0):.1f}% "
                f"({suite.get('row_count_original', '?')} → "
                f"{suite.get('row_count_clean', '?')})"
            )
        engineered = output.get("feature_engineering") or []
        if engineered:
            decisions.append(f"Engineered {len(engineered)} derived feature(s)")
        return decisions
    if phase_number == 4:
        decisions = []
        u = output.get("univariate_analysis") or []
        b = output.get("bivariate_analysis") or []
        if u or b:
            decisions.append(
                f"Profiled {len(u)} variable(s) univariate, {len(b)} pair(s) bivariate"
            )
        biv_strong = [bi for bi in b if bi.get("strength") == "STRONG"]
        if biv_strong:
            decisions.append(f"{len(biv_strong)} STRONG bivariate relationship(s) found")
        anomalies = output.get("anomaly_catalogue") or []
        if anomalies:
            to_p6 = sum(1 for a in anomalies if a.get("investigate_in_phase_6"))
            decisions.append(
                f"Catalogued {len(anomalies)} surprise(s); {to_p6} flagged for Phase 6"
            )
        hyps = output.get("hypotheses") or []
        emergent = sum(1 for h in hyps if h.get("source") == "EMERGENT")
        if hyps:
            decisions.append(
                f"Formed {len(hyps)} hypothesis(es) ({emergent} EMERGENT from EDA)"
            )
        return decisions
    if phase_number == 5:
        decisions = []
        tests = output.get("tests_conducted") or []
        supported = sum(1 for t in tests if t.get("result") == "SUPPORTED")
        rejected = sum(1 for t in tests if t.get("result") == "REJECTED")
        inconclusive = sum(1 for t in tests if t.get("result") == "INCONCLUSIVE")
        decisions.append(
            f"Ran {len(tests)} test(s): {supported} SUPPORTED, "
            f"{rejected} REJECTED, {inconclusive} INCONCLUSIVE"
        )
        high = sum(1 for t in tests if t.get("practical_significance") == "HIGH")
        if high:
            decisions.append(f"{high} finding(s) rated HIGH practical significance")
        mtc = output.get("multiple_testing_correction") or {}
        if mtc.get("applied"):
            survivors = mtc.get("hypotheses_surviving_correction") or []
            decisions.append(
                f"Multiple-testing correction ({mtc.get('method', '?')}) applied: "
                f"{len(survivors)}/{len(tests)} survive"
            )
        underpowered = sum(
            1 for t in tests
            if (t.get("power_analysis") or {}).get("power_flag") == "UNDERPOWERED"
        )
        if underpowered:
            decisions.append(f"{underpowered} test(s) flagged UNDERPOWERED")
        return decisions
    if phase_number == 6:
        decisions = []
        analyses = output.get("analyses") or []
        if analyses:
            methods = sorted({a.get("method_selected", "?") for a in analyses})
            decisions.append(
                f"Ran {len(analyses)} analysis(es): "
                + ", ".join(methods[:3])
                + ("…" if len(methods) > 3 else "")
            )
        chains = output.get("root_cause_chains") or []
        confirmed = sum(
            1 for c in chains
            if (c.get("root_cause") or {}).get("status") == "CONFIRMED"
        )
        hypothesised = sum(
            1 for c in chains
            if (c.get("root_cause") or {}).get("status") == "HYPOTHESISED"
        )
        if chains:
            decisions.append(
                f"Traced {len(chains)} root cause chain(s): "
                f"{confirmed} CONFIRMED, {hypothesised} HYPOTHESISED"
            )
        deep = output.get("segment_deep_dives") or []
        simpsons = sum(1 for d in deep if d.get("simpsons_paradox_detected"))
        if deep:
            decisions.append(
                f"{len(deep)} segment deep-dive(s); {simpsons} Simpson's paradox finding(s)"
            )
        ranks = output.get("insight_ranking") or []
        top_high = sum(1 for r in ranks if r.get("impact") == "HIGH")
        if ranks:
            decisions.append(f"Ranked {len(ranks)} insight(s); {top_high} HIGH-impact")
        unanswered = output.get("unanswered_subquestions") or []
        if unanswered:
            decisions.append(f"{len(unanswered)} sub-question(s) left unanswered")
        return decisions
    if phase_number == 7:
        decisions = []
        specs = output.get("visualisation_specs") or []
        if specs:
            decisions.append(f"Specced {len(specs)} chart(s)")
        arch = output.get("dashboard_architecture") or {}
        if arch.get("dashboard_type"):
            decisions.append(
                f"Dashboard type: {arch['dashboard_type']} "
                f"({len(arch.get('sections') or [])} sections)"
            )
        audit = output.get("anti_pattern_audit") or []
        if audit:
            decisions.append(
                f"Caught and corrected {len(audit)} anti-pattern(s)"
            )
        review = output.get("accessibility_review") or {}
        decisions.append(
            "Accessibility: "
            f"colourblind={'✓' if review.get('colourblind_safe') else '✗'} "
            f"WCAG={'✓' if review.get('wcag_contrast_met') else '✗'} "
            f"alt-text={'✓' if review.get('alt_text_written') else '✗'}"
        )
        return decisions
    if phase_number == 8:
        decisions = []
        summary = output.get("phase_8_summary") or {}
        answered = summary.get("sub_questions_answered") or []
        unanswered = summary.get("sub_questions_unanswered") or []
        decisions.append(
            f"Addressed {len(answered)} sub-question(s) in Key Findings; "
            f"{len(unanswered)} left open for follow-up"
        )
        rec = summary.get("recommendation_count")
        if rec is not None:
            decisions.append(f"Produced {rec} SMART recommendation(s)")
        dist = summary.get("confidence_distribution") or {}
        if dist:
            decisions.append(
                "Confidence mix: "
                f"{dist.get('high', 0)} high / {dist.get('medium', 0)} medium / "
                f"{dist.get('low', 0)} low"
            )
        passed = summary.get("quality_gate_checks_passed")
        failed = summary.get("quality_gate_checks_failed")
        if passed is not None or failed is not None:
            decisions.append(
                f"9-point self-check: {passed} passed / {failed} failed"
            )
        return decisions
    return []


def _extract_reasoning_summary(phase_number: int, output: dict) -> str:
    if phase_number == 1:
        decoding = output.get("stakeholder_decoding") or {}
        return (
            decoding.get("reasoning")
            or decoding.get("gap_analysis")
            or "Phase 1 produced a structured mission brief."
        )
    if phase_number == 2:
        handoff = (output.get("phase_3_handoff_notes") or "").strip()
        if handoff:
            return handoff
        sources = output.get("data_source_map") or []
        if sources:
            first = sources[0]
            return (
                f"Mapped each sub-question to data sources (lead: "
                f"{first.get('sub_question_id')} → "
                f"{', '.join(first.get('sources_needed') or [])})."
            )
        return "Phase 2 produced an extraction plan."
    if phase_number == 3:
        readiness = (output.get("phase_4_readiness_notes") or "").strip()
        if readiness:
            return readiness
        notes = (output.get("validation_suite") or {}).get("notes")
        if notes:
            return notes
        return "Phase 3 profiled the data, applied cleaning, and certified the schema."
    if phase_number == 4:
        handoff = (output.get("phase_5_handoff") or {}).get("notes")
        if handoff:
            return handoff
        return "Phase 4 ran univariate/bivariate/multivariate EDA and produced hypotheses."
    if phase_number == 5:
        priority = output.get("phase_6_priority_insights") or []
        if priority:
            return priority[0]
        caveats = output.get("statistical_caveats") or []
        if caveats:
            return caveats[0]
        return "Phase 5 formally tested hypotheses and computed effect sizes."
    if phase_number == 6:
        viz = output.get("phase_7_top_insights_for_visualisation") or []
        if viz:
            return viz[0]
        ranks = output.get("insight_ranking") or []
        if ranks:
            return ranks[0].get("insight", "")
        return "Phase 6 traced root causes and ranked insights for executive narrative."
    if phase_number == 7:
        narrative = (output.get("phase_8_handoff") or {}).get("narrative_arc_summary")
        if narrative:
            return narrative
        hook = (output.get("narrative_flow") or {}).get("hook")
        if hook:
            return hook
        return "Phase 7 designed the dashboard architecture and chart specs."
    if phase_number == 8:
        summary = output.get("phase_8_summary") or {}
        top = summary.get("top_3_insights") or []
        if top:
            return f"Final stakeholder report delivered. Lead insight: {top[0]}"
        return (
            "Phase 8 synthesised all prior phases into the final stakeholder "
            "report (executive summary, findings, recommendations, caveats)."
        )
    return ""


def _extract_output_summary(phase_number: int, output: dict) -> str:
    if phase_number == 1:
        sq = output.get("sub_questions") or []
        success = output.get("success_definition") or ""
        return (
            f"{len(sq)} sub-questions produced. "
            f"Success definition: {success[:140]}{'…' if len(success) > 140 else ''}"
        )
    if phase_number == 2:
        n_sources = len(output.get("data_source_map") or [])
        n_dict = len(output.get("data_dictionary") or [])
        n_extract = len(output.get("extraction_plan") or [])
        return (
            f"{n_sources} source(s) mapped, {n_extract} extraction step(s), "
            f"{n_dict} column(s) in data dictionary."
        )
    if phase_number == 3:
        n_clean = len(output.get("cleaning_decisions") or [])
        n_log = len(output.get("change_log") or [])
        n_schema = len(output.get("clean_schema") or [])
        suite = output.get("validation_suite") or {}
        return (
            f"{n_clean} cleaning decision(s), {n_log} change log entry(ies), "
            f"clean schema of {n_schema} column(s). Validation: "
            f"null={suite.get('null_check', '?')}, range={suite.get('range_check', '?')}, "
            f"row-loss={suite.get('row_loss_pct', 0):.1f}%."
        )
    if phase_number == 4:
        n_uni = len(output.get("univariate_analysis") or [])
        n_biv = len(output.get("bivariate_analysis") or [])
        n_hyp = len(output.get("hypotheses") or [])
        n_viz = len(output.get("eda_visualisation_spec") or [])
        return (
            f"{n_uni} univariate, {n_biv} bivariate, {n_hyp} hypothesis(es), "
            f"{n_viz} viz spec(s) ready for Phase 7."
        )
    if phase_number == 5:
        n_tests = len(output.get("tests_conducted") or [])
        n_findings = len(output.get("findings_summary") or [])
        n_caveats = len(output.get("statistical_caveats") or [])
        n_priority = len(output.get("phase_6_priority_insights") or [])
        return (
            f"{n_tests} test(s) executed, {n_findings} finding(s) summarised, "
            f"{n_caveats} caveat(s) for Phase 8, {n_priority} priority insight(s) "
            "for Phase 6."
        )
    if phase_number == 6:
        n_analyses = len(output.get("analyses") or [])
        n_chains = len(output.get("root_cause_chains") or [])
        n_insights = len(output.get("insight_ranking") or [])
        n_unanswered = len(output.get("unanswered_subquestions") or [])
        return (
            f"{n_analyses} analysis(es), {n_chains} root cause chain(s), "
            f"{n_insights} insight(s) ranked, {n_unanswered} unanswered."
        )
    if phase_number == 7:
        n_specs = len(output.get("visualisation_specs") or [])
        n_map = len(output.get("insight_to_chart_map") or [])
        n_audit = len(output.get("anti_pattern_audit") or [])
        n_headlines = len(
            (output.get("phase_8_handoff") or {}).get(
                "chart_titles_as_insight_headlines"
            )
            or []
        )
        return (
            f"{n_specs} chart spec(s), {n_map} insight→chart mapping(s), "
            f"{n_audit} anti-pattern correction(s), "
            f"{n_headlines} insight headline(s) handed to Phase 8."
        )
    if phase_number == 8:
        summary = output.get("phase_8_summary") or {}
        report = output.get("final_report") or ""
        n_words = len(report.split())
        return (
            f"Final Markdown report ({n_words} words) + JSON summary. "
            f"{summary.get('recommendation_count', 0)} recommendation(s), "
            f"{len(summary.get('top_3_insights') or [])} top insight(s), "
            f"{len(summary.get('sub_questions_answered') or [])} sub-question(s) "
            "answered."
        )
    return ""


def _extract_warnings(phase_number: int, output: dict) -> list[str]:
    """Per-phase user-visible warnings displayed in the transition card."""
    warnings: list[str] = []
    if phase_number == 2:
        # CLAUDE.md Phase 2 note: INFERRED schemas must surface a warning.
        inferred = [
            s for s in (output.get("schema_reconnaissance") or [])
            if s.get("schema_status") == "INFERRED"
        ]
        if inferred:
            names = ", ".join(s.get("source_name", "?") for s in inferred)
            warnings.append(f"⚠ SCHEMA INFERRED for: {names}")
        # CLAUDE.md: PII governance flags must be resolved before Phase 3.
        unresolved_pii = [
            g for g in (output.get("governance_flags") or [])
            if g.get("flag_type") == "PII" and not (g.get("mitigation") or "").strip()
        ]
        if unresolved_pii:
            cols = ", ".join(g.get("column", "?") for g in unresolved_pii)
            warnings.append(f"⚠ UNRESOLVED PII MITIGATION on: {cols}")
    if phase_number == 3:
        # CLAUDE.md Phase 3 note: bias_audit feeds Phase 8 caveats — surface it.
        bias = output.get("bias_audit") or {}
        if bias.get("severity") in ("MEDIUM", "HIGH"):
            risks = bias.get("risks_found") or []
            preview = "; ".join(map(str, risks[:2])) if risks else "(no specifics)"
            warnings.append(
                f"⚠ BIAS AUDIT severity={bias['severity']}: {preview}"
            )
    if phase_number == 4:
        # CLAUDE.md Phase 4 note: PARTIAL status lists which variables were not
        # profiled and why in the Transition Card.
        if output.get("status") == "PARTIAL":
            handoff_notes = (output.get("phase_5_handoff") or {}).get("notes") or ""
            warnings.append(f"⚠ PARTIAL — see handoff notes: {handoff_notes[:200]}")
    if phase_number == 5:
        # CLAUDE.md Phase 5 note: multiple-testing correction means Phase 6
        # should only investigate hypotheses_surviving_correction.
        mtc = output.get("multiple_testing_correction") or {}
        if mtc.get("applied"):
            survivors = mtc.get("hypotheses_surviving_correction") or []
            tests = output.get("tests_conducted") or []
            dropped = [
                t.get("hypothesis_id")
                for t in tests
                if t.get("hypothesis_id") not in survivors
            ]
            if dropped:
                warnings.append(
                    f"⚠ MTC ({mtc.get('method', '?')}) applied — Phase 6 must "
                    f"ignore hypotheses dropped by correction: {', '.join(dropped)}"
                )
        underpowered = [
            t.get("hypothesis_id") for t in (output.get("tests_conducted") or [])
            if (t.get("power_analysis") or {}).get("power_flag") == "UNDERPOWERED"
        ]
        if underpowered:
            warnings.append(
                f"⚠ UNDERPOWERED test(s): {', '.join(underpowered)} — interpret with caution"
            )
    if phase_number == 6:
        # CLAUDE.md Phase 6 note: Simpson's paradox findings ALWAYS escalate.
        simpsons = [
            d for d in (output.get("segment_deep_dives") or [])
            if d.get("simpsons_paradox_detected")
        ]
        for d in simpsons:
            desc = d.get("simpsons_paradox_description") or "(no description)"
            warnings.append(
                f"⚠ SIMPSON'S PARADOX on {d.get('finding_ref', '?')}: "
                f"{desc[:200]}"
            )
        # CLAUDE.md Phase 6 note: HYPOTHESISED root causes must be labelled in
        # Phase 8 findings — surface them here too.
        hypothesised = [
            c.get("finding_ref")
            for c in (output.get("root_cause_chains") or [])
            if (c.get("root_cause") or {}).get("status") == "HYPOTHESISED"
        ]
        if hypothesised:
            warnings.append(
                "⚠ HYPOTHESISED root cause(s) for: "
                + ", ".join(filter(None, hypothesised))
                + " — Phase 8 must label these as such"
            )
        if output.get("status") == "PARTIAL":
            warnings.append(
                "⚠ Phase 6 PARTIAL — see unanswered_subquestions for what's deferred"
            )
    if phase_number == 7:
        review = output.get("accessibility_review") or {}
        # alt_text_written false is non-blocking but worth surfacing.
        if review.get("alt_text_written") is False:
            warnings.append("⚠ alt_text_written=False — Phase 8 must address before delivery")
        if review.get("min_font_size_met") is False:
            warnings.append("⚠ min_font_size_met=False — readability risk for the dashboard")
        # CLAUDE.md Phase 7 note: chart titles must be insight headlines.
        # If there are obviously bare category-style titles, flag.
        specs = output.get("visualisation_specs") or []
        weak_titles = [
            s.get("chart_name", "?")
            for s in specs
            if s.get("chart_name")
            and not any(c.isdigit() or c in "%" for c in s["chart_name"])
            and "by" in (s["chart_name"] or "").lower()
            and len((s["chart_name"] or "").split()) <= 4
        ]
        if weak_titles:
            warnings.append(
                f"⚠ chart title(s) look like categories, not headlines: {', '.join(weak_titles[:3])}"
            )
    if phase_number == 8:
        summary = output.get("phase_8_summary") or {}
        unanswered = summary.get("sub_questions_unanswered") or []
        if unanswered:
            warnings.append(
                "⚠ sub-question(s) left unanswered — disclosed in the report's "
                "Next Steps: " + ", ".join(str(u) for u in unanswered)
            )
        failed = summary.get("quality_gate_checks_failed")
        if isinstance(failed, int) and failed > 0:
            warnings.append(
                f"⚠ Phase 8 self-check reported {failed} unresolved check(s)"
            )
    return warnings


# ---------- CLI ----------


def _build_cli_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="orchestrator",
        description="Agentic AI Data Analyst — run the pipeline.",
    )
    p.add_argument("--objective", required=True, help="The user's analysis objective")
    p.add_argument(
        "--data-description",
        required=True,
        help="What data is available (tables, files, sources)",
    )
    p.add_argument(
        "--stakeholder",
        required=True,
        help="Who will consume the final output (e.g. 'product team')",
    )
    p.add_argument("--business-domain", default="", help="e.g. SaaS, e-commerce")
    p.add_argument(
        "--dataset-path",
        default="",
        help="Path to a real CSV. When set, phases 3-6 execute pandas against it.",
    )
    p.add_argument("--time-constraint", default="", help="Deadline or urgency")
    p.add_argument("--tools", default="", help="Available tools/stack")
    p.add_argument("--privacy", default="", help="Data sensitivity flags")
    p.add_argument(
        "--phases",
        default="1,2,3,4,5,6,7,8",
        help="Comma-separated phase numbers to run (default: 1,2,3,4,5,6,7,8)",
    )
    p.add_argument("--quiet", action="store_true", help="Suppress transition cards")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_cli_parser().parse_args(argv)
    phases = [int(x) for x in args.phases.split(",") if x.strip()]
    constraints = {
        "time": args.time_constraint,
        "tools": args.tools,
        "privacy": args.privacy,
    }
    orch = DataAnalystOrchestrator(verbose=not args.quiet)
    result = orch.run(
        objective=args.objective,
        data_source_description=args.data_description,
        stakeholder_type=args.stakeholder,
        business_domain=args.business_domain,
        constraints=constraints,
        phases_to_run=phases,
        dataset_path=args.dataset_path,
    )
    if result.blocked_phase is not None:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
