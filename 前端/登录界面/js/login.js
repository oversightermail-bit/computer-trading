/* ============================================================
 * login.js —— 登录 / 注册页逻辑（F1）
 * 登录成功：保存 JWT 与用户，跳回来源页（或首页）
 * ============================================================ */
(function () {
  'use strict';

  var tabBtns = document.querySelectorAll('.auth-tab');
  var loginForm = document.getElementById('loginForm');
  var regForm = document.getElementById('registerForm');

  function switchTab(tab) {
    tabBtns.forEach(function (b) { b.classList.toggle('active', b.dataset.tab === tab); });
    loginForm.hidden = tab !== 'login';
    regForm.hidden = tab !== 'register';
  }
  tabBtns.forEach(function (b) {
    b.onclick = function () { switchTab(b.dataset.tab); };
  });
  document.getElementById('goRegister').onclick = function (e) { e.preventDefault(); switchTab('register'); };
  document.getElementById('goLogin').onclick = function (e) { e.preventDefault(); switchTab('login'); };

  var params = new URLSearchParams(location.search);
  if (params.get('mode') === 'register') switchTab('register');

  function afterLogin() {
    var back = null;
    try { back = sessionStorage.getItem('hwprice_after_login'); } catch (e) {}
    UI.toast('登录成功，欢迎回来！');
    setTimeout(function () { location.href = back || '../首页/shouye.html'; }, 700);
  }

  /* 登录 */
  loginForm.onsubmit = function (e) {
    e.preventDefault();
    var u = document.getElementById('loginUsername').value.trim();
    var p = document.getElementById('loginPassword').value;
    if (!u) { UI.toast('请输入用户名', 'err'); return; }
    if (!p) { UI.toast('请输入密码', 'err'); return; }
    var btn = document.getElementById('loginBtn');
    btn.disabled = true; btn.textContent = '登录中…';
    api.login({ username: u, password: p }).then(function (res) {
      if (res.code === 0) {
        Auth.login({ token: res.data.token, user: u });
        afterLogin();
      } else {
        btn.disabled = false; btn.textContent = '登 录';
        UI.toast(res.message || '登录失败', 'err');
      }
    });
  };

  /* 注册 */
  regForm.onsubmit = function (e) {
    e.preventDefault();
    var u = document.getElementById('regUsername').value.trim();
    var p = document.getElementById('regPassword').value;
    var p2 = document.getElementById('regPassword2').value;
    if (!/^[a-zA-Z0-9_\u4e00-\u9fa5]{3,20}$/.test(u)) { UI.toast('用户名需 3-20 位，仅限字母/数字/下划线/中文', 'err'); return; }
    if (p.length < 6 || p.length > 32) { UI.toast('密码长度需在 6-32 位之间', 'err'); return; }
    if (p !== p2) { UI.toast('两次输入的密码不一致', 'err'); return; }
    var btn = document.getElementById('regBtn');
    btn.disabled = true; btn.textContent = '注册中…';
    api.register({ username: u, password: p }).then(function (res) {
      if (res.code === 0) {
        UI.toast('注册成功，正在自动登录…');
        api.login({ username: u, password: p }).then(function (res2) {
          if (res2.code === 0) {
            Auth.login({ token: res2.data.token, user: u });
            afterLogin();
          } else {
            switchTab('login');
            document.getElementById('loginUsername').value = u;
            btn.disabled = false; btn.textContent = '注册并登录';
          }
        });
      } else {
        btn.disabled = false; btn.textContent = '注册并登录';
        UI.toast(res.message || '注册失败', 'err');
      }
    });
  };

  /* 演示账号一键填入 */
  document.getElementById('demoFill').onclick = function () {
    document.getElementById('loginUsername').value = 'demo';
    document.getElementById('loginPassword').value = 'demo123';
    switchTab('login');
    loginForm.requestSubmit();
  };
})();
