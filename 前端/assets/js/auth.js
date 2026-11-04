/* ============================================================
 * auth.js —— 登录态管理（localStorage token + 顶栏用户区渲染）
 * 游客：显示 登录 / 注册；登录后：额度徽章 + 账户 + 退出
 * ============================================================ */
(function () {
  'use strict';

  var LS_TOKEN = 'hwprice_token';
  var LS_USER = 'hwprice_user';

  var Auth = {
    token: function () { return localStorage.getItem(LS_TOKEN) || ''; },
    user: function () { return localStorage.getItem(LS_USER) || ''; },
    logged: function () { return !!localStorage.getItem(LS_TOKEN) && !!localStorage.getItem(LS_USER); },
    login: function (resp) {
      localStorage.setItem(LS_TOKEN, resp.token);
      localStorage.setItem(LS_USER, resp.user || '');
    },
    logout: function () {
      localStorage.removeItem(LS_TOKEN);
      localStorage.removeItem(LS_USER);
      if (typeof window.onAuthChange === 'function') window.onAuthChange(false);
    },
    /* 需要登录时调用：未登录记下来源页并跳登录；已登录执行 cb */
    requireLogin: function (cb) {
      if (Auth.logged()) { if (cb) cb(); return true; }
      try { sessionStorage.setItem('hwprice_after_login', location.href); } catch (e) {}
      UI.toast('请先登录后再使用 AI 咨询', 'err', 1500);
      setTimeout(function () { location.href = '../登录界面/denlu.html'; }, 900);
      return false;
    },
    /* 渲染顶栏右侧用户区 */
    renderHeader: function () {
      var el = document.getElementById('headerRight');
      if (!el) return;
      if (Auth.logged()) {
        el.innerHTML =
          '<span class="quota-chip" id="headerQuota" title="AI 问答剩余额度"><span class="dot"></span>额度加载中…</span>' +
          '<a class="btn btn-ghost btn-sm" href="../账户/gerenxingxi.html">账户</a>' +
          '<button class="btn btn-ghost btn-sm" id="logoutBtn">退出</button>';
        var logout = document.getElementById('logoutBtn');
        if (logout) logout.onclick = function () {
          Auth.logout();
          UI.toast('已退出登录');
          setTimeout(function () { location.reload(); }, 600);
        };
        if (typeof window.refreshQuotaChip === 'function') window.refreshQuotaChip();
      } else {
        el.innerHTML =
          '<a class="btn btn-ghost btn-sm" href="../登录界面/denlu.html">登录</a>' +
          '<a class="btn btn-primary btn-sm" href="../登录界面/denlu.html?mode=register">注册</a>';
      }
    },
  };

  window.Auth = Auth;
  document.addEventListener('DOMContentLoaded', function () { Auth.renderHeader(); });
})();
