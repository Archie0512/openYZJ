// 按 invoiceNum 精确定位金蝶发票云回调原始报文（含转发诊断字段）。
//
// 背景：invoiceNum 位于回调 data 字段的 base64 内层 JSON，不是 kdcloud_callbacks
//       的打平索引字段（打平的只有 serial_nos / bill_nos / batches / system_sources /
//       interface_code / return_code），因此 admin API 和对 raw_body 直接 grep 都无法命中，
//       必须先 base64 解码 data 再匹配。
//
// 用法（在 mongo 容器内，通过 mongosh --file 运行）：
//   1) 把本文件送入容器：docker cp scripts/find_callback_by_invoice.js openyzj-mongo-1:/tmp/
//   2) 运行：
//      docker exec openyzj-mongo-1 bash -c \
//        'mongosh "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@localhost:27017/yunzhijia?authSource=admin" --quiet --file /tmp/find_callback_by_invoice.js'
//
// 如需查别的发票/时间段，改下面 TARGET / START / END 即可。

var TARGET = "26322000005935198201";
// 金蝶回调时间 2026-07-21 14:45:11（北京时间）= 06:45:11 UTC；received_at 以 UTC 存储。
// 用整天 UTC 窗口覆盖；若命中 0 条可放宽窗口再试。
var START = new Date("2026-07-21T00:00:00Z");
var END = new Date("2026-07-22T00:00:00Z");

var coll = db.getSiblingDB("yunzhijia").kdcloud_callbacks;
var scanned = 0;
var matched = 0;

coll.find({ received_at: { $gte: START, $lt: END } })
  .sort({ received_at: 1 })
  .forEach(function (d) {
    scanned++;
    var inner = null;
    var invs = [];
    try {
      var body = JSON.parse(d.raw_body);
      var data = body.data;
      if (typeof data === "string") {
        data = JSON.parse(Buffer.from(data, "base64").toString("utf8"));
      }
      inner = data;
      var arr = Array.isArray(data) ? data : [data];
      invs = arr.filter(function (e) { return e; })
        .map(function (e) { return e.invoiceNum; });
    } catch (e) {
      // raw_body 非 JSON 或 data 非 base64，跳过匹配
    }

    if (invs.indexOf(TARGET) >= 0) {
      matched++;
      print("==================== MATCH ====================");
      print("_id             : " + d._id);
      print("received_at(UTC): " + d.received_at.toISOString());
      print("endpoint        : " + d.endpoint);
      print("interface_code  : " + d.interface_code);
      print("return_code     : " + d.return_code + "   (非 0 = 开票失败，自动转发会 skip)");
      print("forward_status  : " + d.forward_status);
      print("forward_attempts: " + d.forward_attempts);
      print("matched_client  : " + d.matched_client_id + "   (null = 未匹配到 client / 无 callback_url，不会转发)");
      print("client_ip       : " + d.client_ip);
      print("---- raw_body (原始请求体) ----");
      print(d.raw_body);
      print("---- data 解码后内层 JSON ----");
      printjson(inner);
      if (d.forward_history) {
        print("---- forward_history ----");
        printjson(d.forward_history);
      }
    }
  });

print("");
print(">>> 窗口内扫描 " + scanned + " 条，命中 invoiceNum=" + TARGET + " 共 " + matched + " 条");
if (matched === 0) {
  print(">>> 未命中。可能原因：");
  print(">>>   1) 回调根本没进库 —— 查 nginx/OpenResty access log，确认是否到达 /callbacks/by-invoice；");
  print(">>>   2) 时间窗口不对 —— 放宽 START/END 再试；");
  print(">>>   3) invoiceNum 与报文内实际值不一致。");
}
