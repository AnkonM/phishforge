"""Entry point so `python -m phishforge` works."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from phishforge.cli import main
except ImportError:
    from cli import main

if __name__ == "__main__":
    main()
