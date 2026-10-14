"""
PhishForge — CLI entrypoint.

Command-line interface for the PhishForge closed-loop simulation synthesis engine.
Provides the `run` command supporting scenario specification via CLI flags, JSON files,
or hybrid flag overrides, with live iteration tracing and structured artifact output.

Source of truth: Document A v2 §7, Document B v2 §6.1, Document C v2 Phase 7.

Usage:
    python -m phishforge run --role finance --scenario-type invoice_fraud --difficulty 3 \
        --indicators urgency,authority_impersonation --org-context "..." --verbose --out run.json
    python -m phishforge run --input scenarios/examples/finance_invoice_fraud.json --out run.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core.orchestration.run import run_scenario
from core.safety.safety_gate import SafetyCheckResult
from core.storage.run_writer import save_run
from models.schemas.run import RunRecord
from models.schemas.scenario import ScenarioSpecification
from models.schemas.simulation import GeneratedSimulation
from models.schemas.verification import VerificationResult


def _build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser and subcommands."""
    parser = argparse.ArgumentParser(
        prog="phishforge",
        description=(
            "PhishForge: verifier-guided generative AI for adaptive "
            "phishing-awareness simulation.\n"
            "Closed loop: generation -> safety gate -> verify -> score -> refine."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 'run' subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Execute the closed-loop generation -> safety -> verify -> score -> refine pipeline.",
        description="Execute a PhishForge simulation synthesis run.",
    )

    # Input file option
    run_parser.add_argument(
        "--input",
        "-i",
        type=str,
        dest="input_file",
        help="Path to a scenario JSON specification file (e.g. scenarios/examples/finance_invoice_fraud.json).",
    )

    # Individual scenario parameter flags
    run_parser.add_argument(
        "--role",
        type=str,
        dest="target_role",
        choices=["finance", "hr", "it", "sales", "operations", "executive"],
        help="Target employee role (finance, hr, it, sales, operations, executive).",
    )
    run_parser.add_argument(
        "--scenario-type",
        type=str,
        dest="scenario_type",
        help="Phishing scenario type (e.g. invoice_fraud, password_alert, hr_document_request).",
    )
    run_parser.add_argument(
        "--difficulty",
        type=int,
        choices=[1, 2, 3, 4],
        help="Target difficulty calibration level (1=easy, 4=advanced spear-phishing).",
    )
    run_parser.add_argument(
        "--indicators",
        type=str,
        dest="indicators",
        help="Comma-separated list of phishing indicators (e.g. 'urgency,authority_impersonation').",
    )
    run_parser.add_argument(
        "--org-context",
        type=str,
        dest="org_context",
        help="Organizational context and background details for scenario personalization.",
    )
    run_parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="ISO 639-1 language code (default: 'en').",
    )
    run_parser.add_argument(
        "--prohibited",
        type=str,
        dest="prohibited",
        help="Optional comma-separated list of prohibited content elements.",
    )
    run_parser.add_argument(
        "--constraints",
        type=str,
        dest="constraints",
        help="Optional JSON string of simulation constraints (e.g. '{\"max_words\": 200}').",
    )

    # Execution and output flags
    run_parser.add_argument(
        "--out",
        "-o",
        type=str,
        dest="out_path",
        help="Destination path to write the full RunRecord JSON artifact.",
    )
    run_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print live iteration-by-iteration progress trace to stdout.",
    )
    run_parser.add_argument(
        "--direct-only",
        action="store_true",
        dest="direct_only",
        help="Single-shot baseline mode (bypasses safety gate, verifier, scoring, and refinement).",
    )
    run_parser.add_argument(
        "--demo-unsafe",
        action="store_true",
        dest="demo_unsafe",
        help="Demo/test-only flag: injects a known unsafe simulation to reliably demonstrate deterministic Safety Gate rejection without LLM calls.",
    )

    return parser


