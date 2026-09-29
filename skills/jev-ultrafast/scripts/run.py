#!/usr/bin/env python3
"""Run inside the upstream Jev environment; this module is safe to import offline."""
import argparse
import json
import os
import sys
import time
from urllib.parse import urlsplit


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--max-steps", type=int, default=20,
                   help="Maximum prediction cycles, including stale-page retries (1–60)")
    p.add_argument("--allow-operation", action="append", default=[],
                   choices=["CLICK", "TYPE_TEXT", "SELECT"],
                   help="Explicitly enable an operation in addition to scroll/wait/stop")
    p.add_argument("--expect-text", help="Literal text required in the final viewport")
    p.add_argument("--expect-url", help="Exact URL required after completion")
    p.add_argument("--full-text", action="store_true",
                   help="Include rendered body text in the final output; may contain private data")
    return p


def validate(args):
    url = urlsplit(args.url)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
        raise ValueError("Use an HTTP(S) URL without embedded credentials")
    if not args.goal.strip() or not 1 <= args.max_steps <= 60:
        raise ValueError("Supply a nonempty goal and a step limit between 1 and 60")


def verify(page, text=None, url=None):
    checks = {}
    if text is not None:
        checks["text"] = text in page["text"]
    if url is not None:
        checks["url"] = url == page["url"]
    return checks, all(checks.values()) if checks else None


def execute(args, agent_factory, stale_error):
    allowed = {"SCROLL_DOWN", "SCROLL_UP", "WAIT", "DONE", "BLOCKED", *args.allow_operation}
    start = time.perf_counter()
    with agent_factory(args.url, args.goal) as agent:
        setup_ms = round((time.perf_counter() - start) * 1000)
        execution_start = time.perf_counter()
        status, decisions = "budget_exhausted", []
        for _ in range(args.max_steps):
            try:
                state = agent.command("predict")
                decision = state["decision"]
                decisions.append({k: decision.get(k) for k in ("operation", "model", "latency_ms")})
                if decision["operation"] not in allowed:
                    status = "operation_not_allowed"
                    break
                state = agent.command("act", {"fingerprint": state["page"]["fingerprint"]})
                if state["status"] in {"done", "blocked"}:
                    status = state["status"]
                    break
            except stale_error:
                # A fresh prediction is safe only for the upstream explicit stale-read signal.
                agent.state["page"] = agent.browser.observe(screenshot=False)
                continue
        execution_ms = round((time.perf_counter() - execution_start) * 1000)
        observed = agent.browser.observe(screenshot=False)
        checks, verified = verify(observed, args.expect_text, args.expect_url)
        result = dict(status=status, verified=verified, checks=checks, url=observed["url"],
                      title=observed["title"], setup_ms=setup_ms, execution_ms=execution_ms,
                      decisions=decisions)
        if args.full_text:
            result["text"] = agent.browser.evaluate("document.body.innerText")
        return result


def main():
    p = parser()
    args = p.parse_args()
    try:
        validate(args)
    except ValueError as error:
        p.error(str(error))
    if not os.environ.get("TYPESAFE_API_KEY", "").strip():
        p.error("Set TYPESAFE_API_KEY in the runtime .env or environment")
    if "TYPE_TEXT" in args.allow_operation and not os.environ.get("TEXT_MODEL_API_KEY", "").strip():
        p.error("TYPE_TEXT requires TEXT_MODEL_API_KEY")
    try:
        from jev_ultrafast import Agent
        from jev_ultrafast.browser import StalePage
        result = execute(args, Agent, StalePage)
    except Exception as error:
        # Exception strings may contain provider bodies, browser content or credentials.
        print(json.dumps({"status": "error", "error_type": type(error).__name__,
                          "hint": "Check runtime installation, provider settings and browser-harness --doctor. Do not blindly replay actions."}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "done" and result["verified"] is not False else 1


if __name__ == "__main__":
    sys.exit(main())
