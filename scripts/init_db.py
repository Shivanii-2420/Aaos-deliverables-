from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend.app.database.init_db import create_tables


if __name__ == "__main__":
    create_tables()
    print("AAOS tables created if missing; existing tables were not dropped.")
