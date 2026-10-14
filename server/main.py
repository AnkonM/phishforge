"""server/main.py -- uvicorn entrypoint. Run with: python -m server.main"""

from __future__ import annotations

import uvicorn

from server.config import HOST, PORT


def main() -> None:
    uvicorn.run("server.app:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
