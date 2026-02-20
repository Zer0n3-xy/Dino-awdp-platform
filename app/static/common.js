const TOKEN_KEY = 'awdp_token';

function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
function setToken(token) { localStorage.setItem(TOKEN_KEY, token || ''); }
function logout() { setToken(''); location.href = '/static/login.html'; }

async function api(path, options = {}, auth = false) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (auth && getToken()) headers.Authorization = `Bearer ${getToken()}`;
  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

function v(id) { return document.getElementById(id).value.trim(); }
function show(id, data) { document.getElementById(id).textContent = JSON.stringify(data, null, 2); }

function renderNav() {
  const node = document.getElementById('nav');
  if (!node) return;
  node.innerHTML = `
    <a href="/static/login.html">登录注册</a>
    <a href="/static/competitions.html">比赛管理</a>
    <a href="/static/teams.html">队伍管理</a>
    <a href="/static/challenges.html">题目与容器</a>
    <a href="/static/submissions.html">Flag/Patch 提交</a>
    <a href="/static/leaderboard.html">排行榜</a>
    <a href="#" onclick="logout()">退出登录</a>
  `;
}
