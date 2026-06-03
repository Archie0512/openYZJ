import base64
import qrcode
from pathlib import Path
from app.config import settings

_OUTPUT_DIR = Path(settings.passes_dir)


def generate_qrcode_png(data: dict) -> str:
    """生成纯二维码 PNG，返回相对 URL 路径。

    编码规则：ShopId__Id__Info 的 UTF-8 Base64
    """
    shop_id = str(data.get("ShopId", ""))
    pass_id = str(data.get("Id", ""))
    info = str(data.get("Info", ""))

    raw_text = f"{shop_id}__{pass_id}__{info}"
    qr_content = base64.b64encode(raw_text.encode("utf-8")).decode("ascii")

    # 生成二维码
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # 保存
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUT_DIR / f"{pass_id}.png"
    img.save(str(output_path), "PNG")

    return f"/static/passes/{pass_id}.png"
