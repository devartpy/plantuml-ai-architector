"""Regression checks for the optional live-agent evaluation gate."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from scripts import evaluate_self_correct


class AgentEvaluationTests(unittest.TestCase):
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
