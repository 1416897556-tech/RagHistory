<template>
  <div class="admin-layout animate-fade-in">
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <div class="admin-badge">ADMIN</div>
        <h2 class="sidebar-title">管理中心</h2>
      </div>

      <nav class="sidebar-nav">
        <button
          @click="activeTab = 'users'"
          :class="['nav-btn', activeTab === 'users' ? 'active' : '']"
        >
          <span class="icon">👥</span> 用户管理
        </button>
        <button
          @click="activeTab = 'sessions'"
          :class="['nav-btn', activeTab === 'sessions' ? 'active' : '']"
        >
          <span class="icon">💬</span> 对话监控
        </button>
      </nav>

      <div class="sidebar-footer">
        <button @click="$emit('exit')" class="exit-link">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回引导页
        </button>
      </div>
    </aside>

    <main class="admin-main">
      <header class="content-header">
        <div class="header-info">
          <h1>{{ activeTab === 'users' ? '平台用户概览' : '全局对话监控' }}</h1>
          <p class="text-gray-400 text-sm">正在以管理员 {{ currentUser?.nickname }} 的身份进行操作</p>
        </div>
        <button @click="refreshData" class="refresh-btn" :disabled="loading">
          {{ loading ? '同步中...' : '刷新数据' }}
        </button>
      </header>

      <div v-if="activeTab === 'users'">
        <div class="search-bar-container">
          <div class="search-input-wrapper">
            <span class="search-icon">🔍</span>
            <input
              v-model="searchQuery"
              @input="handleSearch"
              type="text"
              placeholder="输入用户名或昵称模糊搜索..."
              class="search-input"
            />
            <button v-if="searchQuery" @click="clearSearch" class="clear-btn">✕</button>
          </div>
        </div>

        <div class="data-card">
          <table class="admin-table">
            </table>
        </div>
      </div>
      <div class="content-body">
        <div v-if="activeTab === 'users'" class="data-card">
          <table class="admin-table">
            <thead>
              <tr>
                <th>用户 ID</th>
                <th>登录账号</th>
                <th>显示昵称</th>
                <th>当前角色</th>
                <th class="text-right">管理操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in userList" :key="user.id">
                <td class="font-mono text-blue-600">#{{ user.id }}</td>
                <td class="font-semibold">{{ user.username }}</td>
                <td>{{ user.nickname }}</td>
                <td>
                  <span :class="['role-tag', user.role === 'admin' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700']">
                    {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </td>
                <td class="text-right space-x-3">
                  <button @click="handleEditUser(user)" class="action-btn-edit">编辑</button>
                  <button @click="handleDeleteUser(user.id)" class="action-btn-delete">注销</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="userList.length === 0" class="empty-state">暂无用户信息</div>
        </div>

        <div v-else class="sessions-grid">
          <div v-for="session in allSessions" :key="session.id" class="session-card">
            <div class="session-info">
              <div class="session-header">
                <span class="user-label">@{{ session.user_nickname }}</span>
                <span class="time-label">{{ new Date(session.updated_at).toLocaleString() }}</span>
              </div>
              <h3 class="session-title">{{ session.title || '未命名对话' }}</h3>
              <p class="session-id">SID: {{ session.id }}</p>
            </div>
            <div class="session-actions">
              <button @click="handleEditSession(session)" class="icon-action" title="修改标题">📝</button>
              <button @click="handleDeleteSession(session.id)" class="icon-action delete" title="删除对话">🗑️</button>
            </div>
          </div>
          <div v-if="allSessions.length === 0" class="empty-state">目前全系统没有任何对话记录</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';

const props = defineProps(['currentUser']);
const emit = defineEmits(['exit']);

const activeTab = ref('users');
const loading = ref(false);
const userList = ref([]);
const allSessions = ref([]);

const API_BASE = 'http://127.0.0.1:8000/admin';
const searchQuery = ref('');
let searchTimer = null;

// 搜索处理（防抖）
const handleSearch = () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    fetchUsers();
  }, 300); // 停止输入 300ms 后再发送请求
};

// 清除搜索
const clearSearch = () => {
  searchQuery.value = '';
  fetchUsers();
};

// 获取全量用户
const fetchUsers = async () => {
  loading.value = true;
  try {
    const url = new URL(`${API_BASE}/users`);
    url.searchParams.append('current_user_role', props.currentUser.role);
    if (searchQuery.value) {
      url.searchParams.append('q', searchQuery.value);
    }

    const res = await fetch(url);
    if (res.ok) userList.value = await res.json();
  } catch (e) {
    console.error("搜索用户失败", e);
  }
  loading.value = false;
};

