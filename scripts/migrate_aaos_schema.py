from pathlib import Path
import sys

from alembic import command
from alembic.config import Config

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    config = Config(str(project_root / "alembic.ini"))
    command.upgrade(config, "head")
    print("AAOS versioned schema migration completed without dropping existing data.")
