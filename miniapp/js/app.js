/**
 * SPA 路由管理 - app.js
 * 通过 hash 切换页面，display:none/block 控制可见性
 * 支持顶部 Tab 切换和触摸滑动
 */

// 页面初始化函数映射
var pageInitMap = {
  '/passcard': 'initPasscardFormPage',
  '/history': 'initPasscardHistoryPage',
  '/passcard/detail': 'initPasscardDetailPage',
};

// 路由 → 页面容器 ID 映射
function routeToPageId(route) {
  var map = {
    '/passcard': 'page-passcard',
    '/history': 'page-history',
    '/passcard/detail': 'page-detail',
  };
  return map[route] || 'page-passcard';
}

// Tab 路由列表（可滑动切换的）
var tabRoutes = ['/passcard', '/history'];

// 当前活跃的摄像头流（离开页面时需清理）
var _activeStream = null;

// 触摸滑动检测
var _touchStartX = 0;
var _touchStartY = 0;

/**
 * 获取当前路由路径（不含参数）
 */
function getCurrentRoute() {
  var hash = window.location.hash.slice(1) || '/passcard';
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
 * 更新 Tab 栏状态
 */
function updateTabBar() {
  var route = getCurrentRoute();
  var tabBar = document.getElementById('tabBar');
  if (!tabBar) return;

  // detail 页面隐藏 Tab 栏
  if (route === '/passcard/detail') {
    tabBar.style.display = 'none';
    return;
  }

  tabBar.style.display = 'flex';
  var items = tabBar.querySelectorAll('.tab-item');
  items.forEach(function (item) {
    if (item.getAttribute('data-route') === route) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
}

/**
 * 加载并渲染页面（display 切换）
 */
function loadPage() {
  // 清理之前的摄像头
  if (_activeStream) {
    stopCamera(_activeStream);
    _activeStream = null;
  }

  var route = getCurrentRoute();

  // 路由不存在则回退到申请页
  if (!routeToPageId(route) || routeToPageId(route) === 'page-passcard' && route !== '/passcard') {
    route = '/passcard';
  }

  // 隐藏所有页面
  var pages = document.querySelectorAll('.page');
  pages.forEach(function (p) {
    p.style.display = 'none';
    p.classList.remove('active');
  });

  // 显示目标页面
  var pageId = routeToPageId(route);
  var targetPage = document.getElementById(pageId);
  if (targetPage) {
    targetPage.style.display = 'block';
    targetPage.classList.add('active');
  }

  // 更新 Tab 栏状态
  updateTabBar();

  // 执行页面初始化
  var initFn = pageInitMap[route];
  if (initFn && typeof window[initFn] === 'function') {
    window[initFn]();
  }
}

/**
 * 初始化 Tab 栏点击事件
 */
function initTabBar() {
  var tabBar = document.getElementById('tabBar');
  if (!tabBar) return;

  tabBar.addEventListener('click', function (e) {
    var item = e.target.closest('.tab-item');
    if (!item) return;
    var route = item.getAttribute('data-route');
    if (route) {
      navigateTo(route);
    }
  });
}

/**
 * 初始化触摸滑动切换
 */
function initSwipe() {
  var container = document.getElementById('app-container');
  if (!container) return;

  container.addEventListener('touchstart', function (e) {
    _touchStartX = e.touches[0].clientX;
    _touchStartY = e.touches[0].clientY;
  }, { passive: true });

  container.addEventListener('touchend', function (e) {
    var deltaX = e.changedTouches[0].clientX - _touchStartX;
    var deltaY = e.changedTouches[0].clientY - _touchStartY;

    // 只在水平滑动距离大于垂直时触发
    if (Math.abs(deltaX) < 60 || Math.abs(deltaX) < Math.abs(deltaY)) return;

    var route = getCurrentRoute();
    var idx = tabRoutes.indexOf(route);
    if (idx === -1) return;

    if (deltaX < 0 && idx < tabRoutes.length - 1) {
      // 向左滑 → 下一个 Tab
      navigateTo(tabRoutes[idx + 1]);
    } else if (deltaX > 0 && idx > 0) {
      // 向右滑 → 上一个 Tab
      navigateTo(tabRoutes[idx - 1]);
    }
  }, { passive: true });
}

/**
 * 初始化应用
 */
function initApp() {
  // 获取用户信息
  getYZJUser(function (user) {
    console.log('[App] 用户信息:', user.name || user.openid);

    // 初始化 Tab 栏
    initTabBar();

    // 初始化滑动
    initSwipe();

    // 监听路由变化
    window.addEventListener('hashchange', loadPage);

    // 初始加载
    if (!window.location.hash || window.location.hash === '#/login' || window.location.hash === '#/home') {
      window.location.hash = '#/passcard';
    } else {
      loadPage();
    }
  });
}

// DOM 就绪后启动
document.addEventListener('DOMContentLoaded', initApp);
