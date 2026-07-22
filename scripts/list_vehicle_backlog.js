// 列出机动车回调积压的 _id（每行一个），供批量补转发使用。
//
// 判定条件（机动车/无 billNo 且未成功转发的成功开票回调）：
//   endpoint = by-invoice   （只有按票回调才转发）
//   return_code = "0"        （开票成功；9999 失败的按设计 skip，不补）
//   bill_nos = []            （机动车无 billNo，单据号在 serialNo）
//   forward_status != "sent" （包含 None/缺失/failed，$ne 也匹配字段缺失）
//
// 用法：
//   docker cp scripts/list_vehicle_backlog.js openyzj-mongo-1:/tmp/
//   docker exec openyzj-mongo-1 bash -c \
//     'mongosh "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@localhost:27017/yunzhijia?authSource=admin" --quiet --file /tmp/list_vehicle_backlog.js'

db.getSiblingDB("yunzhijia").kdcloud_callbacks.find(
  {
    endpoint: "by-invoice",
    return_code: "0",
    bill_nos: { $size: 0 },
    forward_status: { $ne: "sent" },
  },
  { _id: 1 }
).forEach(function (d) {
  print(d._id.toString());
});
