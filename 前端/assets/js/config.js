/* ============================================================
 * 全局配置（API 切换开关，2026-11 起支持运行时切换）
 *  - 默认 API_MODE = 'real'：全部用户（含游客）走 Java 后端真实数据，
 *    只聚合 source='real' 的真实采集价，采不到显示"暂无数据"。
 *  - 仅演示账号 demo 登录成功后自动切换到 'mock'（本地演示数据），
 *    退出登录自动切回 'real'；注册用户始终使用真实模式。
 *  - mode 持久化在 localStorage（hwprice_api_mode），跨页面保持。
 * ============================================================ */
(function () {
  'use strict';

  var LS_MODE = 'hwprice_api_mode';
  var stored = null;
  try { stored = localStorage.getItem(LS_MODE); } catch (e) {}

  var mode = (stored === 'mock') ? 'mock' : 'real'; // 默认真实模式

  window.AppConfig = {
    API_MODE: mode,
    // 真实后端地址：本地后端默认 8080；file:// 打开页面时直接跨域访问（后端已全放行 CORS）
    API_BASE: 'http://127.0.0.1:8080/api',
    SITE_NAME: '硬核比价',

    /** 切换 API 模式（登录 demo 自动 mock，退出自动 real） */
    setMode: function (m) {
      m = (m === 'mock') ? 'mock' : 'real';
      this.API_MODE = m;
      try { localStorage.setItem(LS_MODE, m); } catch (e) {}
      if (window.MockApi && window.RealApi) {
        window.api = (m === 'mock') ? window.MockApi : window.RealApi;
      }
      if (typeof window.onApiModeChange === 'function') window.onApiModeChange(m);
      return m;
    },
  };
})();
