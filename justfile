default: check

# Keep the development environment outside the checkout and cloud-synced folders.
check-env := env_var_or_default("UV_PROJECT_ENVIRONMENT", home_directory() + "/.cache/dss-agent-skills/venv")

check: portability validate test

portability:
    python3 scripts/check-self-contained.py . --plugin .claude-plugin/plugin.json --check-metadata --check-public-source

validate:
    #!/usr/bin/env bash
    set -euo pipefail
    for skill in */SKILL.md; do
        UV_PROJECT_ENVIRONMENT="{{check-env}}" uv run --locked agentskills validate "$(dirname "$skill")"
    done

test:
    python3 -B -m unittest discover -s tests -v

# Generate pages before Quarto resolves the sidebar on a fresh checkout.
site:
    python3 scripts/build-catalogue.py
    quarto render
    python3 -B scripts/check-site.py

preview port="8791":
    python3 scripts/build-catalogue.py
    quarto preview --host 127.0.0.1 --port {{port}} --no-browser
