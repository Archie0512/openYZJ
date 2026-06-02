"""二维码 PNG 生成模块：为无牌车生成出门单二维码图片。"""
from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image, ImageDraw, ImageFont

from app.config import settings

log = logging.getLogger(__name__)

# 输出目录（可通过 settings 配置，默认项目根下 static/passes/）
_OUTPUT_DIR = Path(getattr(settings, "passes_dir", "static/passes"))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """尝试加载中文字体，失败则 fallback 到默认字体。

    生产环境（Linux 容器）需安装中文字体包，如 fonts-wqy-zenhei。
    """
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",  # Windows 宋体
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    # fallback：Pillow 默认字体（不支持中文，生产环境需安装字体包）
    return ImageFont.load_default()


def generate_pass_png(data: dict, company_name: str) -> str:
    """生成出门单二维码 PNG 图片。

    Args:
        data: MYS4S API 返回的 data 字典，包含 ShopId, Id, Info, StartTime, Service, Desc, No 等字段
        company_name: 门店名称

    Returns:
        相对路径，如 /static/passes/{Id}.png
    """
    # 提取字段
    shop_id = str(data.get("ShopId", ""))
    pass_id = str(data.get("Id", ""))
    info = str(data.get("Info", ""))
    start_time = str(data.get("StartTime", ""))
    service = str(data.get("Service", ""))
    desc = str(data.get("Desc", ""))
    no = str(data.get("No", ""))

    # 编码规则：原始明文 = {ShopId}__{Id}__{Info}，UTF-8 后 Base64
    plaintext = f"{shop_id}__{pass_id}__{info}"
    qr_content = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")

    # 生成二维码图像
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    # 缩放到 200x200
    qr_img = qr_img.resize((200, 200), Image.LANCZOS)

    # 加载字体
    title_font = _load_font(22)
    normal_font = _load_font(16)

    # 计算布局高度
    padding = 15
    line_height_title = 30
    line_height_normal = 24
    qr_size = 200
    separator_height = 1

    # 构建文本行
    lines_before_qr = [
        (f"出门单 {no}", title_font, line_height_title),
        (company_name, normal_font, line_height_normal),
        (f"车牌号码: {info}", normal_font, line_height_normal),
        (f"发放时间: {start_time}", normal_font, line_height_normal),
        (f"放行原因: {service}", normal_font, line_height_normal),
    ]

    lines_after_qr = []
    if desc:
        lines_after_qr.append((f"备注: {desc}", normal_font, line_height_normal))
    lines_after_qr.append(("谢谢惠顾，欢迎再次光临！", normal_font, line_height_normal))

    # 计算总高度
    height = padding  # 上边距
    for _, _, lh in lines_before_qr:
        height += lh
    height += padding  # 分割线前间距
    height += separator_height
    height += padding  # 分割线后间距
    height += line_height_normal  # "出门请扫描下方二维码"
    height += 10  # 间距
    height += qr_size
    height += 10  # 间距
    for _, _, lh in lines_after_qr:
        height += lh
    height += padding  # 下边距

    width = 350

    # 创建画布
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    y = padding

    # 绘制分割线前的文本
    for text, font, lh in lines_before_qr:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        draw.text((x, y), text, fill="black", font=font)
        y += lh

    # 分割线
    y += padding
    draw.line([(0, y), (width, y)], fill="black", width=1)
    y += separator_height + padding

    # 提示文字
    hint = "出门请扫描下方二维码"
    bbox = draw.textbbox((0, 0), hint, font=normal_font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, y), hint, fill="black", font=normal_font)
    y += line_height_normal + 10

    # 二维码
    qr_x = (width - qr_size) // 2
    img.paste(qr_img, (qr_x, y))
    y += qr_size + 10

    # 分割线后的文本
    for text, font, lh in lines_after_qr:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        draw.text((x, y), text, fill="black", font=font)
        y += lh

    # 确保输出目录存在
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 保存 PNG
    output_path = _OUTPUT_DIR / f"{pass_id}.png"
    img.save(str(output_path), "PNG")
    log.info("二维码已生成: %s", output_path)

    return f"/static/passes/{pass_id}.png"
