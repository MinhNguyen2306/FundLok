import sys
from pathlib import Path

# Ensure the repo root is importable as `app.*` when pytest collects tests/.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
