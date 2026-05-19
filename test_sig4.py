
import hmac, hashlib, base64, json

robotId = 'test-robotId'
robotName = 'test-robotName'
operatorOpenid = 'test-userId'
operatorName = 'test-userName'
msgId = 'test-msgId'
content = '你好，你能做什么呢?'
secret = 'test-secret'

# 也许参数的顺序或拼接方式不同？
tests = [
    ('UTF-8逗号拼接', ','.join([robotId, robotName, operatorOpenid, operatorName, '1599727083000', msgId, content])),
]

for name, summary in tests:
    for algo_name, algo in [('HmacSHA1', hashlib.sha1), ('HmacSHA256', hashlib.sha256)]:
        sig = hmac.new(secret.encode('utf-8'), summary.encode('utf-8'), algo).digest()
        sig_b64 = base64.b64encode(sig).decode()
        match = sig_b64 == 'jy/WTAtltv5UVQVDOb0f4H4JPqw='
        print(f'{name} + {algo_name}: {sig_b64[:30]}... Match={match}')

print('\n查看二进制：')
exp = base64.b64decode('jy/WTAtltv5UVQVDOb0f4H4JPqw=')
print(f'Expected hex: {exp.hex()}')
print(f'Length: {len(exp)}')

# 试试反向解码
import binascii
try:
    exp_hex = '8f2fd64c0b65b6fe5455054339bd1fe07e093eac'
    raw = binascii.unhexlify(exp_hex)
    print(f'Reverse from hex: {base64.b64encode(raw).decode()}')
except Exception as e:
    print(f'Error: {e}')
