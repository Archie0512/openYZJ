/**
 * SPA 路由管理 - app.js
 * 通过 hash 切换页面，fetch 加载 HTML 片段注入 #app 容器
 * 支持顶部 Tab 切换和触摸滑动
 */

// 路由配置
var routes = {
  '/passcard': 'pages/passcard-form.html',
  '/history': 'pages/passcard-history.html',
  '/passcard/detail': 'pages/passcard-detail.html',
};

// 页面初始化函数映射
var pageInitMap = {
  '/passcard': 'initPasscardFormPage',
  '/history': 'initPasscardHistoryPage',
  '/passcard/detail': 'initPasscardDetailPage',
};

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
 * 加载并渲染页面
 */
async function loadPage() {
  // 清理之前的摄像头
  if (_activeStream) {
    stopCamera(_activeStream);
    _activeStream = null;
  }

  var route = getCurrentRoute();

  var templatePath = routes[route];
  if (!templatePath) {
    templatePath = routes['/passcard'];
    route = '/passcard';
  }

  var appEl = document.getElementById('app');

  // 更新 Tab 状态
  updateTabBar();

  try {
    var resp = await fetch(templatePath);
    if (!resp.ok) throw new Error('页面加载失败');
    var html = await resp.text();
    appEl.innerHTML = html;

    // innerHTML 注入的 script 不会自动执行，需手动重新插入
    var scripts = appEl.querySelectorAll('script');
    scripts.forEach(function(oldScript) {
      var newScript = document.createElement('script');
      if (oldScript.src) {
        newScript.src = oldScript.src;
      } else {
        newScript.textContent = oldScript.textContent;
      }
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });

    // 执行页面初始化
    var initFn = pageInitMap[route];
    if (initFn && typeof window[initFn] === 'function') {
      window[initFn]();
    }
  } catch (err) {
    appEl.innerHTML = '<div class="empty"><div class="icon">😵</div><p>页面加载失败</p></div>';
    console.error('[Router] 加载页面失败:', err);
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
  var appEl = document.getElementById('app');
  if (!appEl) return;

  appEl.addEventListener('touchstart', function (e) {
    _touchStartX = e.touches[0].clientX;
    _touchStartY = e.touches[0].clientY;
  }, { passive: true });

  appEl.addEventListener('touchend', function (e) {
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
