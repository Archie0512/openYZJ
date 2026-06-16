import hashlib, hmac, time, json, urllib.request

API_KEY = "ak_c9f470d5a9ffcab3f865df60248da31382ba36649b110381"
API_SECRET = "sk_6a14a9164f20e9ab1d44d15b48d0f8ee432d4b488adfd4f06f9b9b17365731df0dda5c87"
BASE_URL = "https://kimpi.cn"
API_PATH = "/api/proxy/v1/invoice/create"
API_ENV = "test"

body = {
    "bills": [{
        "billNo": "AR-B01A-2026021676",
        "invoiceProperty": 0,
        "invoiceType": "10xdp",
        "includeTaxFlag": 1,
        "buyerName": "鲍晶",
        "buyerTaxpayerId": "",
        "buyerProperty": 0,
        "buyerRecipientPhone": "13761879561",
        "sellerName": "上海凡德汽车销售服务有限公司",
        "remark": "WMWLV3102M2P30966/沪B75T71",
        "items": [{
            "seq": 1,
            "goodsName": "维修费",
            "revenueCode": "2020000000000000000",
            "amount": 1398.0,
            "taxRate": "0.13",
            "taxAmount": 160.83,
            "quantity": 1,
            "price": 1398.0
        }]
    }],
    "autoInvoice": False
}

body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))

ts = str(int(time.time()))
sign_payload = b"POST" + API_PATH.encode() + ts.encode() + body_str.encode()
signature = hmac.new(API_SECRET.encode(), sign_payload, hashlib.sha256).hexdigest()

print("=" * 60)
print("调试信息")
print("=" * 60)
print(f"Timestamp:    {ts}")
print(f"Signature:    {signature}")
print()
print("请求 JSON:")
print(json.dumps(body, ensure_ascii=False, indent=2))
print()

print("=" * 60)
print("发送请求")
print("=" * 60)
print(f"POST {BASE_URL}{API_PATH}")

req = urllib.request.Request(
    f"{BASE_URL}{API_PATH}",
    data=body_str.encode(),
    headers={
        "Content-Type": "application/json",
        "X-Proxy-Api-Key": API_KEY,
        "X-Proxy-Timestamp": ts,
        "X-Proxy-Signature": signature,
        "X-Proxy-Env": API_ENV,
    }
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    print(f"\nHTTP Status: {resp.status}")
    resp_data = resp.read().decode()
    print("Response JSON:")
    print(json.dumps(json.loads(resp_data), ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    print(f"\nHTTP Status: {e.code}")
    print("Response Body:")
    print(e.read().decode())
except Exception as e:
    print(f"\nERROR: {e}")
