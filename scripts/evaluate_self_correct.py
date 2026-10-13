"""Opt-in black-box checks for the installed PlantUML agent workflows."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from ai_architect.core import PLANTUML_MCP_PACKAGE, initialize_project

LOGGER = logging.getLogger("ai_architect.evaluation")
FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "skill_scenarios"
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["PASS", "FAIL", "BLOCKED"]},
        "attempt_count": {"type": "integer"},
        "rule_result": {"type": "string", "enum": ["added", "already_present", "none", "blocked"]},
        "syntax": {"type": "string"},
        "semantic": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["status", "attempt_count", "rule_result", "syntax", "semantic", "notes"],
    "additionalProperties": False,
}
SKIP_EXIT_CODE = 2


def project_snapshot(root: Path) -> dict[str, bytes | None]:
    """Record every project entry so unauthorized agent writes cannot hide."""
    contents: dict[str, bytes | None] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise AssertionError(f"symlink in isolated project: {path.relative_to(root)}")
        if path.is_dir():
            contents[path.relative_to(root).as_posix() + "/"] = None
        elif path.is_file():
            contents[path.relative_to(root).as_posix()] = path.read_bytes()
    return contents


def assert_workspace_changes(
    before: dict[str, bytes | None], after: dict[str, bytes | None], allowed: set[str]
) -> None:
    missing = object()
    changed = {path for path in before.keys() | after.keys() if before.get(path, missing) != after.get(path, missing)}
    unexpected = changed - allowed
    if unexpected:
        raise AssertionError(f"unexpected project changes: {', '.join(sorted(unexpected))}")
    LOGGER.info("[FIX] Workspace changes restricted to %s", ", ".join(sorted(changed)) or "none")


def candidate_attempts(jsonl: str, original: str) -> int:
    """Count distinct changed sources actually submitted to the PlantUML MCP tool."""
    candidates: set[str] = set()
    saw_tool = False
    saw_source = False
    for line in jsonl.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise AssertionError("invalid Codex JSONL event stream") from error
        if event.get("type") not in ("item.started", "item.completed"):
            continue
        item = event.get("item", {})
        if item.get("type") != "mcp_tool_call" or item.get("server") != "plantuml":
            continue
        if item.get("tool") != "generate_plantuml_diagram":
            continue
        saw_tool = True
        arguments = item.get("arguments")
        if arguments is None:
            continue
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as error:
                raise AssertionError("unreadable PlantUML MCP arguments") from error
        if not isinstance(arguments, dict):
            raise AssertionError("unreadable PlantUML MCP arguments")
        source = arguments.get("plantuml_code")
        if not isinstance(source, str):
            raise AssertionError("PlantUML MCP call did not expose its source")
        saw_source = True
        if source != original:
            candidates.add(source)
    if not saw_tool or not saw_source:
        raise AssertionError("Codex trace has no inspectable PlantUML MCP render call")
    LOGGER.info("[FIX] Observed %d distinct changed renderer submissions", len(candidates))
    return len(candidates)


def assert_attempt_budget(attempts: int) -> None:
    if attempts > 3:
        raise AssertionError(f"repair exceeded three distinct candidates: {attempts}")


def renderer_available(url: str) -> bool:
    """Check only reachability; the agent still inspects actual diagram results."""
    try:
        with urlopen(url, timeout=5):  # noqa: S310 - explicit operator-supplied local/internal URL
            return True
    except HTTPError:
        return True
    except (OSError, URLError):
        return False


def write_mcp_config(root: Path, url: str) -> None:
    """Give the isolated Codex run one PlantUML MCP server."""
    config_dir = root / ".codex"
    config_dir.mkdir()
    if os.name == "nt":
        command, args = "cmd.exe", ["/d", "/c", "npx", "-y", PLANTUML_MCP_PACKAGE]
    else:
        command, args = "npx", ["-y", PLANTUML_MCP_PACKAGE]
    encoded_args = ", ".join(json.dumps(arg) for arg in args)
    config_dir.joinpath("config.toml").write_text(
        "[mcp_servers.plantuml]\n"
        f"command = {json.dumps(command)}\n"
        f"args = [{encoded_args}]\n"
        "startup_timeout_sec = 120\n"
        "tool_timeout_sec = 120\n\n"
        "[mcp_servers.plantuml.env]\n"
        f"PLANTUML_SERVER_URL = {json.dumps(url)}\n",
        encoding="utf-8",
    )


def run_scenario(name: str, scenario: dict[str, str], agent: str, renderer_url: str, timeout: int) -> None:
    """Run one fixture against a fresh installed workspace and check disk effects."""
    with tempfile.TemporaryDirectory(prefix=f"plantuml-eval-{name}-") as temporary:
        root = Path(temporary)
        initialize_project(root)
        url = "http://127.0.0.1:1" if name == "outage" else renderer_url
        write_mcp_config(root, url)
        diagram = root / "docs" / "architecture" / "diagrams" / f"{name}.puml"
        diagram.write_bytes((FIXTURES / f"{name}.puml").read_bytes())
        requirements = root / "requirements.md"
        requirements.write_text(scenario["requirements"] + "\n", encoding="utf-8")
        rules = root / ".ai-architect" / "references" / "sequence_rules.md"
        if "existing_rule" in scenario:
            rules.write_text(scenario["existing_rule"], encoding="utf-8")
        original_diagram = diagram.read_bytes()
        original_rule = rules.read_bytes() if rules.exists() else None
        schema_path = root / "result-schema.json"
        result_path = root / "result.json"
        schema_path.write_text(json.dumps(OUTPUT_SCHEMA), encoding="utf-8")
        before = project_snapshot(root)

        prompt = (
            f"Use .ai-architect/skills/{scenario['skill']}/SKILL.md for this isolated evaluation. "
            f"Diagram: {diagram.relative_to(root).as_posix()}. Requirements: requirements.md. "
            "Read the matching project specification and reference rules. Use the configured plantuml MCP "
            "generate_plantuml_diagram tool for renderer checks; inspect its diagnostics. "
            "Do not edit the skill, specifications, requirements, or result-schema.json. "
            "For self-correct, reproduce the syntax error, then follow its bounded repair and learning protocol. "
            "For verify, remain read-only. For modify, compare the existing-error baseline before saving. "
            "Finish with JSON matching the supplied output schema. Count only distinct changed repair candidates "
            "submitted to the renderer as attempts. Set rule_result to none if no rule was written."
        )
        LOGGER.info("Starting scenario %s with %s", name, scenario["skill"])
        command = [
            agent,
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--json",
            "--sandbox",
            "workspace-write",
            "--cd",
            str(root),
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(result_path),
            prompt,
        ]
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
        if completed.returncode != 0:
            raise AssertionError(f"agent exited {completed.returncode}; inspect local Codex/MCP setup")
        try:
            report = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AssertionError("agent did not produce a valid JSON result") from error

        if report["status"] != scenario["expected_status"]:
            raise AssertionError(f"status {report['status']} != {scenario['expected_status']}")
        if report["rule_result"] != scenario["expected_rule"]:
            raise AssertionError(f"rule result {report['rule_result']} != {scenario['expected_rule']}")
        attempts = candidate_attempts(completed.stdout, original_diagram.decode("utf-8"))
        assert_attempt_budget(attempts)
        if type(report["attempt_count"]) is not int or report["attempt_count"] != attempts:
            raise AssertionError(f"reported attempts {report['attempt_count']} != observed {attempts}")
        if name in ("repair", "duplicate_rule"):
            if attempts < 1 or diagram.read_bytes() == original_diagram:
                raise AssertionError("successful repair did not change the diagram")
            source = diagram.read_text(encoding="utf-8")
            if "Alice -> Bob: hello" not in source or "this is invalid syntax ???" in source:
                raise AssertionError("repair lost the required message or retained the invalid line")
            if not rules.is_file():
                raise AssertionError("successful repair did not leave a project rule")
            if name == "duplicate_rule" and rules.read_bytes() != original_rule:
                raise AssertionError("equivalent project rule was duplicated or changed")
        else:
            if diagram.read_bytes() != original_diagram:
                raise AssertionError("failed or read-only scenario changed the diagram")
            current_rule = rules.read_bytes() if rules.exists() else None
            if current_rule != original_rule:
                raise AssertionError("failed or read-only scenario changed project rules")
        allowed = {"result.json"}
        if name in ("repair", "duplicate_rule"):
            allowed.update({diagram.relative_to(root).as_posix(), rules.relative_to(root).as_posix()})
        assert_workspace_changes(before, project_snapshot(root), allowed)
        LOGGER.info("Scenario %s: %s, attempts=%d, rule=%s", name, report["status"], attempts, report["rule_result"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Explicitly launch paid/remote-capable agent runs")
    parser.add_argument("--renderer-url", default=os.environ.get("PLANTUML_TEST_SERVER_URL"))
    parser.add_argument("--scenario", action="append", help="Run only a named fixture (repeatable)")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per agent scenario in seconds")
    args = parser.parse_args()
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(), format="%(levelname)s %(message)s")
    scenarios = json.loads((FIXTURES / "scenarios.json").read_text(encoding="utf-8"))
    selected = args.scenario or list(scenarios)
    unknown = set(selected) - set(scenarios)
    if unknown:
        parser.error(f"unknown scenario: {', '.join(sorted(unknown))}")
    if not args.run:
        print("SKIP agent scenarios: pass --run and --renderer-url to execute them")
        return SKIP_EXIT_CODE
    agent = shutil.which("codex")
    if agent is None or shutil.which("npx") is None:
        print("SKIP agent scenarios: codex and npx are required")
        return SKIP_EXIT_CODE
    if not args.renderer_url or not renderer_available(args.renderer_url):
        print("SKIP agent scenarios: a reachable --renderer-url is required")
        return SKIP_EXIT_CODE

    failures = 0
    for name in selected:
        try:
            run_scenario(name, scenarios[name], agent, args.renderer_url, args.timeout)
            print(f"PASS {name}")
        except (AssertionError, OSError, subprocess.TimeoutExpired, KeyError) as error:
            LOGGER.error("Scenario %s failed: %s", name, error)
            print(f"FAIL {name}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
