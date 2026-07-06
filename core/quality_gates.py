"""Per-phase quality gates.

CLAUDE.md defines a `GATES = {phase: lambda out: bool}` shape. We extend it
so each gate also receives the context packet — that lets Phase 1 verify the
mission brief carried through (the doc's `out["mission_brief"]` reference is
satisfied by the packet, not the phase output itself).

Gates return a `GateResult(passed, failure_reason)` so retries can enrich
context with a precise diagnosis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class GateResult:
    passed: bool
    failure_reason: str = ""

    def __bool__(self) -> bool:
        return self.passed


def _ok() -> GateResult:
    return GateResult(passed=True)


def _fail(reason: str) -> GateResult:
    return GateResult(passed=False, failure_reason=reason)


def gate_phase_0(out: dict, context: dict | None = None) -> GateResult:
    valid_complexity = {"QUICK_LOOKUP", "STANDARD_ANALYSIS", "DEEP_INVESTIGATION"}
    if out.get("complexity") not in valid_complexity:
        return _fail(
            f"complexity must be one of {sorted(valid_complexity)} "
            f"(got {out.get('complexity')!r})"
        )
    if not (out.get("complexity_reasoning") or "").strip():
        return _fail("complexity_reasoning is required (audit trail)")

    if "confound_candidates" not in out:
        return _fail("confound_candidates list is required (may be empty only "
                     "if calendar_questions_for_user is populated)")
    candidates = out["confound_candidates"] or []
    if not candidates and not (out.get("calendar_questions_for_user") or []):
        return _fail(
            "the known-event check is never skipped: either document "
            "confound_candidates or list calendar_questions_for_user to ask"
        )
    valid_sources = {"STATED_BY_USER", "KNOWLEDGE_BASE", "TO_ASK_USER"}
    for i, c in enumerate(candidates):
        if not (c.get("event") or "").strip():
            return _fail(f"confound_candidates[{i}].event is required")
        if c.get("source") not in valid_sources:
            return _fail(
                f"confound_candidates[{i}].source must be one of {sorted(valid_sources)}"
            )
        if not (c.get("reasoning") or "").strip():
            return _fail(f"confound_candidates[{i}].reasoning is required")

    if "detected_stakeholder_conflicts" not in out:
        return _fail("detected_stakeholder_conflicts list is required (may be empty)")
    for i, conflict in enumerate(out["detected_stakeholder_conflicts"] or []):
        for key in ("stakeholder_a_view", "stakeholder_b_view"):
            if not (conflict.get(key) or "").strip():
                return _fail(f"detected_stakeholder_conflicts[{i}].{key} is required")

    scope = out.get("scope_and_feasibility") or {}
    if scope.get("deadline_feasibility") not in (
        "FEASIBLE", "FEASIBLE_WITH_DESCOPING", "INFEASIBLE"
    ):
        return _fail(
            "scope_and_feasibility.deadline_feasibility must be FEASIBLE | "
            "FEASIBLE_WITH_DESCOPING | INFEASIBLE"
        )
    if not (scope.get("feasibility_reasoning") or "").strip():
        return _fail("scope_and_feasibility.feasibility_reasoning is required")
    if scope.get("deadline_feasibility") != "FEASIBLE" and not [
        d for d in (scope.get("descope_proposal") or []) if (d or "").strip()
    ]:
        return _fail(
            "deadline_feasibility != FEASIBLE requires a concrete "
            "descope_proposal — never silently promise everything"
        )

    route = out.get("route")
    if route not in ("SKIP_TO_QUICK_ANSWER", "FULL_PIPELINE"):
        return _fail("route must be SKIP_TO_QUICK_ANSWER | FULL_PIPELINE")
    if not (out.get("route_reasoning") or "").strip():
        return _fail("route_reasoning is required (audit trail)")
    if route == "SKIP_TO_QUICK_ANSWER":
        if out.get("complexity") != "QUICK_LOOKUP":
            return _fail(
                "route SKIP_TO_QUICK_ANSWER requires complexity QUICK_LOOKUP "
                f"(got {out.get('complexity')!r})"
            )
        if not (out.get("quick_answer_draft") or "").strip():
            return _fail("route SKIP_TO_QUICK_ANSWER requires a quick_answer_draft")

    return _ok()


def gate_phase_1(out: dict, context: dict | None = None) -> GateResult:
    ctx = context or {}
    mission_brief = ctx.get("mission_brief") or {}

    if not mission_brief.get("objective"):
        return _fail("mission_brief.objective is missing or empty in the context packet")

    sub_questions = out.get("sub_questions")
    if not isinstance(sub_questions, list) or len(sub_questions) < 3:
        return _fail(
            f"sub_questions must contain at least 3 entries; got "
            f"{len(sub_questions) if isinstance(sub_questions, list) else 'none'}"
        )

    for i, sq in enumerate(sub_questions):
        if not isinstance(sq, dict):
            return _fail(f"sub_questions[{i}] must be an object")
        for key in ("id", "question", "priority", "reasoning"):
            if not sq.get(key):
                return _fail(f"sub_questions[{i}].{key} is missing or empty")
        if sq["priority"] not in ("P1", "P2", "P3"):
            return _fail(
                f"sub_questions[{i}].priority must be one of P1/P2/P3, got {sq['priority']!r}"
            )

    success_definition = out.get("success_definition")
    if not isinstance(success_definition, str) or not success_definition.strip():
        return _fail("success_definition must be a non-empty string")

    profile = out.get("stakeholder_profile") or {}
    if not profile.get("primary_audience"):
        return _fail("stakeholder_profile.primary_audience is required")
    if profile.get("technical_tolerance") not in ("Low", "Medium", "High"):
        return _fail(
            "stakeholder_profile.technical_tolerance must be Low | Medium | High; "
            f"got {profile.get('technical_tolerance')!r}"
        )

    classification = out.get("analysis_classification") or {}
    if not classification.get("reasoning"):
        return _fail("analysis_classification.reasoning is required (audit trail)")

    decoding = out.get("stakeholder_decoding") or {}
    if not decoding.get("reasoning"):
        return _fail("stakeholder_decoding.reasoning is required (audit trail)")

    return _ok()


def gate_phase_2(out: dict, context: dict | None = None) -> GateResult:
    sources = out.get("data_source_map") or []
    if not sources:
        return _fail("data_source_map must contain at least one entry")
    if not any(s.get("availability") == "CONFIRMED" for s in sources):
        return _fail("data_source_map must contain at least one CONFIRMED source")

    valid_availability = {"CONFIRMED", "ASSUMED", "MISSING", "REQUIRES_ACCESS"}
    for i, s in enumerate(sources):
        if s.get("availability") not in valid_availability:
            return _fail(
                f"data_source_map[{i}].availability must be one of "
                f"{sorted(valid_availability)}"
            )
        if not (s.get("reasoning") or "").strip():
            return _fail(
                f"data_source_map[{i}].reasoning is required (audit trail)"
            )

    if "governance_flags" not in out:
        return _fail("governance_flags list is required (may be empty)")
    for i, g in enumerate(out["governance_flags"] or []):
        if g.get("flag_type") == "PII" and not (g.get("mitigation") or "").strip():
            return _fail(
                f"governance_flags[{i}] (PII on {g.get('column')!r}) requires "
                "a non-empty mitigation per CLAUDE.md Phase 2 note"
            )

    extraction = out.get("extraction_plan") or []
    if not extraction:
        return _fail("extraction_plan must contain at least one entry")
    for i, e in enumerate(extraction):
        if not (e.get("query_or_steps") or "").strip():
            return _fail(f"extraction_plan[{i}].query_or_steps is empty")
        if not (e.get("reasoning") or "").strip():
            return _fail(f"extraction_plan[{i}].reasoning is required")

    coverage = out.get("completeness_assessment") or []
    if not coverage:
        return _fail("completeness_assessment must contain at least one entry")
    for i, c in enumerate(coverage):
        if not (c.get("reasoning") or "").strip():
            return _fail(f"completeness_assessment[{i}].reasoning is required")

    if not (out.get("data_dictionary") or []):
        return _fail("data_dictionary must contain at least one entry")

    # Cross-phase invariant: every Phase 1 P1 sub-question must have a
    # data_source_map entry. (P2/P3 are nice-to-have per CLAUDE.md.)
    ctx = context or {}
    prior = (ctx.get("prior_outputs") or {})
    phase1 = prior.get(1) or prior.get("1") or prior.get("phase_1") or {}
    p1_ids = [
        sq["id"]
        for sq in (phase1.get("sub_questions") or [])
        if sq.get("priority") == "P1"
    ]
    if p1_ids:
        mapped = {s.get("sub_question_id") for s in sources}
        missing = [sid for sid in p1_ids if sid not in mapped]
        if missing:
            return _fail(
                "data_source_map is missing entries for P1 sub-questions: "
                + ", ".join(missing)
            )

    return _ok()


def gate_phase_3(out: dict, context: dict | None = None) -> GateResult:
    suite = out.get("validation_suite") or {}
    if suite.get("null_check") != "PASSED":
        return _fail("validation_suite.null_check must equal 'PASSED'")
    if not (out.get("change_log") or []):
        return _fail("change_log must contain at least one entry")

    row_loss = suite.get("row_loss_pct")
    if row_loss is None:
        return _fail("validation_suite.row_loss_pct is required")
    if row_loss >= 20.0:
        return _fail(
            f"validation_suite.row_loss_pct ({row_loss:.1f}%) must be < 20.0"
        )

    # Every CRITICAL or WARNING anomaly must have a matching cleaning_decision
    # on the same column. (NOTE-severity anomalies are documentation only.)
    anomalies = out.get("anomaly_taxonomy") or []
    decisions = out.get("cleaning_decisions") or []
    decision_cols = {d.get("column") for d in decisions}
    for a in anomalies:
        if a.get("severity") in ("CRITICAL", "WARNING"):
            if a.get("column") not in decision_cols:
                return _fail(
                    f"{a.get('severity')} anomaly on column "
                    f"{a.get('column')!r} has no matching cleaning_decisions entry"
                )

    for i, d in enumerate(decisions):
        if not (d.get("reasoning") or "").strip():
            return _fail(f"cleaning_decisions[{i}].reasoning is required (audit trail)")

    bias = out.get("bias_audit") or {}
    if "risks_found" not in bias:
        return _fail("bias_audit.risks_found is required (may be an empty list)")
    if bias.get("severity") not in ("LOW", "MEDIUM", "HIGH"):
        return _fail(
            "bias_audit.severity must be LOW | MEDIUM | HIGH "
            f"(got {bias.get('severity')!r})"
        )

    if not (out.get("clean_schema") or []):
        return _fail("clean_schema must contain at least one entry")

    return _ok()


def gate_phase_4(out: dict, context: dict | None = None) -> GateResult:
    hyps = out.get("hypotheses") or []
    if len(hyps) < 2:
        return _fail(f"hypotheses must contain at least 2 entries; got {len(hyps)}")

    seen_ids: set[str] = set()
    for i, h in enumerate(hyps):
        for key in ("id", "statement", "expected_test_type", "reasoning"):
            value = h.get(key)
            if not isinstance(value, str) or not value.strip():
                return _fail(f"hypotheses[{i}].{key} is required")
        hid = h["id"]
        if not hid.startswith("H") or not hid[1:].isdigit():
            return _fail(f"hypotheses[{i}].id must match 'H<n>' (got {hid!r})")
        if hid in seen_ids:
            return _fail(f"duplicate hypothesis id {hid!r}")
        seen_ids.add(hid)
        if h.get("source") not in ("GENERATED_FROM_SUBQUESTION", "EMERGENT"):
            return _fail(
                f"hypotheses[{i}].source must be GENERATED_FROM_SUBQUESTION or "
                f"EMERGENT (got {h.get('source')!r})"
            )
        # Confirmatory-vs-exploratory split: provenance is mandatory so Phase 5
        # can guard against double-dipping (testing a hypothesis on the same
        # data that suggested it).
        if h.get("provenance") not in ("PRE_REGISTERED", "DATA_DERIVED"):
            return _fail(
                f"hypotheses[{i}].provenance must be PRE_REGISTERED or "
                f"DATA_DERIVED (got {h.get('provenance')!r})"
            )
        if h["source"] == "EMERGENT" and h["provenance"] != "DATA_DERIVED":
            return _fail(
                f"hypotheses[{i}] is EMERGENT (formed after seeing the data) "
                "so its provenance must be DATA_DERIVED"
            )

    if not (out.get("univariate_analysis") or []):
        return _fail("univariate_analysis must contain at least one entry")

    biv = out.get("bivariate_analysis") or []
    for i, b in enumerate(biv):
        if not (b.get("reasoning") or "").strip():
            return _fail(f"bivariate_analysis[{i}].reasoning is required")
        if b.get("strength") not in ("STRONG", "MODERATE", "WEAK", "NONE"):
            return _fail(f"bivariate_analysis[{i}].strength must be STRONG/MODERATE/WEAK/NONE")

    viz = out.get("eda_visualisation_spec") or []
    if not viz:
        return _fail("eda_visualisation_spec must contain at least one entry")
    for i, v in enumerate(viz):
        if not (v.get("reasoning") or "").strip():
            return _fail(f"eda_visualisation_spec[{i}].reasoning is required")

    handoff = out.get("phase_5_handoff") or {}
    to_test = handoff.get("hypotheses_to_test") or []
    if not to_test:
        return _fail("phase_5_handoff.hypotheses_to_test must be non-empty")
    unknown = [hid for hid in to_test if hid not in seen_ids]
    if unknown:
        return _fail(
            "phase_5_handoff.hypotheses_to_test references unknown hypothesis "
            "id(s): " + ", ".join(unknown)
        )

    return _ok()


def gate_phase_5(out: dict, context: dict | None = None) -> GateResult:
    tests = out.get("tests_conducted") or []
    if not tests:
        return _fail("tests_conducted must not be empty")

    valid_results = {"SUPPORTED", "REJECTED", "INCONCLUSIVE"}
    valid_practical = {"HIGH", "MEDIUM", "LOW", "NEGLIGIBLE"}
    seen_ids: set[str] = set()

    for i, t in enumerate(tests):
        hid = t.get("hypothesis_id")
        if not isinstance(hid, str) or not hid.startswith("H") or not hid[1:].isdigit():
            return _fail(f"tests_conducted[{i}].hypothesis_id must match 'H<n>'")
        if hid in seen_ids:
            return _fail(f"duplicate hypothesis_id {hid!r} in tests_conducted")
        seen_ids.add(hid)

        p = t.get("p_value")
        if p is None:
            return _fail(f"tests_conducted[{i}].p_value is null")
        # CLAUDE.md test rule: p-values must be floats, not strings.
        if not isinstance(p, (int, float)) or isinstance(p, bool):
            return _fail(
                f"tests_conducted[{i}].p_value must be a number (got {type(p).__name__})"
            )
        if not (0.0 <= float(p) <= 1.0):
            return _fail(f"tests_conducted[{i}].p_value must be in [0, 1]")

        if t.get("result") not in valid_results:
            return _fail(
                f"tests_conducted[{i}].result must be SUPPORTED/REJECTED/INCONCLUSIVE"
            )

        if t.get("practical_significance") not in valid_practical:
            return _fail(
                f"tests_conducted[{i}].practical_significance must be "
                f"HIGH/MEDIUM/LOW/NEGLIGIBLE"
            )

        for key in ("test_selection_reasoning", "practical_significance_reasoning"):
            if not (t.get(key) or "").strip():
                return _fail(f"tests_conducted[{i}].{key} is required (audit trail)")

        if not isinstance(t.get("assumptions_checked"), dict):
            return _fail(f"tests_conducted[{i}].assumptions_checked is required")

        power = t.get("power_analysis") or {}
        if power.get("power_flag") not in ("ADEQUATE", "UNDERPOWERED"):
            return _fail(
                f"tests_conducted[{i}].power_analysis.power_flag must be "
                f"ADEQUATE/UNDERPOWERED"
            )

        effect = t.get("effect_size") or {}
        if not (effect.get("metric") or "").strip():
            return _fail(f"tests_conducted[{i}].effect_size.metric is required")
        if not isinstance(effect.get("value"), (int, float)) or isinstance(effect["value"], bool):
            return _fail(f"tests_conducted[{i}].effect_size.value must be a number")

        # Double-dipping guard: DATA_DERIVED hypotheses may only be graded
        # CONFIRMATORY if a held-out split validated them; otherwise they are
        # EXPLORATORY and must be presented as such downstream.
        grade = t.get("evidence_grade")
        if grade not in ("CONFIRMATORY", "EXPLORATORY"):
            return _fail(
                f"tests_conducted[{i}].evidence_grade must be CONFIRMATORY or "
                f"EXPLORATORY (got {grade!r})"
            )
        provenance = t.get("hypothesis_provenance")
        if provenance not in ("PRE_REGISTERED", "DATA_DERIVED"):
            return _fail(
                f"tests_conducted[{i}].hypothesis_provenance must be "
                f"PRE_REGISTERED or DATA_DERIVED (got {provenance!r})"
            )
        holdout = (t.get("holdout_validation") or "NONE").strip()
        if (
            provenance == "DATA_DERIVED"
            and grade == "CONFIRMATORY"
            and (not holdout or holdout.upper() == "NONE")
        ):
            return _fail(
                f"tests_conducted[{i}] ({hid}) is DATA_DERIVED with no holdout "
                "validation — it cannot be graded CONFIRMATORY; grade it "
                "EXPLORATORY or document the held-out split"
            )

    # CLAUDE.md Phase 5 note: multiple-testing correction must be applied when
    # more than 3 hypotheses are tested.
    mtc = out.get("multiple_testing_correction") or {}
    if len(tests) > 3 and not mtc.get("applied"):
        return _fail(
            f"multiple_testing_correction.applied must be true when n>3 hypotheses "
            f"are tested (n={len(tests)})"
        )
    if mtc.get("applied") and not mtc.get("method"):
        return _fail("multiple_testing_correction.method is required when applied=true")

    # findings_summary must cover every test conducted.
    summary_ids = {f.get("hypothesis_id") for f in (out.get("findings_summary") or [])}
    missing = sorted(seen_ids - summary_ids)
    if missing:
        return _fail(
            "findings_summary missing hypothesis_id(s): " + ", ".join(missing)
        )

    # Cross-phase: every hypothesis declared in Phase 4's handoff must be tested.
    ctx = context or {}
    prior = ctx.get("prior_outputs") or {}
    phase4 = prior.get(4) or prior.get("4") or prior.get("phase_4") or {}
    to_test = (phase4.get("phase_5_handoff") or {}).get("hypotheses_to_test") or []
    untested = [hid for hid in to_test if hid not in seen_ids]
    if untested:
        return _fail(
            "tests_conducted missing hypotheses declared by Phase 4: "
            + ", ".join(untested)
        )

    # Provenance labels must not drift between Phase 4 and Phase 5 — silently
    # relabelling a DATA_DERIVED hypothesis PRE_REGISTERED defeats the guard.
    p4_provenance = {
        h.get("id"): h.get("provenance")
        for h in (phase4.get("hypotheses") or [])
        if h.get("provenance")
    }
    for t in tests:
        hid = t.get("hypothesis_id")
        declared = p4_provenance.get(hid)
        if declared and t.get("hypothesis_provenance") != declared:
            return _fail(
                f"tests_conducted provenance for {hid} "
                f"({t.get('hypothesis_provenance')!r}) contradicts Phase 4's "
                f"label ({declared!r})"
            )

    return _ok()


def gate_phase_6(out: dict, context: dict | None = None) -> GateResult:
    chains = out.get("root_cause_chains") or []
    if not chains:
        return _fail("root_cause_chains must not be empty")

    # CLAUDE.md test rule: every root cause chain has at least 3 links
    # (SYMPTOM → PROXIMATE → ROOT minimum). We require symptom + proximate +
    # root each populated, and the root has CONFIRMED or HYPOTHESISED status.
    for i, c in enumerate(chains):
        for key in ("finding_ref", "symptom"):
            if not (c.get(key) or "").strip():
                return _fail(f"root_cause_chains[{i}].{key} is required")
        proximate = c.get("proximate_cause") or {}
        if not (proximate.get("description") or "").strip():
            return _fail(
                f"root_cause_chains[{i}].proximate_cause.description is required"
            )
        if not (proximate.get("evidence") or "").strip():
            return _fail(
                f"root_cause_chains[{i}].proximate_cause.evidence is required"
            )
        root = c.get("root_cause") or {}
        for key in ("description", "evidence"):
            if not (root.get(key) or "").strip():
                return _fail(f"root_cause_chains[{i}].root_cause.{key} is required")
        if root.get("status") not in ("CONFIRMED", "HYPOTHESISED"):
            return _fail(
                f"root_cause_chains[{i}].root_cause.status must be CONFIRMED or HYPOTHESISED"
            )
        if root.get("status") == "HYPOTHESISED" and not (
            root.get("data_needed_to_confirm") or ""
        ).strip():
            return _fail(
                f"root_cause_chains[{i}].root_cause: HYPOTHESISED status requires "
                "data_needed_to_confirm"
            )

    insights = out.get("insight_ranking") or []
    if not insights:
        return _fail("insight_ranking must not be empty")

    enum_levels = {"HIGH", "MEDIUM", "LOW"}
    seen_ranks: set[int] = set()
    for i, ins in enumerate(insights):
        if not (ins.get("insight") or "").strip():
            return _fail(f"insight_ranking[{i}].insight is required")
        for key in ("impact", "actionability", "confidence"):
            if ins.get(key) not in enum_levels:
                return _fail(
                    f"insight_ranking[{i}].{key} must be HIGH/MEDIUM/LOW"
                )
        rank = ins.get("rank")
        if not isinstance(rank, int) or rank < 1:
            return _fail(f"insight_ranking[{i}].rank must be a positive integer")
        if rank in seen_ranks:
            return _fail(f"insight_ranking has duplicate rank {rank}")
        seen_ranks.add(rank)

    analyses = out.get("analyses") or []
    for i, a in enumerate(analyses):
        if not (a.get("method_reasoning") or "").strip():
            return _fail(f"analyses[{i}].method_reasoning is required (audit trail)")

    ctx = context or {}
    prior = ctx.get("prior_outputs") or {}

    # Systematic confound sweep: every headline finding re-checked across all
    # available dimensions, and every Phase 0 known-event candidate weighed.
    sweep = out.get("confound_sweep") or []
    if not sweep:
        return _fail(
            "confound_sweep must not be empty — every headline finding is "
            "re-run across every available segmenting dimension"
        )
    valid_outcomes = {"HOLDS", "ATTENUATES", "DISAPPEARS", "REVERSES"}
    valid_verdicts = {"ORGANIC", "EVENT_DRIVEN", "MIX_SHIFT", "UNRESOLVED"}
    phase0 = prior.get(0) or prior.get("0") or prior.get("0.0") or prior.get("phase_0") or {}
    has_candidates = bool(phase0.get("confound_candidates"))
    for i, s in enumerate(sweep):
        if not (s.get("finding_ref") or "").strip():
            return _fail(f"confound_sweep[{i}].finding_ref is required")
        dims = s.get("dimensions_swept") or []
        not_sweepable = s.get("dimensions_not_sweepable") or []
        if not dims and not not_sweepable:
            return _fail(
                f"confound_sweep[{i}] ({s.get('finding_ref')}) swept no "
                "dimensions and documented no reason — silence reads as "
                "'checked and clean'"
            )
        for j, d in enumerate(dims):
            if d.get("outcome") not in valid_outcomes:
                return _fail(
                    f"confound_sweep[{i}].dimensions_swept[{j}].outcome must "
                    f"be one of {sorted(valid_outcomes)}"
                )
        for j, d in enumerate(not_sweepable):
            if not (d.get("reason") or "").strip():
                return _fail(
                    f"confound_sweep[{i}].dimensions_not_sweepable[{j}].reason "
                    "is required"
                )
        if has_candidates and not (s.get("known_event_check") or []):
            return _fail(
                f"confound_sweep[{i}] ({s.get('finding_ref')}) has no "
                "known_event_check despite Phase 0 confound_candidates — "
                "every known event must be weighed against every finding"
            )
        if s.get("post_sweep_verdict") not in valid_verdicts:
            return _fail(
                f"confound_sweep[{i}].post_sweep_verdict must be one of "
                f"{sorted(valid_verdicts)}"
            )
        if not (s.get("reasoning") or "").strip():
            return _fail(f"confound_sweep[{i}].reasoning is required (audit trail)")

    # Sensitivity analysis: HIGH-impact findings must be tested against the
    # alternate reasonable choice at each major Phase 3 cleaning decision.
    high_impact = [r for r in insights if r.get("impact") == "HIGH"]
    sensitivity = out.get("sensitivity_analysis") or []
    if high_impact and not sensitivity:
        return _fail(
            "sensitivity_analysis must not be empty when HIGH-impact insights "
            "exist — re-derive each under alternate Phase 3 cleaning choices"
        )
    for i, s in enumerate(sensitivity):
        for key in ("finding_ref", "cleaning_decision_varied", "alternate_choice"):
            if not (s.get(key) or "").strip():
                return _fail(f"sensitivity_analysis[{i}].{key} is required")
        if s.get("robustness") not in ("ROBUST", "FRAGILE"):
            return _fail(
                f"sensitivity_analysis[{i}].robustness must be ROBUST or FRAGILE"
            )

    # External benchmarks may be NONE_AVAILABLE but a quoted value needs a
    # named source — a benchmark without a source is a fabrication.
    for i, b in enumerate(out.get("external_benchmarks") or []):
        value = str(b.get("benchmark_value") or "").strip()
        if value and value.upper() != "NONE_AVAILABLE" and not (b.get("source") or "").strip():
            return _fail(
                f"external_benchmarks[{i}] quotes a value with no source — "
                "never fabricate a benchmark"
            )

    # Cross-phase: every Phase 1 P1 sub-question must be addressed either in
    # analyses or in unanswered_subquestions (CLAUDE.md: "all sub-questions answered").
    phase1 = prior.get(1) or prior.get("1") or prior.get("phase_1") or {}
    p1_ids = [
        sq["id"]
        for sq in (phase1.get("sub_questions") or [])
        if sq.get("priority") == "P1"
    ]
    if p1_ids:
        addressed = {a.get("subquestion_id") for a in analyses}
        addressed |= {u.get("subquestion_id") for u in (out.get("unanswered_subquestions") or [])}
        missing = [sid for sid in p1_ids if sid not in addressed]
        if missing:
            return _fail(
                "Phase 1 P1 sub-question(s) not addressed in analyses or "
                "unanswered_subquestions: " + ", ".join(missing)
            )

    return _ok()


def gate_phase_7(out: dict, context: dict | None = None) -> GateResult:
    specs = out.get("visualisation_specs") or []
    if not specs:
        return _fail("visualisation_specs must not be empty")

    review = out.get("accessibility_review") or {}
    if review.get("colourblind_safe") is not True:
        return _fail("accessibility_review.colourblind_safe must be True")
    # CLAUDE.md Phase 7 note: wcag_contrast_met=false blocks Phase 8.
    if review.get("wcag_contrast_met") is not True:
        return _fail(
            "accessibility_review.wcag_contrast_met must be True before Phase 8 "
            "(CLAUDE.md Phase 7 rule)"
        )

    # CLAUDE.md Phase 7 note: anti-pattern audit is non-optional; every
    # anti_pattern_found entry must have a corresponding correction_applied.
    audit = out.get("anti_pattern_audit") or []
    for i, entry in enumerate(audit):
        if not (entry.get("anti_pattern_found") or "").strip():
            return _fail(f"anti_pattern_audit[{i}].anti_pattern_found is empty")
        if not (entry.get("correction_applied") or "").strip():
            return _fail(
                f"anti_pattern_audit[{i}] (chart {entry.get('chart_name')!r}) "
                "is missing correction_applied"
            )

    # CLAUDE.md invariant #9: never use a pie chart with >4 slices.
    for i, spec in enumerate(specs):
        chart_type = (spec.get("chart_type") or "").lower()
        if "pie" in chart_type or "donut" in chart_type:
            colour = spec.get("colour_encoding") or {}
            # We can't introspect data cardinality but the spec usually carries
            # the slice count in `filters` or `annotations` or a `slice_count`
            # field. Be defensive: if the chart declares slices > 4, block.
            slice_count = spec.get("slice_count")
            if isinstance(slice_count, int) and slice_count > 4:
                return _fail(
                    f"visualisation_specs[{i}] is a pie chart with "
                    f"{slice_count} slices — CLAUDE.md invariant #9 forbids "
                    "pie charts with >4 slices"
                )

    # Every insight_to_chart_map entry must have reasoning (audit trail).
    for i, m in enumerate(out.get("insight_to_chart_map") or []):
        if not (m.get("chart_reasoning") or "").strip():
            return _fail(
                f"insight_to_chart_map[{i}].chart_reasoning is required (audit trail)"
            )

    # Phase 8 handoff must list at least one chart-title insight headline.
    handoff = out.get("phase_8_handoff") or {}
    headlines = handoff.get("chart_titles_as_insight_headlines") or []
    if not headlines:
        return _fail("phase_8_handoff.chart_titles_as_insight_headlines must be non-empty")

    return _ok()


def gate_phase_6_5(out: dict, context: dict | None = None) -> GateResult:
    alts = out.get("alternative_explanations") or []
    if not alts:
        return _fail(
            "alternative_explanations must not be empty — every SUPPORTED "
            "finding and root cause chain gets its strongest rival explanation"
        )
    for i, a in enumerate(alts):
        for key in ("original_finding", "strongest_alt_explanation",
                    "evidence_weighed", "reasoning"):
            if not (a.get(key) or "").strip():
                return _fail(f"alternative_explanations[{i}].{key} is required")
        if not isinstance(a.get("original_survives"), bool):
            return _fail(
                f"alternative_explanations[{i}].original_survives must be a boolean"
            )

    verification = out.get("confound_sweep_verification") or {}
    if "confound_sweep_gaps" not in verification:
        return _fail(
            "confound_sweep_verification.confound_sweep_gaps is required "
            "(may be empty)"
        )

    for i, f in enumerate(out.get("circular_reasoning_flags") or []):
        for key in ("phase", "field", "issue"):
            if not str(f.get(key) or "").strip():
                return _fail(f"circular_reasoning_flags[{i}].{key} is required")

    overclaims = out.get("overclaim_flags") or []
    for i, f in enumerate(overclaims):
        for key in ("finding", "stated_confidence", "corrected_confidence"):
            if not (f.get(key) or "").strip():
                return _fail(f"overclaim_flags[{i}].{key} is required")

    verdict = out.get("verdict")
    if verdict not in ("PROCEED", "PROCEED_WITH_REVISIONS", "BLOCK"):
        return _fail("verdict must be PROCEED | PROCEED_WITH_REVISIONS | BLOCK")
    if not (out.get("verdict_reasoning") or "").strip():
        return _fail("verdict_reasoning is required (audit trail)")

    revisions = [r for r in (out.get("required_revisions") or []) if (r or "").strip()]
    if verdict in ("PROCEED_WITH_REVISIONS", "BLOCK") and not revisions:
        return _fail(f"verdict {verdict} requires a non-empty required_revisions list")

    # Anti-rubber-stamp: a review that killed a finding or flagged an
    # overclaim cannot conclude plain PROCEED with no required changes.
    killed = [a for a in alts if a.get("original_survives") is False]
    if verdict == "PROCEED" and (killed or overclaims):
        return _fail(
            "verdict PROCEED contradicts the review's own findings "
            f"({len(killed)} finding(s) did not survive, "
            f"{len(overclaims)} overclaim flag(s)) — use "
            "PROCEED_WITH_REVISIONS or BLOCK"
        )

    return _ok()


def gate_phase_8(out: dict, context: dict | None = None) -> GateResult:
    summary = out.get("phase_8_summary") or {}
    if not (summary.get("sub_questions_answered") or []):
        return _fail("phase_8_summary.sub_questions_answered must not be empty")
    if summary.get("quality_gate_checks_failed", 1) != 0:
        return _fail("phase_8_summary.quality_gate_checks_failed must be 0")
    return _ok()


def gate_phase_9(out: dict, context: dict | None = None) -> GateResult:
    metrics = out.get("success_metrics") or []
    if not metrics:
        return _fail(
            "success_metrics must not be empty — every recommendation gets a "
            "metric, threshold, and check-in date"
        )
    for i, m in enumerate(metrics):
        for key in ("recommendation_ref", "metric", "cadence", "threshold",
                    "check_in_date", "reasoning"):
            if not (m.get(key) or "").strip():
                return _fail(f"success_metrics[{i}].{key} is required")

    specs = out.get("monitoring_specs") or []
    if not specs:
        return _fail(
            "monitoring_specs must not be empty — every key finding gets a "
            "drift-alert condition"
        )
    for i, s in enumerate(specs):
        for key in ("finding_ref", "alert_condition", "suggested_tool"):
            if not (s.get(key) or "").strip():
                return _fail(f"monitoring_specs[{i}].{key} is required")

    kb = out.get("knowledge_base_entry") or {}
    for key in ("question", "answer_one_paragraph"):
        if not (kb.get(key) or "").strip():
            return _fail(f"knowledge_base_entry.{key} is required")
    if not (kb.get("data_sources") or []):
        return _fail("knowledge_base_entry.data_sources must not be empty")
    if "gotchas_discovered" not in kb:
        return _fail("knowledge_base_entry.gotchas_discovered is required (may be empty)")

    return _ok()


GATES: dict[float, Callable[[dict, dict | None], GateResult]] = {
    0: gate_phase_0,
    1: gate_phase_1,
    2: gate_phase_2,
    3: gate_phase_3,
    4: gate_phase_4,
    5: gate_phase_5,
    6: gate_phase_6,
    6.5: gate_phase_6_5,
    7: gate_phase_7,
    8: gate_phase_8,
    9: gate_phase_9,
}


def check_gate(
    phase_number: int | float, output: dict, context: dict | None = None
) -> GateResult:
    if phase_number not in GATES:
        raise KeyError(f"No quality gate defined for phase {phase_number}")
    return GATES[phase_number](output, context)
