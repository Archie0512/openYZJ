// preset_robots.js — MongoDB 预置脚本
// 
// 从 yzjrob_mys.ini 映射中批量更新 robots 集合的 sid 和 company_name。
// 仅更新已存在的 robot_code（不创建新文档），保留已有 appSecret_encrypted 等字段。
//
// 使用方式（在服务器上执行）：
//   mongosh "mongodb://admin:<MONGO_PASSWORD>@localhost:27017/yunzhijia?authSource=admin" --file scripts/preset_robots.js
//
// 或在 Docker 容器内执行：
//   docker exec -i <mongo_container> mongosh -u "$MONGO_USER" -p "$MONGO_PASSWORD" --authenticationDatabase admin yunzhijia < scripts/preset_robots.js

const updates = [
    { robot_code: "B10ARelease", sid: "1479", company_name: "台州好德宝汽车服务有限公司" },
    { robot_code: "B02ARelease", sid: "20159", company_name: "上海德宝汽车服务有限公司" },
    { robot_code: "B03ARelease", sid: "25834", company_name: "上海好德宝汽车销售服务有限公司" },
    { robot_code: "B16ARelease", sid: "25909", company_name: "南京德宝汽车销售服务有限公司" },
    { robot_code: "B08ARelease", sid: "14262", company_name: "丹阳宝德汽车销售服务有限公司" },
    { robot_code: "B06ARelease", sid: "25797", company_name: "镇江宝德汽车服务有限公司" },
    { robot_code: "B07ARelease", sid: "25949", company_name: "扬中宝德汽车服务有限公司" },
    { robot_code: "B01ARelease", sid: "17899", company_name: "上海凡德汽车销售服务有限公司" },
    { robot_code: "B09ARelease", sid: "41", company_name: "杭州宝荣汽车销售服务有限公司" },
    { robot_code: "P01ARelease", sid: "22512", company_name: "常州宝荣汽车销售服务有限公司" },
    { robot_code: "P02ARelease", sid: "25826", company_name: "徐州宝荣汽车销售服务有限公司" },
    { robot_code: "P03ARelease", sid: "25830", company_name: "镇江宝荣汽车销售服务有限公司" },
    { robot_code: "P04ARelease", sid: "25910", company_name: "扬州宝荣汽车销售服务有限公司" },
    { robot_code: "B11ARelease", sid: "25938", company_name: "句容宝荣汽车服务有限公司" },
    { robot_code: "B04ARelease", sid: "12477", company_name: "南京宁宝汽车服务有限公司" },
    { robot_code: "B12ARelease", sid: "25986", company_name: "常州宁宝汽车销售服务有限公司" },
    { robot_code: "P05ARelease", sid: "26026", company_name: "淮安宁宝汽车销售服务有限公司" },
    { robot_code: "B17ARelease", sid: "26114", company_name: "苏州宝韵汽车销售服务有限公司" },
];

let updated = 0, skipped = 0;

updates.forEach(function (entry) {
    const result = db.robots.updateOne(
        { robot_code: entry.robot_code },
        {
            $set: {
                sid: entry.sid,
                company_name: entry.company_name,
                updated_at: new Date(),
            },
        }
    );

    if (result.matchedCount > 0) {
        print(`[OK] ${entry.robot_code} → sid=${entry.sid} ${entry.company_name}`);
        updated++;
    } else {
        print(`[SKIP] ${entry.robot_code} — robot_code 不存在于 robots 集合，请先通过 admin API 注册`);
        skipped++;
    }
});

print(`\n===== 完成 =====`);
print(`更新: ${updated}  跳过(未注册): ${skipped}`);
