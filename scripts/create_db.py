from pathlib import Path
from dotenv import load_dotenv
import sys

# Ensure environment variables from the project .env are loaded before
# importing backend modules that instantiate pydantic Settings.
root = Path(__file__).resolve().parent.parent
# Try project root .env first, then backend/.env as a fallback
env_paths = [root / ".env", root / "backend" / ".env"]
for p in env_paths:
    if p.exists():
        load_dotenv(dotenv_path=p, override=True)
        break

# Ensure project root is on sys.path so `backend` package is importable
sys.path.insert(0, str(root))

from backend.app.database.init_db import reset_database


if __name__ == "__main__":
    reset_database()
    print("AAOS database reset and created successfully.")