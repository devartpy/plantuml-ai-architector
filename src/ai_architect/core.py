"""Project settings and safe filesystem operations for ``ai-architect init``."""

from __future__ import annotations

import json
import logging
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit, urlunsplit

LOGGER = logging.getLogger(__name__)
DEFAULT_DIAGRAMS_DIR = "docs/architecture/diagrams"
DEFAULT_PLANTUML_SERVER_URL = "https://www.plantuml.com/plantuml"
CONFIG_VERSION = 1
WORKSPACE_DIR = ".ai-architect"
PLANTUML_MCP_PACKAGE = "plantuml-mcp-server@0.2.4"
REQUIRED_SPEC_FILES = (
    "README.md",
    "workflow_matrix.md",
    "use_case_spec.md",
    "c4_container_spec.md",
    "sequence_spec.md",
    "activity_spec.md",
    "state_spec.md",
    "class_spec.md",
    "deployment_spec.md",
)
REQUIRED_SKILL_FILES = (
    "README.md",
    "plantuml-create/SKILL.md",
    "plantuml-modify/SKILL.md",
    "plantuml-verify/SKILL.md",
    "self-correct/SKILL.md",
)


class InitError(Exception):
    """An expected initialization failure that the CLI can explain."""


@dataclass(frozen=True)
class ProjectConfig:
    diagrams_dir: str
    plantuml_server_url: str


@dataclass(frozen=True)
class InitEvent:
    action: str
    path: Path
    detail: str = ""


@dataclass(frozen=True)
class PreparedProject:
    root: Path
    workspace: Path
    config: ProjectConfig
    events: tuple[InitEvent, ...]


@dataclass(frozen=True)
class InitResult:
    config: ProjectConfig
    events: tuple[InitEvent, ...]


def _is_reparse_point(path: Path) -> bool:
    """Include Windows junctions as well as ordinary symbolic links."""
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except FileNotFoundError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _check_project_path(root: Path, target: Path) -> None:
    """Reject paths that escape the project or traverse links/junctions."""
    try:
        parts = target.relative_to(root).parts
    except ValueError as error:
        raise InitError(f"Path is outside the project: {target}") from error

    current = root
    for part in parts:
        current /= part
        if _is_reparse_point(current):
            raise InitError(f"Refusing a symlink or reparse point: {current}")
        if current.exists() and not current.is_dir() and current != target:
            raise InitError(f"A path component is not a directory: {current}")


def _ensure_directory(root: Path, target: Path) -> InitEvent:
    _check_project_path(root, target)
    if target.exists():
        if not target.is_dir():
            raise InitError(f"Expected a directory, found a file: {target}")
        LOGGER.debug("Reusing directory: %s", target)
        return InitEvent("reused", target)
    LOGGER.debug("Creating directory: %s", target)
    try:
        target.mkdir(parents=True)
    except OSError as error:
        raise InitError(f"Cannot create directory {target}: {error}") from error
    return InitEvent("created", target)


