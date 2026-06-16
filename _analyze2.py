import base64, json

encoded = 'W3siYmlsbE5vIjoiQVItQjAxQS0yMDI2MDIxNjc2IiwiaW52b2ljZVByb3BlcnR5IjowLCJpbnZvaWNlVHlwZSI6IjEweGRwIiwiaW5jbHVkZVRheEZsYWciOjEsImJ1eWVyTmFtZSI6IumyjeaZtiIsImJ1eWVyVGF4cGF5ZXJJZCI6IiIsImJ1eWVyUHJvcGVydHkiOjAsImJ1eWVyUmVjaXBpZW50UGhvbmUiOiIxMzc2MTg3OTU2MSIsInNlbGxlck5hbWUiOiLkuIrmtbflh6Hlvrfmsb3ovabplIDllK7mnI3liqHmnInpmZDlhazlj7giLCJyZW1hcmsiOiJXTVdMVjMxMDJNMlAzMDk2Ni/msqpCNzVUNzEiLCJpdGVtcyI6W3sic2VxIjoxLCJnb29kc05hbWUiOiLnu7Tkv67otLkiLCJyZXZlbnVlQ29kZSI6IjIwMjAwMDAwMDAwMDAwMDAwMDAiLCJhbW91bnQiOjEzOTguMCwidGF4UmF0ZSI6IjAuMTMiLCJ0YXhBbW91bnQiOjE2MC44MywicXVhbnRpdHkiOjEsInByaWNlIjoxMzk4LjB9XX1d'

bill = json.loads(base64.b64decode(encoded))[0]

print("=" * 60)
print("Encoding Before/After Analysis")
print("=" * 60)

print()
print("--- Data BEFORE Base64 encoding (decoded from proxy log) ---")
print(json.dumps(bill, ensure_ascii=False, indent=2))

print()
print(f"--- Data AFTER Base64 encoding (sent to Kdcloud) ---")
print(f"Length: {len(encoded)} chars")
print(f"First 80 chars: {encoded[:80]}...")

print()
print("--- Field Analysis ---")
print(f"sellerTaxpayerId: {repr(bill.get('sellerTaxpayerId'))}")
print(f"orgCode:           {repr(bill.get('orgCode'))}")
print(f"invoiceProperty:   {repr(bill['invoiceProperty'])} (type: {type(bill['invoiceProperty']).__name__})")
print(f"buyerProperty:     {repr(bill['buyerProperty'])} (type: {type(bill['buyerProperty']).__name__})")
print(f"includeTaxFlag:    {repr(bill['includeTaxFlag'])} (type: {type(bill['includeTaxFlag']).__name__})")
print(f"taxRate:           {repr(bill['items'][0]['taxRate'])} (type: {type(bill['items'][0]['taxRate']).__name__})")
print(f"amount:            {repr(bill['items'][0]['amount'])} (type: {type(bill['items'][0]['amount']).__name__})")

print()
print("--- Issues Found ---")
issues = []

# Critical: seller identification
if 'sellerTaxpayerId' not in bill or not bill['sellerTaxpayerId']:
    issues.append('CRITICAL: sellerTaxpayerId is empty/missing - Kdcloud cannot identify seller')

# Alternative seller identification
if 'orgCode' not in bill:
    issues.append('MISSING: orgCode (alternative to sellerTaxpayerId for seller identification)')

# Type issues - official API expects strings for enum fields
if isinstance(bill['invoiceProperty'], int):
    issues.append('TYPE: invoiceProperty is int, official API expects string "0"/"1"')
if isinstance(bill['buyerProperty'], int):
    issues.append('TYPE: buyerProperty is int, official API expects string')
if isinstance(bill['includeTaxFlag'], int):
    issues.append('TYPE: includeTaxFlag is int, official API expects string "0"/"1"')

# Missing autoInvoice (was in original request but stripped by proxy)
issues.append('NOTE: autoInvoice field from System A request was stripped by proxy (not part of BILL.PUSH data array)')

if issues:
    for i in issues:
        print(" ", i)
else:
    print("  None")

print()
print("--- Gateway Request Envelope ---")
print(json.dumps({
    "requestId": "1781498379018",
    "businessSystemCode": "openBD",
    "interfaceCode": "BILL.PUSH",
    "data": f"<Base64, {len(encoded)} chars>"
}, ensure_ascii=False, indent=2))

