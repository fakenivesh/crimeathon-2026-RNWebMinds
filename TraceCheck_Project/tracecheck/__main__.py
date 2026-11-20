from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .config import PROJECT_ROOT
from .db import database, initialize
from .demo_data import seed_demo
from .service import analyze_database


def main() -> None:
    parser = argparse.ArgumentParser(prog="tracecheck", description="TraceCheck local investigation application")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="Load the bundled example dataset")
    sub.add_parser("analyze", help="Run correlation and detection rules")
    serve = sub.add_parser("serve", help="Start the Streamlit application")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()

    if args.command == "seed":
        print(seed_demo())
    elif args.command == "analyze":
        initialize()
        with database() as conn:
            print(analyze_database(conn))
    elif args.command == "serve":
        app_file = PROJECT_ROOT / "app.py"
        command = [
            sys.executable, "-m", "streamlit", "run", str(app_file),
            "--server.address", args.host,
            "--server.port", str(args.port),
        ]
        raise SystemExit(subprocess.call(command, cwd=PROJECT_ROOT))


if __name__ == "__main__":
    main()