def build_scenario_from_args(args: argparse.Namespace) -> ScenarioSpecification:
    """
    Construct and validate a ScenarioSpecification from parsed CLI arguments.
    Supports file loading, flag-only definitions, and hybrid overriding.

    Raises
    ------
    ValueError
        If required fields are missing or argument JSON strings are malformed.
    """
    base_data: dict[str, Any] = {}

    # 1. Load from file if --input is provided
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            raise ValueError(f"Input scenario file not found: {args.input_file}")
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                base_data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse scenario JSON from {args.input_file}: {e}")

    # 2. Apply CLI flag overrides
    if args.target_role is not None:
        base_data["target_role"] = args.target_role
    if args.scenario_type is not None:
        base_data["scenario_type"] = args.scenario_type
    if args.difficulty is not None:
        base_data["difficulty"] = args.difficulty
    if args.org_context is not None:
        base_data["organization_context"] = args.org_context
    if args.language is not None:
        base_data["language"] = args.language
    elif "language" not in base_data:
        base_data["language"] = "en"

    if args.indicators is not None:
        indicators = [i.strip() for i in args.indicators.split(",") if i.strip()]
        base_data["desired_indicators"] = indicators

    if args.prohibited is not None:
        prohibited = [p.strip() for p in args.prohibited.split(",") if p.strip()]
        base_data["prohibited_elements"] = prohibited

    if args.constraints is not None:
        try:
            constraints = json.loads(args.constraints)
            if not isinstance(constraints, dict):
                raise ValueError("--constraints must be a JSON object string (e.g. '{\"key\": \"val\"}')")
            base_data["simulation_constraints"] = constraints
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in --constraints: {e}")

    # 3. Check for required fields before Pydantic validation
    missing = []
    if "organization_context" not in base_data or not base_data["organization_context"]:
        missing.append("--org-context (or 'organization_context' in JSON)")
    if "target_role" not in base_data or not base_data["target_role"]:
        missing.append("--role (or 'target_role' in JSON)")
    if "scenario_type" not in base_data or not base_data["scenario_type"]:
        missing.append("--scenario-type (or 'scenario_type' in JSON)")
    if "difficulty" not in base_data or base_data["difficulty"] is None:
        missing.append("--difficulty (or 'difficulty' in JSON)")
    if "desired_indicators" not in base_data or not base_data["desired_indicators"]:
        missing.append("--indicators (or 'desired_indicators' in JSON)")

    if missing:
        raise ValueError(
            "Missing required scenario specification field(s):\n  - " + "\n  - ".join(missing)
        )

    # 4. Validate through Pydantic schema
    try:
        return ScenarioSpecification(**base_data)
    except Exception as e:
        raise ValueError(f"Scenario validation error: {e}")


def _create_verbose_callback():
    """Create an on_iteration callback for live human-readable progress printing."""
    def _on_iteration(
        iter_num: int,
        sim: GeneratedSimulation | None,
        ver: VerificationResult | None,
        safety: SafetyCheckResult | None,
        status: str,
    ) -> None:
        print(f"\n[Iteration {iter_num}] Status: {status}")

        if safety and not safety.passed:
            print(f"  Safety Gate: REJECTED (Unsafe)")
            for finding in safety.findings:
                print(f"    - {finding}")
            return

        if ver:
            print(f"  Quality Score: {ver.overall_score:.1f}/100 ({ver.pass_fail})")
            print(
                f"  Dimensions   : "
                f"Realism: {ver.realism_score:.1f}  "
                f"Relevance: {ver.relevance_score:.1f}  "
                f"Indicators: {ver.indicator_score:.1f}  "
                f"Difficulty: {ver.difficulty_score:.1f}  "
                f"Language: {ver.language_score:.1f}"
            )
            if ver.semantic_findings:
                print(f"  Findings:")
                for finding in ver.semantic_findings:
                    print(f"    - {finding}")

    return _on_iteration


