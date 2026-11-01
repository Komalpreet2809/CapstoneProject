import json
import logging
import sys

import pytest

from voiceserve_common.logs import JsonFormatter, configure_logging
from voiceserve_common.masking import MASK, REDACTED


def _format(record: logging.LogRecord) -> dict[str, object]:
    out: dict[str, object] = json.loads(JsonFormatter("test_service").format(record))
    return out


def _record(msg: str, *args: object, **extra: object) -> logging.LogRecord:
    record = logging.LogRecord("voiceserve.test", logging.INFO, __file__, 1, msg, args, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_shape() -> None:
    out = _format(_record("hello %s", "world"))
    assert out["msg"] == "hello world"
    assert out["level"] == "INFO"
    assert out["service"] == "test_service"
    assert out["logger"] == "voiceserve.test"
    assert isinstance(out["ts"], str)


def test_message_and_args_are_masked() -> None:
    out = _format(_record("GET /fees?student_id=%s", "12215678"))
    assert out["msg"] == f"GET /fees?student_id={MASK}78"


def test_extra_fields_are_masked() -> None:
    out = _format(_record("turn", student_id="DEMO001", otp="482913", call_id="c-1"))
    assert out["student_id"] == f"{MASK}01"
    assert out["otp"] == REDACTED
    assert out["call_id"] == "c-1"


def test_extra_cannot_overwrite_base_fields() -> None:
    out = _format(_record("real message", service="spoofed"))
    assert out["service"] == "test_service"


def test_exceptions_are_masked() -> None:
    try:
        raise ValueError("bad phone 9876543210")
    except ValueError:
        record = logging.LogRecord(
            "voiceserve.test", logging.ERROR, __file__, 1, "boom", None, sys.exc_info()
        )
    out = _format(record)
    assert "9876543210" not in str(out["exc"])
    assert f"{MASK}10" in str(out["exc"])


def test_configure_logging_routes_uvicorn_through_masker(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("svc", "INFO")
    logging.getLogger("uvicorn.access").info('"GET /attendance?student_id=12215678" 200')
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert json.loads(line)["msg"] == f'"GET /attendance?student_id={MASK}78" 200'
