import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def write_tree(root: Path, files: dict) -> Path:
    """Create files under root. str values are written as UTF-8, bytes as-is."""
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
    return root


CORPUS = {
    "a.md": "# Alpha Guide\n\nThe quick brown fox jumps over the lazy dog. Fox fox.\n",
    "b.md": "# Beta Notes\nA fox appears once here, with cats and dogs.\n",
    "sub/c.md": "Some intro text\n# Gamma\nNothing about animals here. Just cats.\n",
    "d.MD": "## Not a title\nDelta has no level one heading. Zebra.\n",
    "notes.txt": "fox fox fox fox\n",
    ".hidden/e.md": "# Hidden\nfox fox fox\n",
    ".secret.md": "# Secret\nfox\n",
    "sub/.draft.md": "# Draft\nfox\n",
}


@pytest.fixture
def corpus(tmp_path):
    return write_tree(tmp_path / "corpus", CORPUS)


@pytest.fixture
def run_cli():
    import subprocess
    import sys

    def run(*args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run(
            [sys.executable, "-m", "mdsearch", *map(str, args)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env,
        )

    return run
