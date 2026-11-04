/* ============================================================
 * quota.js —— 订阅额度展示 + 升级弹窗（42901 / 40301 引导升级）
 * ============================================================ */
(function () {
  'use strict';

  var PLAN_TAG = { 1: 'tag plain', 2: 'tag teal', 3: 'tag blue', 4: 'tag gold' };

  /* 顶栏额度徽章：当前：免费版 · 今日剩余 3 次 */
  async function refreshQuotaChip() {
    var el = document.getElementById('headerQuota');
    if (!el || !Auth.logged()) return;
    try {
      var res = await api.quota();
      if (res.code === 0) {
        var q = res.data;
        el.innerHTML = '<span class="dot"></span>当前：' + UI.esc(q.plan) +
          ' · 今日剩余 <b>' + q.dayRemain + '</b> 次';
        el.title = '本月剩余 ' + q.monthRemain + ' 次';
        if (q.dayRemain <= 0) el.classList.add('empty');
        else el.classList.remove('empty');
      } else if (res.code === 40101) {
        el.innerHTML = '<span class="dot"></span>未登录';
      } else {
        el.innerHTML = '<span class="dot"></span>' + UI.esc(res.message || '额度获取失败');
      }
    } catch (e) {
      el.innerHTML = '<span class="dot"></span>额度获取失败';
    }
  }

  /* 订阅套餐卡片（升级弹窗与账户页共用） */
  function planCardHtml(plan, opts) {
    opts = opts || {};
    var cur = plan.id === opts.currentPlanId;
    var cls = PLAN_TAG[plan.id] || 'tag plain';
    var btns = '';
    if (cur) {
      btns = '<button class="btn btn-ghost btn-sm" disabled>当前方案</button>';
    } else if (plan.id !== 1) {
      btns = '<button class="btn btn-primary btn-sm" data-plan="' + plan.id + '">¥' +
        plan.priceMonth + '/月 立即升级</button>';
    } else if (plan.id === 1 && opts.currentPlanId) {
      btns = '<button class="btn btn-ghost btn-sm" data-plan="1">切换回免费版</button>';
    } else {
      btns = '<button class="btn btn-ghost btn-sm" data-plan="1">免费使用</button>';
    }
    return '' +
      '<div class="plan-card' + (cur ? ' current' : '') + '">' +
      '  <div class="plan-head">' +
      '    <span class="' + cls + '">' + UI.esc(plan.planName) + '</span>' +
      (plan.id === 1 ? '' : '<span class="plan-price">¥' + plan.priceMonth + '<i>/月</i></span>') +
      '  </div>' +
      '  <div class="plan-quota">AI 额度：<b>' + plan.quotaDay + ' 次/日</b> · <b>' + plan.quotaMonth + ' 次/月</b></div>' +
      '  <div class="plan-desc">' + UI.esc(plan.description) + '</div>' +
      '  <div class="plan-feats">' +
      (plan.multimodal ? '<span>✓ 支持图片问答</span>' : '<span>✕ 仅文本问答</span>') +
      (plan.id >= 3 ? '<span>✓ 多硬件对比</span>' : '') +
      (plan.id >= 4 ? '<span>✓ 配置单导出</span>' : '') +
      '  </div>' +
      '  <div class="plan-foot">' + btns + '</div>' +
      '</div>';
  }

  /* 升级弹窗：额度用尽(42901) / 套餐能力不足(40301) 时打开 */
  function openUpgradeModal(opts) {
    if (!Auth.logged()) { Auth.requireLogin(); return; }
    api.plans().then(function (res) {
      if (res.code !== 0) { UI.toast(res.message || '套餐获取失败', 'err'); return; }
      api.quota().then(function (qr) {
        var currentId = qr.code === 0 ? qr.data.planId : null;
        var wrapper = document.createElement('div');
        wrapper.className = 'plan-grid-wrap';
        var inner = document.createElement('div');
        inner.className = 'plan-grid';
        inner.innerHTML = res.data.map(function (p) {
          return planCardHtml(p, { currentPlanId: currentId });
        }).join('');
        wrapper.appendChild(inner);
        var modal = UI.openModal({
          title: '⬆ 升级订阅',
          sub: (opts && opts.reason) || '当前套餐 AI 额度已用完，升级后可继续咨询。',
          body: wrapper,
          buttons: [{ text: '稍后再说', cls: 'btn-ghost' }],
        });
        inner.querySelectorAll('[data-plan]').forEach(function (btn) {
          btn.onclick = function () {
            var planId = +btn.getAttribute('data-plan');
            btn.disabled = true;
            btn.textContent = '开通中…';
            api.subscribe(planId).then(function (r) {
              if (r.code === 0) {
                modal.close();
                UI.toast('已升级为「' + r.data.planName + '」，继续问 AI 吧');
                refreshQuotaChip();
                if (typeof window.onSubscribeChange === 'function') window.onSubscribeChange();
              } else {
                btn.disabled = false;
                btn.textContent = '立即升级';
                UI.toast(r.message || '升级失败', 'err');
              }
            });
          };
        });
      });
    });
  }

  /* 40101 / 额度提示统一处理 */
  function handleAuthError(res) {
    if (res.code === 42901) {
      openUpgradeModal({ reason: res.message });
      return true;
    }
    if (res.code === 40301) {
      openUpgradeModal({ reason: res.message });
      return true;
    }
    if (res.code === 40101) {
      Auth.requireLogin();
      return true;
    }
    return false;
  }

  window.refreshQuotaChip = refreshQuotaChip;
  window.planCardHtml = planCardHtml;
  window.PlanGridTag = PLAN_TAG;
  window.UpgradeModal = { open: openUpgradeModal };
  window.QuotaKit = { refreshQuotaChip: refreshQuotaChip, handleAuthError: handleAuthError, planCardHtml: planCardHtml };
})();
