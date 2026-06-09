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
  // 云之家环境
  if (window.YZJ && window.YZJ.getUser) {
    window.YZJ.getUser(function(result) {
      if (result && result.openid) {
        _currentUser = result;
        callback(result);
      }
    });
  } else {
    // 本地开发 mock 模式
    var mockUser = {
      openid: 'dev_user_001',
      name: '开发测试',
      department: '技术部'
    };
    _currentUser = mockUser;
    callback(mockUser);
  }
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
