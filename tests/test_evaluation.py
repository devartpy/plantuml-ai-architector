"""Regression checks for the optional live-agent evaluation gate."""

from __future__ import annotations

import json
import tempfile
import unittest
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import evaluate_self_correct


class AgentEvaluationTests(unittest.TestCase):
    def test_saved_repair_must_match_submission_and_render_cleanly(self) -> None:
        source = "@startuml\nAlice -> Bob: hello\n@enduml\n"
        with tempfile.TemporaryDirectory() as temporary:
            diagram = Path(temporary) / "repair.puml"
            diagram.write_text(source, encoding="utf-8")
            headers = Message()
            headers["Content-Type"] = "image/svg+xml"
            response = BytesIO(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
            response.headers = headers
            with patch("scripts.evaluate_self_correct.urlopen", return_value=response) as render:
                evaluate_self_correct.verify_saved_diagram(diagram, "http://127.0.0.1:18080", {source})
                self.assertIn("/svg/~h", render.call_args.args[0])
            with self.assertRaisesRegex(AssertionError, "not submitted"):
                evaluate_self_correct.verify_saved_diagram(diagram, "http://127.0.0.1:18080", {"other"})

            error = HTTPError("http://127.0.0.1:18080/svg", 400, "syntax error", headers, None)
            with patch("scripts.evaluate_self_correct.urlopen", side_effect=error):
                with self.assertRaisesRegex(AssertionError, "HTTP 400"):
                    evaluate_self_correct.verify_saved_diagram(diagram, "http://127.0.0.1:18080", {source})

    def test_successful_repair_requires_nonempty_rule_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rules = Path(temporary) / "sequence_rules.md"
            with self.assertRaisesRegex(AssertionError, "did not leave"):
                evaluate_self_correct.verify_rule_file(rules)
            rules.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "incomplete"):
                evaluate_self_correct.verify_rule_file(rules)
            rules.write_text("### Empty rule\n- **Issue:** \n- **Fix Rule:** \n- **Evidence:** \n", encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "incomplete"):
                evaluate_self_correct.verify_rule_file(rules)
            rules.write_text(
                "### Remove invalid line\n- **Issue:** Syntax error\n- **Fix Rule:** Remove invalid text.\n"
                "- **Evidence:** The repaired diagram rendered.\n",
                encoding="utf-8",
            )
            evaluate_self_correct.verify_rule_file(rules)

    def test_skip_is_not_success(self) -> None:
        with patch("sys.argv", ["evaluate_self_correct.py"]):
            self.assertEqual(evaluate_self_correct.main(), 2)

    def test_counts_actual_distinct_renderer_submissions(self) -> None:
        original = "@startuml\nA -> B: hi\n@enduml"
        events = []
        for source in [original, original, "candidate 1", "candidate 1", "candidate 2", "candidate 3", "candidate 4"]:
            events.append(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "mcp_tool_call",
                            "server": "plantuml",
                            "tool": "generate_plantuml_diagram",
                            "arguments": {"plantuml_code": source},
                        },
                    }
                )
            )
        self.assertEqual(evaluate_self_correct.candidate_attempts("\n".join(events), original), 4)
        with self.assertRaisesRegex(AssertionError, "exceeded three"):
            evaluate_self_correct.assert_attempt_budget(4)
        evaluate_self_correct.assert_attempt_budget(3)

    def test_missing_renderer_trace_fails_closed(self) -> None:
        with self.assertRaisesRegex(AssertionError, "no inspectable"):
            evaluate_self_correct.candidate_attempts(json.dumps({"type": "turn.completed"}), "source")

    def test_workspace_detects_unexpected_spec_change(self) -> None:
        before = {"diagram.puml": b"old", ".ai-architect/specs/sequence_spec.md": b"spec"}
        after = {"diagram.puml": b"new", ".ai-architect/specs/sequence_spec.md": b"altered"}
        with self.assertRaisesRegex(AssertionError, "sequence_spec.md"):
            evaluate_self_correct.assert_workspace_changes(before, after, {"diagram.puml"})

    def test_workspace_detects_new_empty_directory(self) -> None:
        with self.assertRaisesRegex(AssertionError, "extra/"):
            evaluate_self_correct.assert_workspace_changes({}, {"extra/": None}, set())


if __name__ == "__main__":
    unittest.main()
