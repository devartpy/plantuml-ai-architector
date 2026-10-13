"""Behavioral checks for the project initialization command."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib import resources
from pathlib import Path
from unittest import mock

from ai_architect.core import REQUIRED_SKILL_FILES, REQUIRED_SPEC_FILES, InitError, initialize_project


class InitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _workspace(self) -> Path:
        return self.root / ".ai-architect"

    def _config(self) -> dict[str, object]:
        return json.loads((self._workspace() / "config.json").read_text(encoding="utf-8"))

    def _example(self) -> dict[str, object]:
        return json.loads((self._workspace() / "mcp-config-example.json").read_text(encoding="utf-8"))

    def test_defaults_copy_all_package_resources(self) -> None:
        result = initialize_project(self.root)
        self.assertEqual(result.config.diagrams_dir, "docs/architecture/diagrams")
        self.assertEqual(result.config.plantuml_server_url, "https://www.plantuml.com/plantuml")
        self.assertEqual(self._config()["schema_version"], 1)
        self.assertTrue((self.root / "docs/architecture/diagrams").is_dir())
        self.assertEqual(list((self._workspace() / "references").iterdir()), [])
        writable_probe = self._workspace() / "references" / "write-probe.md"
        writable_probe.write_text("writable", encoding="utf-8")
        self.assertEqual(writable_probe.read_text(encoding="utf-8"), "writable")
        writable_probe.unlink()

        source = resources.files("ai_architect.templates")
        for relative in (
            "specs/README.md",
            "specs/workflow_matrix.md",
            "specs/c4_container_spec.md",
            "skills/README.md",
            "skills/plantuml-create/SKILL.md",
            "skills/plantuml-modify/SKILL.md",
            "skills/plantuml-verify/SKILL.md",
            "skills/self-correct/SKILL.md",
        ):
            with self.subTest(relative=relative):
                self.assertEqual(
                    (self._workspace() / relative).read_bytes(),
                    source.joinpath(*relative.split("/")).read_bytes(),
                )
        server = self._example()["mcpServers"]["plantuml"]
        self.assertEqual(server["args"], ["-y", "plantuml-mcp-server@0.2.4"])
        self.assertEqual(server["env"]["PLANTUML_SERVER_URL"], result.config.plantuml_server_url)

    def test_every_manifest_resource_is_installed_byte_for_byte(self) -> None:
        initialize_project(self.root)
        source = resources.files("ai_architect.templates")
        for kind, names in (("specs", REQUIRED_SPEC_FILES), ("skills", REQUIRED_SKILL_FILES)):
            for name in names:
                with self.subTest(resource=f"{kind}/{name}"):
                    parts = name.split("/")
                    original = source.joinpath(kind, *parts)
                    installed = self._workspace().joinpath(kind, *parts)
                    self.assertTrue(original.is_file())
                    self.assertEqual(installed.read_bytes(), original.read_bytes())

    def test_missing_manifest_resource_does_not_replace_managed_copies(self) -> None:
        initialize_project(self.root)
        managed_spec = self._workspace() / "specs" / "README.md"
        managed_skill = self._workspace() / "skills" / "plantuml-create" / "SKILL.md"
        managed_spec.write_text("user copy", encoding="utf-8")
        managed_skill.write_text("user copy", encoding="utf-8")
        source = Path(str(resources.files("ai_architect.templates")))

        for kind, names in (("specs", REQUIRED_SPEC_FILES), ("skills", REQUIRED_SKILL_FILES)):
            for name in names:
                with self.subTest(resource=f"{kind}/{name}"), tempfile.TemporaryDirectory() as temporary:
                    package_copy = Path(temporary)
                    shutil.copytree(source / "specs", package_copy / "specs")
                    shutil.copytree(source / "skills", package_copy / "skills")
                    package_copy.joinpath(kind, *name.split("/")).unlink()
                    with mock.patch("ai_architect.core.resources.files", return_value=package_copy):
                        with self.assertRaisesRegex(InitError, "Missing packaged"):
                            initialize_project(self.root)
                    self.assertEqual(managed_spec.read_text(encoding="utf-8"), "user copy")
                    self.assertEqual(managed_skill.read_text(encoding="utf-8"), "user copy")
                    self.assertFalse(any(path.name.startswith(".init-stage-") for path in self._workspace().iterdir()))

    def test_custom_path_and_intranet_renderer(self) -> None:
        initialize_project(
            self.root,
            diagrams_dir="docs/arch/views",
            plantuml_server_url="https://plantuml.intranet.example/plantuml/",
        )
        self.assertTrue((self.root / "docs/arch/views").is_dir())
        self.assertEqual(self._config()["diagrams_dir"], "docs/arch/views")
        self.assertEqual(self._config()["plantuml_server_url"], "https://plantuml.intranet.example/plantuml")
        self.assertEqual(
            self._example()["mcpServers"]["plantuml"]["env"]["PLANTUML_SERVER_URL"],
            "https://plantuml.intranet.example/plantuml",
        )

    def test_deployed_skills_have_matching_specs_and_configured_output_directory(self) -> None:
        initialize_project(self.root, diagrams_dir="docs/system/views")
        workspace = self._workspace()
        spec_names = (
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
        for skill_name in ("plantuml-create", "plantuml-modify", "plantuml-verify", "self-correct"):
            with self.subTest(skill=skill_name):
                skill_dir = workspace / "skills" / skill_name
                self.assertTrue((skill_dir / "SKILL.md").is_file(), skill_dir)
                relative_specs = (skill_dir / "../../specs").resolve()
                self.assertEqual(relative_specs, workspace / "specs")
                for spec_name in spec_names:
                    self.assertTrue((relative_specs / spec_name).is_file(), relative_specs / spec_name)

        configured_directory = self.root / str(self._config()["diagrams_dir"])
        self.assertEqual(configured_directory, self.root / "docs/system/views")
        self.assertTrue(configured_directory.is_dir(), configured_directory)

    def test_repeat_refreshes_managed_resources_but_preserves_user_data_and_config(self) -> None:
        initialize_project(self.root)
        workspace = self._workspace()
        original_config = (workspace / "config.json").read_bytes()
        original_mtime = (workspace / "config.json").stat().st_mtime_ns
        learned_rule = workspace / "references" / "sequence_rules.md"
        learned_rule.write_text("### Close groups\n- **Fix Rule:** Close each group.\n", encoding="utf-8")
        diagram = self.root / "docs/architecture/diagrams/current.puml"
        diagram.write_text("@startuml\n@enduml\n", encoding="utf-8")
        (workspace / "specs" / "stale.md").write_text("remove", encoding="utf-8")
        (workspace / "skills" / "plantuml-create" / "SKILL.md").write_text("old", encoding="utf-8")

        result = initialize_project(self.root)
        self.assertEqual((workspace / "config.json").read_bytes(), original_config)
        self.assertEqual((workspace / "config.json").stat().st_mtime_ns, original_mtime)
        self.assertEqual(
            learned_rule.read_text(encoding="utf-8"), "### Close groups\n- **Fix Rule:** Close each group.\n"
        )
        self.assertEqual(diagram.read_text(encoding="utf-8"), "@startuml\n@enduml\n")
        self.assertFalse((workspace / "specs" / "stale.md").exists())
        self.assertTrue((workspace / "skills" / "self-correct" / "SKILL.md").is_file())
        self.assertFalse((workspace / "skills" / "self-correction").exists())
        self.assertNotEqual((workspace / "skills" / "plantuml-create" / "SKILL.md").read_text(), "old")
        self.assertEqual([event.action for event in result.events[-3:]], ["updated", "updated", "updated"])

    def test_valid_manual_setting_change_refreshes_example_and_creates_new_directory(self) -> None:
        initialize_project(self.root)
        path = self._workspace() / "config.json"
        data = self._config()
        data["diagrams_dir"] = "architecture/diagrams"
        data["plantuml_server_url"] = "http://127.0.0.1:18080"
        path.write_text(json.dumps(data), encoding="utf-8")
        edited = path.read_bytes()

        initialize_project(self.root)
        self.assertEqual(path.read_bytes(), edited)
        self.assertTrue((self.root / "architecture/diagrams").is_dir())
        self.assertEqual(
            self._example()["mcpServers"]["plantuml"]["env"]["PLANTUML_SERVER_URL"],
            "http://127.0.0.1:18080",
        )

    def test_conflicting_options_and_invalid_config_do_not_refresh_resources(self) -> None:
        initialize_project(self.root)
        old_skill = self._workspace() / "skills" / "plantuml-create" / "SKILL.md"
        old_skill.write_text("old", encoding="utf-8")
        with self.assertRaisesRegex(InitError, "conflicts"):
            initialize_project(self.root, diagrams_dir="different/path")
        self.assertEqual(old_skill.read_text(encoding="utf-8"), "old")

        (self._workspace() / "config.json").write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(InitError, "valid JSON"):
            initialize_project(self.root)
        self.assertEqual(old_skill.read_text(encoding="utf-8"), "old")

    def test_invalid_paths_urls_and_directory_collisions(self) -> None:
        for value in (
            "../outside",
            ".ai-architect/specs",
            ".AI-ARCHITECT/specs",
            str(self.root / "absolute"),
            "C:\\outside",
        ):
            with self.subTest(diagrams_dir=value), self.assertRaises(InitError):
                initialize_project(self.root, diagrams_dir=value)
        for value in ("ftp://host", "http://host:bad", "http://user:pass@host", "http://host/?key=x"):
            with self.subTest(url=value), self.assertRaises(InitError):
                initialize_project(self.root, plantuml_server_url=value)
        self.assertFalse(self._workspace().exists())

        (self.root / ".ai-architect").write_text("file", encoding="utf-8")
        with self.assertRaisesRegex(InitError, "directory"):
            initialize_project(self.root)

    def test_configured_diagram_path_cannot_alias_managed_workspace(self) -> None:
        initialize_project(self.root)
        path = self._workspace() / "config.json"
        data = self._config()
        data["diagrams_dir"] = ".AI-ARCHITECT/specs"
        path.write_text(json.dumps(data), encoding="utf-8")
        user_diagram = self._workspace() / "specs" / "user.puml"
        user_diagram.write_text("@startuml\n@enduml\n", encoding="utf-8")

        with self.assertRaisesRegex(InitError, "outside .ai-architect"):
            initialize_project(self.root)

        self.assertTrue(user_diagram.is_file())

    def test_reparse_or_symlink_destination_is_rejected(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        workspace = self._workspace()
        workspace.mkdir()
        link = workspace / "specs"
        try:
            os.symlink(outside, link, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            if os.name != "nt":
                self.skipTest(f"Symlinks unavailable: {error}")
            created = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                self.skipTest(f"Symlinks and junctions unavailable: {error}")
        with self.assertRaisesRegex(InitError, "symlink|reparse"):
            initialize_project(self.root)
        self.assertEqual(list(outside.iterdir()), [])

    def test_copy_failure_restores_previous_managed_directories(self) -> None:
        initialize_project(self.root)
        workspace = self._workspace()
        old_spec = workspace / "specs" / "custom.md"
        old_skill = workspace / "skills" / "custom.md"
        old_spec.write_text("old spec", encoding="utf-8")
        old_skill.write_text("old skill", encoding="utf-8")
        actual_replace = Path.replace

        def fail_install(path: Path, target: Path) -> Path:
            if path.name == "skills" and path.parent.name.startswith(".init-stage-"):
                raise OSError("simulated install failure")
            return actual_replace(path, target)

        with mock.patch.object(Path, "replace", fail_install), self.assertRaisesRegex(InitError, "simulated"):
            initialize_project(self.root)

        self.assertEqual(old_spec.read_text(encoding="utf-8"), "old spec")
        self.assertEqual(old_skill.read_text(encoding="utf-8"), "old skill")
        self.assertFalse(any(path.name.startswith(".init-stage-") for path in workspace.iterdir()))

    def test_cli_output_and_error_status(self) -> None:
        success = subprocess.run(
            [sys.executable, "-m", "ai_architect.cli", "init"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertIn("CREATED", success.stdout)
        self.assertIn("mcp-config-example.json", success.stdout)
        self.assertNotIn("\x1b[", success.stdout)
        failure = subprocess.run(
            [sys.executable, "-m", "ai_architect.cli", "init", "--diagrams-dir", "../outside"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(failure.returncode, 1)
        self.assertIn("ERROR", failure.stderr)
        self.assertNotIn("\x1b[", failure.stderr)
        invalid_option = subprocess.run(
            [sys.executable, "-m", "ai_architect.cli", "init", "--unknown"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(invalid_option.returncode, 1)
        self.assertIn("ERROR unrecognized arguments", invalid_option.stderr)

    def test_cli_help_and_custom_options(self) -> None:
        for arguments, expected in ((["--help"], "init"), (["init", "--help"], "--plantuml-server-url")):
            with self.subTest(arguments=arguments):
                completed = subprocess.run(
                    [sys.executable, "-m", "ai_architect.cli", *arguments],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn(expected, completed.stdout)
                self.assertEqual(completed.stderr, "")
                self.assertFalse(self._workspace().exists())

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "ai_architect.cli",
                "init",
                "--diagrams-dir",
                "docs/system/views",
                "--plantuml-server-url",
                "http://127.0.0.1:18080/",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((self.root / "docs/system/views").is_dir())
        self.assertEqual(self._config()["diagrams_dir"], "docs/system/views")
        self.assertEqual(self._config()["plantuml_server_url"], "http://127.0.0.1:18080")
        self.assertIn("NEXT Add .ai-architect/mcp-config-example.json", completed.stdout)

    def test_invalid_config_schema_and_missing_field_preserve_managed_resources(self) -> None:
        initialize_project(self.root)
        managed = self._workspace() / "specs" / "README.md"
        before = managed.read_bytes()
        path = self._workspace() / "config.json"
        for payload, fragment in (
            ({"schema_version": 2}, "Unsupported schema_version"),
            ({"schema_version": 1, "diagrams_dir": "views"}, "Missing config field"),
            ({"schema_version": True}, "Invalid config schema"),
        ):
            with self.subTest(payload=payload):
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(InitError, fragment):
                    initialize_project(self.root)
                self.assertEqual(managed.read_bytes(), before)

    def test_existing_file_collisions_leave_user_files_intact(self) -> None:
        for relative in (".ai-architect/references", "docs/architecture/diagrams", ".ai-architect/specs"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                collision = root / relative
                collision.parent.mkdir(parents=True, exist_ok=True)
                collision.write_text("user data", encoding="utf-8")
                with self.assertRaises(InitError):
                    initialize_project(root)
                self.assertEqual(collision.read_text(encoding="utf-8"), "user data")


if __name__ == "__main__":
    unittest.main()