def _print_summary(record: RunRecord, out_path: str | None = None) -> None:
    """Print the final run summary block to stdout."""
    print("\n" + "=" * 78)
    print("                      PHISHFORGE SYNTHESIS SUMMARY")
    print("=" * 78)
    print(f"Run ID         : {record.run_id}")
    print(f"Condition      : {record.condition}")
    print(f"Terminal State : {record.terminal_state}")
    print(f"Total Steps    : {len(record.iterations)}")

    # Extract final iteration details
    last_iteration = record.iterations[-1] if record.iterations else None
    sim_data = last_iteration.get("simulation") if last_iteration else None
    ver_data = last_iteration.get("verification") if last_iteration else None

    if ver_data and "overall_score" in ver_data and ver_data["overall_score"] is not None:
        score = ver_data["overall_score"]
        band = ver_data.get("pass_fail", "N/A")
        print(f"Final Score    : {score:.1f}/100 ({band})")

    if sim_data:
        print("\n" + "-" * 78)
        print("                        SYNTHESIZED SIMULATION")
        print("-" * 78)
        print(f"Subject : {sim_data.get('subject', 'N/A')}")
        print(f"Sender  : {sim_data.get('sender', 'N/A')}")
        print(f"\nBody:\n{sim_data.get('body', 'N/A')}")
        print("-" * 78)
    elif record.terminal_state == "REJECTED_UNSAFE":
        safety_data = last_iteration.get("safety_result") if last_iteration else None
        print("\n" + "-" * 78)
        print("                        SAFETY GATE REJECTION")
        print("-" * 78)
        if safety_data and safety_data.get("findings"):
            print("Violations:")
            for f in safety_data["findings"]:
                print(f"  - {f}")
        print("-" * 78)

    if out_path:
        print(f"\nSaved RunRecord artifact JSON to: {out_path}")
    print("=" * 78 + "\n")


def main(args_list: list[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(args_list)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        try:
            spec = build_scenario_from_args(args)
        except ValueError as err:
            print(f"\nError: {err}\n", file=sys.stderr)
            sys.exit(2)

        on_iteration = _create_verbose_callback() if args.verbose else None

        _mock_gen = None
        if args.demo_unsafe:
            import uuid
            def _unsafe_generator(s: ScenarioSpecification, revision_instructions: str | None = None) -> GeneratedSimulation:
                return GeneratedSimulation(
                    generation_id=str(uuid.uuid4()),
                    scenario_id=s.scenario_id,
                    subject="URGENT: Your PayPal Account Has Been Suspended - Verify Identity",
                    sender="PayPal Security <security-alert@paypal.com>",
                    body=(
                        "Dear Customer,\n\nWe detected unauthorized access attempts on your account. "
                        "Please verify your credentials immediately at https://www.paypal.com/signin and confirm your "
                        "Social Security Number (000-12-3456) and primary card details to unlock the account.\n\n"
                        "Download the attached patch: update.exe\n\nRegards,\nPayPal Security Team"
                    ),
                    intended_indicators=["urgency", "authority_impersonation"],
                    metadata={"demo_mode": "unsafe_injection"},
                    model="demo-unsafe-injector",
                    prompt_version="v1",
                )
            _mock_gen = _unsafe_generator

        try:
            record = run_scenario(
                spec,
                condition="baseline_direct" if args.direct_only else "verifier_guided",
                on_iteration=on_iteration,
                direct_only=args.direct_only,
                _generator_fn=_mock_gen,
            )
        except Exception as err:
            print(f"\nExecution Failure: {err}\n", file=sys.stderr)
            sys.exit(1)

        # Save output if requested
        if args.out_path:
            try:
                save_run(record, args.out_path)
            except Exception as err:
                print(f"Warning: Failed to save RunRecord to {args.out_path}: {err}", file=sys.stderr)

        # Always print final summary
        _print_summary(record, out_path=args.out_path)

        # Exit code policy: 0 for all evaluated outcomes, 1 for execution failures
        if record.terminal_state == "GENERATION_FAILURE":
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
