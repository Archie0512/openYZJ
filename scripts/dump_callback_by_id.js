// 按 _id dump 单条金蝶回调的完整原始报文 + 解码后内层 JSON（用于确认接收内容）。
//
// 用法（在 mongo 容器内）：
//   docker cp scripts/dump_callback_by_id.js openyzj-mongo-1:/tmp/
//   docker exec openyzj-mongo-1 bash -c \
//     'mongosh "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@localhost:27017/yunzhijia?authSource=admin" --quiet --file /tmp/dump_callback_by_id.js'
//
// 换记录改下面 ID 即可。

var ID = "6a5f1577bf03a75afd1c2172";

var d = db.getSiblingDB("yunzhijia").kdcloud_callbacks.findOne({ _id: ObjectId(ID) });
if (!d) {
  print("NOT FOUND: " + ID);
} else {
  print("_id               : " + d._id);
  print("received_at(UTC)  : " + d.received_at.toISOString());
  print("endpoint          : " + d.endpoint);
  print("interface_code    : " + d.interface_code);
  print("return_code       : " + d.return_code);
  print("forward_status    : " + d.forward_status);
  print("forward_attempts  : " + d.forward_attempts);
  print("last_forward_error: " + d.last_forward_error);
  print("matched_client    : " + d.matched_client_id);
  print("bill_nos          : " + JSON.stringify(d.bill_nos));
  print("serial_nos        : " + JSON.stringify(d.serial_nos));
  print("client_ip         : " + d.client_ip);
  print("---- raw_body (原始请求体) ----");
  print(d.raw_body);
  print("---- data 解码后内层 JSON ----");
  try {
    var body = JSON.parse(d.raw_body);
    var data = body.data;
    if (typeof data === "string") {
      data = JSON.parse(Buffer.from(data, "base64").toString("utf8"));
    }
    printjson(data);
    if (data && !Array.isArray(data)) {
      print("---- 内层关键字段 ----");
      print("billNo     = " + data.billNo);
      print("serialNo   = " + data.serialNo);
      print("invoiceNum = " + data.invoiceNum + "   (type=" + (typeof data.invoiceNum) + ")");
      print("systemSource = " + data.systemSource);
    }
  } catch (e) {
    print("decode error: " + e);
  }
  if (d.forward_history) {
    print("---- forward_history ----");
    printjson(d.forward_history);
  }
}
