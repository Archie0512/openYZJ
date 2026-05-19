"""storage 模块轻量测试：验证 model_dump 字段完整性与 Pydantic 校验。

不依赖真实 MongoDB 连接，仅校验数据结构层面。
"""
from __future__ import annotations

import sys
import os

# 让测试能 import app 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone

from app.models.message import MessageDoc
from app.models.session import SessionDoc
from app.models.command_log import CommandLogDoc, ApiCallLog


# ── 公共 payload fixture ──────────────────────────
SAMPLE_PAYLOAD = {
    "type": 2,
    "robotId": "test-robotId",
    "robotName": "test-robotName",
    "operatorOpenid": "test-userId",
    "operatorName": "test-userName",
    "time": 1599727083000,
    "msgId": "test-msgId-001",
    "content": "你好，你能做什么呢?",
}


def test_message_doc_fields():
    """MessageDoc model_dump 包含所有必要字段。"""
    doc = MessageDoc(
        robot_code="demo",
        robotId=SAMPLE_PAYLOAD["robotId"],
        robotName=SAMPLE_PAYLOAD["robotName"],
        operatorOpenid=SAMPLE_PAYLOAD["operatorOpenid"],
        operatorName=SAMPLE_PAYLOAD["operatorName"],
        msgId=SAMPLE_PAYLOAD["msgId"],
        content=SAMPLE_PAYLOAD["content"],
        type=SAMPLE_PAYLOAD["type"],
        time=SAMPLE_PAYLOAD["time"],
        sessionId="sess-001",
        sign_algo="sha256",
        is_test=True,
        raw_payload=SAMPLE_PAYLOAD,
    )
    d = doc.model_dump()
    assert d["robot_code"] == "demo"
    assert d["is_test"] is True
    assert d["sign_algo"] == "sha256"
    assert d["sessionId"] == "sess-001"
    assert d["msgId"] == "test-msgId-001"
    assert isinstance(d["received_at"], datetime)
    assert d["raw_payload"] == SAMPLE_PAYLOAD


def test_message_doc_defaults():
    """可选字段默认值正确。"""
    doc = MessageDoc(
        robot_code="demo",
        robotId="r", robotName="rn",
        operatorOpenid="o", operatorName="on",
        msgId="m", content="c", type=2, time=0,
        sessionId="s",
    )
    assert doc.is_test is False
    assert doc.sign_algo is None
    assert isinstance(doc.received_at, datetime)
    assert doc.raw_payload == {}


def test_session_doc_fields():
    """SessionDoc model_dump 包含会话管理必要字段。"""
    doc = SessionDoc(
        sessionId="sess-002",
        robot_code="demo",
        robotId="test-robotId",
        operatorOpenid="test-userId",
        operatorName="test-userName",
        last_msgId="msg-1",
        last_content="hello",
        message_count=3,
    )
    d = doc.model_dump()
    assert d["sessionId"] == "sess-002"
    assert d["message_count"] == 3
    assert isinstance(d["created_at"], datetime)
    assert isinstance(d["updated_at"], datetime)
    assert d["context"] == {}


def test_command_log_doc_fields():
    """CommandLogDoc 和 ApiCallLog 字段正确。"""
    api_call = ApiCallLog(url="https://example.com/api", status_code=200, cost_ms=42)
    doc = CommandLogDoc(
        msgId="msg-1",
        robotId="r",
        sessionId="s",
        command="echo",
        handler="echo_handler",
        status="success",
        request_content="hello",
        response_content="echo: hello",
        external_api_calls=[api_call],
        cost_ms=55,
    )
    d = doc.model_dump()
    assert d["command"] == "echo"
    assert d["status"] == "success"
    assert len(d["external_api_calls"]) == 1
    assert d["external_api_calls"][0]["status_code"] == 200
    assert isinstance(d["created_at"], datetime)


if __name__ == "__main__":
    tests = [
        test_message_doc_fields,
        test_message_doc_defaults,
        test_session_doc_fields,
        test_command_log_doc_fields,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL: {t.__name__} - {e}")
            failed += 1
    print(f"\n{'All tests passed!' if not failed else f'{failed} test(s) failed.'}")
    sys.exit(failed)
