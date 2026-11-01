"""The API contract: the OpenAPI document the app generates, frozen at docs/api/openapi.json.

`python -m mini_ums_api.contract <path>` (or `make openapi`) rewrites the frozen file after a
deliberate API change; tests fail whenever the app drifts from it.
"""

import json
import sys
from pathlib import Path
from typing import Any

from mini_ums_api.main import create_app
from mini_ums_api.settings import Settings


def openapi_document() -> dict[str, Any]:
    # Generating the schema never touches the database; the lifespan doesn't run.
    app = create_app(Settings(database_url="postgresql://contract@127.0.0.1:1/none"), checks={})
    return app.openapi()


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python -m mini_ums_api.contract <output.json>")
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(openapi_document()), encoding="utf-8", newline="\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
