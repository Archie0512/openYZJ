import base64, json
encoded='W3siYmlsbE5vIjoiQVItQjAxQS0yMDI2MDIxNjc2IiwiaW52b2ljZVByb3BlcnR5IjowLCJpbnZvaWNlVHlwZSI6IjEweGRwIiwiaW5jbHVkZVRheEZsYWciOjEsImJ1eWVyTmFtZSI6IumyjeaZtiIsImJ1eWVyVGF4cGF5ZXJJZCI6IiIsImJ1eWVyUHJvcGVydHkiOjAsImJ1eWVyUmVjaXBpZW50UGhvbmUiOiIxMzc2MTg3OTU2MSIsInNlbGxlck5hbWUiOiLkuIrmtbflh6Hlvrfmsb3ovabplIDllK7mnI3liqHmnInpmZDlhazlj7giLCJyZW1hcmsiOiJXTVdMVjMxMDJNMlAzMDk2Ni/msqpCNzVUNzEiLCJpdGVtcyI6W3sic2VxIjoxLCJnb29kc05hbWUiOiLnu7Tkv67otLkiLCJyZXZlbnVlQ29kZSI6IjIwMjAwMDAwMDAwMDAwMDAwMDAiLCJhbW91bnQiOjEzOTguMCwidGF4UmF0ZSI6IjAuMTMiLCJ0YXhBbW91bnQiOjE2MC44MywicXVhbnRpdHkiOjEsInByaWNlIjoxMzk4LjB9XX1d'
bill=json.loads(base64.b64decode(encoded))[0]
print('sellerTaxpayerId:', repr(bill.get('sellerTaxpayerId')))
print('orgCode:', repr(bill.get('orgCode')))
print()
print('invoiceProperty:', repr(bill['invoiceProperty']), type(bill['invoiceProperty']).__name__)
print('buyerProperty:', repr(bill['buyerProperty']), type(bill['buyerProperty']).__name__)
print('includeTaxFlag:', repr(bill['includeTaxFlag']), type(bill['includeTaxFlag']).__name__)
print()
print('taxRate:', repr(bill['items'][0]['taxRate']), type(bill['items'][0]['taxRate']).__name__)
print('amount:', repr(bill['items'][0]['amount']), type(bill['items'][0]['amount']).__name__)
print()
issues = []
if 'sellerTaxpayerId' not in bill or not bill['sellerTaxpayerId']:
    issues.append('MISSING: sellerTaxpayerId (critical for seller identification)')
if 'orgCode' not in bill:
    issues.append('MISSING: orgCode (alternative to sellerTaxpayerId)')
if isinstance(bill['invoiceProperty'], int):
    issues.append('TYPE: invoiceProperty is int, official API expects string')
if isinstance(bill['buyerProperty'], int):
    issues.append('TYPE: buyerProperty is int, official API expects string')
if isinstance(bill['includeTaxFlag'], int):
    issues.append('TYPE: includeTaxFlag is int, official API expects string')
print('--- Issues Found ---')
if issues:
    for i in issues:
        print(' ', i)
else:
    print('  None')
