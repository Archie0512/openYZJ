/**
 * 车牌正则工具 - plate.js
 * 与后端 Python 版保持一致
 */

// 车牌正则（兼容新能源 7 位 + 传统 6 位 + 无牌车）
var PLATE_REGEX = /(无[A-NP-Za-np-z0-9]{7}|[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Za-z][A-Za-z0-9]{5,6})/;

// 省份列表
var PROVINCES = [
  '京', '津', '沪', '渝', '冀', '豫', '云', '辽', '黑', '湘',
  '皖', '鲁', '新', '苏', '浙', '赣', '鄂', '桂', '甘', '晋',
  '蒙', '陕', '吉', '闽', '贵', '粤', '川', '青', '藏', '琼', '宁'
];

/**
 * 验证车牌号是否合法
 * @param {string} plate 车牌号
 * @returns {boolean}
 */
function isValidPlate(plate) {
  return PLATE_REGEX.test(plate);
}

/**
 * 从文本中提取车牌号
 * @param {string} text 待匹配文本
 * @returns {string|null} 匹配到的车牌号或 null
 */
function extractPlate(text) {
  var match = text.match(PLATE_REGEX);
  return match ? match[1] : null;
}
