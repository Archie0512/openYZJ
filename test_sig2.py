
import hmac, hashlib, base64

robotId = 'test-robotId'
robotName = 'test-robotName'
operatorOpenid = 'test-userId'
operatorName = 'test-userName'
msgId = 'test-msgId'
content = '你好，你能做什么呢?'
secret = 'test-secret'

print('=== 尝试 1：字符串 time 1599727083000 ===')
summary1 = robotId + ',' + robotName + ',' + operatorOpenid + ',' + operatorName + ',' + '1599727083000' + ',' + msgId + ',' + content
sig1 = hmac.new(secret.encode('utf-8'), summary1.encode('utf-8'), hashlib.sha256).digest()
sig1_b64 = base64.b64encode(sig1).decode()
print('Result:', sig1_b64)

print('\n期望值: jy/WTAtltv5UVQVDOb0f4H4JPqw=')
decoded_expected = base64.b64decode('jy/WTAtltv5UVQVDOb0f4H4JPqw=')
print('期望值字节长度:', len(decoded_expected), '(20=SHA1, 32=SHA256)')
