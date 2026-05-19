#!/usr/bin/env python3
"""生成云之家测试签名及可直接执行的 curl 命令。

使用文档第 7 章固定测试参数，输出 SHA256 与 SHA1 两种签名。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys


# ── 第7章固定测试参数 ────────────────────────────
TEST_PARAMS = {
    "robotId": "test-robotId",
    "robotName": "test-robotName",
    "operatorOpenid": "test-userId",
    "operatorName": "test-userName",
    "time": 1599727083000,
    "msgId": "test-msgId",
    "content": "你好，你能做什么呢?",
}
TEST_SECRET = "test-secret"
SESSION_ID = "test-session-001"


def calc_sign(secret: str, params: dict, algo: str = "sha256") -> str:
    """计算 HMAC 签名。"""
    fields = [
        params["robotId"],
        params["robotName"],
        params["operatorOpenid"],
        params["operatorName"],
        str(params["time"]),
        params["msgId"],
        params["content"],
    ]
    summary = ",".join(fields)
    hash_func = hashlib.sha256 if algo == "sha256" else hashlib.sha1
    digest = hmac.new(
        secret.encode("utf-8"),
        summary.encode("utf-8"),
        hash_func,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def main():
    parser = argparse.ArgumentParser(description="生成云之家测试签名和 curl 命令")
    parser.add_argument("--domain", default="https://kimpi.cn", help="目标域名")
    parser.add_argument("--robot-code", default="test", help="URL 路径中的 robot_code")
    parser.add_argument("--algo", default="sha256", choices=["sha256", "sha1"], help="curl 命令使用的签名算法")
    args = parser.parse_args()

    # 计算两种签名
    sign_sha256 = calc_sign(TEST_SECRET, TEST_PARAMS, "sha256")
    sign_sha1 = calc_sign(TEST_SECRET, TEST_PARAMS, "sha1")

    print("=" * 60)
    print("云之家机器人测试签名生成工具")
    print("=" * 60)
    print(f"\n拼接字符串: {','.join([TEST_PARAMS['robotId'], TEST_PARAMS['robotName'], TEST_PARAMS['operatorOpenid'], TEST_PARAMS['operatorName'], str(TEST_PARAMS['time']), TEST_PARAMS['msgId'], TEST_PARAMS['content']])}")
    print(f"\n密钥: {TEST_SECRET}")
    print(f"\nSHA256 签名: {sign_sha256}")
    print(f"SHA1   签名: {sign_sha1}")
    print(f"\n文档第7章期望签名: jy/WTAtltv5UVQVDOb0f4H4JPqw=")
    print(f"SHA1 匹配文档期望: {'✓ 匹配' if sign_sha1 == 'jy/WTAtltv5UVQVDOb0f4H4JPqw=' else '✗ 不匹配'}")

    # 选定 curl 使用的签名
    sign_for_curl = sign_sha256 if args.algo == "sha256" else sign_sha1

    body = json.dumps({"type": 2, **TEST_PARAMS}, ensure_ascii=False)
    url = f"{args.domain}/api/yunzhijia/webhook/{args.robot_code}"

    print(f"\n{'=' * 60}")
    print(f"curl 命令（使用 {args.algo.upper()} 签名）：")
    print(f"{'=' * 60}\n")
    curl_cmd = (
        f'curl -X POST "{url}" \\\n'
        f'  -H "Content-Type: application/json; charset=utf-8" \\\n'
        f'  -H "sign: {sign_for_curl}" \\\n'
        f'  -H "sessionId: {SESSION_ID}" \\\n'
        f"  -d '{body}'"
    )
    print(curl_cmd)

    # 额外输出使用文档期望签名的 curl
    print(f"\n{'=' * 60}")
    print("curl 命令（使用文档第7章期望签名 - SHA1）：")
    print(f"{'=' * 60}\n")
    curl_doc = (
        f'curl -X POST "{url}" \\\n'
        f'  -H "Content-Type: application/json; charset=utf-8" \\\n'
        f'  -H "sign: jy/WTAtltv5UVQVDOb0f4H4JPqw=" \\\n'
        f'  -H "sessionId: {SESSION_ID}" \\\n'
        f"  -d '{body}'"
    )
    print(curl_doc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
