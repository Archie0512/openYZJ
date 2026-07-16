# InvoiceCallback 接口文档

> 版本：1.2  
> 更新日期：2026-07-16  
> 代码文件：`src/com/kingdee/eas/auto4s/callback/kdcloud/InvoiceCallbackServlet.java`

---

## 一、接口概述

发票开具结果回调接口。对接发票云(金蝶云)5.1.02按票回调接口。发票云在发票开具成功/作废/红冲后，通过此接口回调通知 EAS 系统更新应收单（T_AR_OtherBill）的发票数据。

**安全说明**：本接口不涉及签名验证，仅处理 Base64 解码。

---

## 二、接口地址

| 环境 | URL |
|------|-----|
| 测试环境 | `http://baodetest.haverise.com:23822/callback/invoiceCallback` |
| 生产环境 | `http://<生产服务器地址>/callback/invoiceCallback` |

**请求方式**：`POST`  
**Content-Type**：`application/json; charset=UTF-8`

---

## 三、请求参数

### 3.1 外层结构

请求体为 JSON，包含以下顶层字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `interfaceCode` | string | 是 | 业务编码。`INVOICE.OPEN`(开具)、`INVOICE.CANCEL`(作废)、`INVOICE.RED`(红冲)、`FILLIN`(回填)。本接口**仅校验非空**，不校验具体取值 |
| `returnCode` | string | 是 | 返回编码。`"0"`=成功，`"9999"`=失败。本接口**仅校验非空**，不据此区分处理 |
| `returnMsg` | string | 否 | 返回信息。成功返回 `"success"`，失败返回失败原因。本接口**读取但未使用** |
| `data` | string | 是 | 内层发票数据 JSON 经 **Base64 编码**后的字符串 |

### 3.2 data 解码后内层结构（发票数据）

`data` 字段 Base64 解码后为 JSON，包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `billNo` | string | 是 | EAS 应收单编号（T_AR_OtherBill.FNUMBER），用于查询和更新 |
| `invoiceDate` | string | 否 | 开票日期，格式 `yyyy-MM-dd`（如 `2026-06-30`）。为空时不更新日期字段 |
| `invoiceNum` | string | 否 | 发票号码 |
| `totalAmount` | number | 否 | 合计金额（不含税） |
| `totalTaxAmount` | number | 否 | 合计税额 |
| `invoicePdfFileUrl` | string | 否 | 发票 PDF 文件地址 |
| `drawer` | string | 否 | 开票人姓名 |

### 3.3 请求示例

**原始请求体**（外层 JSON）：

```json
{
    "interfaceCode": "INVOICE.OPEN",
    "returnCode": "0",
    "returnMsg": "success",
    "data": "eyJiaWxsTm8iOiJBUi1CMDFBLTIwMjYwMjQ3MDMiLCJpbnZvaWNlRGF0ZSI6IjIwMjYtMDYtMzAiLCJpbnZvaWNlTnVtIjoiMjYzMTIwMDAwMDQxMzM2NzUxMTYiLCJ0b3RhbEFtb3VudCI6NzAwLjg4LCJ0b3RhbFRheEFtb3VudCI6OTEuMTIsImludm9pY2VQZGZGaWxlVXJsIjoiaHR0cHM6Ly9hcGkucGlhb3pvbmUuY29tL3JwYS9mcmVlL3ByZXZpZXcvNTM2ODcyNjM5MS85MTMxMDE1NzI5NDA0OTgyVy81V1BFSTZKQUdRQ1BUUk1QWjlETD90eXBlPTAiLCJkcmF3ZXIiOiLpu4fn5pmu6ImNIn0="
}
```

**data 解码后内容**：

```json
{
    "billNo": "AR-B01A-2026024703",
    "invoiceDate": "2026-06-30",
    "invoiceNum": "26312000004133675116",
    "totalAmount": 700.88,
    "totalTaxAmount": 91.12,
    "invoicePdfFileUrl": "https://api.piaozone.com/rpa/free/preview/5368726391/91310115729404982W/5WPEI6JAGQCPTRMPZ9DL?type=0",
    "drawer": "黄春萍"
}
```

**data 编码方式**：将内层 JSON 字符串用 Base64 编码后放入 `data` 字段。使用的是标准 Base64 编码。

---

## 四、业务处理逻辑

### 4.1 执行流程

```
1. 读取请求体
2. 解析外层 JSON（interfaceCode / returnCode / returnMsg / data）
3. 参数校验（interfaceCode / returnCode / data 非空）
4. Base64 解码 data 字段
5. 解析内层 JSON（billNo / invoiceDate / invoiceNum / ...）
6. 获取 EAS Context
7. 数据库查询：SELECT fid, FISINVOICED, CFBDIOSTATUS FROM T_AR_OtherBill WHERE FNUMBER = ?
8. 写日志（logToBdApiLogs，工厂方法，先于 UPDATE）
9. 业务更新（if/else-if 优先级链，单次命中一支）
10. 发送响应
```

