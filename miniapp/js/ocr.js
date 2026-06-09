/**
 * OCR 识别封装 - ocr.js
 * 使用 Tesseract.js (通过 CDN 全局引入)
 */

/**
 * 识别车牌号
 * @param {string|HTMLCanvasElement|ImageData} imageData 图片数据
 * @returns {Promise<string|null>} 匹配到的车牌号或 null
 */
async function recognizePlate(imageData) {
  if (typeof Tesseract === 'undefined') {
    showToast('OCR 引擎未加载，请稍后重试');
    return null;
  }

  try {
    var result = await Tesseract.recognize(imageData, 'chi_sim+eng', {
      logger: function () {},
    });

    var text = result.data.text || '';
    // 去除空白字符
    text = text.replace(/\s+/g, '');
    // 用车牌正则匹配
    var plate = extractPlate(text);
    return plate;
  } catch (err) {
    console.error('[OCR] 识别失败:', err);
    return null;
  }
}

/**
 * 启动摄像头
 * @param {HTMLVideoElement} videoElement video 元素
 * @returns {Promise<MediaStream>}
 */
async function startCamera(videoElement) {
  var constraints = {
    video: {
      facingMode: { ideal: 'environment' }, // 优先后置摄像头
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  };

  try {
    var stream = await navigator.mediaDevices.getUserMedia(constraints);
    videoElement.srcObject = stream;
    await videoElement.play();
    return stream;
  } catch (err) {
    console.error('[Camera] 启动失败:', err);
    throw err;
  }
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

/**
 * 从视频中截取一帧
 * @param {HTMLVideoElement} videoElement video 元素
 * @returns {HTMLCanvasElement} canvas 元素
 */
function captureFrame(videoElement) {
  var canvas = document.createElement('canvas');
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;
  var ctx = canvas.getContext('2d');
  ctx.drawImage(videoElement, 0, 0);
  return canvas;
}
