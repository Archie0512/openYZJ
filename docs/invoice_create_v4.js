/**
 * invoice_create_v4.js - 开票申请单生成（v4）
 *
 * v3 变更（继承）:
 *   1. 恢复第 6 节 getEntryRows，基于 getCell().getValue() 重构
 *   2. 新增 mergeEntryRows 合并逻辑（参照 开票申请单生成路线1.sql 第 29-47 行）
 *   3. 修复 notZero 对 String(null) → "null" 的误判
 *   4. 浮点精度修正：金额/税额/单价统一 round2()，lineProperty 仅内部使用不输出
 *   5. 验签方案升级：去掉 MD5，改为 body 直签（与 open_api_doc.md 3.1 节一致）
 *
 * v4 变更：
 *   6. toJsNative 增加 null 值过滤 → 解决 body 字节不一致导致 401 签名验证失败
 *   7. revenueCode 空指针保护 → getValue() 判空后再 .get("mergecode")
 *   8. 数据获取优化：单头/分录改用 pluginCtx.getDataObject() 一次性获取，减少 EAS API 调用次数
 *   9. 请求体对齐 open_api_doc.md：
 *      - items → billDetail
 *      - 新增 requestId（单头必填）, detailId（分录必填）
 *      - 恢复 lineProperty: 2（固定值）
 *      - 删除 seq
 *  10. 内部 _splitFlag 重命名，避免与 API 的 lineProperty 混淆
 *  11. 增加 body MD5 调试弹窗
 */

var API_KEY    = "ak_c9f470d5a9ffcab3f865df60248da31382ba36649b110381";
var API_SECRET = "sk_6a14a9164f20e9ab1d44d15b48d0f8ee432d4b488adfd4f06f9b9b17365731df0dda5c87";
var BASE_URL   = "https://kimpi.cn";
var API_ENV    = "test";  // "test" / "prod"

handleInvoiceCreate(pluginCtx);

// ============================================================
// 2. 加密工具（HMAC-SHA256 签名）
// ============================================================

function bytesToHex(bytes) {
    var s = "";
    for (var i = 0; i < bytes.length; i++) {
        var b = bytes[i] & 0xFF;
        // 使用 0x100 | b 确保 toHexString 始终返回 3 位十六进制，
        // 再 substring(1) 取后 2 位，彻底解决 Rhino 中 Java String.length
        // 不可靠导致的前导零丢失问题
        s += java.lang.Integer.toHexString(0x100 | b).substring(1);
    }
    return s;
}

function sign(method, path, body, apiKey, apiSecret) {
    var ts = String(Math.floor(new Date().getTime() / 1000));
    // v3: 去掉 MD5，body 直签（open_api_doc.md §3.1）
    // signature = HMAC-SHA256(apiSecret, method + path + timestamp + body)
    var payload = method + path + ts + body;

    var mac = javax.crypto.Mac.getInstance("HmacSHA256");
    var keyBytes = new java.lang.String(apiSecret).getBytes("UTF-8");
    var spec = new javax.crypto.spec.SecretKeySpec(keyBytes, "HmacSHA256");
    mac.init(spec);
    var sig = bytesToHex(mac.doFinal(new java.lang.String(payload).getBytes("UTF-8")));

    return { apiKey: apiKey, timestamp: ts, signature: sig };
}

// ============================================================
// 3. HTTP POST 请求
// ============================================================

function httpPost(url, headers, body) {
    var conn = new java.net.URL(url).openConnection();
    conn.setRequestMethod("POST");
    conn.setDoOutput(true);
    conn.setDoInput(true);
    conn.setConnectTimeout(10000);
    conn.setReadTimeout(30000);

    for (var k in headers) {
        if (headers.hasOwnProperty(k)) {
            conn.setRequestProperty(k, String(headers[k]));
        }
    }

    var bodyBytes = new java.lang.String(body).getBytes("UTF-8");
    var out = conn.getOutputStream();
    out.write(bodyBytes);
    out.flush();
    out.close();

    var code = conn.getResponseCode();
    var stream;
    try {
        stream = conn.getInputStream();
    } catch (e) {
        stream = conn.getErrorStream();
    }
    var reader = new java.io.BufferedReader(new java.io.InputStreamReader(stream, "UTF-8"));
    var sb = new java.lang.StringBuilder();
    var line;
    while ((line = reader.readLine()) != null) sb.append(line);
    reader.close();
    conn.disconnect();

    return { code: code, body: sb.toString() };
}

// ============================================================
// 4. JSON 序列化（基于 Rhino 内置 JSON.stringify）
// ============================================================

