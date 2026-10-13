"""Validate bundled diagram specifications without external dependencies."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "templates" / "specs"
TYPE_FILES = (
    "use_case_spec.md",
    "c4_container_spec.md",
    "sequence_spec.md",
    "activity_spec.md",
    "state_spec.md",
    "class_spec.md",
    "deployment_spec.md",
)
REQUIRED_SECTIONS = (
    "Purpose and Selection",
    "Required Inputs",
    "Modeling Rules",
    "PlantUML Syntax",
    "Complete Example",
    "Semantic Acceptance Checks",
    "Output Contract",
)
LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
FENCE = re.compile(r"^\s*```([a-zA-Z]*)\s*$")
LOGGER = logging.getLogger("validate_specs")


def check_links(path: Path, content: str) -> list[str]:
    """Report broken local Markdown links in one file."""
    LOGGER.debug("Checking links in %s", path.relative_to(ROOT))
    errors = []
    for target in LINK.findall(content):
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            continue
        destination = (path.parent / unquote(parsed.path)).resolve()
        if not destination.is_file():
            errors.append(f"{path.relative_to(ROOT)}: broken link {target}")
    return errors


def extract_fences(path: Path, content: str) -> tuple[list[str], list[str]]:
    """Find PlantUML blocks and unbalanced Markdown fences."""
    LOGGER.debug("Checking fences in %s", path.relative_to(ROOT))
    blocks = []
    errors = []
    opening = None
    body = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = FENCE.match(line)
        if match is None:
            if opening is not None:
                body.append(line)
            continue
        if opening is None:
            opening = (line_number, match.group(1).lower())
            body = []
        else:
            if match.group(1):
                errors.append(f"{path.relative_to(ROOT)}:{line_number}: closing fence has a language label")
            if opening[1] == "plantuml":
                blocks.append("\n".join(body))
            opening = None
    if opening is not None:
        errors.append(f"{path.relative_to(ROOT)}:{opening[0]}: unclosed fence")
    return blocks, errors


def check_type_spec(path: Path, content: str) -> list[str]:
    """Check the shared document contract and one complete example."""
    LOGGER.debug("Checking type specification %s", path.relative_to(ROOT))
    errors = []
    headings = re.findall(r"^## (.+)$", content, flags=re.MULTILINE)
    if headings != list(REQUIRED_SECTIONS):
        errors.append(f"{path.relative_to(ROOT)}: required sections missing or out of order")
    blocks, fence_errors = extract_fences(path, content)
    errors.extend(fence_errors)
    if len(blocks) != 1:
        errors.append(f"{path.relative_to(ROOT)}: expected one complete PlantUML example, found {len(blocks)}")
    for block in blocks:
        starts = list(re.finditer(r"(?m)^@startuml\s*$", block))
        ends = list(re.finditer(r"(?m)^@enduml\s*$", block))
        if len(starts) != 1 or len(ends) != 1 or starts[0].start() >= ends[0].start():
            errors.append(f"{path.relative_to(ROOT)}: example needs ordered @startuml and @enduml")
    return errors


def check_matrix(content: str) -> list[str]:
    """Require one route for each supported diagram type."""
    targets = re.findall(r"\]\(([a-z0-9_]+_spec\.md)\)", content)
    if len(targets) != len(TYPE_FILES) or set(targets) != set(TYPE_FILES):
        return ["templates/specs/workflow_matrix.md: matrix must link each of the seven types exactly once"]
    return []


def main() -> int:
    """Validate all bundled Markdown specifications and report a concise result."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level_name, logging.INFO), format="%(levelname)s %(message)s")
    LOGGER.debug("Starting specification validation in %s", SPECS)
    paths = sorted(SPECS.glob("*.md"))
    errors = []
    expected_files = {"README.md", "workflow_matrix.md", *TYPE_FILES}
    found_files = {path.name for path in paths}
    if found_files != expected_files:
        errors.append(f"templates/specs: expected {sorted(expected_files)}, found {sorted(found_files)}")
    for path in paths:
        content = path.read_text(encoding="utf-8")
        errors.extend(check_links(path, content))
        if path.name in TYPE_FILES:
            errors.extend(check_type_spec(path, content))
        elif path.name == "workflow_matrix.md":
            errors.extend(check_matrix(content))
            _, fence_errors = extract_fences(path, content)
            errors.extend(fence_errors)
        else:
            _, fence_errors = extract_fences(path, content)
            errors.extend(fence_errors)
    for error in errors:
        LOGGER.error("%s", error)
    failed_files = {error.split(":")[0] for error in errors}
    LOGGER.info("Checked %d files: %d passed, %d errors", len(paths), len(paths) - len(failed_files), len(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
