#!/usr/bin/env python3
"""Native CX review binding CLI; see --help."""
import os
import sys
from pathlib import Path
sys.dont_write_bytecode = True

def hooks_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = []
    if len(here.parents) >= 4:
        candidates.append(here.parents[3] / 'hooks')
    env_home = os.environ.get('CODEX_HOME')
    if env_home:
        candidates.append(Path(env_home) / 'hooks')
    candidates.append(Path.home() / '.codex' / 'hooks')
    for directory in candidates:
        if (directory / '_review_binding.py').is_file():
            return directory
    raise SystemExit('review binding hooks not found; expected package hooks or ~/.codex/hooks')

sys.path.insert(0, str(hooks_dir()))
from _review_binding import main
if __name__ == '__main__':
    raise SystemExit(main())
