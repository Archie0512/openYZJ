import json


def build_pass_card_data(
    pass_data: dict,
    company_name: str,
    car_no: str,
    service: str,
    qr_image_url: str,
) -> str:
    """构建道闸通行证卡片的 dataContent JSON 字符串。

    变量与云之家卡片模板 (templateId: 6a1ff701e4b0bd1d0dce47b9) 对应：
    - title: 卡片顶部标题
    - company_name: 门店名称
    - car_no: 车牌号码
    - start_time: 发放时间
    - end_time: 有效截止
    - service: 放行事由
    - qr_image_url: 纯二维码图片 URL
    - desc: 备注信息
    - textLiPrefix1~6: 各行前缀标签
    - static_text: 底部静态提示文本
    """
    data = {
        "title": f"出门单 #{pass_data.get('No', '')}",
        "textLiPrefix4": "门店：",
        "company_name": company_name,
        "textLiPrefix3": "车牌：",
        "car_no": car_no,
        "textLiPrefix1": "发放时间：",
        "start_time": pass_data.get("StartTime", ""),
        "textLiPrefix2": "截止时间：",
        "end_time": pass_data.get("EndTime", ""),
        "textLiPrefix5": "事由：",
        "service": service,
        "qr_image_url": qr_image_url,
        "textLiPrefix6": "备注：",
        "desc": pass_data.get("Desc", "") or "请在有效期内使用",
        "static_text": "该出门单有效期为1小时",
    }
    return json.dumps(data, ensure_ascii=False)
