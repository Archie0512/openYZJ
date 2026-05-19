
import hmac, hashlib, base64

robotId = 'test-robotId'
robotName = 'test-robotName'
operatorOpenid = 'test-userId'
operatorName = 'test-userName'
msgId = 'test-msgId'
content = '你好，你能做什么呢?'
secret = 'test-secret'

print('=== SHA1 尝试 ===')
summary = robotId + ',' + robotName + ',' + operatorOpenid + ',' + operatorName + ',' + '1599727083000' + ',' + msgId + ',' + content
sig_sha1 = hmac.new(secret.encode('utf-8'), summary.encode('utf-8'), hashlib.sha1).digest()
sig_sha1_b64 = base64.b64encode(sig_sha1).decode()
print('SHA1 Result:', sig_sha1_b64)

print('\n=== SHA256 尝试（文档所说） ===')
sig_sha256 = hmac.new(secret.encode('utf-8'), summary.encode('utf-8'), hashlib.sha256).digest()
sig_sha256_b64 = base64.b64encode(sig_sha256).decode()
print('SHA256 Result:', sig_sha256_b64)

print('\n期望值:', 'jy/WTAtltv5UVQVDOb0f4H4JPqw=')
print('SHA1 匹配:', sig_sha1_b64 == 'jy/WTAtltv5UVQVDOb0f4H4JPqw=')