def _normalize_diagrams_dir(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InitError("diagrams_dir must be a non-empty project-relative path")
    if any(character.isspace() and character not in " " for character in value):
        raise InitError("diagrams_dir contains a control character")
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        raise InitError("diagrams_dir must be relative to the project root")
    if PureWindowsPath(value).drive:
        raise InitError("diagrams_dir must not contain a drive or UNC path")
    if os.name != "nt" and "\\" in value:
        raise InitError("Use forward slashes in diagrams_dir for portability")

    parts = Path(value).parts
    if not parts or any(part == ".." for part in parts):
        raise InitError("diagrams_dir must not contain '..'")
    normalized = Path(*parts).as_posix()
    if normalized in ("", ".") or normalized.split("/")[0].casefold() == WORKSPACE_DIR.casefold():
        LOGGER.error("[FIX] Rejected diagram directory overlapping managed workspace: %s", value)
        raise InitError("diagrams_dir must be outside .ai-architect and below the project root")
    LOGGER.debug("[FIX] Accepted diagram directory outside managed workspace: %s", normalized)
    return normalized


def _normalize_plantuml_url(value: str) -> str:
    if not isinstance(value, str) or value != value.strip() or any(character.isspace() for character in value):
        raise InitError("plantuml_server_url must be a valid HTTP or HTTPS base URL")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise InitError("plantuml_server_url has an invalid host or port") from error
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise InitError("plantuml_server_url needs an HTTP(S) host and must not contain credentials")
    if parsed.query or parsed.fragment or (port is not None and not 0 < port < 65536):
        raise InitError("plantuml_server_url must be a base URL without query or fragment")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def _read_config(path: Path) -> ProjectConfig:
    LOGGER.debug("Reading existing project settings: %s", path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InitError(f"Cannot read valid JSON from {path}: {error}") from error
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int:
        raise InitError(f"Invalid config schema in {path}: expected schema_version {CONFIG_VERSION}")
    if data["schema_version"] != CONFIG_VERSION:
        raise InitError(f"Unsupported schema_version in {path}: {data['schema_version']}")
    try:
        return ProjectConfig(
            diagrams_dir=_normalize_diagrams_dir(data["diagrams_dir"]),
            plantuml_server_url=_normalize_plantuml_url(data["plantuml_server_url"]),
        )
    except KeyError as error:
        raise InitError(f"Missing config field in {path}: {error.args[0]}") from error


def prepare_project(
    root: Path,
    diagrams_dir: str | None = None,
    plantuml_server_url: str | None = None,
) -> PreparedProject:
    """Read or create stable project settings and preserve user-owned directories."""
    LOGGER.debug("Preparing project root: %s", root)
    root = root.resolve()
    if not root.is_dir():
        raise InitError(f"Project root is not a directory: {root}")

    requested_dir = _normalize_diagrams_dir(diagrams_dir) if diagrams_dir is not None else None
    requested_url = _normalize_plantuml_url(plantuml_server_url) if plantuml_server_url is not None else None
    workspace = root / WORKSPACE_DIR
    config_path = workspace / "config.json"
    _check_project_path(root, workspace)
    if workspace.exists() and not workspace.is_dir():
        raise InitError(f"Expected a directory, found a file: {workspace}")
    _check_project_path(root, config_path)
    if config_path.exists():
        if not config_path.is_file():
            raise InitError(f"Expected a configuration file: {config_path}")
        config = _read_config(config_path)
        if requested_dir is not None and requested_dir != config.diagrams_dir:
            raise InitError(f"--diagrams-dir conflicts with existing {config_path}; edit the setting explicitly")
        if requested_url is not None and requested_url != config.plantuml_server_url:
            raise InitError(f"--plantuml-server-url conflicts with existing {config_path}; edit the setting explicitly")
    else:
        config = ProjectConfig(
            diagrams_dir=requested_dir or DEFAULT_DIAGRAMS_DIR,
            plantuml_server_url=requested_url or DEFAULT_PLANTUML_SERVER_URL,
        )

    diagrams_path = root / Path(config.diagrams_dir)
    _check_project_path(root, diagrams_path)
    references_path = workspace / "references"
    _check_project_path(root, references_path)
    for managed_name in ("specs", "skills"):
        managed_path = workspace / managed_name
        _check_project_path(root, managed_path)
        if managed_path.exists() and not managed_path.is_dir():
            raise InitError(f"Expected a managed directory: {managed_path}")

    events: list[InitEvent] = []
    events.append(_ensure_directory(root, workspace))
    events.append(_ensure_directory(root, references_path))
    events.append(_ensure_directory(root, diagrams_path))

    if config_path.exists():
        events.append(InitEvent("reused", config_path))
    else:
        LOGGER.debug("Creating project settings: %s", config_path)
        payload = {
            "schema_version": CONFIG_VERSION,
            "diagrams_dir": config.diagrams_dir,
            "plantuml_server_url": config.plantuml_server_url,
        }
        try:
            with config_path.open("x", encoding="utf-8", newline="\n") as output:
                json.dump(payload, output, indent=2)
                output.write("\n")
        except OSError as error:
            raise InitError(f"Cannot write {config_path}: {error}") from error
        events.append(InitEvent("created", config_path))

    LOGGER.debug("Prepared project with %d directory/settings events", len(events))
    return PreparedProject(root, workspace, config, tuple(events))


def _copy_resource_tree(source: object, destination: Path) -> int:
    """Copy a package resource subtree, preserving its relative structure."""
    destination.mkdir()
    count = 0
    for child in sorted(source.iterdir(), key=lambda item: item.name):
        target = destination / child.name
        if child.is_dir():
            count += _copy_resource_tree(child, target)
        elif child.is_file():
            target.write_bytes(child.read_bytes())
            count += 1
        else:
            raise InitError(f"Unsupported packaged resource: {child}")
    return count


def _check_resource_manifest(package_root: object) -> None:
    for name in REQUIRED_SPEC_FILES:
        if not package_root.joinpath("specs", name).is_file():
            raise InitError(f"Missing packaged specification: specs/{name}")
    for name in REQUIRED_SKILL_FILES:
        if not package_root.joinpath("skills", *name.split("/")).is_file():
            raise InitError(f"Missing packaged skill resource: skills/{name}")


def _mcp_example(config: ProjectConfig) -> dict[str, object]:
    return {
        "mcpServers": {
            "plantuml": {
                "command": "npx",
                "args": ["-y", PLANTUML_MCP_PACKAGE],
                "env": {"PLANTUML_SERVER_URL": config.plantuml_server_url},
            }
        }
    }


def deploy_resources(prepared: PreparedProject) -> tuple[InitEvent, ...]:
    """Replace package-managed directories and refresh the generated MCP example."""
    LOGGER.debug("Loading packaged templates for %s", prepared.root)
    try:
        package_root = resources.files("ai_architect.templates")
        _check_resource_manifest(package_root)
    except (ModuleNotFoundError, OSError, TypeError) as error:
        raise InitError(f"Cannot load packaged templates: {error}") from error

    example_path = prepared.workspace / "mcp-config-example.json"
    _check_project_path(prepared.root, example_path)
    if example_path.exists() and not example_path.is_file():
        raise InitError(f"Expected a generated example file: {example_path}")
    for kind in ("specs", "skills"):
        target = prepared.workspace / kind
        _check_project_path(prepared.root, target)
        if target.exists() and not target.is_dir():
            raise InitError(f"Expected a managed directory: {target}")

    stage = Path(tempfile.mkdtemp(prefix=".init-stage-", dir=prepared.workspace))
    _check_project_path(prepared.root, stage)
    backups = stage / "backups"
    backups.mkdir()
    previous: dict[str, bool] = {}
    installed: set[str] = set()
    keep_stage = False
    try:
        counts = {kind: _copy_resource_tree(package_root.joinpath(kind), stage / kind) for kind in ("specs", "skills")}
        if any(count == 0 for count in counts.values()):
            raise InitError("Packaged specs or skills directory is empty")
        example_stage = stage / "mcp-config-example.json"
        example_stage.write_text(json.dumps(_mcp_example(prepared.config), indent=2) + "\n", encoding="utf-8")

        for kind in ("specs", "skills"):
            target = prepared.workspace / kind
            _check_project_path(prepared.root, target)
            previous[kind] = target.exists()
            if previous[kind]:
                LOGGER.debug("Backing up managed directory: %s", target)
                target.replace(backups / kind)
            LOGGER.debug("Installing %d %s resources into %s", counts[kind], kind, target)
            (stage / kind).replace(target)
            installed.add(kind)

        example_existed = example_path.exists()
        LOGGER.debug("Writing generated MCP example: %s", example_path)
        example_stage.replace(example_path)
        return (
            InitEvent(
                "updated" if previous["specs"] else "created", prepared.workspace / "specs", f"{counts['specs']} files"
            ),
            InitEvent(
                "updated" if previous["skills"] else "created",
                prepared.workspace / "skills",
                f"{counts['skills']} files",
            ),
            InitEvent("updated" if example_existed else "created", example_path),
        )
    except (OSError, InitError) as error:
        LOGGER.error("Template deployment failed for %s: %s", prepared.workspace, error)
        rollback_errors: list[str] = []
        for kind in ("skills", "specs"):
            target = prepared.workspace / kind
            try:
                if kind in installed and target.exists():
                    target.replace(stage / f"discard-{kind}")
                if previous.get(kind) and (backups / kind).exists():
                    (backups / kind).replace(target)
            except OSError as rollback_error:
                rollback_errors.append(f"{target}: {rollback_error}")
        if rollback_errors:
            keep_stage = True
            raise InitError(
                f"Deployment failed and rollback needs attention; backup retained at {stage}: "
                + "; ".join(rollback_errors)
            ) from error
        raise InitError(f"Cannot deploy packaged templates: {error}") from error
    finally:
        if not keep_stage:
            _check_project_path(prepared.root, stage)
            shutil.rmtree(stage)


def initialize_project(
    root: Path,
    diagrams_dir: str | None = None,
    plantuml_server_url: str | None = None,
) -> InitResult:
    """Initialize a user project from bundled defaults without changing user-owned content."""
    LOGGER.debug("Starting initialization: root=%s", root)
    prepared = prepare_project(root, diagrams_dir, plantuml_server_url)
    resource_events = deploy_resources(prepared)
    result = InitResult(prepared.config, prepared.events + resource_events)
    LOGGER.debug("Initialization complete: root=%s, events=%d", prepared.root, len(result.events))
    return result
