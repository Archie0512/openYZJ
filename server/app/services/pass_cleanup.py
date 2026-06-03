import time
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

MAX_AGE_SECONDS = 3600  # 1 小时


def cleanup_expired_passes():
    """删除超过 1 小时的 PNG 文件。"""
    passes_dir = Path(settings.passes_dir)
    if not passes_dir.exists():
        return
    now = time.time()
    removed = 0
    for f in passes_dir.glob("*.png"):
        try:
            if now - f.stat().st_mtime > MAX_AGE_SECONDS:
                f.unlink(missing_ok=True)
                removed += 1
        except OSError:
            pass
    if removed:
        logger.info(f"Cleaned up {removed} expired pass PNG files")
