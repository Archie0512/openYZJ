
import hmac, hashlib, base64

robotId = 'test-robotId'
robotName = 'test-robotName'
operatorOpenid = 'test-userId'
operatorName = 'test-userName'
time_val = '1599727083000'
msgId = 'test-msgId'
content = '你好，你能做什么呢?'
secret = 'test-secret'

expected_sig = 'jy/WTAtltv5UVQVDOb0f4H4JPqw='
expected_bytes = base64.b64decode(expected_sig)
print(f'期望值字节: {expected_bytes.hex()}')
print()

# SHA1尝试
params = [robotId, robotName, operatorOpenid, operatorName, time_val, msgId, content]
summary = ','.join(params)
print(f'拼接字符串: {repr(summary)}')
print()

sig = hmac.new(secret.encode('utf-8'), summary.encode('utf-8'), hashlib.sha1).digest()
sig_hex = sig.hex()
print(f'计算SHA1: {sig_hex}')
print(f'期望值:   {expected_bytes.hex()}')
print(f'匹配: {sig_hex == expected_bytes.hex()}')
print()

# 也许secret要用某种特殊处理
print('尝试不同的secret编码:')
for secret_encoding in [secret, secret.encode('utf-8').decode('latin1')]:
    try:
        sig = hmac.new(secret_encoding.encode('utf-8'), summary.encode('utf-8'), hashlib.sha1).digest()
        sig_b64 = base64.b64encode(sig).decode()
        print(f'  Secret={repr(secret_encoding[:10])}: {sig_b64[:30]}...')
    except:
        pass
