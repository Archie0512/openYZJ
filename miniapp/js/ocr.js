/**
 * OCR 识别封装 - ocr.js
 * 通过服务端 API 识别车牌
 */

/**
 * 上传图片进行 OCR 识别车牌
 * @param {File} file 图片文件
 * @returns {Promise<string|null>} 识别到的车牌号或 null
 */
function uploadForOCR(file) {
  // 如果是桌面端，不启动摄像头，隐藏拍照区域
  if (isDesktop()) {
    var ocrSection = document.getElementById('ocrSection') || document.querySelector('.ocr-section');
    if (ocrSection) {
      ocrSection.style.display = 'none';
    }
    return Promise.resolve(null);
  }

  return api.ocrPlate(file)
    .then(function (res) {
      var plates = (res.data && res.data.plates) || [];
      if (plates.length > 0) {
        return plates[0];
      }
      return null;
    })
    .catch(function (err) {
      console.error('[OCR] 识别失败:', err);
      return null;
    });
}

/**
 * 停止摄像头
 * @param {MediaStream} stream 媒体流
 */
function stopCamera(stream) {
  if (stream) {
    stream.getTracks().forEach(function (track) {
      track.stop();
    });
  }
}
