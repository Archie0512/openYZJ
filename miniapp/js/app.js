/**
 * SPA 路由管理 - app.js
 * 通过 hash 切换页面，fetch 加载 HTML 片段注入 #app 容器
 */

// 路由配置
var routes = {
  '/login': 'pages/login.html',
  '/home': 'pages/home.html',
  '/passcard': 'pages/passcard-form.html',
  '/passcard/detail': 'pages/passcard-detail.html',
  '/passcard/history': 'pages/passcard-history.html',
};

// 页面初始化函数映射
var pageInitMap = {
  '/login': initLoginPage,
  '/home': initHomePage,
  '/passcard': initPasscardFormPage,
  '/passcard/detail': initPasscardDetailPage,
  '/passcard/history': initPasscardHistoryPage,
};

// 当前活跃的摄像头流（离开页面时需清理）
var _activeStream = null;

/**
 * 获取当前路由路径（不含参数）
 */
function getCurrentRoute() {
  var hash = window.location.hash.slice(1) || '/login';
  var qIdx = hash.indexOf('?');
  return qIdx > -1 ? hash.slice(0, qIdx) : hash;
}

/**
 * 导航到指定路由
 * @param {string} path 路由路径
 * @param {object} [params] URL 参数
 */
function navigateTo(path, params) {
  var hash = '#' + path;
  if (params) {
    var qs = Object.keys(params).map(function (k) {
      return k + '=' + encodeURIComponent(params[k]);
    }).join('&');
    hash += '?' + qs;
  }
  window.location.hash = hash;
}

/**
 * 加载并渲染页面
 */
async function loadPage() {
  // 清理之前的摄像头
  if (_activeStream) {
    stopCamera(_activeStream);
    _activeStream = null;
  }

  var route = getCurrentRoute();

  // 登录检查（非登录页需要 token）
  if (route !== '/login' && !isLoggedIn()) {
    window.location.hash = '#/login';
    return;
  }

  // 已登录访问登录页则重定向到首页
  if (route === '/login' && isLoggedIn()) {
    window.location.hash = '#/home';
    return;
  }

  var templatePath = routes[route];
  if (!templatePath) {
    templatePath = routes['/home'];
    route = '/home';
  }

  var appEl = document.getElementById('app');

  try {
    var resp = await fetch(templatePath);
    if (!resp.ok) throw new Error('页面加载失败');
    var html = await resp.text();
    appEl.innerHTML = html;

    // 执行页面初始化
    var initFn = pageInitMap[route];
    if (initFn) initFn();
  } catch (err) {
    appEl.innerHTML = '<div class="empty"><div class="icon">😵</div><p>页面加载失败</p></div>';
    console.error('[Router] 加载页面失败:', err);
  }
}

/**
 * 初始化应用
 */
function initApp() {
  // 监听路由变化
  window.addEventListener('hashchange', loadPage);

  // 初始加载
  if (!window.location.hash) {
    window.location.hash = '#/login';
  } else {
    loadPage();
  }
}

// DOM 就绪后启动
document.addEventListener('DOMContentLoaded', initApp);
