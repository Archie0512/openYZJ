/**
 * 通用工具函数 - utils.js
 */

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

/**
 * 检查是否已登录
 * @returns {boolean}
 */
function isLoggedIn() {
  return !!localStorage.getItem('token');
}

/**
 * 获取 Token
 * @returns {string}
 */
function getToken() {
  return localStorage.getItem('token') || '';
}

/**
 * 登出清除 Token
 */
function logout() {
  localStorage.removeItem('token');
  window.location.hash = '#/login';
}
