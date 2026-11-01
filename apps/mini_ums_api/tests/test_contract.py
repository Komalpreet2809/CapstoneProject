"""M2 freezes the API: the app must match the committed OpenAPI document exactly."""

import json
from pathlib import Path

from mini_ums_api.contract import openapi_document

CONTRACT = Path(__file__).resolve().parents[3] / "docs" / "api" / "openapi.json"


def _endpoints(document: dict[str, object]) -> set[str]:
    paths = document["paths"]
    assert isinstance(paths, dict)
    return {f"{method.upper()} {path}" for path, ops in paths.items() for method in ops}


def test_app_matches_frozen_contract() -> None:
    frozen = json.loads(CONTRACT.read_text(encoding="utf-8"))
    current = openapi_document()
    added = _endpoints(current) - _endpoints(frozen)
    removed = _endpoints(frozen) - _endpoints(current)
    assert not added and not removed, f"endpoints added {added}, removed {removed}"
    assert current == frozen, (
        "The API no longer matches docs/api/openapi.json. If the change is deliberate, "
        "review it and run `make openapi`."
    )


def test_contract_keeps_identity_out_of_requests() -> None:
    # Rule 1 at the contract level: no personal route accepts a student identifier.
    document = openapi_document()
    for path, ops in document["paths"].items():
        if not path.startswith("/me"):
            continue
        for op in ops.values():
            names = {p["name"] for p in op.get("parameters", [])}
            assert not names & {"student_id", "reg_no"}, f"{path} takes a student identifier"