function toJsNative(val) {
    if (val == null || val == undefined) return null;

    if (typeof java != "undefined" && val instanceof java.lang.CharSequence) {
        return String(val);
    }

    if (typeof java != "undefined" && val instanceof java.lang.Number) {
        return Number(val);
    }

    var t = typeof val;
    if (t == "string" || t == "number" || t == "boolean") {
        return val;
    }

    if (val instanceof Array || (typeof java != "undefined" && val instanceof java.util.List)) {
        var arr = [];
        var len = val.length != undefined ? val.length : val.size();
        for (var i = 0; i < len; i++) {
            arr.push(toJsNative(val.length != undefined ? val[i] : val.get(i)));
        }
        return arr;
    }

    // 兜底：未识别的 Java 对象 → 转字符串
    if (typeof java != "undefined" && val instanceof java.lang.Object) {
        return String(val);
    }

    if (t == "object") {
        var obj = {};
        for (var k in val) {
            if (val.hasOwnProperty && !val.hasOwnProperty(k)) continue;
            var v = val[k];
            if (v == undefined || typeof v == "function") continue;
            var converted = toJsNative(v);
            if (converted === null) continue;  // v4: 剔除 null 值，避免 body 字节不一致导致签验证失败
            obj[k] = converted;
        }
        return obj;
    }

    return val;
}

function toJson(obj) {
    return JSON.stringify(toJsNative(obj));
}

// ============================================================
// 5. 辅助函数
// ============================================================

function mapInvoiceType(type) {
    if (type === "DeiSpecialVAT") return "08xdp";
    return "10xdp";
}

function mapBuyerProperty(type) {
    return type === "2" ? 0 : 1;
}

function formatTaxRate(rate) {
    return (rate / 100).toFixed(2);
}

/**
 * "0"/0/"null"/null 视为空 → 返回 null
 * v3 修复：增加 "null" 判断，防止 String(Java null) → "null" 穿透
 */
function notZero(v) {
    if (v === null || v === undefined || v === "" || v === "0" || v === 0 || v === "null") return null;
    return v;
}

/** 金额保留 2 位小数，解决 IEEE 754 浮点精度问题 */
function round2(v) {
    return Math.round(v * 100) / 100;
}

/** v4: 清洗 ID 中的特殊字符，仅保留 [a-zA-Z0-9_] */
function sanitizeId(v) {
    if (v == null) return "";
    return String(v).replace(/[^a-zA-Z0-9_]/g, "_");
}

function splitFlag(coreBillType, zhubie, seq) {
    var incomeMatch = (coreBillType == "精品配件销售单" || coreBillType == "采购订单" || coreBillType == "调拨订单");
    var enlpMatch = (zhubie == "SPLIT" || zhubie == "TH-SPLIT");
    if (incomeMatch && enlpMatch) {
        return seq;   // 拆分
    }
    return 0;         // 合并
}

function invoiceProperty(amount) {
    if (amount == null) { amount = java.math.BigDecimal.ZERO; }
    return amount.compareTo(java.math.BigDecimal.ZERO) < 0 ? 1 : 0;
}

// ============================================================
// 6. 获取分录数据 & 合并逻辑
// ============================================================

/**
 * v4: 从 DataObject 的 entry 集合提取原始分录数据
 * @param {DataObjectInfo} dao - pluginCtx.getDataObject() 返回的对象
 */
function getEntryRows(dao) {
    var entryColl = dao.get("entry");
    if (entryColl == null) return [];
    var rows = [];
    var it = entryColl.iterator();
    var idx = 0;
    while (it.hasNext()) {
        var e = it.next();
        idx++;
        var taxNoObj = e.get("bdtaxno");
        rows.push({
            seq:              idx,
            coreBillType:     e.get("coreBillType"),
            zhubie:           e.get("zhubie"),
            goodsName:        e.get("bdinvname"),
            revenueCode:      taxNoObj != null ? taxNoObj.get("mergecode") : null,
            amountLocal:      e.get("amountlocal"),
            taxAmountLocal:   e.get("taxamountlocal"),
            taxRate:          e.get("taxrate"),
            quantity:         e.get("quantity"),
            taxPrice:         e.get("taxprice"),
            detailId:         sanitizeId(e.get("id")),
            specification:    e.get("materialmodel"),
            measureUnit:      e.get("measureunit")
        });
    }
    return rows;
}

/**
 * 分录合并（参照 开票申请单生成路线1.sql 第 29-47 行）
 *
 * 合并规则：
 *   - GROUP BY: goodsName + revenueCode + taxRate + spec + unit + _splitFlag
 *   - MERGE 行（_splitFlag == 0）: SUM 金额/税额/单价, 数量→±1
 *   - SPLIT 行（_splitFlag > 0）: 保持原样不合并
 *   - 税额校准: |SUM(税额) - 理论税额| > 0.06 时用 ROUND(理论税额, 2)
 *     理论税额 = 含税金额 - 含税金额/(1+税率)
 */