### 4.2 业务分支（if/else-if 优先级链）

根据查询到的 `FISINVOICED` 和 `CFBDIOSTATUS` 字段，执行以下分支（**单次命中一支**）：

| 优先级 | 条件 | 操作 | SQL |
|--------|------|------|-----|
| 1 | `FISINVOICED = 0`（未开票） | 更新发票数据，FISINVOICED 置 1 | `UPDATE T_AR_OtherBill SET FBILLDATE=?, FARINVOICENUMBERS=?, FINVOICEDATE=?, FINVOICEDAMT=?, CFINVOICEDTAXAMT=?, FISINVOICED=1, FRECBILLADRESS=? WHERE fid=?` |
| 2 | `CFBDIOSTATUS = 'ArtiInst'`（手工开票） | 更新摘要为"已被手工开票反写，{invoiceNum}，开票人：{drawer}" | `UPDATE T_AR_OtherBill SET FABSTRACTNAME=? WHERE fid=?` |
| 3 | `FISINVOICED = 1`（已开票） | 记录异常，摘要="开票回传异常，..."，CFBDIOSTATUS 置 'IOError' | `UPDATE T_AR_OtherBill SET FABSTRACTNAME=?, CFBDIOSTATUS='IOError' WHERE fid=?` |
| - | 以上均不命中 | 不执行更新，仍返回成功 | - |

### 4.3 事务与日志

**执行顺序（2026-07-16 改造后）**：

```
写日志（logToBdApiLogs）  ←  先执行
  ↓
DbUtil.execute(UPDATE)     ←  后执行
  ↓
sendResponse               ←  最后执行
```

- 日志写入使用 `DynamicObjectFactory.addnew()`（工厂方法），审计字段自动填充
- 日志失败时框架调用 `setRollbackOnly()`，但此时 UPDATE 尚未执行，无业务数据可回滚
- UPDATE 失败时抛 SQLException，不触发 `setRollbackOnly()`，日志记录保留

---

## 五、返回参数

### 5.1 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | string | 描述信息。成功为 `"success"`，失败为错误原因。**当为 null 时该字段不出现在 JSON 中**（fastjson 行为） |
| `code` | string | `"200"`=成功，`"500"`=失败 |
| `success` | boolean | `true`=成功，`false`=失败 |

### 5.2 成功响应

```json
{
    "message": "success",
    "code": "200",
    "success": true
}
```

### 5.3 失败响应

```json
{
    "message": "未找到单据：AR-B01A-2026024703",
    "code": "500",
    "success": false
}
```

---

## 六、错误码清单

| code | success | message | 触发条件 | 是否记日志 |
|------|---------|---------|---------|-----------|
| 500 | false | (无 message 字段) | 请求体为空（NPE） | 否 |
| 500 | false | JSON 解析异常文本 | 请求体非合法 JSON | 否 |
| 500 | false | `interfaceCode不能为空` | interfaceCode 为空 | 否 |
| 500 | false | `returnCode不能为空` | returnCode 为空 | 否 |
| 500 | false | `data不能为空` | data 为空 | 否 |
| 500 | false | `data字段Base64解码失败` | data 非 Base64 或解码后为空 | 否 |
| 500 | false | 内层 JSON 解析异常文本 | data 解码后非合法 JSON | 否 |
| 500 | false | Context 构建异常文本 | EAS 上下文构建失败 | 视 ctx 是否已创建 |
| 500 | false | `未找到单据：<billNo>` | billNo 在 T_AR_OtherBill 不存在 | 是 |
| 500 | false | SQL/类型转换异常文本 | UPDATE 执行失败 | 是 |
| 200 | true | `success` | 正常完成 | 是 |

---

## 七、测试样例

### 7.1 正常回调（未开票 -> 更新发票数据）

**前提**：T_AR_OtherBill 中存在 `FNUMBER='AR-B01A-2026024703'` 且 `FISINVOICED=0` 的记录。

**请求**：

```bash
curl -X POST http://baodetest.haverise.com:23822/callback/invoiceCallback \
  -H "Content-Type: application/json; charset=UTF-8" \
  -d '{
    "interfaceCode": "INVOICE.OPEN",
    "returnCode": "0",
    "returnMsg": "success",
    "data": "eyJiaWxsTm8iOiJBUi1CMDFBLTIwMjYwMjQ3MDMiLCJpbnZvaWNlRGF0ZSI6IjIwMjYtMDYtMzAiLCJpbnZvaWNlTnVtIjoiMjYzMTIwMDAwMDQxMzM2NzUxMTYiLCJ0b3RhbEFtb3VudCI6NzAwLjg4LCJ0b3RhbFRheEFtb3VudCI6OTEuMTIsImludm9pY2VQZGZGaWxlVXJsIjoiaHR0cHM6Ly9hcGkucGlhb3pvbmUuY29tL3JwYS9mcmVlL3ByZXZpZXcvNTM2ODcyNjM5MS85MTMxMDE1NzI5NDA0OTgyVy81V1BFSTZKQUdRQ1BUUk1QWjlETD90eXBlPTAiLCJkcmF3ZXIiOiLpu4fn5pmu6ImNIn0="
  }'
```

