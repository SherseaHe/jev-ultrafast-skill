# Jev Ultrafast Skill

[English](README.md) | [简体中文](README.zh-CN.md)

A portable Agent Skill for using [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) with Codex and other agents that support SKILL.md. Community wrapper; not affiliated with or endorsed by Browser Use or TypeSafe.

Jev chooses browser operations and targets; Browser Harness controls Chrome. This repository provides agent instructions and a small bounded runner. It does not contain the upstream runtime, model weights, API keys or browser profiles.

## Install the Skill

Install directly from GitHub and select your agent:

```sh
npx skills add SherseaHe/jev-ultrafast-skill --skill jev-ultrafast
```

For a local clone, run `npx skills add . --skill jev-ultrafast` from its root. Add `-g` for a global installation. Alternatively copy `skills/jev-ultrafast` to your agent's documented skills directory (for Codex, `~/.codex/skills/jev-ultrafast`). Preserve an existing custom Skill before replacing it.

Install/configure the separate upstream runtime using [setup instructions](skills/jev-ultrafast/references/setup.md). Set `JEV_ULTRAFAST_HOME` if your checkout is outside `~/.local/share/jev-ultrafast`. Keep the `.env` in the runtime checkout, never in this repository.

## Use

Ask your agent:

> Use $jev-ultrafast to open https://01.me/ and scroll until the article “当所有人都去卷 Coding，我在做什么？” is visible. Verify the title and stop.

The runner defaults to scroll/wait/stop. Enable CLICK, SELECT or TYPE_TEXT only for an authorized task. See [SKILL.md](skills/jev-ultrafast/SKILL.md) for invocation and verification.

## Behavior and limits

- Executes repeated observations and Jev decisions with a 20-cycle default budget.
- Verifies optional expected viewport text and/or exact URL independently of DONE.
- Does not automatically retry unknown execution failures.
- Closes its created tab when the run ends, including errors.
- Reports setup and execution timing separately. No universal speed claims.
- Full-text output is opt-in. Default observations are viewport-scoped; scrolling reads more.
- A coarse operation allowlist is not a security sandbox. Use explicit step-by-step review for consequential actions.
- Inherits upstream limitations for frames, shadow DOM, canvas and other unsupported controls.

API calls incur provider charges. Task page content is transmitted to configured model providers. Test outcomes are specific to the tested site and runtime, not a reliability guarantee.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 skills/jev-ultrafast/scripts/run.py --help
```

Tests are offline and do not access credentials, browser sessions or paid APIs. Runtime reference: upstream commit `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`. Python wrapper requires Python 3.12+ through that runtime.

## License

MIT for this wrapper. The upstream runtime retains its own MIT license and attribution; it is installed separately. No upstream source is vendored.
