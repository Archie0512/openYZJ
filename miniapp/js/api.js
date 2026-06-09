/**
 * API 调用封装 - api.js
 * 统一 Bearer Token 鉴权
 */

var API_BASE = '/api/v1';

// 本地开发 token（生产环境由后端分配）
var API_TOKEN = 'dev_token_placeholder';

/**
 * 获取鉴权 token
 * @returns {string}
 */
function getAuthToken() {
  // 优先从 localStorage 读取（管理端配置）
  return localStorage.getItem('api_token') || API_TOKEN;
}

/**
 * 通用请求函数
 * @param {string} method HTTP 方法
 * @param {string} path API 路径
 * @param {object} [data] 请求体（POST/PUT）
 * @returns {Promise<object>} 响应 JSON
 */
function request(method, path, data) {
  var token = getAuthToken();
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
        showToast('认证失败，请联系管理员');
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
 * 上传文件请求（multipart/form-data）
 * @param {string} path API 路径
 * @param {FormData} formData 表单数据
 * @returns {Promise<object>} 响应 JSON
 */
function uploadRequest(path, formData) {
  var token = getAuthToken();
  var url = API_BASE + path;
  var options = {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
    },
    body: formData,
  };

  return fetch(url, options)
    .then(function (resp) {
      if (resp.status === 401) {
        showToast('认证失败，请联系管理员');
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
   * 获取事由列表
   */
  getServiceReasons: function () {
    return request('GET', '/service-reasons');
  },

  /**
   * 获取用户门店信息
   * @param {string} openid 用户 openid
   */
  getUserStore: function (openid) {
    return request('GET', '/user/store?openid=' + encodeURIComponent(openid));
  },

  /**
   * OCR 识别车牌
   * @param {File} file 图片文件
   */
  ocrPlate: function (file) {
    var formData = new FormData();
    formData.append('file', file);
    return uploadRequest('/ocr/plate', formData);
  },

  /**
   * 获取申请记录
   * @param {number} page 页码
   * @param {number} size 每页条数
   * @param {string} openid 用户 openid
   */
  getHistory: function (page, size, openid) {
    page = page || 1;
    size = size || 10;
    var url = '/passcard/history?page=' + page + '&size=' + size;
    if (openid) {
      url += '&openid=' + encodeURIComponent(openid);
    }
    return request('GET', url);
  },
};