// 获取全量对话
const fetchSessions = async () => {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/sessions?current_user_role=${props.currentUser.role}`);
    if (res.ok) allSessions.value = await res.json();
  } catch (e) { console.error("加载对话失败", e); }
  loading.value = false;
};

const refreshData = () => {
  activeTab.value === 'users' ? fetchUsers() : fetchSessions();
};

onMounted(refreshData);
watch(activeTab, refreshData);

// --- 用户操作 ---
const handleEditUser = async (user) => {
  const newNickname = prompt("请输入新的昵称:", user.nickname);
  const newRole = prompt("请输入角色 (user/admin):", user.role);
  if (newNickname && newRole) {
    const res = await fetch(`${API_BASE}/users/${user.id}?current_user_role=${props.currentUser.role}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname: newNickname, role: newRole })
    });
    if (res.ok) fetchUsers();
  }
};

const handleDeleteUser = async (id) => {
  if (confirm("🚨 警告：注销用户将清空其所有数据且不可恢复！确定吗？")) {
    const res = await fetch(`${API_BASE}/users/${id}?current_user_role=${props.currentUser.role}`, {
      method: 'DELETE'
    });
    if (res.ok) fetchUsers();
  }
};

// --- 对话操作 ---
const handleEditSession = async (session) => {
  const newTitle = prompt("修改对话标题:", session.title);
  if (newTitle) {
    const res = await fetch(`${API_BASE}/sessions/${session.id}?current_user_role=${props.currentUser.role}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle })
    });
    if (res.ok) fetchSessions();
  }
};

const handleDeleteSession = async (id) => {
  if (confirm("确定要删除这段对话内容吗？")) {
    const res = await fetch(`${API_BASE}/sessions/${id}?current_user_role=${props.currentUser.role}`, {
      method: 'DELETE'
    });
    if (res.ok) fetchSessions();
  }
};
</script>

<style scoped>
.admin-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  background-color: #f1f5f9;
  font-family: "Inter", sans-serif;
}

/* 侧边栏：采用 Guide 页面的深蓝色调 */
.admin-sidebar {
  width: 280px;
  background-color: #0f172a;
  color: white;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 3rem 2rem;
}

.admin-badge {
  background: #f59e0b;
  color: #000;
  font-size: 0.6rem;
  font-weight: 900;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 0.5rem;
}

.sidebar-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.025em;
}

.sidebar-nav {
  flex: 1;
  padding: 0 1rem;
}

.nav-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  margin-bottom: 0.5rem;
  border-radius: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-btn:hover {
  background: rgba(255,255,255,0.05);
  color: white;
}

.nav-btn.active {
  background: #3b82f6;
  color: white;
  box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
}

.sidebar-footer {
  padding: 2rem;
  border-top: 1px solid rgba(255,255,255,0.05);
}

.exit-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.875rem;
  cursor: pointer;
}

.exit-link:hover { color: #f87171; }

/* 内容区主样式 */
.admin-main {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.content-header {
  background: white;
  padding: 1.5rem 2.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.content-header h1 {
  font-size: 1.25rem;
  font-weight: 800;
  color: #1e293b;
}

.refresh-btn {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 1.25rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.refresh-btn:hover { background: #f1f5f9; }

.content-body {
  padding: 2.5rem;
}

/* 数据卡片 & 表格 */
.data-card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.admin-table th {
  padding: 1rem 1.5rem;
  background: #f8fafc;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #64748b;
  letter-spacing: 0.05em;
}

.admin-table td {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #f1f5f9;
  font-size: 0.9rem;
}

.role-tag {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.action-btn-edit { color: #2563eb; font-weight: 600; }
.action-btn-delete { color: #ef4444; font-weight: 600; }

/* 会话网格布局 */
.sessions-grid {
  display: grid;
  grid-template-cols: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.session-card {
  background: white;
  padding: 1.5rem;
  border-radius: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.session-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 10px 20px -5px rgba(0,0,0,0.05);
}

.session-header {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.user-label {
  color: #3b82f6;
  font-weight: 800;
  font-size: 0.75rem;
}

.time-label {
  color: #94a3b8;
  font-size: 0.75rem;
}

.session-title {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.session-id {
  font-size: 0.7rem;
  color: #cbd5e1;
  font-family: monospace;
}

.session-actions {
  display: flex;
  gap: 0.5rem;
}

.icon-action {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 0.5rem;
  cursor: pointer;
}

.icon-action:hover { background: #eff6ff; }
.icon-action.delete:hover { background: #fef2f2; }

.empty-state {
  text-align: center;
  padding: 5rem;
  color: #94a3b8;
  font-style: italic;
}

.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>