function mergeEntryRows(rows) {
    // 第1步：为每行计算派生字段
    for (var i = 0; i < rows.length; i++) {
        var r = rows[i];
        r._splitFlag = splitFlag(
            String(r.coreBillType),
            String(r.zhubie),
            r.seq
        );
        // 含税金额 = 金额 + 税额
        r.taxIncludedAmount = Number(r.amountLocal) + Number(r.taxAmountLocal);
    }

    // 第2步：分组
    // 分组键: goodsName + revenueCode + taxRate + specification + measureUnit + _splitFlag
    var groups = {};
    var groupOrder = [];

    for (var i = 0; i < rows.length; i++) {
        var r = rows[i];
        var key = [
            String(r.goodsName),
            String(r.revenueCode),
            formatTaxRate(r.taxRate),
            r.specification != null ? String(r.specification) : "",
            r.measureUnit != null ? String(r.measureUnit) : "",
            String(r._splitFlag)
        ].join("|||");

        if (!groups[key]) {
            groups[key] = {
                goodsName:      r.goodsName,
                revenueCode:    r.revenueCode,
                taxRate:        r.taxRate,
                specification:  r.specification,
                measureUnit:    r.measureUnit,
                _splitFlag:     r._splitFlag,
                amountSum:      0,
                taxAmountSum:   0,
                taxPriceSum:    0,
                quantitySum:    0,
                subRows:        []
            };
            groupOrder.push(key);
        }

        var g = groups[key];
        g.amountSum    += r.taxIncludedAmount;
        g.taxAmountSum += Number(r.taxAmountLocal);
        g.taxPriceSum  += Number(r.taxPrice) * Number(r.quantity);
        g.quantitySum  += Number(r.quantity);
        g.subRows.push(r);
    }

    // 第3步：构建合并后的 billDetail
    var billDetail = [];

    for (var gi = 0; gi < groupOrder.length; gi++) {
        var g = groups[groupOrder[gi]];

        if (g._splitFlag == 0) {
            // ============ MERGE 行：聚合 ============

            // 税额校准（SQL 第20行 & 第46行）
            // 理论税额 = 含税金额 - 含税金额 / (1 + 税率)
            var taxRateDecimal = Number(g.taxRate) / 100;
            var calTaxAmount = g.amountSum - (g.amountSum / (taxRateDecimal + 1));

            var finalTaxAmount;
            if (Math.abs(g.taxAmountSum - calTaxAmount) > 0.06) {
                finalTaxAmount = Math.round(calTaxAmount * 100) / 100;
            } else {
                finalTaxAmount = g.taxAmountSum;
            }

            // 数量（SQL 第38-41行）：金额>0→1, 金额<0→-1
            var finalQty = 0;
            if (g.amountSum > 0) {
                finalQty = 1;
            } else if (g.amountSum < 0) {
                finalQty = -1;
            }

            billDetail.push({
                lineProperty:   2,
                goodsName:      String(g.goodsName),
                revenueCode:    String(g.revenueCode),
                detailId:       String(g.subRows[0].detailId),
                amount:         round2(g.amountSum),
                taxRate:        formatTaxRate(g.taxRate),
                taxAmount:      round2(finalTaxAmount),
                quantity:       finalQty,
                price:          round2(g.taxPriceSum),
                specification:  g.specification != null ? notZero(String(g.specification)) : null,
                units:          g.measureUnit != null ? notZero(String(g.measureUnit)) : null
            });

        } else {
            // ============ SPLIT 行：保持原样 ============
            for (var ri = 0; ri < g.subRows.length; ri++) {
                var r = g.subRows[ri];
                billDetail.push({
                    lineProperty:   2,
                    goodsName:      String(r.goodsName),
                    revenueCode:    String(r.revenueCode),
                    detailId:       String(r.detailId),
                    amount:         round2(r.taxIncludedAmount),
                    taxRate:        formatTaxRate(r.taxRate),
                    taxAmount:      round2(Number(r.taxAmountLocal)),
                    quantity:       Number(r.quantity),
                    price:          round2(Number(r.taxPrice) * Number(r.quantity) * 1),
                    specification:  r.specification != null ? notZero(String(r.specification)) : null,
                    units:          r.measureUnit != null ? notZero(String(r.measureUnit)) : null
                });
            }
        }
    }

    return billDetail;
}

// ============================================================
// 7. 构建 API 请求体
// ============================================================

