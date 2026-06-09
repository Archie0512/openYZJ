/**
 * API 调用封装 - api.js
 * 统一 Bearer Token 鉴权
 */

var API_BASE = '/api/v1';

/**
 * 通用请求函数
 * @param {string} method HTTP 方法
 * @param {string} path API 路径
 * @param {object} [data] 请求体（POST/PUT）
 * @returns {Promise<object>} 响应 JSON
 */
function request(method, path, data) {
  var token = getToken();
  var url = API_BASE + path;
  var options = {
    method: method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token,
    },
  };

  if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    options.body = JSON.stringify(data);
  }

  return fetch(url, options)
    .then(function (resp) {
      if (resp.status === 401) {
        showToast('登录已过期，请重新登录');
        logout();
        return Promise.reject(new Error('Unauthorized'));
      }
      return resp.json();
    })
    .then(function (json) {
      if (json.code !== undefined && json.code !== 0) {
        return Promise.reject(new Error(json.message || '请求失败'));
      }
      return json;
    });
}

/**
 * API 接口集合
 */
var api = {
  /**
   * 发送通行证
   * @param {object} data {car_no, service, sid, operator_name}
   */
  sendPasscard: function (data) {
    return request('POST', '/passcard/send', data);
  },

  /**
   * 查询通行证详情
   * @param {string} id 通行证 ID
   */
  getPasscard: function (id) {
    return request('GET', '/passcard/' + id);
  },

  /**
   * 获取机器人（门店）列表
   */
  getRobots: function () {
    return request('GET', '/robots');
  },

  /**
   * 获取申请记录
   * @param {number} page 页码
   * @param {number} size 每页条数
   */
  getHistory: function (page, size) {
    page = page || 1;
    size = size || 10;
    return request('GET', '/passcard/history?page=' + page + '&size=' + size);
  },
};
