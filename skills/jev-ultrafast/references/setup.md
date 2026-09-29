# Runtime setup

Prerequisites: Git, uv, Python 3.12+ (uv can provision it), and a supported local Chrome installation. This wrapper has been exercised on macOS with Chrome; other platforms are not validated here.

Install the upstream runtime separately, pinned to the revision this wrapper was checked against:

```sh
JEV_RUNTIME="${JEV_ULTRAFAST_HOME:-$HOME/.local/share/jev-ultrafast}"
git clone https://github.com/browser-use/jev-ultrafast.git "$JEV_RUNTIME"
cd "$JEV_RUNTIME"
git checkout 1231850a0bf1a0c0341fe408ef1668dbbfdfac46
uv sync --locked --python 3.12
cp .env.example .env
chmod 600 .env
```

Do not clone over an existing directory or overwrite an existing `.env`. For an existing runtime, verify its location and version first; do not reset local changes. This wrapper is not vendoring upstream code or credentials.

Edit `.env` locally:

```dotenv
TYPESAFE_API_KEY=
TYPESAFE_MODEL=jev-latest
TEXT_MODEL_API_KEY=
TEXT_MODEL_BASE_URL=https://openrouter.ai/api/v1
TEXT_MODEL=inception/mercury-2.5
TEXT_MODEL_REASONING=none
```

Get the Jev key from https://console.typesafe.ai/keys. The text-helper example requires a separate OpenRouter key. Text generation is only needed for TYPE_TEXT. Model names and availability may change; use the chosen provider's current documentation. Credentials are sent to the configured providers; observed task page content is sent to TypeSafe and text-helper context to the text provider when needed. Chrome uses the user's logged-in profile.

In Chrome open `chrome://inspect/#remote-debugging`, enable debugging and approve its connection prompt. Diagnose with `uv run browser-harness --doctor`. Local Chrome does not require Browser Use Cloud login. Official connection guide: https://github.com/browser-use/browser-harness/blob/main/install.md.

For the upstream inspector, run `uv run jev` from the runtime directory and open http://127.0.0.1:8766. The Skill runner does not require this inspector server.
