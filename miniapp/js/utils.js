/**
 * 通用工具函数 - utils.js
 */

// ─── 云之家 JS-SDK 用户信息 ───
var _currentUser = null;

/**
 * 获取云之家用户信息
 * @param {function} callback 回调函数(user)
 */
function getYZJUser(callback) {
  // 检测云之家环境（移动端/桌面端）
  var isYzjApp = navigator.userAgent.match(/Qing\/.*;(iPhone|Android).*/);
  var isCloudHub = /cloudhub 10204/.test(navigator.userAgent);

  if (isYzjApp || isCloudHub) {
    // 云之家环境：调用 XuntongJSBridge 获取用户信息
    XuntongJSBridge.call('getPersonInfo', {}, function(result) {
      if (typeof result === 'string') result = JSON.parse(result); // 桌面端返回 string
      if (String(result.success) === 'true' && result.data) {
        _currentUser = {
          openid: result.data.openId,
          name: result.data.name,
          eid: result.data.eid,
          photoUrl: result.data.photoUrl
        };
        callback(_currentUser);
      } else {
        // 获取失败，使用空用户
        console.warn('[YZJ] getPersonInfo 失败:', result.error);
        _currentUser = { openid: '', name: '未知用户' };
        callback(_currentUser);
      }
    });
  } else {
    // 非云之家环境（本地开发/外部浏览器）
    _currentUser = { openid: 'dev_user_001', name: '开发测试', department: '技术部' };
    callback(_currentUser);
  }
}

/**
 * 判断是否为云之家桌面端
 * @returns {boolean}
 */
function isDesktop() {
  return /cloudhub 10204/.test(navigator.userAgent);
}

/**
 * 获取当前用户
 * @returns {object|null}
 */
function getCurrentUser() {
  return _currentUser;
}

/**
 * 显示 Toast 提示
 * @param {string} msg 提示文本
 * @param {number} duration 显示时长(ms)，默认 2000
 */
function showToast(msg, duration) {
  duration = duration || 2000;
  var existing = document.querySelector('.toast');
  if (existing) existing.remove();

  var el = document.createElement('div');
  el.className = 'toast show';
  el.textContent = msg;
  document.body.appendChild(el);

  setTimeout(function () {
    el.classList.remove('show');
    setTimeout(function () { el.remove(); }, 300);
  }, duration);
}

/**
 * 显示 Loading
 * @param {HTMLElement} container 容器元素
 * @param {string} text 加载文案
 */
function showLoading(container, text) {
  container.innerHTML = '<div class="loading">' + (text || '加载中...') + '</div>';
}

/**
 * 格式化日期时间
 * @param {string|number} dateStr ISO 字符串或时间戳
 * @returns {string} yyyy-MM-dd HH:mm
 */
function formatDateTime(dateStr) {
  if (!dateStr) return '-';
  var d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var day = String(d.getDate()).padStart(2, '0');
  var h = String(d.getHours()).padStart(2, '0');
  var min = String(d.getMinutes()).padStart(2, '0');
  return y + '-' + m + '-' + day + ' ' + h + ':' + min;
}

/**
 * 获取 URL hash 中的参数
 * @param {string} name 参数名
 * @returns {string|null}
 */
function getHashParam(name) {
  var hash = window.location.hash;
  var queryIndex = hash.indexOf('?');
  if (queryIndex === -1) return null;
  var queryStr = hash.slice(queryIndex + 1);
  var params = new URLSearchParams(queryStr);
  return params.get(name);
}

/**
 * 设置按钮为加载状态
 * @param {HTMLElement} btn 按钮元素
 * @param {boolean} loading 是否加载中
 * @param {string} text 加载时文案
 */
function setBtnLoading(btn, loading, text) {
  if (loading) {
    btn._originalText = btn.textContent;
    btn.textContent = text || '处理中...';
    btn.classList.add('btn-disabled');
  } else {
    btn.textContent = btn._originalText || '提交';
    btn.classList.remove('btn-disabled');
  }
}
