---
title: kdcloud
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
code_clipboard: true
highlight_theme: darkula
headingLevel: 2
generator: "@tarslib/widdershins v4.0.30"
---

# kdcloud

Base URLs:

* <a href="https://baode.test.kdcloud.com">测试环境: https://baode.test.kdcloud.com</a>

* <a href="https://baode.kdcloud.com">正式环境: https://baode.kdcloud.com</a>


# Authentication

# 授权

## POST 1.01.获取app_token

POST /api/getAppToken.do

发票云旗舰版，针对不同环境和不同租户有不同的访问地址，所以
- 如果已经有星瀚公有云沙箱环境，可以连接沙箱环境测试
拿到app_token后通过[1.02获取access_token](api-145421045)登录，后续用该access_token作为其他业务接口的认证信息。

> Body 请求参数

```json
{
    "appId": "FPY001",
    "appSecret": "FPY001fpy@2023fpy",
    "accountId": "1742050739649250304",
    "tenantid": "1",
    "language": "en"
}
```

> 测试环境_示例账号

```json
{
	"appId": "501036081",
	"appSecret": "uQNK5zv/jcK4xxNvD6WWQMJTDzswm/kZUURZTtkZJF0=",
	"tenantid": "baode.test",
	"accountId": "2360175391307559936",
	"language": "en"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|access_token|header|string| 否 |none|
|body|body|object| 否 |none|
|» appId|body|string| 是 |第三方应用id（必填）|
|» appSecret|body|string| 是 |第三方应用Securet（必填）|
|» tenantid|body|string| 否 |租户id（可为空）|
|» accountId|body|string| 是 |租户数据中心id（必填）|
|» language|body|string| 否 |语言（可为空）|

> 返回示例

> 200 Response

```json
{
    "data": {
        "app_token": "e42bf075-695d-49f6-8040-7aeea3903027",
        "success": true,
        "error_desc": "",
        "expire_time": 1708414721911,
        "error_code": "0"
    },
    "state": "success",
    "status": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» data|object|true|none||返回数据|
|»» app_token|string|true|none||apptoken，login需要用到|
|»» success|boolean|true|none||none|
|»» error_desc|string|true|none||返回描述|
|»» expire_time|number|true|none||超时截止时间|
|»» error_code|string|true|none||返回码|
|» state|string|true|none||成功状态|

## POST 1.02获取access_token

POST /api/login.do

发票云旗舰版，针对不同环境和不同租户有不同的访问地址，所以
- 如果已经有星瀚公有云沙箱环境，可以连接沙箱环境测试
- 私有化的具体访问地址，请联系具体的实施人员。（有效期两小时）

> Body 请求参数

```json
{
    "user": "15815530006",
    "apptoken": "e42bf075-695d-49f6-8040-7aeea3903027",
    "accountId": "1742050739649250304"
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|access_token|header|string| 否 |none|
|body|body|object| 否 |none|
|» user|body|string| 是 |登录用户（必填）|
|» apptoken|body|string| 是 |通过1.01接口从返回值获取|
|» tenantid|body|string| 否 |租户id（可为空）|
|» accountId|body|string| 是 |租户数据中心id（必填）|
|» usertype|body|string| 是 |用户类型，固定传 UserName 或者 Mobile|

#### 枚举值

|属性|值|
|---|---|
|» usertype|UserName|
|» usertype|Mobile|

> 返回示例

> 200 Response

```json
{
    "data": {
        "access_token": "1742050739649250304_MBB21m4dd2w8RGbv7o1Mkypn7yBd1lBnN3ghr9ybEBJQAI3IVJRhWc9XTFrNOrN7BUghq4j4knv6b19zSW9uNK851RRvQima7x52",
        "success": true,
        "error_desc": "",
        "expire_time": 1708414785680,
        "error_code": "0"
    },
    "state": "success",
    "status": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» data|object|true|none||返回数据|
|»» access_token|string|true|none||access_token，调用开票接口需要用到|
|»» success|boolean|true|none||none|
|»» error_desc|string|true|none||none|
|»» expire_time|number|true|none||超时截止时间对应时间戳|
|»» error_code|string|true|none||none|
|» state|string|true|none||请求状态，"success"表示请求成功|

# 开票/直接开票接口/数电开票

## POST 2.1.02 数电票回调

POST /此为对接发票云方提供的回调地址（对接方必须按照成功响应示例报文返回 json ）

返回编码统一参考：[《返回编码说明》](doc-3799582)
通过2.1.01数电蓝字发票开具、2.1.04数电票红冲接口开具数电发票后，通过本接口回调

> Body 请求参数

```json
{
  "returnMsg": "string",
  "returnCode": "string",
  "interfaceCode": "string",
  "data": {
    "serialNo": "string",
    "invoiceNum": "string",
    "invoiceProperty": "0",
    "invoiceDate": "string",
    "invoiceType": "01",
    "includeTaxAmount": 0,
    "sellerName": "string",
    "sellerTaxpayerId": "string",
    "sellerBank": "string",
    "sellerBankAccount": "string",
    "sellerAddress": "string",
    "sellerTel": "string",
    "naturalPersonFlag": "string",
    "buyerName": "string",
    "buyerTaxpayerId": "string",
    "buyerBank": "string",
    "buyerBankAccount": "string",
    "buyerAddress": "string",
    "buyerTel": "string",
    "specialType": "null",
    "buyerRecipientPhone": "string",
    "buyerRecipientMail": "string",
    "remark": "string",
    "drawer": "string",
    "deduction": 0,
    "deductionType": "空",
    "purchaseType": "空",
    "exportationType": "空",
    "vatTaxRefundType": "01",
    "originalInvoiceNumber": "string",
    "originalIssueTime": "string",
    "redInfoBillNo": "string",
    "govRedConfirmBillUuid": "string",
    "redConfirmBillStatus": "01",
    "agentUser": "string",
    "agentCardType": "string",
    "agentCardNo": "string",
    "agentCountry": "string",
    "agentTaxNo": "string",
    "invoiceFileUrl": "string",
    "xmlFileUrl": "string",
    "ofdFileUrl": "string",
    "invoiceDetail": [
      {
        "seq": 0,
        "detailRowNo": 0,
        "lineProperty": "string",
        "billSourceId": "string",
        "goodsCode": "string",
        "goodsName": "string",
        "revenueCode": "string",
        "specification": "string",
        "units": "string",
        "quantity": 0,
        "price": 0,
        "amount": 0,
        "taxRate": "string",
        "taxAmount": 0,
        "discountAmount": 0,
        "discountRate": "string",
        "privilegeType": "01"
      }
    ],
    "estateSaleInfo": {
      "provinceAdress": "string",
      "cityAdreess": "string",
      "simpleAddress": "string",
      "detailAddress": "string",
      "crossCitySign": "0",
      "areaunit": "平方千米",
      "startLeaseDate": "2019-08-24",
      "endLeaseDate": "2019-08-24",
      "estateId": "string",
      "specialIndustryNumber": "string",
      "carBrandNo": "string"
    },
    "estateLeaseInfo": {
      "provinceAdress": "string",
      "cityAdreess": "string",
      "simpleAddress": "string",
      "detailAddress": "string",
      "crossCitySign": "0",
      "areaunit": "平方千米",
      "startLeaseDate": "2019-08-24",
      "endLeaseDate": "2019-08-24",
      "estateId": "string",
      "specialIndustryNumber": "string",
      "carBrandNo": "string"
    },
    "buildInfo": {
      "simpleAddress": "string",
      "detailAddress": "string",
      "crossCitySign": "0",
      "buildingName": "string",
      "landTaxNo": "string",
      "specialIndustryNumber": "string",
      "crossCityTaxVerifyNo": "string"
    },
    "travelerList": [
      [
        {
          "traveler": "string",
          "cardType": "100",
          "cardNo": "string",
          "travelDate": "2024-04-02",
          "startPlace": "广东省深圳市宝安区",
          "endPlace": "广东省东莞市南城区",
          "transportType": "1",
          "seatClass": "一等座"
        }
      ]
    ]
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» returnMsg|body|string| 是 | 回调信息|开票失败时返回失败原因，开票成功返回 success|
|» returnCode|body|string| 是 | 回调代码|0-成功 9999-失败|
|» interfaceCode|body|string| 是 | 接口业务编码|固定值，回调蓝票时：INVOICE.OPEN，回调红票时：INVOICE.RED|
|» data|body|object| 是 ||需要把data的值进行解密|
|»» serialNo|body|string| 是 | 外部流水号|返回调用时传入的流水号|
|»» invoiceNum|body|string| 是 | 发票号码|none|
|»» invoiceProperty|body|string| 是 | 开票类型|none|
|»» invoiceDate|body|string| 是 | 开票日期|none|
|»» invoiceType|body|string| 是 | 发票种类|none|
|»» includeTaxAmount|body|number| 是 | 含税金额|none|
|»» sellerName|body|string| 是 | 销方名称|【长度：不超过100】|
|»» sellerTaxpayerId|body|string| 是 | 销方税号|none|
|»» sellerBank|body|string| 否 | 销方银行|【销方银行+销方银行账号 GBK编码150字节】|
|»» sellerBankAccount|body|string| 否 | 销方银账号|【销方银行+销方银行账号 GBK编码150字节】|
|»» sellerAddress|body|string| 否 | 销方地址|【销方地址+销方电话 GBK编码120字节】|
|»» sellerTel|body|string| 否 | 销方电话|【销方地址+销方电话 GBK编码120字节】|
|»» naturalPersonFlag|body|string| 否 | 自然人标识|Y-是，N-否；默认根据购方纳税人识别号取反，有值时为N，无值时为Y|
|»» buyerName|body|string| 是 | 购买方名称|【长度：不超过100】|
|»» buyerTaxpayerId|body|string| 否 | 购买方税号|专票必填|
|»» buyerBank|body|string| 否 | 购买方银行|【购买方银行+购买方银行账号 150字节】|
|»» buyerBankAccount|body|string| 否 | 购买方银行账号|【购买方银行+购买方银行账号 150字节】|
|»» buyerAddress|body|string| 否 | 购买方地址|【购买方地址+购买方电话 120字节】|
|»» buyerTel|body|string| 否 | 购买方电话|【购买方地址+购买方电话 120字节】|
|»» specialType|body|[数电票特定要素类型](#schema数电票特定要素类型)| 否 | 特定要素类型代码|空：非特定要素；01：成品油发票；02：稀土发票；03：建筑服务发票；04：货物运输服务发票；05：不动产销售服务发票；06：不动产租赁服务发票；07：代收车船税；08：通行费；09：旅客运输服务发票(待开发)；10：医疗服务（住院）发票；11：医疗服务（门诊）发票；12：自产农产品销售发票；13：拖拉机和联合收割机发票；14：机动车；15：二手车；16：农产品收购发票；17：光伏收购发票；18：卷烟发票|
|»» buyerRecipientPhone|body|string| 否 | 电子发票收票手机号|none|
|»» buyerRecipientMail|body|string| 否 | 电子发票收票邮箱|none|
|»» remark|body|string| 否 | 备注|none|
|»» drawer|body|string| 是 | 开票人|none|
|»» deduction|body|number| 否 | 差额征税差额|【长度：(14,2)】,征税方式为【差额征税】时必填|
|»» deductionType|body|string| 否 | 差额征税类型代码|默认为空|
|»» purchaseType|body|string| 否 | 收购发票类型代码|none|
|»» exportationType|body|string| 否 | 出口业务适用政策代码|none|
|»» vatTaxRefundType|body|[即征即退类型](#schema即征即退类型)| 否 | 增值税即征即退类型|空：非增值税即征即退|
|»» originalInvoiceNumber|body|string| 否 | 原蓝票发票号码|开红票必传【长度：20】|
|»» originalIssueTime|body|string| 否 | 原蓝票开票日期|开红字普票时，且发票云不存在该蓝票时必填|
|»» redInfoBillNo|body|string| 否 | 红字确认单编号|数电票红票、红冲必传【长度：16】|
|»» govRedConfirmBillUuid|body|string| 否 | 红字确认单税局uuid|（数电票红票必填）|
|»» redConfirmBillStatus|body|[红字确认单状态](#schema红字确认单状态)| 否 | 红字确认单状态|发票云版本5.0.024支持|
|»» agentUser|body|string| 否 | 经办人名称|none|
|»» agentCardType|body|string| 否 | 经办人证件类型|none|
|»» agentCardNo|body|string| 否 | 经办人证件号码|none|
|»» agentCountry|body|string| 否 | 经办人国籍(地区)|none|
|»» agentTaxNo|body|string| 否 | 经办人自然人纳税人识别号|none|
|»» invoiceFileUrl|body|string| 否 | PDF文件URL|none|
|»» xmlFileUrl|body|string| 否 | XML文件URL|none|
|»» ofdFileUrl|body|string| 否 | OFD文件URL|none|
|»» invoiceDetail|body|[object]| 是 | 发票明细|none|
|»»» seq|body|number| 是 | 明细序号|none|
|»»» detailRowNo|body|number| 是 | 发票明细序号|从1开始|
|»»» lineProperty|body|string| 是 | 行性质|0：正常商品行；1：折扣行[折扣行金额需为负数，它的上一行必须是被折扣行]；2：被折扣行[此商品行下一行必须是折扣行]【长度：2】|
|»»» billSourceId|body|string| 是 | 业务系统明细id|用于反写回原业务系统明细  【长度：32】|
|»»» goodsCode|body|string| 否 | 星瀚商品编码|【长度：32】，可不传，传了会进行商品匹配|
|»»» goodsName|body|string| 是 | 税收项目名称|不需要传含*税分编码简称*|
|»»» revenueCode|body|string| 是 | 税收分类编码|必填【长度：19】|
|»»» specification|body|string| 否 | 规格型号|GBK编码不超过40字节|
|»»» units|body|string| 否 | 计量单位|GBK编码不超过22字节|
|»»» quantity|body|number| 否 | 数量|金额不为空时，数量、单价可都为空，或通过另外一个换算得出；金额为空时，数量、单价都必填；【长度：20】|
|»»» price|body|number| 否 | 不含税单价|【长度：(14,8)】，不含税|
|»»» amount|body|number| 是 | 金额|【长度：(14,2)】，红票金额小于0，蓝票金额大于0，含税标识includeTaxFlag=1时该金额为含税|
|»»» taxRate|body|string| 是 | 税率|必传【0.13，0.09，0.06等】|
|»»» taxAmount|body|number| 是 | 税额|，若传入则校验误差[不含税金额*税率-税额≤±0.06]；【长度：(14,2)】|
|»»» discountAmount|body|number| 否 | 折扣金额|可以是正数也可以是负数，会根据此生成一行折扣行【长度：(14,2)】，折扣行必填|
|»»» discountRate|body|string| 否 | 折扣率|支持小数位[0.01]、百分比[1%]两种方式，如果传入了折扣金额，以折扣金额为准【长度：10】|
|»»» privilegeType|body|[优惠政策标识](#schema优惠政策标识)| 否 | 优惠政策标识|01：简易征收；02：稀土产品；03：免税；04：不征税；05：先征后退；06：100%先征后退；07：50%先征后退；08：按3%简易征收；09：按5%简易征收；10：按5%简易征收减按1.5%计征；11：即征即退30%；12：即征即退50%；13：即征即退70%；14：即征即退100%；15：超税负3%即征即退；16：超税负8%即征即退；17 ：超税负12%即征即退；18：超税负6%即征即退|
|»» estateSaleInfo|body|[不动产租赁](#schema不动产租赁)| 否 | 不动产销售服务信息|特定业务类型为05时必填|
|»»» provinceAdress|body|string| 是 ||省份|
|»»» cityAdreess|body|string| 是 ||城市|
|»»» simpleAddress|body|string| 否 ||不动产地址 ；不动产地址+不动产详细地址总长度限制为120|
|»»» detailAddress|body|string| 是 ||不动产详细地址；不动产地址+不动产详细地址总长度限制为120|
|»»» crossCitySign|body|string| 否 ||跨地（市）标志|
|»»» areaunit|body|string| 是 ||面积单位|
|»»» startLeaseDate|body|string(date)| 是 ||租赁开始日期 格式为yyyy-MM-dd|
|»»» endLeaseDate|body|string(date)| 是 ||租赁结束日期 格式为yyyy-MM-dd|
|»»» estateId|body|string| 是 ||房屋产权证书/不动产权证号|
|»»» specialIndustryNumber|body|string| 否 ||不动产基础资料编码：其他（除日期）参数为空时，自动根据该编号对应的基础资料补全剩余参数|
|»»» carBrandNo|body|string| 否 ||车牌号|
|»» estateLeaseInfo|body|[不动产租赁](#schema不动产租赁)| 否 | 不动产经营租赁服务信息|特定业务类型为06时必填|
|»»» provinceAdress|body|string| 是 ||省份|
|»»» cityAdreess|body|string| 是 ||城市|
|»»» simpleAddress|body|string| 否 ||不动产地址 ；不动产地址+不动产详细地址总长度限制为120|
|»»» detailAddress|body|string| 是 ||不动产详细地址；不动产地址+不动产详细地址总长度限制为120|
|»»» crossCitySign|body|string| 否 ||跨地（市）标志|
|»»» areaunit|body|string| 是 ||面积单位|
|»»» startLeaseDate|body|string(date)| 是 ||租赁开始日期 格式为yyyy-MM-dd|
|»»» endLeaseDate|body|string(date)| 是 ||租赁结束日期 格式为yyyy-MM-dd|
|»»» estateId|body|string| 是 ||房屋产权证书/不动产权证号|
|»»» specialIndustryNumber|body|string| 否 ||不动产基础资料编码：其他（除日期）参数为空时，自动根据该编号对应的基础资料补全剩余参数|
|»»» carBrandNo|body|string| 否 ||车牌号|
|»» buildInfo|body|[建筑服务](#schema建筑服务)| 否 | 建筑服务信息|特定业务类型为03时必填|
|»»» simpleAddress|body|string| 是 ||建筑服务发生地|
|»»» detailAddress|body|string| 是 ||具体地址|
|»»» crossCitySign|body|string| 否 ||跨地（市）标志|
|»»» buildingName|body|string| 是 ||建筑项目名称|
|»»» landTaxNo|body|string| 否 ||土地增值税项目编号|
|»»» specialIndustryNumber|body|string| 否 ||不动产基础资料编码：其他参数为空时，自动根据该编号对应的基础资料补全剩余参数|
|»»» crossCityTaxVerifyNo|body|string| 否 ||跨区域涉税事项报验管理编号，当跨地市标志为是时必填|
|»» travelerList|body|[[旅客运输](#schema旅客运输)]| 否 | 旅客运输信息|特定业务为09时必填|
|»»» traveler|body|string| 是 ||出行人|
|»»» cardType|body|string| 是 ||出行人证件类型|
|»»» cardNo|body|string| 是 ||出行人证件号码|
|»»» travelDate|body|string(date)| 是 ||出行日期，日期格式YYYY-MM-DD|
|»»» startPlace|body|string| 是 ||出发地（省市区县）|
|»»» endPlace|body|string| 是 ||到达地 （省市区县）|
|»»» transportType|body|string| 是 ||交通工具类型|
|»»» seatClass|body|string| 是 ||等级（等级 若交通工具类型选择“火车、飞机、船舶”，则等级为必填项，否则为非必填项）|

#### 枚举值

|属性|值|
|---|---|
|»» invoiceProperty|0|
|»» invoiceProperty|1|
|»» invoiceType|01|
|»» invoiceType|02|
|»» specialType|null|
|»» specialType|01|
|»» specialType|E02|
|»» specialType|03|
|»» specialType|04|
|»» specialType|05|
|»» specialType|06|
|»» specialType|07|
|»» specialType|08|
|»» specialType|09|
|»» specialType|10|
|»» specialType|11|
|»» specialType|12|
|»» specialType|13|
|»» specialType|14|
|»» specialType|15|
|»» specialType|02|
|»» specialType|17|
|»» specialType|18|
|»» deductionType|空|
|»» deductionType|01|
|»» deductionType|02|
|»» purchaseType|空|
|»» purchaseType|01|
|»» exportationType|空|
|»» exportationType|01|
|»» exportationType|02|
|»» exportationType|03|
|»» vatTaxRefundType|01|
|»» vatTaxRefundType|02|
|»» vatTaxRefundType|03|
|»» vatTaxRefundType|04|
|»» vatTaxRefundType|05|
|»» vatTaxRefundType|06|
|»» vatTaxRefundType|07|
|»» vatTaxRefundType|08|
|»» vatTaxRefundType|09|
|»» vatTaxRefundType|10|
|»» vatTaxRefundType|11|
|»» vatTaxRefundType|12|
|»» redConfirmBillStatus|01|
|»» redConfirmBillStatus|02|
|»» redConfirmBillStatus|03|
|»» redConfirmBillStatus|04|
|»» redConfirmBillStatus|05|
|»» redConfirmBillStatus|06|
|»» redConfirmBillStatus|07|
|»» redConfirmBillStatus|08|
|»» redConfirmBillStatus|09|
|»» redConfirmBillStatus|10|
|»»» privilegeType|01|
|»»» privilegeType|02|
|»»» privilegeType|03|
|»»» privilegeType|04|
|»»» privilegeType|05|
|»»» privilegeType|06|
|»»» privilegeType|07|
|»»» privilegeType|08|
|»»» privilegeType|09|
|»»» privilegeType|10|
|»»» privilegeType|11|
|»»» privilegeType|12|
|»»» privilegeType|13|
|»»» privilegeType|14|
|»»» privilegeType|15|
|»»» privilegeType|16|
|»»» privilegeType|17|
|»»» privilegeType|18|
|»»» crossCitySign|0|
|»»» crossCitySign|1|
|»»» areaunit|平方千米|
|»»» areaunit|平方米|
|»»» areaunit|公顷|
|»»» areaunit|亩|
|»»» areaunit|h㎡|
|»»» areaunit|k㎡|
|»»» areaunit|㎡|
|»»» crossCitySign|0|
|»»» crossCitySign|1|
|»»» areaunit|平方千米|
|»»» areaunit|平方米|
|»»» areaunit|公顷|
|»»» areaunit|亩|
|»»» areaunit|h㎡|
|»»» areaunit|k㎡|
|»»» areaunit|㎡|
|»»» crossCitySign|0|
|»»» crossCitySign|1|
|»»» cardType|100|
|»»» cardType|101|
|»»» cardType|102|
|»»» cardType|103|
|»»» cardType|199|
|»»» cardType|200|
|»»» cardType|201|
|»»» cardType|202|
|»»» cardType|203|
|»»» cardType|204|
|»»» cardType|205|
|»»» cardType|206|
|»»» cardType|207|
|»»» cardType|208|
|»»» cardType|209|
|»»» cardType|210|
|»»» cardType|211|
|»»» cardType|212|
|»»» cardType|213|
|»»» cardType|214|
|»»» cardType|215|
|»»» cardType|216|
|»»» cardType|217|
|»»» cardType|218|
|»»» cardType|219|
|»»» cardType|220|
|»»» cardType|221|
|»»» cardType|222|
|»»» cardType|223|
|»»» cardType|224|
|»»» cardType|225|
|»»» cardType|226|
|»»» cardType|227|
|»»» cardType|228|
|»»» cardType|229|
|»»» cardType|230|
|»»» cardType|231|
|»»» cardType|232|
|»»» cardType|233|
|»»» cardType|234|
|»»» cardType|235|
|»»» cardType|236|
|»»» cardType|237|
|»»» cardType|238|
|»»» cardType|239|
|»»» cardType|240|
|»»» cardType|241|
|»»» cardType|291|
|»»» cardType|299|
|»»» transportType|1|
|»»» transportType|2|
|»»» transportType|3|
|»»» transportType|4|
|»»» transportType|5|
|»»» transportType|6|
|»»» transportType|7|
|»»» transportType|9|
|»»» seatClass|一等座|
|»»» seatClass|二等座|
|»»» seatClass|软席（软座、软卧）|
|»»» seatClass|硬席（硬座、硬卧）|
|»»» seatClass|公务舱|
|»»» seatClass|头等舱|
|»»» seatClass|经济舱|
|»»» seatClass|一等舱|
|»»» seatClass|二等舱|
|»»» seatClass|三等舱|

> 返回示例

> 200 Response

```json
{
	"message": "回调成功",
	"errorCode": "0",
	"success": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» message|string|true|none||none|
|» errorCode|string|true|none||响应码，成功-0|
|» success|boolean|true|none||成功传true|

# 开票/直接开票接口/税控开票

## POST 2.2.08税控发票打印发票打印（需安装套打打印组件，仅适用于局域网内的HTTP调用方式）

POST /http://127.0.0.1:61623

状态码：
**成功**:1011
**失败**:9999

> Body 请求参数

```json
{
  "czlx": "string",
  "sjd": {
    "splx": "string",
    "fplx": "string",
    "qdbz": "string",
    "dylx": "string",
    "bz": "string",
    "fpdm": "string",
    "fphm": "string",
    "yfpdm": "string",
    "yfphm": "string",
    "mmq": "string",
    "kprq": "string",
    "jqbh": "string",
    "kplx": "string",
    "bmbb": "string",
    "zfbz": "string",
    "tspz": "string",
    "zhsl": "string",
    "jym": "string",
    "hsbz": "string",
    "xhf_nsrsbh": "string",
    "xhf_mc": "string",
    "xhf_dzdh": "string",
    "xhf_yhzh": "string",
    "ghf_nsrsbh": "string",
    "ghf_mc": "string",
    "ghf_dzdh": "string",
    "ghf_yhzh": "string",
    "kpy": "string",
    "sky": "string",
    "fhr": "string",
    "hjje": "string",
    "hjse": "string",
    "jshj": "string",
    "items": [
      {
        "xmlx": "string",
        "xmdw": "string",
        "xmmc": "string",
        "xmsl": "string",
        "xmje": "string",
        "ggxh": "string",
        "se": "string",
        "sl": "string",
        "xmdj": "string",
        "taxcode": {
          "kce": "string",
          "lslvbs": "string",
          "ssflbm": "string",
          "yhzc": "string",
          "yhzcnr": "string"
        }
      }
    ]
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|name|query|string| 是 ||client_secret+金税盘号|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» czlx|body|string| 是 ||固定传1|
|» sjd|body|object| 是 ||none|
|»» splx|body|string| 是 ||税盘类型 0:航信 1:百望 2:Ukey|
|»» fplx|body|string| 是 ||发票类型 0:纸质专票 2:纸质普票 12：机动车统一销售发票 目前仅支持以上三种|
|»» qdbz|body|string| 是 ||清单标志|
|»» dylx|body|string| 是 ||1 发票 2清单|
|»» bz|body|string| 是 ||备注|
|»» fpdm|body|string| 是 ||发票代码|
|»» fphm|body|string| 是 ||发票号码|
|»» yfpdm|body|string| 是 ||原发票代码（红票需要）|
|»» yfphm|body|string| 是 ||原发票号码（红票需要|
|»» mmq|body|string| 是 ||密码区|
|»» kprq|body|string| 是 ||开票日期 格式： 20210930|
|»» jqbh|body|string| 是 ||机器编号|
|»» kplx|body|string| 是 ||开票类型|
|»» bmbb|body|string| 是 ||编码版本|
|»» zfbz|body|string| 是 ||作废标志|
|»» tspz|body|string| 是 ||特殊票种|
|»» zhsl|body|string| 是 ||综合税率|
|»» jym|body|string| 是 ||校验码|
|»» hsbz|body|string| 是 ||含税标志|
|»» xhf_nsrsbh|body|string| 是 ||销方税号|
|»» xhf_mc|body|string| 是 ||销方名称|
|»» xhf_dzdh|body|string| 是 ||销方地址电话|
|»» xhf_yhzh|body|string| 是 ||销方银行账号|
|»» ghf_nsrsbh|body|string| 否 ||购方税号|
|»» ghf_mc|body|string| 是 ||购方名称|
|»» ghf_dzdh|body|string| 否 ||购方地址电话|
|»» ghf_yhzh|body|string| 否 ||购方银行账号|
|»» kpy|body|string| 是 ||开票员|
|»» sky|body|string| 否 ||收款人|
|»» fhr|body|string| 否 ||复核人|
|»» hjje|body|string| 是 ||合计金额（不含税）|
|»» hjse|body|string| 是 ||合计税额|
|»» jshj|body|string| 是 ||价税合计|
|»» items|body|[object]| 是 ||none|
|»»» xmlx|body|string| 否 ||行类型 0：正常行（默认） 1：折扣行 2：被折扣行|
|»»» xmdw|body|string| 否 ||单位|
|»»» xmmc|body|string| 否 ||名称|
|»»» xmsl|body|string| 否 ||数量|
|»»» xmje|body|string| 否 ||金额|
|»»» ggxh|body|string| 否 ||规格型号|
|»»» se|body|string| 否 ||税额|
|»»» sl|body|string| 否 ||税率|
|»»» xmdj|body|string| 否 ||单价|
|»»» taxcode|body|object| 否 ||none|
|»»»» kce|body|string| 是 ||扣除额|
|»»»» lslvbs|body|string| 是 ||零税率标识|
|»»»» ssflbm|body|string| 是 ||税收分类编码|
|»»»» yhzc|body|string| 是 ||税收优惠政策|
|»»»» yhzcnr|body|string| 是 ||税收优惠政策内容|

> 返回示例

> 200 Response

```json
{"description":"操作成功","errcode":"1011"}

```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» errcode|string|true|none||none|
|» description|string|true|none||none|

# 开票/回调接口（支持除数电票直接开票接口外的开票回调）

## POST 5.1.03回调接口-按单回调（单据对应的所有发票开票完毕后一起回调（包含开票成功和开票失败），不支持合并又拆分的场景）

POST /：忽略该接口前缀，此为对接发票云方提供的回调地址（对接方必须按照成功响应示例报文返回 json ）

一个开票申请单如果拆分开具了N张发票，在发票开具完毕后，只全部回调一次（包含开票成功和开票失败），不支持合并又拆分的场景，开票成功失败的都会返回。
（业务编码 businessSystemCode 以 3std1 开头，就会开启这种方式的回调）

> Body 请求参数

```json
{
  "interfaceCode": "string",
  "returnCode": "string",
  "returnMsg": "string",
  "data": [
    {
      "batch": "string",
      "billNo": "string",
      "invoiceProperty": 0,
      "invoiceType": "028",
      "buyerProperty": 0,
      "buyerName": "string",
      "buyerTaxpayerId": "string",
      "buyerAddressAndTel": "string",
      "buyerBankAndAccount": "string",
      "buyerRecipientMail": "string",
      "buyerRecipientPhone": "string",
      "deduction": 0,
      "includeTaxFlag": 0,
      "totalTaxAmount": 0,
      "totalAmount": 0,
      "includeTaxAmount": 0,
      "taxedType": 0,
      "sellerName": "string",
      "sellerTaxpayerId": "string",
      "sellerAddressAndTel": "string",
      "sellerBankAndAccount": "string",
      "inventoryMark": "string",
      "drawer": "string",
      "reviewer": "string",
      "payee": "string",
      "canceler": "string",
      "abolishReason": "string",
      "deviceNo": "string",
      "remark": "string",
      "invoiceStatus": "string",
      "invoiceCode": "string",
      "invoiceNum": "string",
      "invoiceDate": "string",
      "invoiceDetail": [
        {
          "amount": 0,
          "billSourceId": "string",
          "goodsName": "string",
          "includeTaxAmount": 0,
          "includeTaxPrice": "string",
          "lineProperty": 0,
          "price": "string",
          "privilegeContent": "string",
          "privilegeFlag": 0,
          "quantity": "string",
          "revenueCode": "string",
          "revenueName": "string",
          "seq": 0,
          "specification": "string",
          "taxAmount": 0,
          "taxRate": "string",
          "units": "string",
          "zeroTaxRateFlag": "string"
        }
      ],
      "invoiceFileUrl": "string",
      "invoiceImageUrl": "string",
      "invoicePdfFileUrl": "string",
      "invoiceXmlFileUrl": "string",
      "orderNo": "string",
      "issueErrorMessage": "string",
      "originalInvoiceCode": "string",
      "originalInvoiceNumber": "string",
      "originalInvoiceStatus": "string",
      "originalIssueTime": "string",
      "printFlag": "string",
      "redInfoBillNo": "string",
      "serialNo": "string",
      "systemSource": "string",
      "terminalNo": "string",
      "checkCode": "string",
      "skm": "string"
    }
  ],
  "bizControl": {
    "issueBizType": "string",
    "bizType": "string",
    "monthSurplusLimit": 0,
    "daySurplusLimit": 0,
    "isWarning": true
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» interfaceCode|body|string| 是 | 业务编码|业务编码，开票回调是INVOICE.OPEN，作废回调是INVOICE.CANCEL，红冲回调是INVOICE.RED|
|» returnCode|body|string| 是 | 返回编码|0成功，9999失败，按单回调无法根据此状态码判断，会存在部分开具成功，部分失败的情况，根据是否存在发票代码号码判断|
|» returnMsg|body|string| 是 | 返回信息|开票失败原因，成功返回success|
|» data|body|[object]| 是 | 按单回调请求参数|需要把data里面的base64字符串解密|
|»» batch|body|string| 是 | 批次号|批次号|
|»» billNo|body|string| 是 | 单据编号|单据编号|
|»» invoiceProperty|body|number| 是 | 开票类型|开票类型，0蓝票，1红票 【长度：1】|
|»» invoiceType|body|[发票种类](#schema发票种类)| 是 | 发票种类|发票种类， 028-增值税电子专用发票， 004-增值税纸质专用发票， 026-增值税电子普通发票， 007-增值税纸质普通发票 【长度：4】|
|»» buyerProperty|body|number| 是 | 购买方性质|[购方]购买方性质，0-企业，1-个人|
|»» buyerName|body|string| 是 | 购买方名称|[购方]购买方名称|
|»» buyerTaxpayerId|body|string| 是 | 购买方税号|[购方]购买方税号|
|»» buyerAddressAndTel|body|string| 是 | 购买方地址和电话|[购方]购买方地址和电话，GBK编码100字节，开专票时若未传入则用名称匹配系统维护的地址电话【长度：100】|
|»» buyerBankAndAccount|body|string| 是 | 购买方银行和账号|[购方]购买方银行和账号，GBK编码100字节，开专票时若未传入则用名称匹配系统维护的银行和账号【长度：100】|
|»» buyerRecipientMail|body|string| 是 | 购买方邮箱|[购方/交付]电子发票收票邮箱|
|»» buyerRecipientPhone|body|string| 是 | 购买方手机号|[购方/交付]电子发票收票手机号|
|»» deduction|body|number| 是 | 差额征税差额|[税]差额征税差额【长度：(14,2)】|
|»» includeTaxFlag|body|number| 是 | 含税标识|[税]含税标识，0-不含税，1-含税【长度：1】|
|»» totalTaxAmount|body|number| 是 | 合计税额|[税]合计税额|
|»» totalAmount|body|number| 是 | 合计金额|[税]合计金额|
|»» includeTaxAmount|body|number| 是 | 价税合计|[税]价税合计|
|»» taxedType|body|number| 是 | 征税方式|[税]征税方式，0-普通 2-差额|
|»» sellerName|body|string| 是 | 销方名称|[销方]销方名称|
|»» sellerTaxpayerId|body|string| 是 | 销方税号|[销方]销方税号|
|»» sellerAddressAndTel|body|string| 是 | 销方地址和电话|[销方]销方地址和电话|
|»» sellerBankAndAccount|body|string| 是 | 销方银行和账号|[销方]销方银行和账号|
|»» inventoryMark|body|string| 是 | 清单标志|[销方]清单标志，0-非清单发票，1-清单发票【长度：1】|
|»» drawer|body|string| 是 | 开票人|[销方]开票人【长度：10】|
|»» reviewer|body|string| 是 | 复核人|[销方]复核人【长度：10】|
|»» payee|body|string| 是 | 收款人|[销方]收款人【长度：10】|
|»» canceler|body|string| 是 | 作废人|[销方]作废人|
|»» abolishReason|body|string| 是 | 作废原因|[销方]作废原因|
|»» deviceNo|body|string| 是 | 设备编号|[销方]设备编号|
|»» remark|body|string| 是 | 备注|备注，GBK编码230字节【长度：230】|
|»» invoiceStatus|body|string| 是 | 发票状态|发票状态 0-正常 2-待开 3-红冲 6-作废|
|»» invoiceCode|body|string| 是 | 发票代码|发票代码|
|»» invoiceNum|body|string| 是 | 发票号码|发票号码|
|»» invoiceDate|body|string| 是 | 开票日期|开票日期|
|»» invoiceDetail|body|[object]| 否 | 发票明细|发票明细|
|»»» amount|body|number| 是 | 金额|金额【长度：(14,2)】|
|»»» billSourceId|body|string| 是 | 业务系统明细id|业务系统明细id，用于反写回原业务系统明细  【长度：32】|
|»»» goodsName|body|string| 是 | 商品名称|商品名称， GBK编码不超过92字节（含*税分编码简称*的长度）【长度：92】|
|»»» includeTaxAmount|body|number| 是 | 价税合计|价税合计|
|»»» includeTaxPrice|body|string| 是 | 明细含税单价|明细含税单价|
|»»» lineProperty|body|number| 是 | 行性质|行性质，0正常商品行，1折扣行[折扣行金额需为负数，它的上一行必须是被折扣行]，2被折扣行[此商品行下一行必须是折扣行]【长度：2】|
|»»» price|body|string| 是 | 单价|单价【长度：(14,8)】|
|»»» privilegeContent|body|string| 是 | 享受优惠内容|享受优惠内容【长度：50】|
|»»» privilegeFlag|body|number| 否 | 是否享受优惠|是否享受优惠，0-不享受，1-享受【长度：1】|
|»»» quantity|body|string| 是 | 数量|数量，金额不为空时，数量、单价可都为空，或通过另外一个换算得出；金额为空时，数量、单价都必填；【长度：20】|
|»»» revenueCode|body|string| 是 | 税收分类编码|税收分类编码【长度：19】|
|»»» revenueName|body|string| 是 | 税收分类简称|税收分类简称|
|»»» seq|body|number| 是 | 明细序号|明细序号|
|»»» specification|body|string| 是 | 规格型号|规格型号，GBK编码不超过40字节【长度：90】|
|»»» taxAmount|body|number| 是 | 税额|税额，若传入则校验误差[不含税金额*税率-税额≤±0.06]；【长度：(14,2)】|
|»»» taxRate|body|string| 是 | 税率|税率，支持小数位[0.01]、百分比[1%]、直接数值[1]三种传入格式,小数位最多3位【长度：5】|
|»»» units|body|string| 是 | 计量单位|计量单位，GBK编码不超过22字节【长度：22】|
|»»» zeroTaxRateFlag|body|string| 是 | 零税率标识|零税率标识，1出口退税，2不征税，3普通零税率【长度：1】|
|»» invoiceFileUrl|body|string| 是 | 版式文件下载地址|版式文件下载地址，航信百旺税盘开普通电票为PDF文件，开电子专票为ofd文件，ukey开电票都是ofd文件，数电票为ofd文件|
|»» invoiceImageUrl|body|string| 是 | PDF转图片预览地址|PDF转图片预览地址|
|»» invoicePdfFileUrl|body|string| 是 | 数电票PDF地址|数电票pdf地址，星瀚版本5.0.022支持|
|»» invoiceXmlFileUrl|body|string| 是 | 数电票XML地址|数电票xml地址，星瀚版本5.0.022支持|
|»» orderNo|body|string| 是 | 发票流水号|发票流水号|
|»» issueErrorMessage|body|string| 是 | 开票失败原因|开票失败原因|
|»» originalInvoiceCode|body|string| 否 | 原蓝票发票代码|原蓝票发票代码，开红票必传【长度：12】|
|»» originalInvoiceNumber|body|string| 否 | 原蓝票发票号码|原蓝票发票号码，开红票必传【长度：8】|
|»» originalInvoiceStatus|body|string| 否 | 原蓝票状态|原蓝票状态，红冲、回调时存在，红冲回调为3、作废回调为6|
|»» originalIssueTime|body|string| 否 | 原蓝票开票时间|原蓝票开票时间，红冲、回调时存在，格式为"yyyyMMdd"|
|»» printFlag|body|string| 是 | 纸票打印标识|纸票打印标识，0-未打印 1-已打印|
|»» redInfoBillNo|body|string| 是 | 红字信息表编号|红字信息表编号，专用发票红冲必传【长度：16】|
|»» serialNo|body|string| 是 | 序列号|序列号 【拆分合并后重新生成的编号】|
|»» systemSource|body|string| 是 | 系统来源|系统来源|
|»» terminalNo|body|string| 是 | 终端号码|终端号码|
|»» checkCode|body|string| 是 | 校验码|校验码|
|»» skm|body|string| 是 | 密码区|密码区|
|» bizControl|body|object| 是 ||none|
|»» issueBizType|body|string| 是 | 企业业务管控编码|企业业务管控编码，企业在发票云旗舰版设置的企业开票业务管理编码|
|»» bizType|body|string| 是 | 业务类型编码|业务类型编码，企业在发票云旗舰版设置的开票业务类型编码|
|»» monthSurplusLimit|body|number| 是 | 月剩余额度|月剩余额度，企业每月电子税局可开票额度的剩余额度|
|»» daySurplusLimit|body|number| 是 | 每日剩余额|每日剩余额，企业某业务上设置每日可开票额度的剩余额度|
|»» isWarning|body|boolean| 是 | 是否已超过月预警阈值|是否已超过月预警阈值，当前开票额度达到企业设置的每月电子税局开票额度预警阈值|

#### 枚举值

|属性|值|
|---|---|
|»» invoiceType|028|
|»» invoiceType|026|
|»» invoiceType|004|
|»» invoiceType|007|
|»» invoiceType|025|
|»» invoiceType|08xdp|
|»» invoiceType|10xdp|

> 返回示例

> 200 Response

```json
{
  "message": "string",
  "code": "string",
  "success": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» message|string|true|none|描述信息|none|
|» code|string|true|none|错误代码|none|
|» success|boolean|true|none|成功响应|成功响应|

# 开票/扫码开票接口（税控+数电）/业务系统生成二维码链接模式

## GET 3.1.01业务系统组装二维码链接格式

GET /

`测试环境参数`
`key: Evjf8VxmUW`
示例扫码地址（测试）：https://cosmic-demo.piaozone.com?k=key,ddh,je,timestamps,md5,$
示例扫码地址（生产）：https://cosmic.piaozone.com?k=key,ddh,je,timestamps,md5,$

key：设备key，由金蝶生成（位于星瀚发票云-动态二维码设置-key值）
![](http://api-doc.piaozone.com/upload/pageImage/8bbc09021bd33dfb087b91fc60f6f77e/1671602353image.png)
ddh：小票订单号
je: 小票金额
timestamps: 13位毫秒级时间戳（tips：java语言可以使用 Instant.now().toEpochMilli() 获取）
md5: MD5加密值

注意：以英文逗号分隔，最后要拼接$结尾

2 MD5值说明

md5 的值：先key + key，接着对其反转， 最后对反转后的值进行MD5
即：MD5(反转(key + key))

> Body 请求参数

```yaml
{}

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 3.1.03 扫码提交购方抬头规则

POST /

**1  规则说明**

示例扫码地址：https://cosmic-demo.piaozone.com?k=key,ddh,je,timestamps,md5&amp;lx=2

lx：   固定传2，扫码后仅提交抬头
key：key值，由金蝶生成（位于星瀚发票云-动态二维码设置-key值）
![Image_20220908092345.png](https://img.cdn.apipost.cn/client/user/293847/avatar/f72d1a2aad4ace40404ce603f5bddf056319443a22d00.png)
ddh：小票订单号
je: 小票金额
timestamps: 时间戳
md5: MD5加密值

注意：以英文逗号分隔，最后要拼接$结尾

**2  MD5值说明**

md5 的值：先key + key，接着对其反转， 最后对反转后的值进行MD5
即：MD5(反转(key + key))

> Body 请求参数

```yaml
{}

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 3.1.02查询订单接口(由客户提供)

POST /此为对接发票云方提供的查询订单接口地址（对接方必须按照成功响应示例报文返回 json ） 接口配置地址关联动态二维码配置里的业务编码（位于 发票云->系统管理->业务系统）

扫码开票二维码规则：
1 规则说明

示例扫码地址：http://scan.piaozone.com/demo/tyqr?k=key,ddh,je,timestamps,md5,$

key：门店id，由金蝶分配
ddh：小票单号
je: 小票金额
timestamps: 时间戳
md5: MD5加密值

注意：最后要拼接$结尾

2 MD5值说明

MD5(KEY + DDH + MD5(public_key+ DDH) + JE)

第一步：
MD5_1 = MD5(public_key + DDH)
第二步：
MD5_2 = MD5(KEY + DDH + MD5_1 + JE)
附：

public_key 由金蝶分配，每个租户分配一对（查看路径:发票云--系统管理--云应用参数配置--移动云参数配置）
public_key 由 key 关联查询（金蝶端校验）

***流程步骤：***
1.对接客户通过以下接口生成二维码给到用户(http://scan.piaozone.com/demo/tyqr?k=key,ddh,je,timestamps,md5,$)
2.用户扫码到开票界面，填写购方信息
3.用户提交开票
4.发票云系统通过客户提供给发票云的明细查询地址（http://xxxxxxx/scanInvoice/queryOrder）查询单据编号对应的明细数据
5.完成开票

> Body 请求参数

```json
{
  "interfaceCode": "GET.ORDER",
  "data": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» interfaceCode|body|string| 是 ||固定业务编码 GET.ORDER|
|» data|body|string| 是 ||单据编号，是BASE64编码或AES密文，根据设置的加密规则进行解码或解密|

> 返回示例

> 200 Response

```json
{
    "code": "0",
    "message": "查询订单成功",
    "data": {
        "billNo": "5232512300923491142",
        "drawer": "开票人",
        "billDate": "2025-12-30",
        "includeTaxFlag": "1",
        "billProperty": "1",
        "sellerTaxpayerId": "销方税号",
        "cancalState": "0",
        "billAmount": 43.05,
        "billDetail": [
            {
                "skuId": 1029891,
                "amount": 36.36,
                "quantity": 1,
                "discountAmount": 0,
                "taxRate": 0.06000000,
                "goodsCode": "29656",
                "lineProperty": "2",
                "goodsName": "五台豆腐丸子HSX",
                "revenueCode": "3070401000000000000"
            },
            {
                "skuId": 571716,
                "amount": 6.69,
                "quantity": 1,
                "discountAmount": 0,
                "taxRate": 0.09000000,
                "goodsCode": "01515",
                "lineProperty": "2",
                "goodsName": "莜面",
                "revenueCode": "1030101990000000000"
            }
        ]
    }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|string|true|none||返回"0"则表示成功，其他表示失败|
|» message|string|true|none||接口返回成功消息，失败返回失败原因|
|» data|object|true|none||data数据为明文不需要加密|
|»» billNo|string|true|none||单据编号，必填|
|»» drawer|string|true|none||开票人，必填|
|»» payee|string|false|none||付款人|
|»» reviewer|string|false|none||复核人|
|»» billDate|string|true|none||单据日期，必填  格式yyyy-MM-dd|
|»» remark|string|false|none||发票备注，选填|
|»» includeTaxFlag|string|true|none||含税标识，必填   0-不含税   1-含税|
|»» billProperty|string|true|none||单据性质，必填  1-正数     -1负数|
|»» sellerTaxpayerId|string|true|none||销售方纳税人识别号，必填|
|»» buyerTaxpayerId|string|false|none||购方税号|
|»» buyerName|string|false|none||购方名称|
|»» buyerBankAndAccount|string|false|none||购方银行账号|
|»» buyerAddressAndTel|string|false|none||购方地址电话|
|»» cancalState|string|true|none||作废标识，必填。 0-未作废，1-作废|
|»» billAmount|number|true|none||单据金额，必填。如果含税标识是含税就是含税金额，不含税就是不含税金额|
|»» billTax|number|false|none||单据税额，选填|
|»» issueBizType|string|false|none||调度开票业务类型（传开票业务类型编码）|
|»» billDetail|[object]|true|none||none|
|»»» amount|number|false|none||明细金额，必填。需保留2位小数，如果含税标识是含税就是含税金额，不含税就是不含税金额|
|»»» quantity|string|false|none||数量，选填|
|»»» discountAmount|number|false|none||折扣金额，选填|
|»»» specification|string|false|none||规格型号，选填|
|»»» units|string|false|none||单位，选填|
|»»» privilegeContent|string|false|none||优惠政策内容，选填|
|»»» taxRate|string|false|none||税率，必填|
|»»» privilegeFlag|string|false|none||是否享受优惠政策，选填     0-不享受  1-享受|
|»»» price|string|false|none||单价，选填|
|»»» goodsCode|string|false|none||商品编码，选填。(如果传了，可以自动匹配单价、税收编码、税率等）|
|»»» lineProperty|string|false|none||行性质，必填。   2-正常商品行    0-商品带折扣行|
|»»» taxAmount|number|false|none||税额，选填（会自动计算）|
|»»» goodsName|string|false|none||商品名称，选填，不传则以税收分类编码的商品名称开票|
|»»» revenueCode|string|false|none||税收分类编码，必填|

## POST 3.1.04账单中心开票小程序短链接生成

POST /kapi/app/imasm/generateurllink

本接口用于开票账单中心生成微信二维码短链接，生成的url可作为app等非微信客户端打开微信小程序的请求地址

> Body 请求参数

```json
{
  "businessScene": "string",
  "sysSource": "string",
  "dataAccountId": "string",
  "ddh": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token，获取方式参见1.01，1.02|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» businessScene|body|string| 是 ||打开页面类型，5-开票列表页面，6-订单开票页面|
|» sysSource|body|string| 是 ||账单中心系统来源标识|
|» dataAccountId|body|string| 是 ||数据中心id|
|» ddh|body|string| 是 ||开票订单号，AES或者DES加密|

> 返回示例

> 200 Response

```json
{
  "errorCode": "string",
  "message": "string",
  "data": {
    "url_link": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» errorCode|string|true|none||结果代码，0-成功|
|» message|string|true|none||错误描述|
|» data|object|true|none||响应结果|
|»» url_link|string|true|none||微信短链接地址|

# 收票/全票池引入

## POST 5.01全票池导入

POST /kapi/app/rim/invoiceImport

导入发票数据至票池。
:::warning[]
本接口正在优化升级中，请您暂时不要进行对接操作，待优化完成后我们会及时通知您。
:::

> Body 请求参数

```json
{
  "invoice": [
    {
      "invoiceType": "string",
      "……": "string",
      "invoiceIndex": 0,
      "expenseInfo": [
        {
          "status": "string",
          "billNo": "string",
          "billId": "string",
          "billType": "string",
          "billTaxNo": "string",
          "orgNumber": "string"
        }
      ],
      "voucherInfo": [
        {
          "vouchNo": "string",
          "accountDate": "string",
          "vouchId": "string",
          "businessDate": "string"
        }
      ]
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» invoice|body|[object]| 是 | 发票|发票数量限制：100|
|»» invoiceType|body|string| 否 | 发票种类|不支持导入的发票类型为：其他发票（invoiceType=11）|
|»» ……|body|string| 否 | 发票信息|发票信息字段详见：[发票数据结构](doc-3656826),不支持导入的发票类型为：其他发票（invoiceType=11）|
|»» invoiceIndex|body|integer| 否 | 发票下标|none|
|»» expenseInfo|body|[object]| 否 | 单据信息|none|
|»»» status|body|string| 是 | 单据状态|1-未报销，30-审批中，60-审批通过|
|»»» billNo|body|string| 是 | 单据编码|none|
|»»» billId|body|string| 否 | 单据id|none|
|»»» billType|body|string| 否 | 单据类型|none|
|»»» billTaxNo|body|string| 否 | 单据所属企业税号|none|
|»»» orgNumber|body|string| 否 | 苍穹组织编码|none|
|»» voucherInfo|body|[object]| 否 | 凭证信息|none|
|»»» vouchNo|body|string| 是 | 凭证编号|none|
|»»» accountDate|body|string| 是 | 所属账期|yyyy-MM|
|»»» vouchId|body|string| 否 | 凭证id|none|
|»»» businessDate|body|string| 否 | 业务日期|yyyy-MM-dd|

> 返回示例

> 200 Response

```json
{
  "data": {
    "fail": [
      {
        "invoiceIndex": "string",
        "msg": "string"
      }
    ],
    "invoiceCount": "string",
    "failCount": "string"
  },
  "message": "string",
  "errorCode": "string",
  "success": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» data|object|true|none|结果集|none|
|»» fail|[object]|true|none|导入失败发票信息|none|
|»»» invoiceIndex|string|false|none|导入失败发票的下标|none|
|»»» msg|string|false|none|导入失败原因|none|
|»» invoiceCount|string|true|none|导入成功发票数量|none|
|»» failCount|string|true|none|导入失败发票数量|none|
|» message|string|true|none|结果描述|none|
|» errorCode|string|true|none||0000-成功|
|» success|boolean|true|none||true或false|

# 收票/查询全票池的发票

## POST 1.03获取单据文件信息

POST /kapi/app/rim/queryCover

- 发票数据结构在文档：《[发票数据结构](doc-3656826)》有描述

> Body 请求参数

```json
{
  "billType": "string",
  "billId": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» billType|body|string| 是 ||单据类型|
|» billId|body|string| 是 ||单据id|

> 返回示例

> 200 Response

```json
{
  "message": "string",
  "errorCode": "string",
  "data": {
    "cover": [
      {
        "localUrl": "string",
        "coverNo": "string",
        "snapshotUrl": "string",
        "fileType": "string"
      }
    ],
    "attachment": [
      {
        "attachmentName": "string",
        "localUrl": "string",
        "snapshotUrl": "string",
        "serialNo": "string",
        "remark": "string",
        "attachmentType": "1"
      }
    ]
  },
  "invoice": [
    {}
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» message|string|true|none||描述信息|
|» errorCode|string|true|none||错误代码，0000-成功|
|» data|object|true|none||none|
|»» cover|[object]|true|none||none|
|»»» localUrl|string|true|none||封面地址|
|»»» coverNo|string|true|none||封面编码|
|»»» snapshotUrl|string|true|none||封面快照|
|»»» fileType|string|true|none||封面类型，1-pdf，2-图片|
|»» attachment|[object]|true|none||none|
|»»» attachmentName|string|true|none||附件名称|
|»»» localUrl|string|true|none||附件地址|
|»»» snapshotUrl|string|false|none||快照地址|
|»»» serialNo|string|false|none||发票流水号，当附件关联发票是有|
|»»» remark|string|false|none||附件备注|
|»»» attachmentType|string|true|none||文件类型|
|» invoice|[object]|true|none||发票结构：[发票数据结构](doc-3656826)|

#### 枚举值

|属性|值|
|---|---|
|attachmentType|1|
|attachmentType|2|
|attachmentType|3|
|attachmentType|4|
|attachmentType|5|
|attachmentType|6|
|attachmentType|7|
|attachmentType|8|

# 收票/税局下载发票和勾选认证

## POST 4.18 出口退税勾选统计查询

POST /kapi/app/rim/deduction

本接口用于支持直连税局电子发票服务平台进行发票用途确认——出口退税统计信息查询，根据自然月份查询纳税人在该月成功提交至税局勾选出口退税的发票、海关缴款书数量的统计数据；
前置条件：
纳税人为小规模纳税人则不支持
仅支持【基础资料-企业信息-发票勾选确认通道】为“电子发票服务平台”的税号，并且保持“收票默认账号”登录且该账号能访问电票平台【勾选确认-退税勾选】模块，方可方位税局查询成功
注意：乐企出口退税勾选即完成用途确认，且乐企不支持查询局端属期出口退税已勾选或确认用途的发票统计信息，接口根据星瀚全票池已认证且用途为出口退税的发票数据统计
税局页面参考：![image.png](https://api.apifox.com/api/v1/projects/3905935/resources/587647/image-preview)

日期 | 变更描述 | 变更人 | 版本 
----  | ---- | ---- | ---- 
2025/12/11 | 新增接口 | 黄潮鑫 | V1.0 |

> Body 请求参数

```json
{
  "businessSystemCode": "string",
  "interfaceCode": "exportRebateStatisticQuery",
  "requestId": "string",
  "data": {
    "taxNo": "string",
    "taxPeriod": "202501",
    "queryType": "1"
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||access_token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» businessSystemCode|body|string| 是 | 来源系统编码|对接不同系统来源编码，用于区分不同系统的回调接口；例如SRM系统，你可以传入SRM|
|» interfaceCode|body|string| 是 | 接口编码|定义本接口的操作种类，传固定字符串值：exportRebateStatisticQuery|
|» requestId|body|string| 否 | 请求ID|定义本次接口的请求ID码，可用当前13位毫秒级时间戳加3位随机数字(总共16位)生成的字符串|
|» data|body|object| 是 ||需要把data的值加密成字符串，默认为base64|
|»» taxNo|body|string| 是 | 纳税人识别号|本次进行统计查询的纳税人识别号（税号）|
|»» taxPeriod|body|string| 否 | 月份|本次进行查询的月份（须小于等于当前自然月），出口退税统计信息按操作发票确认用途的自然月查询|
|»» queryType|body|string| 否 | 查询类型|默认查询当前月份已勾选未确认的统计信息|

#### 枚举值

|属性|值|
|---|---|
|»» queryType|0|
|»» queryType|1|

> 返回示例

> 200 Response

```json
{
  "errorCode": "string",
  "message": "string",
  "success": true,
  "data": {
    "statInfoArr": [
      {
        "statInvoiceType": "01",
        "num": 0,
        "totalTaxAmount": 0
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» errorCode|string|true|none|返回响应码|0000：成功|
|» message|string|true|none|响应描述|none|
|» success|boolean|true|none|请求是否成功|none|
|» data|object|true|none|返回内容data|需要解密，默认为base64|
|»» statInfoArr|[object]|true|none|统计信息（字符数组）|none|
|»»» statInvoiceType|string|true|none|统计的发票；|非具体发票类型，税局只区分专票和海关缴款书|
|»»» num|number|true|none|份数|none|
|»»» totalTaxAmount|number|true|none|本期有效抵扣税额合计|none|

#### 枚举值

|属性|值|
|---|---|
|statInvoiceType|01|
|statInvoiceType|04|

# 收票/识别查验

## POST 2.04 发票编辑

POST /kapi/app/rim/message

非增值税发票，调用【2.02发票识别查验】进行识别，如果识别数据有误，可以调【2.04发票编辑】接口，变更发票信息
本接口返回的发票结构参见：[发票数据结构](doc-3656826)

> Body 请求参数

```json
{
  "messageType": "string",
  "messageId": "string",
  "data": {}
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» messageType|body|string| 是 ||接口类型:invoiceEdit|
|» messageId|body|string| 是 ||请求id|
|» data|body|object| 是 ||发票结构：参见[发票数据结构](doc-3656826)|

> 返回示例

> 200 Response

```json
{
  "success": "string",
  "errorCode": "string",
  "message": "string",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» success|string|true|none|调用结果|true或false|
|» errorCode|string|true|none|错误码|0000-成功|
|» message|string|true|none|结果描述|结果描述|
|» data|object|true|none|发票数据|发票结构：参见[发票数据结构](doc-3656826)|

# 收票/全球发票识别/全球发票识别异步接口

## POST 6.03 回调全球发票识别任务结果

POST /对接方提供的回调地址（对接方必须按照成功响应示例报文返回 json ）

需在星瀚配置对应回调地址

> Body 请求参数

```json
{
  "taskId": "string",
  "taskType": "asyncAiRecognition",
  "created_at": "string",
  "taskStatus": "SUCCESS",
  "errorCode": "2005",
  "errorMessage": "string",
  "data": [
    {
      "serialNo": "string",
      "invoiceType": "30",
      "invoiceNo": "12683726300",
      "invoiceDate": "2025-05-16",
      "totalAmount": "100.00",
      "country": "Singapore",
      "currency": "SGD",
      "buyerName": "string",
      "salerName": "string",
      "totalTaxAmount": "string",
      "verifyResult": "string",
      "invoiceSubType": "380",
      "extJson": {
        "header": {
          "billFrom": {},
          "billTo": {},
          "payment": {},
          "basic": {},
          "bussiness": {}
        },
        "detail": {
          "detailOfGoodsOrServices": [
            null
          ],
          "detailOfTaxSummary": [
            null
          ]
        }
      },
      "invoiceAmount": "string",
      "salerTaxNo": "string",
      "buyerTaxNo": "string",
      "status": "success",
      "errorMessage": "string",
      "errorCode": "2002"
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» taskId|body|string| 是 | 任务号|请求接口返回的任务号|
|» taskType|body|string| 是 | 任务类型|asyncAiRecognition|
|» created_at|body|string| 是 | 时间戳|none|
|» taskStatus|body|string| 是 | 任务状态|none|
|» errorCode|body|string| 否 | 错误码|none|
|» errorMessage|body|string| 是 | 错误描述|none|
|» data|body|[[全球发票返回结果 新](#schema全球发票返回结果 新)]| 是 ||none|
|»» serialNo|body|string| 否 | 系统唯一流水号|none|
|»» invoiceType|body|string| 否 | 票据类型|none|
|»» invoiceNo|body|string| 否 | 发票号码|none|
|»» invoiceDate|body|string| 否 | 开票日期|none|
|»» totalAmount|body|string| 否 | 价税合计|none|
|»» country|body|string| 否 | 国家|none|
|»» currency|body|string| 否 | 币别|none|
|»» buyerName|body|string| 否 | 购方名称|none|
|»» salerName|body|string| 否 | 销方名称|none|
|»» totalTaxAmount|body|string| 否 | 税额|none|
|»» verifyResult|body|string| 否 | 合规性校验结果|verifyFlag为1时，返回的合规性校验结果，参考"进项发票合规校验结果"|
|»» invoiceSubType|body|string| 否 | invoice类型|当票据类型为invoice时返回|
|»» extJson|body|object| 否 | 发票详情数据|包含发票完整的数据，可通过解析获取所需字段|
|»»» header|body|object| 否 | 表头信息|none|
|»»»» billFrom|body|object| 否 | 销方信息|none|
|»»»»» billFromBankAccount|body|string| 否 ||none|
|»»»»» billFromCity|body|string| 否 ||none|
|»»»»» billFromEmail|body|string| 否 ||none|
|»»»»» billFromComposite|body|string| 否 ||none|
|»»»»» billFromTelephone|body|string| 否 ||none|
|»»»»» billFromFax|body|string| 否 ||none|
|»»»»» billFromStateOrProvince|body|string| 否 ||none|
|»»»»» billFromPostalCode|body|string| 否 ||none|
|»»»»» billFromBankOfAccount|body|string| 否 ||none|
|»»»»» billFromCountry|body|string| 否 ||none|
|»»»» billTo|body|object| 否 | 购方信息|none|
|»»»»» billToBankOfAccount|body|string| 否 ||none|
|»»»»» billToEmail|body|string| 否 ||none|
|»»»»» billToPostalCode|body|string| 否 ||none|
|»»»»» billToCity|body|string| 否 ||none|
|»»»»» billToComposite|body|string| 否 ||none|
|»»»»» billToTelephone|body|string| 否 ||none|
|»»»»» billToRecipient|body|string| 否 ||none|
|»»»»» billToBankAccount|body|string| 否 ||none|
|»»»»» billToFax|body|string| 否 ||none|
|»»»»» billToCountry|body|string| 否 ||none|
|»»»»» billToStateOrProvince|body|string| 否 ||none|
|»»»» payment|body|object| 否 | 支付信息|none|
|»»»»» exchangeRate|body|string| 否 ||none|
|»»»»» dueDate|body|string| 否 ||none|
|»»»»» paymentMethod|body|string| 否 ||none|
|»»»»» paymentCurrency|body|string| 否 ||none|
|»»»»» paidAmount|body|string| 否 ||none|
|»»»»» paymentStatus|body|string| 否 ||none|
|»»»»» paymentTerms|body|string| 否 ||none|
|»»»» basic|body|object| 否 | 基础信息|none|
|»»»»» nameOfInvoice|body|string| 否 ||none|
|»»»»» sourceFileHash|body|string| 否 ||none|
|»»»»» page|body|[string]| 否 ||none|
|»»»»» invoiceCode|body|string| 否 ||none|
|»»»» bussiness|body|object| 否 | 业务信息|none|
|»»»»» endDate|body|string| 否 ||none|
|»»»»» purchaseOrderNumber|body|string| 否 ||none|
|»»»»» contractNumber|body|string| 否 ||none|
|»»»»» startDate|body|string| 否 ||none|
|»»» detail|body|object| 否 | 明细信息|none|
|»»»» detailOfGoodsOrServices|body|[object]| 否 | 商品明细信息|none|
|»»»»» unitPrice|body|string| 否 ||none|
|»»»»» taxRate|body|string| 否 ||none|
|»»»»» articleName|body|string| 否 ||none|
|»»»»» quantity|body|string| 否 ||none|
|»»»»» orderNumber|body|string| 否 ||none|
|»»»»» unitOfMeasure|body|string| 否 ||none|
|»»»»» netAmount|body|string| 否 ||none|
|»»»»» articleID|body|string| 否 ||none|
|»»»»» description|body|string| 否 ||none|
|»»»»» tax|body|string| 否 ||none|
|»»»»» grossAmount|body|string| 否 ||none|
|»»»» detailOfTaxSummary|body|[object]| 否 | 税明细信息|none|
|»»»»» taxRate|body|string| 否 ||none|
|»»»»» netTaxableAmount|body|string| 否 ||none|
|»»»»» tax|body|string| 否 ||none|
|»»»»» taxCategory|body|string| 否 ||none|
|»» invoiceAmount|body|string| 否 | 不含税金额|none|
|»» salerTaxNo|body|string| 否 | 销方税号|none|
|»» buyerTaxNo|body|string| 否 | 购方税号|none|
|»» status|body|string| 是 | 状态码|none|
|»» errorMessage|body|string| 否 | 错误描述|none|
|»» errorCode|body|string| 否 | 错误码|none|

#### 枚举值

|属性|值|
|---|---|
|» taskStatus|SUCCESS|
|» taskStatus|FAILED|
|» taskStatus|PARTIAL_SUCCESS|
|» errorCode|2005|
|» errorCode|C0110|
|»» invoiceType|30|
|»» invoiceType|31|
|»» invoiceSubType|380|
|»» invoiceSubType|381|
|»» invoiceSubType|388|
|»» invoiceSubType|325|
|»» status|success|
|»» status|failed|
|»» errorCode|2002|

> 返回示例

> 200 Response

```json
{
    "status": "false",
    "errorCode": "0001",
    "errorMessage": "esse in deserunt Ut"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|string|true|none|调用结果|true或false|
|» errorCode|string|true|none|错误码|0000-成功|
|» errorMessage|string|true|none|错误描述|none|

# 收票/发票签收

## POST 7.01 单据发票签收接口

POST /kapi/v2/rim/message/service

单据发票签收接口用于纸质发票签收比对，比对后更新单据或发票的签收状态。
支持通过单据维度签收单据下所有发票，也支持签收指定发票

> Body 请求参数

```json
{
  "messageType": "billSign",
  "messageId": "string",
  "data": {
    "signType": "01",
    "billId": "string",
    "bussinSysCode": "string",
    "billType": "er_dailyreimbursebill",
    "invoiceData": [
      {
        "serialNo": "string",
        "invoiceType": "1",
        "invoiceNo": "string",
        "invoiceCode": "string",
        "fileDownUrl": "string",
        "fileType": "1"
      }
    ]
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» messageType|body|string| 是 ||接口类型：billSign|
|» messageId|body|string| 是 ||请求id|
|» data|body|object| 是 ||none|
|»» signType|body|string| 是 | 签收类型|01-签收 02-反签收|
|»» billId|body|string| 否 | 单据唯一ID|对接系统中单据的唯一标识符，可用于与其他系统进行数据关联（billtId+bussinSyscode或billtId+billType联合唯一标识）；|
|»» bussinSysCode|body|string| 否 | 来源系统|对接系统数据来源标识，用于区分不同系统的发票来源。命名规范按照品牌+产品的大小写英文命名，长度不超过20字符。如：KdCosmic、KdEAS、KdCloud、KdGalaxy|
|»» billType|body|string| 否 | 单据控制规则编码|发票云系统基础资料中已维护的单据类型，用于区分不同业务场景，如费用报销单、采购订单等。|
|»» invoiceData|body|[object]| 是 | 发票数据|发票信息|
|»»» serialNo|body|string| 否 | 发票流水号|发票流水号或发票类型+发票号码+发票代码 必填|
|»»» invoiceType|body|string| 否 | 发票类型|发票流水号或发票类型+发票号码+发票代码 必填|
|»»» invoiceNo|body|string| 否 | 发票号码|发票流水号或发票类型+发票号码+发票代码 必填|
|»»» invoiceCode|body|string| 否 | 发票代码|发票流水号或发票类型+发票号码+发票代码 必填|
|»»» fileDownUrl|body|string| 否 | 发票文件地址|苍穹文件服务器地址或可以直接打开的http地址|
|»»» fileType|body|string| 否 | 发票文件类型|当发票文件地址有值时，该字段必传|

#### 详细说明

**»» billId**: 对接系统中单据的唯一标识符，可用于与其他系统进行数据关联（billtId+bussinSyscode或billtId+billType联合唯一标识）；
参数限制：数字、英文、下划线；长度不超过50字符

**»» billType**: 发票云系统基础资料中已维护的单据类型，用于区分不同业务场景，如费用报销单、采购订单等。
系统基础资料预置类型：er_dailyreimbursebill（费用报销单），er_checkingpaybill（商旅付款申请单），ap_finapbill（应付单），er_publicreimbursebill（对公报销单），er_tripreimbursebill（差旅报销单），pur_invoice（开票单），ap_invoice（收票单）

**»»» fileType**: 当发票文件地址有值时，该字段必传
1-pdf，2-图片（png/jpg等），4-ofd

#### 枚举值

|属性|值|
|---|---|
|»» signType|01|
|»» signType|02|
|»»» invoiceType|1|
|»»» invoiceType|2|
|»»» invoiceType|3|
|»»» invoiceType|4|
|»»» invoiceType|5|
|»»» invoiceType|12|
|»»» invoiceType|13|
|»»» invoiceType|15|
|»»» invoiceType|26|
|»»» invoiceType|27|
|»»» invoiceType|28|
|»»» invoiceType|29|
|»»» fileType|1|
|»»» fileType|2|
|»»» fileType|4|
|»»» fileType|9|

> 返回示例

> 200 Response

```json
{
  "status": "string",
  "errorCode": "string",
  "message": "string",
  "data": {
    "billId": "string",
    "billNo": "string",
    "bussinSysBillStatus": "13",
    "invoiceData": [
      {
        "serialNo": "string",
        "invoiceType": "string",
        "invoiceNo": "string",
        "invoiceCode": "string",
        "signStatus": "1",
        "message": "string"
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|string|true|none|状态|请求的状态信息，表示接口调用成功返回。<br />true或false|
|» errorCode|string|true|none|失败代码|返回选择发票页面的事件代码，用于后续流程处理。|
|» message|string|true|none|错误描述|错误信息描述，提供详细的错误原因或提示信息。|
|» data|object|true|none||none|
|»» billId|string|false|none|单据id|none|
|»» billNo|string|false|none|单据编号|none|
|»» bussinSysBillStatus|string|false|none|单据状态|13-单据提交审核（含纸质发票或纸质附件，待签收）<br />14-单据提交审核（含纸质发票或纸质附件，已签收）|
|»» invoiceData|[object]|false|none|发票信息|none|
|»»» serialNo|string|false|none|发票流水号|通过调用发票云采集能力获取的发票流水号，用于标识发票信息。32位的随机字符串，由数字和小写字母组成。|
|»»» invoiceType|string|false|none|发票类型|none|
|»»» invoiceNo|string|false|none|发票号码|none|
|»»» invoiceCode|string|false|none|发票代码|none|
|»»» signStatus|string|true|none|签收结果|none|
|»»» message|string|false|none|签收失败原因|none|

#### 枚举值

|属性|值|
|---|---|
|bussinSysBillStatus|13|
|bussinSysBillStatus|14|
|signStatus|1|
|signStatus|0|

# 页面类

## POST 2.1、退出登录API接口

POST /api/logout.do

> Body 请求参数

```json
{
  "access_token": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» access_token|body|string| 是 | access_token|none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 页面类/收票页面

## GET 移动端打开选择发票页面

GET /mobile.html

参照：[《快速开始》](doc-3655357#收票对接)的收票对接一节

> Body 请求参数

```yaml
{}

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|form|query|string| 是 ||页面id，选择发票页面固定值：rim_mobile_index|
|eventCode|query|string| 是 ||收票接口/收票报销/3.01获取的打开选择发票eventCode|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 页面类/数据统计页面

## GET 销项发票统计页面

GET /index.html

打开页面前需要做登录认证，第三方登录对接参照
https://vip.kingdee.com/knowledge/specialDetail/228892721203874816?category=294837154306673920&id=651355093371008256&productLineId=29&lang=zh-CN
页面参数：
{baseurl}/index.html?formId=sim_buyer_report,销项购方统计
{baseurl}/index.html?formId=sim_goods_report,销项商品统计
{baseurl}/index.html?formId=sim_status_report,销项发票状态统计
{baseurl}/index.html?formId=sim_taxrate_report,销项税率统计
{baseurl}/index.html?formId=sim_count_invoice_tab,销项对账汇总
{baseurl}/index.html?formId=sim_menu&menu=report,报表统计-菜单
{baseurl}/index.html?formId=sim_invstatistics_report,资料统计

> Body 请求参数

```yaml
{}

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|body|body|object| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 影像/1.基础接口

## POST 1.01获取eventCode

POST /kapi/app/bds/getEventCode

> Body 请求参数

```json
{
  "scanBillNo": "string",
  "resource": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» scanBillNo|body|string| 是 ||影像编码，多个影像编码用逗号隔开|
|» resource|body|string| 是 ||发票来源，外部系统与星瀚业务约定的常量，同一系统所有接口的来源应保持一致|

> 返回示例

> 200 Response

```json
{
  "success": true,
  "errorCode": "string",
  "message": "string",
  "data": {
    "eventCode": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» success|boolean|true|none||true或false|
|» errorCode|string|true|none||0000为成功|
|» message|string|true|none||错误描述|
|» data|object|true|none||请求结果|
|»» eventCode|string|true|none||加密字符串，作为打开影像页面的参数|

## POST 1.02接收ERP单据推送接口

POST /kapi/app/bds/erpBillPush

> Body 请求参数

```json
{
  "fscanBillNo": "string",
  "fbillId": "string",
  "fbillTypeCode": "FYBX",
  "fbillTypeDes": "费用报销单",
  "fapplyUserName": "string",
  "fapplyUserPhone": "string",
  "fapplyErpUserName": "string",
  "fapplyOrganizationCode": "string",
  "fapplyOrganizationName": "string",
  "resource": "EAS",
  "billNo": "string",
  "taxNo": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» fscanBillNo|body|string| 是 ||影像编码|
|» fbillId|body|string| 是 ||ERP单据为一值（单据整个生命周期都不可变）|
|» fbillTypeCode|body|string| 是 ||单据类型编码|
|» fbillTypeDes|body|string| 否 ||单据类型名称|
|» fapplyUserName|body|string| 否 ||提单人姓名|
|» fapplyUserPhone|body|string| 否 ||提单人电话号码|
|» fapplyErpUserName|body|string| 否 ||提单人ERP用户名（非姓名）|
|» fapplyOrganizationCode|body|string| 否 ||提单组织编码|
|» fapplyOrganizationName|body|string| 否 ||提单组织名称|
|» resource|body|string| 是 ||发票来源，外部系统与星瀚业务约定的常量，同一系统所有接口的来源应保持一致|
|» billNo|body|string| 否 ||单据编码|
|» taxNo|body|string| 否 ||税号|

> 返回示例

> 200 Response

```json
{
  "success": true,
  "errorCode": "string",
  "message": "string",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» success|boolean|true|none||true或false|
|» errorCode|string|true|none||0000为成功|
|» message|string|true|none||错误描述|
|» data|object|true|none||请求结果|

# 影像/2.影像页面

## GET 2.04影像匹配结果页面

GET /{baseUrl}/index.html

> Body 请求参数

```yaml
{}

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|baseUrl|path|string| 是 ||none|
|formId|query|string| 是 ||页面id，选择发票页面固定值：bds_match_list|
|eventCode|query|string| 是 ||1.01获取eventCode|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 2.02移动端影像调阅

GET /{baseUrl}/mobile.html

> Body 请求参数

```yaml
{}

```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|baseUrl|path|string| 是 ||苍穹url|
|form|query|string| 是 ||页面id，选择发票页面固定值：bds_mobile_image_list|
|eventCode|query|string| 是 ||1.01获取eventCode|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 影像/3.影像操作

## POST 3.06影像状态查询

POST /kapi/app/bds/operate

> Body 请求参数

```json
{
  "operateType": "string",
  "operateId": "string",
  "data": {
    "scanBillNo": "string",
    "resource": "string"
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||参考授权接口|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» operateType|body|string| 是 ||接口类型：queryBillStatus|
|» operateId|body|string| 是 ||请求id|
|» data|body|object| 是 ||请求参数|
|»» scanBillNo|body|string| 是 ||影像编码|
|»» resource|body|string| 是 ||发票来源，外部系统与星瀚业务约定的常量，同一系统所有接口的来源应保持一致|

> 返回示例

> 200 Response

```json
{
  "success": "string",
  "errorCode": "string",
  "message": "string",
  "data": {
    "imageStatus": "1",
    "billType": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» success|string|true|none||true或false|
|» errorCode|string|true|none||0000-成功|
|» message|string|true|none||结果描述|
|» data|object|true|none||none|
|»» imageStatus|string|true|none||影像状态|
|»» billType|string|true|none||单据类型|

#### 枚举值

|属性|值|
|---|---|
|imageStatus|1|
|imageStatus|2|
|imageStatus|9|
|imageStatus|5|
|imageStatus|3|
|imageStatus|4|
|imageStatus|0|
|imageStatus|10|
|imageStatus|11|
|imageStatus|12|
|imageStatus|13|
|imageStatus|14|
|imageStatus|15|
|imageStatus|16|
|imageStatus|17|
|imageStatus|18|

# 影像/4.采集接口

## POST 4.01影像文件采集

POST /kapi/app/bds/fileCollect

base64和fileDownUrl至少需要其中一个。

> Body 请求参数

```json
{
  "base64": "string",
  "fileDownUrl": "string",
  "fileSuffix": "string",
  "fileType": "string",
  "scanBillNo": "string",
  "billType": "string",
  "resource": "string",
  "needRecognition": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» base64|body|string| 是 ||文件base64|
|» fileDownUrl|body|string| 是 ||文件下载地址，无授权文件地址或者苍穹服务器的path路径|
|» fileSuffix|body|string| 是 ||文件后缀|
|» fileType|body|string| 否 ||文件类型，invoice-发票，cover-封面，attach-附件。默认为附件|
|» scanBillNo|body|string| 是 ||影像编码--保证影像编码+来源唯一|
|» billType|body|string| 是 ||单据类型，在发票云-基础资料-收票资料维护-单据类型维护|
|» resource|body|string| 是 ||发票来源，外部系统与星瀚业务约定的常量，同一系统所有接口的来源应保持一致。收单机对接固定来源：REG_SDJ|
|» needRecognition|body|string| 是 ||是否需要识别，默认不识别，为1时走识别|

> 返回示例

> 200 Response

```json
{
  "success": "string",
  "errorCode": "string",
  "message": "string",
  "data": {
    "srcPath": "string",
    "fileNo": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» success|string|true|none||true或false|
|» errorCode|string|true|none||0000-成功|
|» message|string|true|none||结果描述|
|» data|object|true|none||none|
|»» srcPath|string|true|none||原文件path|
|»» fileNo|string|true|none||文件流水号|

## POST 4.02影像单据提交

POST /kapi/app/bds/scanBillSubmit

base64和fileDownUrl至少需要其中一个。
fileNo文件流水号和srcPath原文件文件地址至少填写一个。

> Body 请求参数

```json
{
  "scanBillNo": "string",
  "resource": "string",
  "billType": {},
  "modelType": "string",
  "saveType": "string",
  "isSubmitErp": "string",
  "fileList": [
    {
      "fileNo": "string",
      "srcPath": "string"
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» scanBillNo|body|string| 是 ||影像编码--保证影像编码+来源唯一|
|» resource|body|string| 是 ||发票来源，外部系统与星瀚业务约定的常量，同一系统所有接口的来源应保持一致|
|» billType|body|object| 是 ||单据类型，在发票云-基础资料-收票资料维护-单据类型维护|
|» modelType|body|string| 否 ||未找到影像单据时是否新增，1-新增，0-不新增。默认：0|
|» saveType|body|string| 否 ||保存方式，upload-覆盖更新，add-追加。默认：upload|
|» isSubmitErp|body|string| 是 ||是否自动提交Erp，0-否，1-是|
|» fileList|body|[object]| 是 ||none|
|»» fileNo|body|string| 否 ||4.01影像文件采集接口返回的文件流水号|
|»» srcPath|body|string| 否 ||4.01影像文件采集接口返回的文原文件path|

> 返回示例

> 200 Response

```json
{
  "success": "string",
  "errorCode": "string",
  "message": "string",
  "data": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» success|string|true|none||true或false|
|» errorCode|string|true|none||0000-成功|
|» message|string|true|none||结果描述|
|» data|object|true|none||none|

# 设置类

## POST 3.4、查询电子税局账号

POST /kapi/app/sim/openApi

> Body 请求参数

```json
{
    "requestId": "string",
    "businessSystemCode": "string",
    "interfaceCode": "ALLE.ACCOUNT.CHECK",
    "data": {
        "taxno": "税号"
    }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 否 ||none|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» requestId|body|string| 是 ||时间戳|
|» businessSystemCode|body|string| 是 ||对接不同系统来源编码，用于区分不同系统的回调接口|
|» interfaceCode|body|string| 是 ||接口业务编码|
|» data|body|object| 是 ||none|
|»» taxno|body|string| 是 ||税号|

> 返回示例

```json

```

```json
{
    "errorCode": "string",
    "message": "string",
    "data": [
        {
            "etaxAccount": "string",
            "etaxAccountType": "string",
            "defaultFlag": "string",
            "defaultType": "string"
        }
    ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» errorCode|string|true|none||0为成功|
|» message|string|true|none||错误信息|
|» data|[object]|true|none||none|
|»» etaxAccount|string|true|none||用户账号|
|»» etaxAccountType|string|true|none||税局权限：1.开票 2.收票 3.开票+收票 4.都没有|
|»» defaultFlag|string|true|none||默认账号：1.是 0.否|
|»» defaultType|string|true|none||默认业务：0-无 1-开票 2-收票 3-开票+收票|

## POST 3.1、切换组织

POST /kapi/app/bdm/switchorg

> Body 请求参数

```json
{
  "orgNumber": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||前一步生成的access_token|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» orgNumber|body|string| 是 ||组织编码|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 3.2、新增组织（星空ERP专用）

POST /trdPlatform/add/org

1、星空新增星瀚组织，会同时对税号或税盘进行授权；
2、税号或税盘授权，前提是需在kbc下单购买对应的产品，并绑定税号或税盘进行激活；
3、若未经过订单激活过程，则会提示对应税号或税盘授权失败。

> Body 请求参数

```json
{
  "orgList": [
    {
      "taxNo": "string",
      "orgNo": "string",
      "orgName": "string",
      "equipmentNos": [
        {
          "equipmentNo": "string",
          "equipmentType": 0,
          "equipmentName": "string",
          "paperCommonQuota": 0,
          "paperSpecialQuota": 0,
          "eleCommonQuota": 0,
          "eleSpecialQuota": 0,
          "payee": "string",
          "reviewer": "string",
          "drawer": "string"
        }
      ]
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|Content-Type|header|string| 是 ||none|
|Authorization|header|string| 是 ||none|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» orgList|body|[object]| 是 ||组织列表|
|»» taxNo|body|string| 否 ||税号|
|»» orgNo|body|string| 否 ||星空组织编码|
|»» orgName|body|string| 否 ||星空组织名称|
|»» equipmentNos|body|[object]| 否 ||设备列表|
|»»» equipmentNo|body|string| 否 ||设备编号|
|»»» equipmentType|body|number| 否 ||设备类型 0 税务UKEY, 1 税控盘, 2 金税盘|
|»»» equipmentName|body|string| 否 ||设备名称|
|»»» paperCommonQuota|body|number| 否 ||纸质普票限额|
|»»» paperSpecialQuota|body|number| 否 ||纸质专票票限额|
|»»» eleCommonQuota|body|number| 否 ||电子普票限额|
|»»» eleSpecialQuota|body|number| 否 ||电子专票限额|
|»»» payee|body|string| 否 ||付款人|
|»»» reviewer|body|string| 否 ||复核人|
|»»» drawer|body|string| 否 ||开票人|

> 返回示例

> 200 Response

```json
{
	"data": [
		{
			"equipmentNo": "44555555555511",
			"flag": false,
			"msg": "税盘未通过订单激活",
			"taxNo": "91510000673516714K"
		},
		{
			"flag": false,
			"msg": "税号未通过订单激活",
			"taxNo": "91440101MA5CQYUB21"
		}
	],
	"description": "成功",
	"errcode": "0000"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» description|string|true|none||描述|
|» errcode|string|true|none||错误码 0000为成功，其他为失败|
|» data|[object]|false|none||会返回授权失败的税号或税盘信息列表，若为空则全部授权成功|
|»» taxNo|string|false|none||税号|
|»» equipmentNo|string|false|none||设备编码|
|»» flag|boolean|false|none||是否授权成功|
|»» msg|string|false|none||描述|

## POST 3.3、新增租户组织下的员工

POST /trdPlatform/add/employee

# 授权注册接口说明
&gt;发票云关于第三方授权发送与租户注册相关接口说明

## 一、调用说明
&gt;以下小节对相关业务场景的接口调用数据流与顺序进行简要说明

&lt;a name=&quot;app_register&quot;&gt;&lt;/a&gt;
### 1.1 线下应用平台注册
&gt;线下平台提供相关的平台信息资料到发票云，由发票云对平台进行注册，并将授权信息通过邮件方式交付都按平台方

本流程暂未有线上流程，申请资料与交付流程均走线下。

**平台需提供的字段**

|字段|类型|是否必须|描述|
|:-|:-:|:-:|:-|
|name|string|是|平台简称|
|epName|string|是|平台注册企业名称|
|epTaxno|string|是|平台注册企业税号|
|epAddr|string|否|平台注册企业地址|
|epTelno|string|否|平台注册企业联系电话|
|adminName|string|否|平台方管理员，也作为紧急联系人 |
|adminPhone|string|否|平台方管理员手机号|
|adminEmail|string|否|平台方管理员邮箱  |

**发票云返回的字段**

|字段|类型|描述|
|:-|:-:|:-|
|clientId|string|平台clientId|
|clientSecret|string|平台clientSecret|
|enckey|string|平台加密key|

### 1.2 线下平台新租户注册，订单激活
&gt;第三方平台新用户在使用发票云相关功能模块时，需要先对租户进行注册，订单进行激活，目前采用线下的模式，平台方把租户信息、企业信息、产品信息提供到发票云，**线下流程完成后，最终会将租户的appid/appSecret/tenantid/用户访问页面域名，以及企业的组织编号等信息，通过邮件返回给用户**；

#### 每个用户的页面访问域名是根据tenantid而不一样，若只有一个租户则是相同的

### 1.3 全流程图
![](http://ec2-52-83-46-230.cn-northwest-1.compute.amazonaws.com.cn:9999/upload/pageImage/1f77c8b4d032237e1259dcf13dc4e780/1640912815调用链路.png)

> Body 请求参数

```json
{
  "employees": [
    {
      "name": "string",
      "phone": "string",
      "email": "string",
      "orgNumber": [
        "string"
      ]
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|Content-Type|header|string| 是 ||none|
|Authorization|header|string| 是 ||none|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» employees|body|[object]| 是 ||员工信息数组|
|»» name|body|string| 否 ||用户名称|
|»» phone|body|string| 否 ||用户手机号，和邮箱，两者必传其一|
|»» email|body|string| 否 ||用户邮箱，和手机号，两者必传其一|
|»» orgNumber|body|[string]| 否 ||企业组织编码数组|

> 返回示例

> 200 Response

```json
{
    
    "errcode": "0000",
    "description": "成功"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» description|string|true|none||描述|
|» errcode|string|true|none||错误码 0000为成功，其他为失败|

# 订单

## POST 1.01 产品订阅（平台服务商专用）

POST /ierp/kapi/app/ocm/ThirdPlatOrderApi

> Body 请求参数

```json
{
  "opType": "addCosmicApiOrder",
  "systemSource": "string",
  "callbackUrl": "string",
  "thirdOrderNo": "string",
  "data": {
    "taxUserList": [
      {
        "middleNumber": {},
        "roleText": "string",
        "etaxPassword": "string",
        "etaxAccount": "string"
      }
    ],
    "companyInfo": {
      "contactEmail": "string",
      "companyName": "string",
      "taxNo": "string",
      "companyType": "string",
      "areaCode": "string",
      "registerAddress": "string",
      "bankName": "string",
      "bankAccount": {},
      "contactName": "string"
    },
    "collectChannel": 0,
    "taxChannel": 0,
    "taxDeviceList": [
      {
        "deviceType": 0,
        "deviceNo": "string"
      }
    ]
  },
  "orderContent": [
    {
      "product_end_date": "string",
      "product_start_date": "string",
      "subscribe_days": 0,
      "productName": 0
    }
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|query|string| 是 ||{access_token}|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» opType|body|string| 是 ||固定：addCosmicApiOrder|
|» systemSource|body|string| 是 ||来源；由发票云线下给出|
|» callbackUrl|body|string| 否 ||回调地址，用于开票结果通知；订阅开票产品必填|
|» thirdOrderNo|body|string| 是 ||订单id，由平台服务商生成，用来双方系统对账使用|
|» data|body|object| 是 ||纳税人信息（整个data内容需要进行加密）|
|»» taxUserList|body|[object]| 是 ||账号列表，目前暂时用第一个|
|»»» middleNumber|body|object| 否 ||中间号；已购买中间号的客户填写|
|»»» roleText|body|string| 否 ||登录身份: 财务负责人, 法定代表人, 办税员, 购票员, 普通管理员, 开票员, 其他|
|»»» etaxPassword|body|string| 否 ||电子税局登录密码|
|»»» etaxAccount|body|string| 否 ||电子税局登录账号；一般为手机号码，也可以是姓名|
|»» companyInfo|body|object| 是 ||企业相关信息内容|
|»»» contactEmail|body|string| 否 ||企业管理员联系邮箱，若同时想接收出初始化的指引邮件，则必填|
|»»» companyName|body|string| 是 ||纳税人名称|
|»»» taxNo|body|string| 是 ||纳税人识别号|
|»»» companyType|body|string| 是 ||企业类型；03: 一般纳税人, 02: 小规模纳税人|
|»»» areaCode|body|string| 是 ||地区编码(参考码表)；如果是开票，则必填|
|»»» registerAddress|body|string| 否 ||注册地址|
|»»» bankName|body|string| 否 ||银行名称|
|»»» bankAccount|body|object| 否 ||银行账号|
|»»» contactName|body|string| 否 ||企业联系人|
|»» collectChannel|body|number| 是 ||收票通道：1: RPA, 2: 软证书； 3：乐企,  默认为：1 RPA|
|»» taxChannel|body|number| 是 ||税局开票通道：1: RPA, 2: 乐企, 3: 服务商；默认为: 1|
|»» taxDeviceList|body|[object]| 是 ||税盘相关信息内容|
|»»» deviceType|body|number| 否 ||税盘类型，10航信单机盘 11航信托管盘 12 百望单机盘  13 百望托管盘  14税务UKEY|
|»»» deviceNo|body|string| 否 ||税盘设备编号|
|» orderContent|body|[object]| 是 ||订单内容|
|»» product_end_date|body|string| 否 ||约定结束时间（格式：YYYY-MM-DD）|
|»» product_start_date|body|string| 否 ||约定开始时间（格式：YYYY-MM-DD）|
|»» subscribe_days|body|number| 否 ||订阅产品的服务周期（单位：天）|
|»» productName|body|number| 否 ||订阅产品：1: 云API开票, 2: 云API收票；默认为：1；元素类型是number|

> 返回示例

> 200 Response

```json
{
  "data": {
    "addressUrl": "string",
    "accountId": "string",
    "appId": "string",
    "appSecuret": "string",
    "user": "string",
    "businessSystemCode": "string",
    "aesKey": "string",
    "userType": "string",
    "requestUrl": "string"
  },
  "message": "string",
  "errorCode": "string",
  "success": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» data|object|true|none||none|
|»» addressUrl|string|true|none||RPA初始化的界面地址（即H5地址 addressUrl）|
|»» accountId|string|true|none||数据中心id，用于获取access_token|
|»» appId|string|true|none||应用授权id,用于获取access_token|
|»» appSecuret|string|true|none||应用授权秘钥,用于获取access_token|
|»» user|string|true|none||用户|
|»» businessSystemCode|string|true|none||业务系统编码|
|»» aesKey|string|true|none||加密密钥|
|»» userType|string|true|none||用户类型|
|»» requestUrl|string|true|none||星瀚发票云平台地址|
|» message|string|true|none||描述|
|» errorCode|string|true|none||返回码|
|» success|boolean|true|none||返回成功状态|

## POST 发票云创建组织

POST /sim/openApi

> Body 请求参数

```json
{
  "requestId": "string",
  "businessSystemCode": "string",
  "interfaceCode": "YYPT.ADD.ORG",
  "data": {
    "companyName": "string",
    "taxNo": "string",
    "systemSource": "string",
    "callbackUrl": "string",
    "taxChannel": "string",
    "productName": "string",
    "collectChannel": "string",
    "tenantInfo": {
      "clientId": "string",
      "clientSecret": "string",
      "encryptKey": "string",
      "tenantName": "string",
      "tenantNo": "string"
    },
    "taxUserList": [
      {
        "etaxPassword": "string",
        "etaxAccount": "string"
      }
    ]
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|access_token|header|string| 否 ||none|
|body|body|object| 否 ||none|
|» requestId|body|string| 是 ||none|
|» businessSystemCode|body|string| 是 ||固定传 BUSINESS_SYSTEM|
|» interfaceCode|body|string| 是 ||固定传 YYPT.ADD.ORG|
|» data|body|object| 是 ||none|
|»» companyName|body|string| 是 ||none|
|»» taxNo|body|string| 是 ||none|
|»» systemSource|body|string| 是 ||对应发票云的业务系统编码|
|»» callbackUrl|body|string| 是 ||回调地址|
|»» taxChannel|body|string| 是 ||税局开票通道：1: RPA, 2: 乐企, 3: 服务商；默认为: 1|
|»» productName|body|string| 是 ||订阅产品：1: 云API开票, 2: 云API收票；默认为：1；元素类型是number|
|»» collectChannel|body|string| 是 ||税局开票通道：1: RPA, 2: 乐企, 3: 服务商；默认为: 1|
|»» tenantInfo|body|object| 是 ||none|
|»»» clientId|body|string| 是 ||none|
|»»» clientSecret|body|string| 是 ||none|
|»»» encryptKey|body|string| 是 ||none|
|»»» tenantName|body|string| 是 ||none|
|»»» tenantNo|body|string| 是 ||none|
|»» taxUserList|body|[object]| 是 ||none|
|»»» etaxPassword|body|string| 否 ||none|
|»»» etaxAccount|body|string| 否 ||none|

> 返回示例

> 200 Response

```json
{
  "data": {
    "requestUrl": "string",
    "appId": "string",
    "appSecuret": "string",
    "accountId": "string",
    "user": "string",
    "aesKey": "string",
    "businessSystemCode": "string",
    "userType": "string"
  },
  "errorCode": "string",
  "status": true,
  "success": true
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» data|object|true|none||none|
|»» requestUrl|string|true|none||none|
|»» appId|string|true|none||none|
|»» appSecuret|string|true|none||none|
|»» accountId|string|true|none||none|
|»» user|string|true|none||none|
|»» aesKey|string|true|none||none|
|»» businessSystemCode|string|true|none||none|
|»» userType|string|true|none||none|
|» errorCode|string|true|none||none|
|» status|boolean|true|none||none|
|» success|boolean|true|none||none|

# 数据模型

<h2 id="tocS_不动产租赁">不动产租赁</h2>

<a id="schema不动产租赁"></a>
<a id="schema_不动产租赁"></a>
<a id="tocS不动产租赁"></a>
<a id="tocs不动产租赁"></a>

```json
{
  "provinceAdress": "string",
  "cityAdreess": "string",
  "simpleAddress": "string",
  "detailAddress": "string",
  "crossCitySign": "0",
  "areaunit": "平方千米",
  "startLeaseDate": "2019-08-24",
  "endLeaseDate": "2019-08-24",
  "estateId": "string",
  "specialIndustryNumber": "string",
  "carBrandNo": "string"
}

```

不动产租赁必填，发票云版本5.0.017支持

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|provinceAdress|string|true|none||省份|
|cityAdreess|string|true|none||城市|
|simpleAddress|string|false|none||不动产地址 ；不动产地址+不动产详细地址总长度限制为120|
|detailAddress|string|true|none||不动产详细地址；不动产地址+不动产详细地址总长度限制为120|
|crossCitySign|string|false|none||跨地（市）标志|
|areaunit|string|true|none||面积单位|
|startLeaseDate|string(date)|true|none||租赁开始日期 格式为yyyy-MM-dd|
|endLeaseDate|string(date)|true|none||租赁结束日期 格式为yyyy-MM-dd|
|estateId|string|true|none||房屋产权证书/不动产权证号|
|specialIndustryNumber|string|false|none||不动产基础资料编码：其他（除日期）参数为空时，自动根据该编号对应的基础资料补全剩余参数|
|carBrandNo|string|false|none||车牌号|

#### 枚举值

|属性|值|
|---|---|
|crossCitySign|0|
|crossCitySign|1|
|areaunit|平方千米|
|areaunit|平方米|
|areaunit|公顷|
|areaunit|亩|
|areaunit|h㎡|
|areaunit|k㎡|
|areaunit|㎡|

<h2 id="tocS_建筑服务">建筑服务</h2>

<a id="schema建筑服务"></a>
<a id="schema_建筑服务"></a>
<a id="tocS建筑服务"></a>
<a id="tocs建筑服务"></a>

```json
{
  "simpleAddress": "string",
  "detailAddress": "string",
  "crossCitySign": "0",
  "buildingName": "string",
  "landTaxNo": "string",
  "specialIndustryNumber": "string",
  "crossCityTaxVerifyNo": "string"
}

```

建筑服务必填，发票云版本5.0.017支持

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|simpleAddress|string|true|none||建筑服务发生地|
|detailAddress|string|true|none||具体地址|
|crossCitySign|string|false|none||跨地（市）标志|
|buildingName|string|true|none||建筑项目名称|
|landTaxNo|string|false|none||土地增值税项目编号|
|specialIndustryNumber|string|false|none||不动产基础资料编码：其他参数为空时，自动根据该编号对应的基础资料补全剩余参数|
|crossCityTaxVerifyNo|string|false|none||跨区域涉税事项报验管理编号，当跨地市标志为是时必填|

#### 枚举值

|属性|值|
|---|---|
|crossCitySign|0|
|crossCitySign|1|

<h2 id="tocS_不动产销售">不动产销售</h2>

<a id="schema不动产销售"></a>
<a id="schema_不动产销售"></a>
<a id="tocS不动产销售"></a>
<a id="tocs不动产销售"></a>

```json
{
  "estateCode": "string",
  "provinceAdress": "string",
  "cityAdreess": "string",
  "simpleAddress": "string",
  "detailAddress": "string",
  "crossCitySign": "0",
  "landTaxNo": "string",
  "approvedPrice": "string",
  "actualTurnover": "string",
  "areaunit": "平方千米",
  "estateId": "string",
  "specialIndustryNumber": "string"
}

```

不动产销售必填，发票云版本5.0.020支持

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|estateCode|string|false|none||不动产单元代码/网签合同备案编号|
|provinceAdress|string|true|none||省份|
|cityAdreess|string|true|none||城市|
|simpleAddress|string|true|none||不动产地址  ，不动产地址+不动产详细地址总长度限制为120|
|detailAddress|string|true|none||不动产详细地址，不动产地址+不动产详细地址总长度限制为120|
|crossCitySign|string|true|none||跨地（市）标志|
|landTaxNo|string|false|none||土地增值税项目编号|
|approvedPrice|string|false|none||核定计税价格|
|actualTurnover|string|false|none||实际成交含税金额：按核定计税价格征税的，必填|
|areaunit|string|true|none||面积单位|
|estateId|string|false|none||房屋产权证书/不动产权证号|
|specialIndustryNumber|string|false|none||不动产基础资料编码：其他参数为空时，自动根据该编号对应的基础资料补全剩余参数|

#### 枚举值

|属性|值|
|---|---|
|crossCitySign|0|
|crossCitySign|1|
|areaunit|平方千米|
|areaunit|平方米|
|areaunit|公顷|
|areaunit|亩|
|areaunit|h㎡|
|areaunit|k㎡|
|areaunit|㎡|

<h2 id="tocS_货物运输服务">货物运输服务</h2>

<a id="schema货物运输服务"></a>
<a id="schema_货物运输服务"></a>
<a id="tocS货物运输服务"></a>
<a id="tocs货物运输服务"></a>

```json
[
  {
    "startPlace": "string",
    "endPlace": "string",
    "transportType": "铁路运输",
    "licensePlate": "string",
    "transportGoods": "string"
  }
]

```

货物运输服务必填，发票云版本5.0.022支持

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|startPlace|string|true|none||起运地 省市区县|
|endPlace|string|true|none||到达地 省市区县|
|transportType|string|true|none||运输工具种类|
|licensePlate|string|true|none||运输工具牌号|
|transportGoods|string|true|none||运输货物名称|

#### 枚举值

|属性|值|
|---|---|
|transportType|铁路运输|
|transportType|公路运输|
|transportType|水路运输|
|transportType|航空运输|
|transportType|管道运输|
|transportType|其它运输工具|

<h2 id="tocS_旅客运输">旅客运输</h2>

<a id="schema旅客运输"></a>
<a id="schema_旅客运输"></a>
<a id="tocS旅客运输"></a>
<a id="tocs旅客运输"></a>

```json
[
  {
    "traveler": "string",
    "cardType": "100",
    "cardNo": "string",
    "travelDate": "2024-04-02",
    "startPlace": "广东省深圳市宝安区",
    "endPlace": "广东省东莞市南城区",
    "transportType": "1",
    "seatClass": "一等座"
  }
]

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|traveler|string|true|none||出行人|
|cardType|string|true|none||出行人证件类型|
|cardNo|string|true|none||出行人证件号码|
|travelDate|string(date)|true|none||出行日期，日期格式YYYY-MM-DD|
|startPlace|string|true|none||出发地（省市区县）|
|endPlace|string|true|none||到达地 （省市区县）|
|transportType|string|true|none||交通工具类型|
|seatClass|string|true|none||等级（等级 若交通工具类型选择“火车、飞机、船舶”，则等级为必填项，否则为非必填项）|

#### 枚举值

|属性|值|
|---|---|
|cardType|100|
|cardType|101|
|cardType|102|
|cardType|103|
|cardType|199|
|cardType|200|
|cardType|201|
|cardType|202|
|cardType|203|
|cardType|204|
|cardType|205|
|cardType|206|
|cardType|207|
|cardType|208|
|cardType|209|
|cardType|210|
|cardType|211|
|cardType|212|
|cardType|213|
|cardType|214|
|cardType|215|
|cardType|216|
|cardType|217|
|cardType|218|
|cardType|219|
|cardType|220|
|cardType|221|
|cardType|222|
|cardType|223|
|cardType|224|
|cardType|225|
|cardType|226|
|cardType|227|
|cardType|228|
|cardType|229|
|cardType|230|
|cardType|231|
|cardType|232|
|cardType|233|
|cardType|234|
|cardType|235|
|cardType|236|
|cardType|237|
|cardType|238|
|cardType|239|
|cardType|240|
|cardType|241|
|cardType|291|
|cardType|299|
|transportType|1|
|transportType|2|
|transportType|3|
|transportType|4|
|transportType|5|
|transportType|6|
|transportType|7|
|transportType|9|
|seatClass|一等座|
|seatClass|二等座|
|seatClass|软席（软座、软卧）|
|seatClass|硬席（硬座、硬卧）|
|seatClass|公务舱|
|seatClass|头等舱|
|seatClass|经济舱|
|seatClass|一等舱|
|seatClass|二等舱|
|seatClass|三等舱|

<h2 id="tocS_车船税明细">车船税明细</h2>

<a id="schema车船税明细"></a>
<a id="schema_车船税明细"></a>
<a id="tocS车船税明细"></a>
<a id="tocs车船税明细"></a>

```json
{
  "policyNo": "string",
  "shipsNo": "string",
  "periodStartDate": "string",
  "periodEndDate": "string",
  "vehicleCode": "string",
  "vehicleVesselAmount": 0,
  "vehicleLateAmount": 0,
  "vehicleTotalAmount": 0
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|policyNo|string|true|none||保险单号，字符40位|
|shipsNo|string|true|none||车牌号/船舶登记号，字符40位|
|periodStartDate|string|true|none||税款所属期起，格式：yyyy-MM|
|periodEndDate|string|true|none||税款所属期止，格式：yyyy-MM|
|vehicleCode|string|true|none||车辆识别代码/车架号码，字符17位|
|vehicleVesselAmount|number|true|none||代收车船税金额|
|vehicleLateAmount|number|true|none||滞纳金金额|
|vehicleTotalAmount|number|true|none||金额合计|

<h2 id="tocS_医疗服务（住院）--开发中">医疗服务（住院）--开发中</h2>

<a id="schema医疗服务（住院）--开发中"></a>
<a id="schema_医疗服务（住院）--开发中"></a>
<a id="tocS医疗服务（住院）--开发中"></a>
<a id="tocs医疗服务（住院）--开发中"></a>

```json
{
  "medicalBizSerialNo": "string",
  "patientName": "string",
  "patientIdTypeCode": "101",
  "patientIdNo": "string",
  "patientGenderCode": "1",
  "medicalRecordNo": "string",
  "hospitalizationNo": "string",
  "hospitalDepartment": "string",
  "hospitalizationStartDate": "yyyy-MM-dd",
  "hospitalizationEndDate": "yyyy-MM-dd",
  "medicalInstitutionTypeCode": "A",
  "otherMedicalInstitutionType": "string",
  "medicalInsuranceTypeCode": "01",
  "otherMedicalInsuranceType": "string",
  "medicalInsuranceNo": "string",
  "insurancePoolFundAmount": "string",
  "otherPaymentAmount": "string",
  "personalAccountAmount": "string",
  "personalCashAmount": "string",
  "personalSelfPayAmount": "string",
  "personalOutOfPocketAmount": "string",
  "prepaidAmount": "string",
  "supplementaryAmount": "string",
  "refundAmount": "string",
  "inpatientCharges": [
    {
      "detailSeq": "string",
      "expenseDetail": "string",
      "quantity": "string",
      "unit": "string",
      "amount": "string",
      "taxFlag": 0,
      "taxRate": "string",
      "taxAmount": "string",
      "medicalServiceStandardCode": "string",
      "remark": "string"
    }
  ]
}

```

医疗服务（住院）

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|medicalBizSerialNo|string|true|none|医疗业务流水号|none|
|patientName|string|true|none|患者姓名|none|
|patientIdTypeCode|[经办人证件类型](#schema经办人证件类型)|true|none|患者身份证件类型代码|证件类型，数电发票农产品收购类必填|
|patientIdNo|string|true|none|患者身份证件号码|none|
|patientGenderCode|string|true|none|性别|none|
|medicalRecordNo|string|true|none|病历号|none|
|hospitalizationNo|string|true|none|住院号|none|
|hospitalDepartment|string|true|none|住院科别|none|
|hospitalizationStartDate|string|true|none|住院时间起|none|
|hospitalizationEndDate|string|true|none|住院时间止|none|
|medicalInstitutionTypeCode|[医疗机构类型代码](#schema医疗机构类型代码)|true|none|医疗机构类型代|none|
|otherMedicalInstitutionType|string|false|none|其他医疗机构类型|none|
|medicalInsuranceTypeCode|[医保类型](#schema医保类型)|true|none|医保类型|none|
|otherMedicalInsuranceType|string|false|none|其他医保类型|medicalInsuranceTypeCode=04时必填|
|medicalInsuranceNo|string|false|none|医保编号|none|
|insurancePoolFundAmount|string|false|none|医保统筹基金支付金额|none|
|otherPaymentAmount|string|false|none|其他支付金额|none|
|personalAccountAmount|string|false|none|个人账户支付金额|none|
|personalCashAmount|string|false|none|个人现金支付金额|none|
|personalSelfPayAmount|string|false|none|个人自付金额|none|
|personalOutOfPocketAmount|string|false|none|个人自费金额|none|
|prepaidAmount|string|false|none|预缴金额|none|
|supplementaryAmount|string|false|none|补缴金额|none|
|refundAmount|string|false|none|退费金额|none|
|inpatientCharges|[object]|true|none|住院收费明细|none|
|» detailSeq|string|true|none|明细序号|填写items[]的顺序，多行收费明细可以对应同一行发票的商品行|
|» expenseDetail|string|true|none|费用明细|none|
|» quantity|string|false|none|数量|none|
|» unit|string|false|none|单位|none|
|» amount|string|true|none|金额（含税）|含税|
|» taxFlag|number|true|none|含税标志|含税标记 0:不含税1:含税|
|» taxRate|string|true|none|增值税税率/征收率|none|
|» taxAmount|string|true|none|税额|none|
|» medicalServiceStandardCode|string|false|none|医疗服务贯标码|none|
|» remark|string|false|none|备注|none|

#### 枚举值

|属性|值|
|---|---|
|patientGenderCode|1|
|patientGenderCode|2|

<h2 id="tocS_医疗服务（门诊）">医疗服务（门诊）</h2>

<a id="schema医疗服务（门诊）"></a>
<a id="schema_医疗服务（门诊）"></a>
<a id="tocS医疗服务（门诊）"></a>
<a id="tocs医疗服务（门诊）"></a>

```json
{
  "medicalBizSerialNo": "string",
  "patientName": "string",
  "patientIdTypeCode": "101",
  "patientIdNo": "string",
  "patientGenderCode": "1",
  "outpatientNo": "string",
  "outpatientVisitTime": "string",
  "medicalInstitutionTypeCode": "A",
  "otherMedicalInstitutionType": "string",
  "medicalInsuranceTypeCode": "01",
  "otherMedicalInsuranceType": "string",
  "medicalInsuranceNo": "string",
  "insurancePoolFundAmount": "string",
  "otherPaymentAmount": "string",
  "personalAccountAmount": "string",
  "personalCashAmount": "string",
  "personalSelfPayAmount": "string",
  "personalOutOfPocketAmount": "string"
}

```

医疗服务（门诊）

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|medicalBizSerialNo|string|true|none|医疗业务流水号|none|
|patientName|string|true|none|患者姓名|none|
|patientIdTypeCode|[经办人证件类型](#schema经办人证件类型)|true|none|患者身份证件类型代码|证件类型，数电发票农产品收购类必填|
|patientIdNo|string|true|none|患者身份证件号码|none|
|patientGenderCode|string|true|none|性别|none|
|outpatientNo|string|true|none|门诊号|none|
|outpatientVisitTime|string|true|none|门诊就诊时间|none|
|medicalInstitutionTypeCode|[医疗机构类型代码](#schema医疗机构类型代码)|false|none|医疗机构类型|none|
|otherMedicalInstitutionType|string|false|none|其他医疗机构类型|none|
|medicalInsuranceTypeCode|[医保类型](#schema医保类型)|false|none|医保类型代码|none|
|otherMedicalInsuranceType|string|false|none|其他医保类型|medicalInsuranceTypeCode=04时必填|
|medicalInsuranceNo|string|false|none|医保编号|none|
|insurancePoolFundAmount|string|false|none|医保统筹基金支付金额|none|
|otherPaymentAmount|string|false|none|其他支付金额|none|
|personalAccountAmount|string|false|none|个人账户支付金额|none|
|personalCashAmount|string|false|none|个人现金支付金额|none|
|personalSelfPayAmount|string|false|none|个人自付金额|none|
|personalOutOfPocketAmount|string|false|none|个人自费金额|none|

#### 枚举值

|属性|值|
|---|---|
|patientGenderCode|1|
|patientGenderCode|2|

<h2 id="tocS_不抵扣原因">不抵扣原因</h2>

<a id="schema不抵扣原因"></a>
<a id="schema_不抵扣原因"></a>
<a id="tocS不抵扣原因"></a>
<a id="tocs不抵扣原因"></a>

```json
"1"

```

不抵扣原因

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||不抵扣原因|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|1|
|*anonymous*|2|
|*anonymous*|3|
|*anonymous*|4|
|*anonymous*|5|

<h2 id="tocS_勾选结果代码">勾选结果代码</h2>

<a id="schema勾选结果代码"></a>
<a id="schema_勾选结果代码"></a>
<a id="tocS勾选结果代码"></a>
<a id="tocs勾选结果代码"></a>

```json
"1"

```

勾选结果代码，成功：1

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||勾选结果代码，成功：1|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|1|
|*anonymous*|2|
|*anonymous*|3|
|*anonymous*|4|
|*anonymous*|5|
|*anonymous*|7|
|*anonymous*|8|
|*anonymous*|10|
|*anonymous*|11|
|*anonymous*|12|
|*anonymous*|13|
|*anonymous*|15|
|*anonymous*|16|
|*anonymous*|17|
|*anonymous*|18|
|*anonymous*|19|
|*anonymous*|20|
|*anonymous*|21|
|*anonymous*|31|
|*anonymous*|32|
|*anonymous*|23|
|*anonymous*|24|
|*anonymous*|25|
|*anonymous*|26|

<h2 id="tocS_发票状态（进项，收票）  ">发票状态（进项，收票）  </h2>

<a id="schema发票状态（进项，收票）  "></a>
<a id="schema_发票状态（进项，收票）  "></a>
<a id="tocS发票状态（进项，收票）  "></a>
<a id="tocs发票状态（进项，收票）  "></a>

```json
"0"

```

发票状态

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|发票状态|string|false|none|发票状态|none|

#### 枚举值

|属性|值|
|---|---|
|发票状态|0|
|发票状态|1|
|发票状态|2|
|发票状态|3|
|发票状态|4|
|发票状态|7|
|发票状态|8|

<h2 id="tocS_统计表状态">统计表状态</h2>

<a id="schema统计表状态"></a>
<a id="schema_统计表状态"></a>
<a id="tocS统计表状态"></a>
<a id="tocs统计表状态"></a>

```json
"01"

```

统计表状态

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||统计表状态|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|01|
|*anonymous*|02|
|*anonymous*|03|
|*anonymous*|04|
|*anonymous*|05|
|*anonymous*|21|
|*anonymous*|22|

<h2 id="tocS_收票全票池发票增值税用途勾选状态">收票全票池发票增值税用途勾选状态</h2>

<a id="schema收票全票池发票增值税用途勾选状态"></a>
<a id="schema_收票全票池发票增值税用途勾选状态"></a>
<a id="tocS收票全票池发票增值税用途勾选状态"></a>
<a id="tocs收票全票池发票增值税用途勾选状态"></a>

```json
"0"

```

收票全票池发票增值税用途勾选状态

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|收票全票池发票增值税用途勾选状态|string|false|none|收票全票池发票增值税用途勾选状态|none|

#### 枚举值

|属性|值|
|---|---|
|收票全票池发票增值税用途勾选状态|0|
|收票全票池发票增值税用途勾选状态|1|
|收票全票池发票增值税用途勾选状态|2|
|收票全票池发票增值税用途勾选状态|3|
|收票全票池发票增值税用途勾选状态|4|

<h2 id="tocS_全球发票返回结果 新">全球发票返回结果 新</h2>

<a id="schema全球发票返回结果 新"></a>
<a id="schema_全球发票返回结果 新"></a>
<a id="tocS全球发票返回结果 新"></a>
<a id="tocs全球发票返回结果 新"></a>

```json
{
  "serialNo": "string",
  "invoiceType": "30",
  "invoiceSubType": "380",
  "invoiceNo": "12683726300",
  "invoiceDate": "2025-05-16",
  "totalAmount": "100.00",
  "invoiceAmount": "string",
  "totalTaxAmount": "string",
  "country": "Singapore",
  "currency": "SGD",
  "buyerName": "string",
  "buyerTaxNo": "string",
  "salerName": "string",
  "salerTaxNo": "string",
  "extJson": {
    "header": {
      "billFrom": {
        "billFromBankAccount": "string",
        "billFromCity": "string",
        "billFromEmail": "string",
        "billFromComposite": "string",
        "billFromTelephone": "string",
        "billFromFax": "string",
        "billFromStateOrProvince": "string",
        "billFromPostalCode": "string",
        "billFromBankOfAccount": "string",
        "billFromCountry": "string"
      },
      "billTo": {
        "billToBankOfAccount": "string",
        "billToEmail": "string",
        "billToPostalCode": "string",
        "billToCity": "string",
        "billToComposite": "string",
        "billToTelephone": "string",
        "billToRecipient": "string",
        "billToBankAccount": "string",
        "billToFax": "string",
        "billToCountry": "string",
        "billToStateOrProvince": "string"
      },
      "payment": {
        "exchangeRate": "string",
        "dueDate": "string",
        "paymentMethod": "string",
        "paymentCurrency": "string",
        "paidAmount": "string",
        "paymentStatus": "string",
        "paymentTerms": "string"
      },
      "basic": {
        "nameOfInvoice": "string",
        "sourceFileHash": "string",
        "page": [
          "string"
        ],
        "invoiceCode": "string"
      },
      "bussiness": {
        "startDate": "string",
        "endDate": "string",
        "purchaseOrderNumber": "string",
        "contractNumber": "string"
      }
    },
    "detail": {
      "detailOfGoodsOrServices": [
        {
          "unitPrice": "string",
          "taxRate": "string",
          "articleName": "string",
          "quantity": "string",
          "orderNumber": "string",
          "unitOfMeasure": "string",
          "netAmount": "string",
          "articleID": "string",
          "description": "string",
          "tax": "string",
          "grossAmount": "string"
        }
      ],
      "detailOfTaxSummary": [
        {
          "taxRate": "string",
          "netTaxableAmount": "string",
          "tax": "string",
          "taxCategory": "string"
        }
      ]
    }
  },
  "verifyResult": "string",
  "status": "success",
  "errorCode": "2002",
  "errorMessage": "string"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|serialNo|string|false|none|系统唯一流水号|系统内部生成的唯一业务追踪流水号|
|invoiceType|string|false|none|票据类型|票据的大类枚举值：30代表发票，31代表收据|
|invoiceSubType|string|false|none|票据细分类型|当票据类型为invoice(30)时返回的具体子类，如商业发票、贷记单、增值税发票等|
|invoiceNo|string|false|none|发票号码|票据票面上的唯一编号|
|invoiceDate|string|false|none|开票日期|票据开具的日期，通常格式为 YYYY-MM-DD|
|totalAmount|string|false|none|价税合计|含税的总金额，即不含税金额与税额之和|
|invoiceAmount|string|false|none|不含税金额|票据扣除税率后的净额|
|totalTaxAmount|string|false|none|税额|票据上列明的总税费金额|
|country|string|false|none|国家|开票所属国家或地区名称|
|currency|string|false|none|币别|结算使用的货币代码，如SGD、USD、CNY|
|buyerName|string|false|none|购方名称|购买方（客户）的单位全称或个人姓名|
|buyerTaxNo|string|false|none|购方税号|购买方的纳税人识别号或统一社会信用代码|
|salerName|string|false|none|销方名称|销售方（供应商）的单位全称|
|salerTaxNo|string|false|none|销方税号|销售方的纳税人识别号或统一社会信用代码|
|extJson|object|false|none|发票详情结构化数据|包含发票完整解析后的明细数据对象，包含表头和行项目|
|» header|object|false|none|表头信息|发票的主体非明细信息，如购销双方详情、支付条款等|
|»» billFrom|object|false|none|销方详细信息|none|
|»»» billFromBankAccount|string|false|none|销方银行账号|销方开户行账号|
|»»» billFromCity|string|false|none|销方城市|销方所属城市|
|»»» billFromEmail|string|false|none|销方邮箱|销方联系电子邮件|
|»»» billFromComposite|string|false|none|销方地址全称|销方完整的办公或注册地址|
|»»» billFromTelephone|string|false|none|销方电话|销方联系电话|
|»»» billFromFax|string|false|none|销方传真|销方传真号码|
|»»» billFromStateOrProvince|string|false|none|销方省份|销方所属省/州|
|»»» billFromPostalCode|string|false|none|销方邮编|销方地址邮政编码|
|»»» billFromBankOfAccount|string|false|none|销方开户行|销方银行账户的开户行名称|
|»»» billFromCountry|string|false|none|销方国家|销方所属国家代码或名称|
|»» billTo|object|false|none|购方详细信息|none|
|»»» billToBankOfAccount|string|false|none|购方开户行|购方银行账户开户行名称|
|»»» billToEmail|string|false|none|购方邮箱|购方联系电子邮件|
|»»» billToPostalCode|string|false|none|购方邮编|购方地址邮政编码|
|»»» billToCity|string|false|none|购方城市|购方所属城市|
|»»» billToComposite|string|false|none|购方地址全称|购方完整的注册或收票地址|
|»»» billToTelephone|string|false|none|购方电话|购方联系电话|
|»»» billToRecipient|string|false|none|购方收件人|指定的发票接收人姓名|
|»»» billToBankAccount|string|false|none|购方银行账号|购方银行账号|
|»»» billToFax|string|false|none|购方传真|购方传真号码|
|»»» billToCountry|string|false|none|购方国家|购方所属国家|
|»»» billToStateOrProvince|string|false|none|购方省份|购方所属省/州|
|»» payment|object|false|none|支付信息|涉及付款条件、汇率及支付状态的信息|
|»»» exchangeRate|string|false|none|汇率|外币结算时的转换比率|
|»»» dueDate|string|false|none|付款截止日期|发票规定的最后付款限期|
|»»» paymentMethod|string|false|none|支付方式|如银行转账、现金、支票等|
|»»» paymentCurrency|string|false|none|支付币别|实际支付时使用的币种|
|»»» paidAmount|string|false|none|已付金额|该张票据已完成支付的金额|
|»»» paymentStatus|string|false|none|支付状态|当前付款进度状态|
|»»» paymentTerms|string|false|none|付款条件|付款约定的描述，如Net 30|
|»» basic|object|false|none|基础信息|发票的基础元数据|
|»»» nameOfInvoice|string|false|none|发票名称|票据上印刷的正式标题|
|»»» sourceFileHash|string|false|none|源文件哈希|附件文件的哈希值|
|»»» page|[string]|false|none|页码列表|发票所在的页码范围|
|»»» invoiceCode|string|false|none|发票代码|部分国家或地区发票特有的代码|
|»» bussiness|object|false|none|业务信息|关联的业务单据信息|
|»»» startDate|string|false|none|服务开始日期|周期性服务合同的开始时间|
|»»» endDate|string|false|none|服务结束日期|周期性服务合同的结束时间|
|»»» purchaseOrderNumber|string|false|none|采购订单号(PO)|客户侧的采购订单编号|
|»»» contractNumber|string|false|none|合同编号|该交易所依据的合同号|
|» detail|object|false|none|明细信息|发票的行项目数据|
|»» detailOfGoodsOrServices|[object]|false|none|商品明细信息|逐行列出的具体商品或服务项目清单|
|»»» unitPrice|string|false|none|单价|单位商品或服务的价格|
|»»» taxRate|string|false|none|税率|该行对应的税率比例|
|»»» articleName|string|false|none|商品名称|货物或服务的简要名称|
|»»» quantity|string|false|none|数量|商品或服务的成交数量|
|»»» orderNumber|string|false|none|行号|明细行在票面上的序号|
|»»» unitOfMeasure|string|false|none|计量单位|如：件、套、月、小时等|
|»»» netAmount|string|false|none|净额|该行不含税的总金额|
|»»» articleID|string|false|none|商品编号|销方内部的商品SKU或编码|
|»»» description|string|false|none|描述|该行项目的详细描述说明|
|»»» tax|string|false|none|税额|该行产生的税费金额|
|»»» grossAmount|string|false|none|含税金额|该行项目的价税合计金额|
|»» detailOfTaxSummary|[object]|false|none|税明细信息|按税率或税种分类统计的汇总信息|
|»»» taxRate|string|false|none|税率|对应的税率百分比|
|»»» netTaxableAmount|string|false|none|应纳税净额|该税率下对应的计税基数（不含税）|
|»»» tax|string|false|none|税额|该分类下的总税金|
|»»» taxCategory|string|false|none|税种类别|税种描述，如VAT、GST、WHT等|
|verifyResult|string|false|none|合规性校验结果|当verifyFlag开启时，返回的详细自动化校验结论|
|status|string|true|none|状态码|接口调用的结果状态：success表示成功，failed表示失败|
|errorCode|string|false|none|错误码|业务执行失败时的错误分类代码|
|errorMessage|string|false|none|错误描述|具体的错误原因详细文本，便于人工排查|

#### 枚举值

|属性|值|
|---|---|
|invoiceType|30|
|invoiceType|31|
|invoiceSubType|380|
|invoiceSubType|381|
|invoiceSubType|388|
|invoiceSubType|325|
|status|success|
|status|failed|
|errorCode|2002|

<h2 id="tocS_数据来源">数据来源</h2>

<a id="schema数据来源"></a>
<a id="schema_数据来源"></a>
<a id="tocS数据来源"></a>
<a id="tocs数据来源"></a>

```json
{
  "buyertype": "0"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|buyertype|string|true|none||none|

#### 枚举值

|属性|值|
|---|---|
|buyertype|0|
|buyertype|1|
|buyertype|2|
|buyertype|3|
|buyertype|4|
|buyertype|5|
|buyertype|6|
|buyertype|7|
|buyertype|8|
|buyertype|9|
|buyertype|10|
|buyertype|11|
|buyertype|12|

<h2 id="tocS_发票状态">发票状态</h2>

<a id="schema发票状态"></a>
<a id="schema_发票状态"></a>
<a id="tocS发票状态"></a>
<a id="tocs发票状态"></a>

```json
{
  "invoiceStatus": "0"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|invoiceStatus|string|true|none|发票状态|none|

#### 枚举值

|属性|值|
|---|---|
|invoiceStatus|0|
|invoiceStatus|1|
|invoiceStatus|2|
|invoiceStatus|3|
|invoiceStatus|4|
|invoiceStatus|6|
|invoiceStatus|7|

<h2 id="tocS_销项发票冲红原因">销项发票冲红原因</h2>

<a id="schema销项发票冲红原因"></a>
<a id="schema_销项发票冲红原因"></a>
<a id="tocS销项发票冲红原因"></a>
<a id="tocs销项发票冲红原因"></a>

```json
{
  "redReason": "1"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|redReason|string|true|none|冲红原因|none|

#### 枚举值

|属性|值|
|---|---|
|redReason|1|
|redReason|2|
|redReason|3|
|redReason|4|

<h2 id="tocS_特殊票种">特殊票种</h2>

<a id="schema特殊票种"></a>
<a id="schema_特殊票种"></a>
<a id="tocS特殊票种"></a>
<a id="tocs特殊票种"></a>

```json
{
  "specialType": "00"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|specialType|string|true|none|特殊票种|none|

#### 枚举值

|属性|值|
|---|---|
|specialType|00|
|specialType|02|
|specialType|06|
|specialType|07|
|specialType|08|
|specialType|11|
|specialType|18|
|specialType|E01|
|specialType|E03|
|specialType|E04|
|specialType|E05|
|specialType|E06|
|specialType|E07|
|specialType|E09|
|specialType|E12|
|specialType|E14|
|specialType|E18|

<h2 id="tocS_减按征税类型">减按征税类型</h2>

<a id="schema减按征税类型"></a>
<a id="schema_减按征税类型"></a>
<a id="tocS减按征税类型"></a>
<a id="tocs减按征税类型"></a>

```json
{
  "reductionTaxType": "01"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|reductionTaxType|string|true|none|减按征税类型|none|

#### 枚举值

|属性|值|
|---|---|
|reductionTaxType|01|
|reductionTaxType|02|
|reductionTaxType|03|
|reductionTaxType|04|
|reductionTaxType|05|
|reductionTaxType|51|
|reductionTaxType|52|
|reductionTaxType|53|

<h2 id="tocS_数电票-差额征税">数电票-差额征税</h2>

<a id="schema数电票-差额征税"></a>
<a id="schema_数电票-差额征税"></a>
<a id="tocS数电票-差额征税"></a>
<a id="tocs数电票-差额征税"></a>

```json
[
  {
    "evidenceType": "01",
    "etaxInvoiceNo": "string",
    "invoiceCode": "string",
    "invoiceNo": "string",
    "evidenceNo": "string",
    "invoiceDate": "string",
    "evidenceAmount": 0,
    "deductionedAmount": 0,
    "deduction": 0,
    "remark": "string"
  }
]

```

数电票差额征税-差额开票必填，发票云版本5.0.020支持

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|evidenceType|string|true|none||凭证类型|
|etaxInvoiceNo|string|false|none||全电发票号码|
|invoiceCode|string|false|none||发票代码|
|invoiceNo|string|false|none||发票号码|
|evidenceNo|string|false|none||凭证号码|
|invoiceDate|string|false|none||开具日期 日期格式"YYYY-MM-DD"|
|evidenceAmount|number|true|none||凭证合计金额|
|deductionedAmount|number|false|none||已扣除金额|
|deduction|number|true|none||本次扣除金额|
|remark|string|false|none||备注|

#### 枚举值

|属性|值|
|---|---|
|evidenceType|01|
|evidenceType|02|
|evidenceType|03|
|evidenceType|04|
|evidenceType|05|
|evidenceType|06|
|evidenceType|07|
|evidenceType|08|
|evidenceType|09|
|evidenceType|12|
|evidenceType|13|
|evidenceType|14|
|evidenceType|16|

<h2 id="tocS_发票种类">发票种类</h2>

<a id="schema发票种类"></a>
<a id="schema_发票种类"></a>
<a id="tocS发票种类"></a>
<a id="tocs发票种类"></a>

```json
"028"

```

发票种类

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||发票种类|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|028|
|*anonymous*|026|
|*anonymous*|004|
|*anonymous*|007|
|*anonymous*|025|
|*anonymous*|08xdp|
|*anonymous*|10xdp|

<h2 id="tocS_发票状态（销项）">发票状态（销项）</h2>

<a id="schema发票状态（销项）"></a>
<a id="schema_发票状态（销项）"></a>
<a id="tocS发票状态（销项）"></a>
<a id="tocs发票状态（销项）"></a>

```json
"0"

```

发票状态

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||发票状态|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|0|
|*anonymous*|1|
|*anonymous*|2|
|*anonymous*|3|
|*anonymous*|4|
|*anonymous*|6|
|*anonymous*|7|

<h2 id="tocS_数电票特定要素类型">数电票特定要素类型</h2>

<a id="schema数电票特定要素类型"></a>
<a id="schema_数电票特定要素类型"></a>
<a id="tocS数电票特定要素类型"></a>
<a id="tocs数电票特定要素类型"></a>

```json
"null"

```

证件类型，数电发票农产品收购类必填

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||证件类型，数电发票农产品收购类必填|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|null|
|*anonymous*|01|
|*anonymous*|E02|
|*anonymous*|03|
|*anonymous*|04|
|*anonymous*|05|
|*anonymous*|06|
|*anonymous*|07|
|*anonymous*|08|
|*anonymous*|09|
|*anonymous*|10|
|*anonymous*|11|
|*anonymous*|12|
|*anonymous*|13|
|*anonymous*|14|
|*anonymous*|15|
|*anonymous*|02|
|*anonymous*|17|
|*anonymous*|18|

<h2 id="tocS_红冲原因">红冲原因</h2>

<a id="schema红冲原因"></a>
<a id="schema_红冲原因"></a>
<a id="tocS红冲原因"></a>
<a id="tocs红冲原因"></a>

```json
"1"

```

红冲原因

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||红冲原因|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|1|
|*anonymous*|2|
|*anonymous*|3|
|*anonymous*|4|

<h2 id="tocS_红字确认单状态">红字确认单状态</h2>

<a id="schema红字确认单状态"></a>
<a id="schema_红字确认单状态"></a>
<a id="tocS红字确认单状态"></a>
<a id="tocs红字确认单状态"></a>

```json
"01"

```

红字确认单状态。发票云版本5.0.024支持

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||红字确认单状态。发票云版本5.0.024支持|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|01|
|*anonymous*|02|
|*anonymous*|03|
|*anonymous*|04|
|*anonymous*|05|
|*anonymous*|06|
|*anonymous*|07|
|*anonymous*|08|
|*anonymous*|09|
|*anonymous*|10|

<h2 id="tocS_发票明细行性质">发票明细行性质</h2>

<a id="schema发票明细行性质"></a>
<a id="schema_发票明细行性质"></a>
<a id="tocS发票明细行性质"></a>
<a id="tocs发票明细行性质"></a>

```json
0

```

发票明细行性质 

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|number|false|none||发票明细行性质|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|0|
|*anonymous*|1|
|*anonymous*|2|

<h2 id="tocS_证件类型">证件类型</h2>

<a id="schema证件类型"></a>
<a id="schema_证件类型"></a>
<a id="tocS证件类型"></a>
<a id="tocs证件类型"></a>

```json
"103"

```

证件类型，数电发票农产品收购类必填

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||证件类型，数电发票农产品收购类必填|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|103|
|*anonymous*|201|
|*anonymous*|208|
|*anonymous*|210|
|*anonymous*|213|
|*anonymous*|215|
|*anonymous*|219|
|*anonymous*|220|
|*anonymous*|221|
|*anonymous*|233|
|*anonymous*|299|

<h2 id="tocS_经办人证件类型">经办人证件类型</h2>

<a id="schema经办人证件类型"></a>
<a id="schema_经办人证件类型"></a>
<a id="tocS经办人证件类型"></a>
<a id="tocs经办人证件类型"></a>

```json
"101"

```

证件类型，数电发票农产品收购类必填

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||证件类型，数电发票农产品收购类必填|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|101|
|*anonymous*|102|
|*anonymous*|103|
|*anonymous*|199|
|*anonymous*|201|
|*anonymous*|202|
|*anonymous*|203|
|*anonymous*|204|
|*anonymous*|205|
|*anonymous*|206|
|*anonymous*|207|
|*anonymous*|208|
|*anonymous*|210|
|*anonymous*|212|
|*anonymous*|213|
|*anonymous*|214|
|*anonymous*|215|
|*anonymous*|216|
|*anonymous*|217|
|*anonymous*|218|
|*anonymous*|219|
|*anonymous*|220|
|*anonymous*|221|
|*anonymous*|222|
|*anonymous*|224|
|*anonymous*|225|
|*anonymous*|226|
|*anonymous*|227|
|*anonymous*|228|
|*anonymous*|229|
|*anonymous*|230|
|*anonymous*|231|
|*anonymous*|232|
|*anonymous*|233|
|*anonymous*|234|
|*anonymous*|235|
|*anonymous*|236|
|*anonymous*|237|
|*anonymous*|238|
|*anonymous*|239|
|*anonymous*|240|
|*anonymous*|241|
|*anonymous*|291|
|*anonymous*|299|

<h2 id="tocS_优惠政策标识">优惠政策标识</h2>

<a id="schema优惠政策标识"></a>
<a id="schema_优惠政策标识"></a>
<a id="tocS优惠政策标识"></a>
<a id="tocs优惠政策标识"></a>

```json
"01"

```

优惠政策标识

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||优惠政策标识|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|01|
|*anonymous*|02|
|*anonymous*|03|
|*anonymous*|04|
|*anonymous*|05|
|*anonymous*|06|
|*anonymous*|07|
|*anonymous*|08|
|*anonymous*|09|
|*anonymous*|10|
|*anonymous*|11|
|*anonymous*|12|
|*anonymous*|13|
|*anonymous*|14|
|*anonymous*|15|
|*anonymous*|16|
|*anonymous*|17|
|*anonymous*|18|

<h2 id="tocS_即征即退类型">即征即退类型</h2>

<a id="schema即征即退类型"></a>
<a id="schema_即征即退类型"></a>
<a id="tocS即征即退类型"></a>
<a id="tocs即征即退类型"></a>

```json
"01"

```

即征即退类型 “有效增值税即征即退备案信息纳税人”在发票开具时若选择的商编在商编表中“即征即退”列非空且该条明细属于增值税即征即退收入时，为必填项

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||即征即退类型 “有效增值税即征即退备案信息纳税人”在发票开具时若选择的商编在商编表中“即征即退”列非空且该条明细属于增值税即征即退收入时，为必填项|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|01|
|*anonymous*|02|
|*anonymous*|03|
|*anonymous*|04|
|*anonymous*|05|
|*anonymous*|06|
|*anonymous*|07|
|*anonymous*|08|
|*anonymous*|09|
|*anonymous*|10|
|*anonymous*|11|
|*anonymous*|12|

<h2 id="tocS_苍穹API接口返回值">苍穹API接口返回值</h2>

<a id="schema苍穹api接口返回值"></a>
<a id="schema_苍穹API接口返回值"></a>
<a id="tocS苍穹api接口返回值"></a>
<a id="tocs苍穹api接口返回值"></a>

```json
{
  "success": true,
  "errorCode": "string",
  "message": "string",
  "data": {}
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|success|boolean|true|none||true或false|
|errorCode|string|true|none||"0"为成功|
|message|string|true|none||错误描述|
|data|object|true|none||请求结果|

<h2 id="tocS_含税标志">含税标志</h2>

<a id="schema含税标志"></a>
<a id="schema_含税标志"></a>
<a id="tocS含税标志"></a>
<a id="tocs含税标志"></a>

```json
"0"

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|0|
|*anonymous*|1|

<h2 id="tocS_发票查询明细">发票查询明细</h2>

<a id="schema发票查询明细"></a>
<a id="schema_发票查询明细"></a>
<a id="tocS发票查询明细"></a>
<a id="tocs发票查询明细"></a>

```json
{
  "amount": 0,
  "billSourceId": "string",
  "detailId": "string",
  "detailRowNo": 0,
  "goodsName": "string",
  "includeTaxAmount": 0,
  "includeTaxPrice": "string",
  "lineProperty": 0,
  "price": "string",
  "privilegeContent": "string",
  "privilegeFlag": 0,
  "quantity": "string",
  "remainRedAmount": 0,
  "remainRedQuantity": "string",
  "remainRedTax": 0,
  "revenueCode": "string",
  "revenueName": "string",
  "seq": 0,
  "specification": "string",
  "taxAmount": 0,
  "taxFlag": "0",
  "taxRate": "string",
  "units": "string",
  "zeroTaxRateFlag": "string"
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|amount|number|true|none||金额【长度：(14,2)】|
|billSourceId|string|true|none||none|
|detailId|string|true|none|对应业务系统明细ID|对应业务系统明细ID【长度：32】|
|detailRowNo|number|true|none|明细行序号|明细的序号|
|goodsName|string|true|none|商品名称|GBK编码不超过92字节（含*税分编码简称*的长度）【长度：92】|
|includeTaxAmount|number|true|none|含税金额|none|
|includeTaxPrice|string|true|none|含税单价|none|
|lineProperty|[发票明细行性质](#schema发票明细行性质)|true|none|行性质|发票明细行性质|
|price|string|true|none|单价|none|
|privilegeContent|string|true|none|享受优惠内容|none|
|privilegeFlag|integer|true|none|是否享受优惠|none|
|quantity|string|true|none|数量|none|
|remainRedAmount|number|true|none|剩余可红冲金额|none|
|remainRedQuantity|string|true|none|剩余可红冲数量|none|
|remainRedTax|number|true|none|剩余可红冲税额|none|
|revenueCode|string|true|none|税收分类编码|none|
|revenueName|string|true|none|税收商品大类名称|none|
|seq|integer|true|none||none|
|specification|string|true|none|规格型号|none|
|taxAmount|number|true|none|税额|none|
|taxFlag|[含税标志](#schema含税标志)|true|none|含税标志|none|
|taxRate|string|true|none|税率|none|
|units|string|true|none|计量单位|none|
|zeroTaxRateFlag|string|true|none|零税率标识|none|

#### 枚举值

|属性|值|
|---|---|
|privilegeFlag|0|
|privilegeFlag|1|

<h2 id="tocS_医疗机构类型代码">医疗机构类型代码</h2>

<a id="schema医疗机构类型代码"></a>
<a id="schema_医疗机构类型代码"></a>
<a id="tocS医疗机构类型代码"></a>
<a id="tocs医疗机构类型代码"></a>

```json
"A"

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|A|
|*anonymous*|A1|
|*anonymous*|A100|
|*anonymous*|A2|
|*anonymous*|A210|
|*anonymous*|A220|
|*anonymous*|A221|
|*anonymous*|A222|
|*anonymous*|A223|
|*anonymous*|A224|
|*anonymous*|A229|
|*anonymous*|A3|
|*anonymous*|A300|
|*anonymous*|A4|
|*anonymous*|A411|
|*anonymous*|A412|
|*anonymous*|A413|
|*anonymous*|A414|
|*anonymous*|A419|
|*anonymous*|A5|
|*anonymous*|A511|
|*anonymous*|A512|
|*anonymous*|A513|
|*anonymous*|A514|
|*anonymous*|A515|
|*anonymous*|A516|
|*anonymous*|A517|
|*anonymous*|A518|
|*anonymous*|A519|
|*anonymous*|A520|
|*anonymous*|A521|
|*anonymous*|A522|
|*anonymous*|A523|
|*anonymous*|A524|
|*anonymous*|A525|
|*anonymous*|A526|
|*anonymous*|A527|
|*anonymous*|A528|
|*anonymous*|A529|
|*anonymous*|A539|
|*anonymous*|A6|
|*anonymous*|A600|
|*anonymous*|A7|
|*anonymous*|A710|
|*anonymous*|A720|
|*anonymous*|B|
|*anonymous*|B1|
|*anonymous*|B100|
|*anonymous*|B2|
|*anonymous*|B200|
|*anonymous*|C|
|*anonymous*|C2|
|*anonymous*|C210|
|*anonymous*|C220|
|*anonymous*|D|
|*anonymous*|D1|
|*anonymous*|D110|
|*anonymous*|D120|
|*anonymous*|D121|
|*anonymous*|D122|
|*anonymous*|D130|
|*anonymous*|D140|
|*anonymous*|D150|
|*anonymous*|D151|
|*anonymous*|D152|
|*anonymous*|D153|
|*anonymous*|D154|
|*anonymous*|D155|
|*anonymous*|D159|
|*anonymous*|D2|
|*anonymous*|D211|
|*anonymous*|D212|
|*anonymous*|D213|
|*anonymous*|D214|
|*anonymous*|D215|
|*anonymous*|D216|
|*anonymous*|D217|
|*anonymous*|D229|
|*anonymous*|D3|
|*anonymous*|D300|
|*anonymous*|D4|
|*anonymous*|D400|
|*anonymous*|D5|
|*anonymous*|D500|
|*anonymous*|D6|
|*anonymous*|D600|
|*anonymous*|E|
|*anonymous*|E1|
|*anonymous*|E100|
|*anonymous*|E2|
|*anonymous*|E200|
|*anonymous*|E3|
|*anonymous*|E300|
|*anonymous*|F|
|*anonymous*|F1|
|*anonymous*|F110|
|*anonymous*|F120|
|*anonymous*|F130|
|*anonymous*|F2|
|*anonymous*|F200|
|*anonymous*|G|
|*anonymous*|G1|
|*anonymous*|G100|
|*anonymous*|G2|
|*anonymous*|G200|
|*anonymous*|G3|
|*anonymous*|G300|
|*anonymous*|G4|
|*anonymous*|G400|
|*anonymous*|H|
|*anonymous*|H1|
|*anonymous*|H111|
|*anonymous*|H112|
|*anonymous*|H113|
|*anonymous*|H119|
|*anonymous*|H2|
|*anonymous*|H211|
|*anonymous*|H212|
|*anonymous*|H213|
|*anonymous*|H214|
|*anonymous*|H215|
|*anonymous*|H216|
|*anonymous*|H217|
|*anonymous*|H218|
|*anonymous*|H219|
|*anonymous*|H220|
|*anonymous*|H229|
|*anonymous*|J|
|*anonymous*|J1|
|*anonymous*|J100|
|*anonymous*|J2|
|*anonymous*|J200|
|*anonymous*|J3|
|*anonymous*|J300|
|*anonymous*|J4|
|*anonymous*|J400|
|*anonymous*|K|
|*anonymous*|K1|
|*anonymous*|K100|
|*anonymous*|L|
|*anonymous*|L1|
|*anonymous*|L100|
|*anonymous*|L2|
|*anonymous*|L200|
|*anonymous*|L3|
|*anonymous*|L300|
|*anonymous*|L4|
|*anonymous*|L400|
|*anonymous*|L5|
|*anonymous*|L500|
|*anonymous*|L6|
|*anonymous*|L600|
|*anonymous*|L9|
|*anonymous*|L900|
|*anonymous*|M|
|*anonymous*|M1|
|*anonymous*|M100|
|*anonymous*|M2|
|*anonymous*|M200|
|*anonymous*|M3|
|*anonymous*|M300|
|*anonymous*|M4|
|*anonymous*|M400|
|*anonymous*|M5|
|*anonymous*|M500|
|*anonymous*|M6|
|*anonymous*|M611|
|*anonymous*|M612|
|*anonymous*|M613|
|*anonymous*|M614|
|*anonymous*|M615|
|*anonymous*|M616|
|*anonymous*|M617|
|*anonymous*|M618|
|*anonymous*|M619|
|*anonymous*|M620|
|*anonymous*|M621|
|*anonymous*|M622|
|*anonymous*|M623|
|*anonymous*|M624|
|*anonymous*|M625|
|*anonymous*|M626|
|*anonymous*|M627|
|*anonymous*|M628|
|*anonymous*|M629|
|*anonymous*|M630|
|*anonymous*|M631|
|*anonymous*|M632|
|*anonymous*|M633|
|*anonymous*|M634|
|*anonymous*|M649|
|*anonymous*|M7|
|*anonymous*|M700|
|*anonymous*|N|
|*anonymous*|N1|
|*anonymous*|N110|
|*anonymous*|N111|
|*anonymous*|N112|
|*anonymous*|N113|
|*anonymous*|N119|
|*anonymous*|N120|
|*anonymous*|N121|
|*anonymous*|N122|
|*anonymous*|N123|
|*anonymous*|N124|
|*anonymous*|N129|
|*anonymous*|N2|
|*anonymous*|N210|
|*anonymous*|N211|
|*anonymous*|N212|
|*anonymous*|N219|
|*anonymous*|N220|
|*anonymous*|N221|
|*anonymous*|N222|
|*anonymous*|N223|
|*anonymous*|N229|
|*anonymous*|N3|
|*anonymous*|N300|
|*anonymous*|O|
|*anonymous*|O1|
|*anonymous*|O100|
|*anonymous*|O2|
|*anonymous*|O200|
|*anonymous*|P|
|*anonymous*|P1|
|*anonymous*|P110|
|*anonymous*|P120|
|*anonymous*|P2|
|*anonymous*|P210|
|*anonymous*|P220|
|*anonymous*|P230|
|*anonymous*|P290|
|*anonymous*|P9|
|*anonymous*|P911|

<h2 id="tocS_医保类型">医保类型</h2>

<a id="schema医保类型"></a>
<a id="schema_医保类型"></a>
<a id="tocS医保类型"></a>
<a id="tocs医保类型"></a>

```json
"01"

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|*anonymous*|string|false|none||none|

#### 枚举值

|属性|值|
|---|---|
|*anonymous*|01|
|*anonymous*|02|
|*anonymous*|03|
|*anonymous*|04|
|*anonymous*|05|

<h2 id="tocS_国家及地区数字代码">国家及地区数字代码</h2>

<a id="schema国家及地区数字代码"></a>
<a id="schema_国家及地区数字代码"></a>
<a id="tocS国家及地区数字代码"></a>
<a id="tocs国家及地区数字代码"></a>

```json
"004"

```

国家及地区代码

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|国家及地区代码|string|false|none|国家及地区代码|none|

#### 枚举值

|属性|值|
|---|---|
|国家及地区代码|004|
|国家及地区代码|008|
|国家及地区代码|010|
|国家及地区代码|012|
|国家及地区代码|016|
|国家及地区代码|020|
|国家及地区代码|024|
|国家及地区代码|028|
|国家及地区代码|031|
|国家及地区代码|032|
|国家及地区代码|036|
|国家及地区代码|040|
|国家及地区代码|044|
|国家及地区代码|048|
|国家及地区代码|050|
|国家及地区代码|051|
|国家及地区代码|052|
|国家及地区代码|056|
|国家及地区代码|060|
|国家及地区代码|064|
|国家及地区代码|068|
|国家及地区代码|070|
|国家及地区代码|072|
|国家及地区代码|074|
|国家及地区代码|076|
|国家及地区代码|084|
|国家及地区代码|086|
|国家及地区代码|090|
|国家及地区代码|092|
|国家及地区代码|096|
|国家及地区代码|100|
|国家及地区代码|104|
|国家及地区代码|108|
|国家及地区代码|112|
|国家及地区代码|116|
|国家及地区代码|120|
|国家及地区代码|124|
|国家及地区代码|132|
|国家及地区代码|136|
|国家及地区代码|140|
|国家及地区代码|144|
|国家及地区代码|148|
|国家及地区代码|152|
|国家及地区代码|156|
|国家及地区代码|158|
|国家及地区代码|162|
|国家及地区代码|166|
|国家及地区代码|170|
|国家及地区代码|174|
|国家及地区代码|175|
|国家及地区代码|178|
|国家及地区代码|180|
|国家及地区代码|184|
|国家及地区代码|188|
|国家及地区代码|191|
|国家及地区代码|192|
|国家及地区代码|196|
|国家及地区代码|203|
|国家及地区代码|204|
|国家及地区代码|208|
|国家及地区代码|212|
|国家及地区代码|214|
|国家及地区代码|218|
|国家及地区代码|222|
|国家及地区代码|226|
|国家及地区代码|231|
|国家及地区代码|232|
|国家及地区代码|233|
|国家及地区代码|234|
|国家及地区代码|238|
|国家及地区代码|239|
|国家及地区代码|242|
|国家及地区代码|246|
|国家及地区代码|250|
|国家及地区代码|254|
|国家及地区代码|258|
|国家及地区代码|260|
|国家及地区代码|262|
|国家及地区代码|266|
|国家及地区代码|268|
|国家及地区代码|270|
|国家及地区代码|275|
|国家及地区代码|276|
|国家及地区代码|288|
|国家及地区代码|292|
|国家及地区代码|296|
|国家及地区代码|300|
|国家及地区代码|304|
|国家及地区代码|308|
|国家及地区代码|312|
|国家及地区代码|316|
|国家及地区代码|320|
|国家及地区代码|324|
|国家及地区代码|328|
|国家及地区代码|332|
|国家及地区代码|334|
|国家及地区代码|336|
|国家及地区代码|340|
|国家及地区代码|344|
|国家及地区代码|348|
|国家及地区代码|352|
|国家及地区代码|356|
|国家及地区代码|360|
|国家及地区代码|364|
|国家及地区代码|368|
|国家及地区代码|372|
|国家及地区代码|376|
|国家及地区代码|380|
|国家及地区代码|384|
|国家及地区代码|388|
|国家及地区代码|392|
|国家及地区代码|398|
|国家及地区代码|400|
|国家及地区代码|404|
|国家及地区代码|408|
|国家及地区代码|410|
|国家及地区代码|414|
|国家及地区代码|417|
|国家及地区代码|418|
|国家及地区代码|422|
|国家及地区代码|426|
|国家及地区代码|428|
|国家及地区代码|430|
|国家及地区代码|434|
|国家及地区代码|438|
|国家及地区代码|440|
|国家及地区代码|442|
|国家及地区代码|446|
|国家及地区代码|450|
|国家及地区代码|454|
|国家及地区代码|458|
|国家及地区代码|462|
|国家及地区代码|466|
|国家及地区代码|470|
|国家及地区代码|474|
|国家及地区代码|478|
|国家及地区代码|480|
|国家及地区代码|484|
|国家及地区代码|492|
|国家及地区代码|496|
|国家及地区代码|498|
|国家及地区代码|499|
|国家及地区代码|500|
|国家及地区代码|504|
|国家及地区代码|508|
|国家及地区代码|512|
|国家及地区代码|516|
|国家及地区代码|520|
|国家及地区代码|524|
|国家及地区代码|528|
|国家及地区代码|530|
|国家及地区代码|533|
|国家及地区代码|540|
|国家及地区代码|548|
|国家及地区代码|554|
|国家及地区代码|558|
|国家及地区代码|562|
|国家及地区代码|566|
|国家及地区代码|570|
|国家及地区代码|574|
|国家及地区代码|578|
|国家及地区代码|580|
|国家及地区代码|581|
|国家及地区代码|583|
|国家及地区代码|584|
|国家及地区代码|585|
|国家及地区代码|586|
|国家及地区代码|591|
|国家及地区代码|598|
|国家及地区代码|600|
|国家及地区代码|604|
|国家及地区代码|608|
|国家及地区代码|612|
|国家及地区代码|616|
|国家及地区代码|620|
|国家及地区代码|624|
|国家及地区代码|626|
|国家及地区代码|630|
|国家及地区代码|634|
|国家及地区代码|638|
|国家及地区代码|642|
|国家及地区代码|643|
|国家及地区代码|646|
|国家及地区代码|654|
|国家及地区代码|659|
|国家及地区代码|660|
|国家及地区代码|662|
|国家及地区代码|666|
|国家及地区代码|670|
|国家及地区代码|674|
|国家及地区代码|678|
|国家及地区代码|682|
|国家及地区代码|686|
|国家及地区代码|688|
|国家及地区代码|690|
|国家及地区代码|694|
|国家及地区代码|702|
|国家及地区代码|703|
|国家及地区代码|704|
|国家及地区代码|705|
|国家及地区代码|706|
|国家及地区代码|710|
|国家及地区代码|716|
|国家及地区代码|724|
|国家及地区代码|728|
|国家及地区代码|732|
|国家及地区代码|736|
|国家及地区代码|740|
|国家及地区代码|744|
|国家及地区代码|748|
|国家及地区代码|752|
|国家及地区代码|756|
|国家及地区代码|760|
|国家及地区代码|762|
|国家及地区代码|764|
|国家及地区代码|768|
|国家及地区代码|772|
|国家及地区代码|776|
|国家及地区代码|780|
|国家及地区代码|784|
|国家及地区代码|788|
|国家及地区代码|792|
|国家及地区代码|795|
|国家及地区代码|796|
|国家及地区代码|798|
|国家及地区代码|800|
|国家及地区代码|804|
|国家及地区代码|807|
|国家及地区代码|818|
|国家及地区代码|826|
|国家及地区代码|831|
|国家及地区代码|832|
|国家及地区代码|833|
|国家及地区代码|834|
|国家及地区代码|840|
|国家及地区代码|850|
|国家及地区代码|854|
|国家及地区代码|858|
|国家及地区代码|860|
|国家及地区代码|862|
|国家及地区代码|876|
|国家及地区代码|882|
|国家及地区代码|887|
|国家及地区代码|891|
|国家及地区代码|894|
|国家及地区代码|A00|

