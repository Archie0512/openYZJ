"""
test_invoice_api.py - 发票 API 调试脚本

直接用 JSON 字符串调用 OpenYZJ 代理接口，用于独立 Debug 签名和响应。
与 EAS DEP 完全解耦，可在本地 Python 环境运行。

用法：
    python test_invoice_api.py

依赖：requests（pip install requests）
"""

import hashlib
import hmac
import json
import time

import requests

# ============================================================
# 配置
# ============================================================
API_KEY = "ak_c9f470d5a9ffcab3f865df60248da31382ba36649b110381"
API_SECRET = "sk_6a14a9164f20e9ab1d44d15b48d0f8ee432d4b488adfd4f06f9b9b17365731df0dda5c87"
BASE_URL = "https://kimpi.cn"
API_PATH = "/api/proxy/v1/invoice/create"
API_ENV = "test"   # "test" / "prod"

# ============================================================
# 请求体（与 EAS DEP 生成的 JSON 完全一致）
# ============================================================
# 修改此 JSON 可快速验证不同数据场景
body_json = json.dumps({
    "requestId": "L0tAN6c2Qj6VzMn5nlBFcvyRDvM=",
    "bills": [
        {
        "billNo": "AR-B01A-2026022003",
        "invoiceProperty": 0,
        "invoiceType": "08xdp",
        "includeTaxFlag": 1,
        "buyerName": "南侨食品集团（上海）股份有限公司",
        "buyerTaxpayerId": "91310000558792983B",
        "buyerProperty": 1,
        "buyerRecipientPhone": "18621762397",
        "buyerRecipientMail": "850090044@QQ.COM",
        "orgCode": "B01A",
        "sellerName": "上海凡德汽车销售服务有限公司",
        "remark": "WBA21EH01PCM64489",
        "billDetail": [
            {
            "lineProperty": 2,
            "goodsName": "维修费",
            "revenueCode": "2020000000000000000",
            "detailId": "1tCF/duTTEy6VZfYXzFw0LyRaT8=",
            "amount": 1598,
            "taxRate": "0.13",
            "taxAmount": 183.84,
            "quantity": 1,
            "price": 1598
            }
        ]
        }
    ],
    "autoInvoice": False
}, ensure_ascii=False, separators=(",", ":"))

# ============================================================
# 签名（open_api_doc.md §3.1 直签模式）
# ============================================================
# sign_payload = method + path + timestamp + body (raw bytes)
timestamp = str(int(time.time()))

sign_payload = (
    "POST".encode()
    + API_PATH.encode()
    + timestamp.encode()
    + body_json.encode()
)

signature = hmac.new(
    API_SECRET.encode(),
    sign_payload,
    hashlib.sha256
).hexdigest()

# ============================================================
# 调试输出
# ============================================================
print("=" * 60)
print("调试信息")
print("=" * 60)
print(f"Timestamp:    {timestamp}")
print(f"Sign Payload: POST{API_PATH}{timestamp}[body {len(body_json)} bytes]")
print(f"Signature:    {signature}")
print()

print("请求 JSON:")
try:
    parsed = json.loads(body_json)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"(无法解析为 JSON) {e}")
    print(body_json)
print()

# ============================================================
# 发送请求
# ============================================================
print("=" * 60)
print("发送请求")
print("=" * 60)

headers = {
    "Content-Type": "application/json",
    "X-Proxy-Api-Key": API_KEY,
    "X-Proxy-Timestamp": timestamp,
    "X-Proxy-Signature": signature,
    "X-Proxy-Env": API_ENV,
}

url = f"{BASE_URL}{API_PATH}"
print(f"POST {url}")

try:
    resp = requests.post(url, data=body_json.encode("utf-8"), headers=headers, timeout=30)

    print(f"\nHTTP Status: {resp.status_code}")
    print(f"Response Headers: {dict(resp.headers)}")
    print()

    try:
        resp_data = resp.json()
        print("Response JSON:")
        print(json.dumps(resp_data, ensure_ascii=False, indent=2))
    except Exception:
        print("Response Text:")
        print(resp.text)

except requests.exceptions.Timeout:
    print("ERROR: 请求超时（30s）")
except requests.exceptions.ConnectionError as e:
    print(f"ERROR: 连接失败 — {e}")
except Exception as e:
    print(f"ERROR: {e}")
