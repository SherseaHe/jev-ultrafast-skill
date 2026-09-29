import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "runner", Path(__file__).resolve().parents[1] / "skills/jev-ultrafast/scripts/run.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class StalePage(Exception):
    pass


class FakeAgent:
    def __init__(self, operations, fail=None):
        self.operations = iter(operations)
        self.fail = fail
        self.browser = self
        self.state = {"page": self.observe()}
        self.actions = []
        self.closed = False
        self.read_full_text = False
        self.predictions = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def observe(self, **_):
        return dict(text="Target article", url="https://example.com/", title="Example", fingerprint="fresh")

    def evaluate(self, expression):
        self.read_full_text = True
        return "Full page content"

    def command(self, name, body=None):
        if name == "predict":
            self.predictions += 1
            self.state["decision"] = {"operation": next(self.operations)}
        elif name == "act":
            assert body == {"fingerprint": "fresh"}
            if self.fail:
                raise self.fail
            operation = self.state["decision"]["operation"]
            self.actions.append(operation)
            self.state["status"] = operation.lower() if operation in {"DONE", "BLOCKED"} else "ready"
        return self.state


class RunnerTests(unittest.TestCase):
    def args(self, *extra):
        return runner.parser().parse_args(["--url", "https://example.com/", "--goal", "Find article", *extra])

    def execute(self, agent, *extra):
        return runner.execute(self.args(*extra), lambda *_: agent, StalePage)

    def test_multiple_steps_and_independent_verification(self):
        agent = FakeAgent(["SCROLL_DOWN", "DONE"])
        result = self.execute(agent, "--expect-text", "Target article")
        self.assertEqual(agent.actions, ["SCROLL_DOWN", "DONE"])
        self.assertTrue(result["verified"])
        self.assertEqual(result["status"], "done")
        self.assertTrue(agent.closed)
        self.assertFalse(agent.read_full_text)

    def test_done_is_not_proof_of_success(self):
        result = self.execute(FakeAgent(["DONE"]), "--expect-text", "Missing article")
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "done")
        self.assertIsNone(self.execute(FakeAgent(["DONE"]))["verified"])

    def test_disallowed_action_never_executes(self):
        agent = FakeAgent(["CLICK"])
        result = self.execute(agent)
        self.assertEqual(result["status"], "operation_not_allowed")
        self.assertEqual(agent.actions, [])
        self.assertTrue(agent.closed)

    def test_explicit_action_permission(self):
        agent = FakeAgent(["CLICK", "DONE"])
        self.execute(agent, "--allow-operation", "CLICK")
        self.assertEqual(agent.actions, ["CLICK", "DONE"])

    def test_step_budget_also_bounds_stale_retries(self):
        for fail in (None, StalePage()):
            agent = FakeAgent(["SCROLL_DOWN"] * 3, fail=fail)
            result = self.execute(agent, "--max-steps", "2")
            self.assertEqual(result["status"], "budget_exhausted")
            self.assertEqual(agent.predictions, 2)
            self.assertTrue(agent.closed)

    def test_unknown_failure_not_replayed(self):
        agent = FakeAgent(["CLICK", "CLICK"], fail=RuntimeError("uncertain outcome"))
        with self.assertRaises(RuntimeError):
            self.execute(agent, "--allow-operation", "CLICK")
        self.assertEqual(agent.predictions, 1)
        self.assertTrue(agent.closed)

    def test_full_text_only_when_requested(self):
        agent = FakeAgent(["DONE"])
        result = self.execute(agent, "--full-text")
        self.assertEqual(result["text"], "Full page content")
        self.assertTrue(agent.read_full_text)

    def test_input_constraints(self):
        runner.validate(self.args())
        for url in ("file:///etc/passwd", "https://user:pass@example.com", "https://"):
            args = self.args()
            args.url = url
            with self.assertRaises(ValueError):
                runner.validate(args)
        with self.assertRaises(ValueError):
            runner.validate(self.args("--max-steps", "0"))


if __name__ == "__main__":
    unittest.main()
