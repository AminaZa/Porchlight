"""Porchlight.

Loading ``.env`` happens here, on package import, and that is deliberate rather
than lazy. Every entry point — ``demo/run_demo.py``, ``python -m src.intake.cli``,
``python -m src.provider --list``, and the tests — imports something from this
package before it reads a single environment variable, so this is the one place
that covers all of them.

Without it, the README's instruction to put your verified Bedrock inference
profile ids in ``.env`` silently does nothing: the values sit in a file nobody
reads while ``provider.py`` falls back to its unverified defaults, and the run
fails at the first model call with an error that looks like bad credentials.

``override=False`` is the default and is what we want — a variable already set
in the shell beats the file, so ``FNA_DB_PATH=/tmp/x python demo/run_demo.py``
and pytest's ``monkeypatch.setenv`` both still work.
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_env() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        # A missing optional dependency should not stop the package importing;
        # say so once, clearly, because the symptom otherwise is a confusing
        # model-id failure much later.
        if os.environ.get("FNA_QUIET_ENV") != "1":
            print(
                "warning: .env exists but python-dotenv is not installed, so it "
                "is being ignored.\n         pip install -r requirements.txt"
            )
        return
    load_dotenv(env_file)


_load_env()
