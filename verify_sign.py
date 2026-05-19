# -*- coding: utf-8 -*-
import hmac, hashlib, base64

robotId = 'test-robotId'
robotName = 'test-robotName'
operatorOpenid = 'test-userId'
operatorName = 'test-userName'
time_str = '1599727083000'
msgId = 'test-msgId'
content = '你好，你能做什么呢?'
secret = 'test-secret'

summary = ','.join([robotId, robotName, operatorOpenid, operatorName, time_str, msgId, content])
print('Summary:', repr(summary))

sig = hmac.new(secret.encode(), summary.encode(), hashlib.sha256).digest()
sig_b64 = __import__('base64').b64encode(sig).decode()
print('Base64:', sig_b64)
print('Expected: jy/WTAtltv5UVQVDOb0f4H4JPqw=')
print('PASS' if sig_b64 == 'jy/WTAtltv5UVQVDOb0f4H4JPqw=' else 'FAIL')