**预期响应**：

```json
{
    "message": "success",
    "code": "200",
    "success": true
}
```

**验证**：
```sql
-- 验证应收单已更新
SELECT FISINVOICED, FARINVOICENUMBERS, FINVOICEDATE, FINVOICEDAMT
FROM T_AR_OtherBill WHERE FNUMBER = 'AR-B01A-2026024703';

-- 验证日志已写入（审计字段非NULL）
SELECT FID, FNAME_L2, FNUMBER, FCREATORID, FCREATETIME, CFKDISSUCCEED
FROM CT_CUS_BdApiLogs
WHERE FNAME_L2 = 'InvoiceCallback'
ORDER BY FCREATETIME DESC;
```

### 7.2 单据不存在

**请求**：data 中 billNo 为不存在的编号。

**预期响应**：

```json
{
    "message": "未找到单据：AR-B01A-NOTEXIST",
    "code": "500",
    "success": false
}
```

### 7.3 参数缺失

**请求**：

```bash
curl -X POST http://baodetest.haverise.com:23822/callback/invoiceCallback \
  -H "Content-Type: application/json; charset=UTF-8" \
  -d '{"interfaceCode": "", "returnCode": "0", "data": "test"}'
```

**预期响应**：

```json
{
    "message": "interfaceCode不能为空",
    "code": "500",
    "success": false
}
```

### 7.4 data 生成方式

如需自行生成 data 字段，将内层 JSON 用 Base64 编码：

```python
import base64, json

inner_json = {
    "billNo": "AR-B01A-2026024703",
    "invoiceDate": "2026-06-30",
    "invoiceNum": "26312000004133675116",
    "totalAmount": 700.88,
    "totalTaxAmount": 91.12,
    "invoicePdfFileUrl": "https://example.com/invoice.pdf",
    "drawer": "黄春萍"
}

data = base64.b64encode(json.dumps(inner_json, ensure_ascii=False).encode("utf-8")).decode("utf-8")
print(data)
```

---

## 八、日志记录

每次调用（成功或失败）会向 `CT_CUS_BdApiLogs` 表写入一条日志记录。

| 字段 | 值 |
|------|-----|
| FNAME_L2 | `InvoiceCallback` |
| FNUMBER | `calogs_` + 时间戳（如 `calogs_20260716123903165`） |
| FSIMPLENAME | billNo（成功时）或 null（失败时） |
| CFKDREQUESTHEADER_L2 | 请求体原文 |
| CFKDRESPONDHEADER_L2 | 响应 JSON |
| CFKDSYNCDATE | 调用时间 |
| CFKDISSUCCEED | 1（成功）/ 0（失败） |
| FCREATORID | 当前登录用户ID（框架自动填充） |
| FCREATETIME | 调用时间（框架自动填充） |

**日志写入方式**：`DynamicObjectFactory.addnew()`（工厂方法，非 SQL INSERT）

**服务器日志排查**：搜索关键词 `===InvoiceCallback`、`==fid`、`===updateSql`、`===BdApiLogs addnew`

---

## 九、数据库表

### 9.1 查询表

```sql
SELECT fid, FISINVOICED, CFBDIOSTATUS
FROM T_AR_OtherBill
WHERE FNUMBER = ?;
```

### 9.2 更新表

| 分支 | 更新字段 |
|------|---------|
| 未开票 | FBILLDATE, FARINVOICENUMBERS, FINVOICEDATE, FINVOICEDAMT, CFINVOICEDTAXAMT, FISINVOICED, FRECBILLADRESS |
| 手工开票 | FABSTRACTNAME |
| 已开票异常 | FABSTRACTNAME, CFBDIOSTATUS |

### 9.3 日志表

```sql
SELECT FID, FNAME_L2, FNUMBER, FSIMPLENAME,
       FCREATORID, FCREATETIME, FLASTUPDATEUSERID, FLASTUPDATETIME,
       CFKDREQUESTHEADER_L2, CFKDRESPONDHEADER_L2, CFKDSYNCDATE, CFKDISSUCCEED,
       FCONTROLUNITID
FROM CT_CUS_BdApiLogs
WHERE FNAME_L2 = 'InvoiceCallback'
ORDER BY FCREATETIME DESC;
```