function buildRequestBody(pluginCtx) {
    // v4: 一次性获取 DataObject，减少 EAS API 调用次数
    var dao = pluginCtx.getDataObject();

    // --- 销方信息（不在 bill DataObject 中，仍需单独获取）---
    var companyOrgUnit = pluginCtx.getKDBizPromptBox("prmtCompanyOrgUnit").getValue();
    var sellerName = companyOrgUnit.get("Name");
    var orgCode    = companyOrgUnit.get("Number");

    // --- 购方信息（从 DataObject 提取）---
    var buyerName  = String(dao.get("cominvoicename"));
    var buyerTaxId = notZero(String(dao.get("taxno")));

    // --- 单据信息（从 DataObject 提取）---
    var billNo      = String(dao.get("number"));
    var requestId   = String(dao.get("id"));
    var digiType    = String(dao.get("diginvoicetype"));
    var includeTax  = 1;
    var custType    = String(dao.get("customertype"));
    var amount      = dao.get("totalamountlocal");

    // --- IO 状态 ---
    var ioStatus    = String(dao.get("bdiostatus"));
    var autoInvoice = (ioStatus == "IOInst");

    // --- 分录 → 合并 → billDetail ---
    var rawRows = getEntryRows(dao);
    var billDetail = mergeEntryRows(rawRows);

    // 构建 billElement
    var bill = {
        billNo:               billNo,
        invoiceProperty:      invoiceProperty(amount),
        invoiceType:          mapInvoiceType(digiType),
        includeTaxFlag:       includeTax,
        buyerName:            buyerName,
        buyerTaxpayerId:      buyerTaxId,
        buyerProperty:        mapBuyerProperty(custType),
        // buyerAddressAndTel:   notZero(String(dao.get("addressandtel"))),
        // buyerBankAndAccount:  notZero(String(dao.get("obankandacountnum"))),
        buyerRecipientPhone:  notZero(String(dao.get("recbillphone"))),
        buyerRecipientMail:   notZero(String(dao.get("recbillemail"))),
        orgCode:              orgCode,
        sellerName:           sellerName,
        remark:               notZero(String(dao.get("bdinvremark"))),
        billDetail:           billDetail
    };

    return {
        requestId: requestId,
        bills: [bill],
        autoInvoice: autoInvoice
    };
}

// ============================================================
// 8. 主入口：处理开票
// ============================================================

function handleInvoiceCreate(pluginCtx) {
    var billNo = pluginCtx.getKDTextField("txtNumber").getText();

    var ioStatus = pluginCtx.getKDComboBox("combobDIOStatus").getSelectedItem().getValue();
    if (ioStatus != "IOOnly" && ioStatus != "IOInst") {
        com.kingdee.eas.util.client.MsgBox.showInfo("[invoice_create] 跳过 " + billNo + "：CFBDIOSTATUS=" + ioStatus);
       return;
    }

    com.kingdee.eas.util.client.MsgBox.showInfo("[invoice_create] 开始处理 " + billNo + " ...");

    try {
        var payload = buildRequestBody(pluginCtx);
        var bodyJson = toJson(payload);

        // --- DEBUG: body MD5 调试验证（v4 新增）---
//        var bodyMd5 = bytesToHex(java.security.MessageDigest.getInstance("MD5")
//            .digest(new java.lang.String(bodyJson).getBytes("UTF-8")));
//        com.kingdee.eas.util.client.MsgBox.showInfo("[DEBUG] Body MD5: " + bodyMd5);
//        com.kingdee.eas.util.client.MsgBox.showInfo("[DEBUG] Body length: " + bodyJson.length);

        var path = "/api/proxy/v1/invoice/create";
        var sig = sign("POST", path, bodyJson, API_KEY, API_SECRET);

        var headers = {
            "Content-Type":       "application/json",
            "X-Proxy-Api-Key":    sig.apiKey,
            "X-Proxy-Timestamp":  sig.timestamp,
            "X-Proxy-Signature":  sig.signature,
            "X-Proxy-Env":        API_ENV
        };

        var resp = httpPost(BASE_URL + path, headers, bodyJson);

        com.kingdee.eas.util.client.MsgBox.showInfo("[invoice_create] HTTP " + resp.code);
        com.kingdee.eas.util.client.MsgBox.showInfo("[invoice_create] Response: " + resp.body);

        // 回写结果（待调试通过后启用）
        // if (resp.code === 200) { ... }

    } catch (e) {
        com.kingdee.eas.util.client.MsgBox.showInfo("[invoice_create] " + billNo + " 异常：" + e.message);
        try { pluginCtx.getKDTextField("CFBDIOSTATUS").setText("IOError"); } catch(e2) {}
    }
}
