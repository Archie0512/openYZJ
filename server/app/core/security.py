"""云之家签名计算与验证模块。

支持双算法路径：先 SHA256 再 SHA1，任一通过即合法。
参考文档第 3.2 节（HmacSHA256）与第 7 章（测试签名疑似 SHA1）。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from typing import Optional, Tuple

log = logging.getLogger(__name__)

ALGOS = {
    "sha256": hashlib.sha256,
    "sha1": hashlib.sha1,
}


def calc_sign(
    secret: str,
    robot_id: str,
    robot_name: str,
    operator_openid: str,
    operator_name: str,
    time_str: str,
    msg_id: str,
    content: str,
    algo: str = "sha256",
) -> str:
    """根据指定算法计算 HMAC 签名并返回 Base64 编码字符串。

    拼接顺序：robotId,robotName,operatorOpenid,operatorName,time,msgId,content
    """
    summary = ",".join([
        robot_id, robot_name, operator_openid,
        operator_name, time_str, msg_id, content,
    ])
    digest = hmac.new(
        secret.encode("utf-8"),
        summary.encode("utf-8"),
        ALGOS[algo],
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _normalize(s: str) -> str:
    """容错 Base64 末尾 = padding 缺失的情况。"""
    return s.rstrip("=")


def verify_sign(
    secret: str,
    robot_id: str,
    robot_name: str,
    operator_openid: str,
    operator_name: str,
    time_str: str,
    msg_id: str,
    content: str,
    sign_header: str,
) -> Tuple[bool, Optional[str]]:
    """先尝试 SHA256，再尝试 SHA1。任一通过即合法。

    Returns:
        (True, 'sha256'|'sha1') 或 (False, None)
    """
    expected_norm = _normalize(sign_header)
    for algo in ("sha256", "sha1"):
        actual = calc_sign(
            secret, robot_id, robot_name, operator_openid,
            operator_name, time_str, msg_id, content, algo=algo,
        )
        if hmac.compare_digest(_normalize(actual), expected_norm):
            log.info("签名命中算法: %s", algo)
            return True, algo
    return False, None
