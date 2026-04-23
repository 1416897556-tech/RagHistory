<template>
  <div class="login-card">
    <div class="header-section">
      <div class="logo-placeholder">📜</div>
      <h2>{{ isRegister ? '注 册 账 号' : '欢 迎 回 来' }}</h2>
      <p class="subtitle">{{ isRegister ? '加入历史 AI 助手，开启探索' : '请输入凭据进入历史实验室' }}</p>

      <button @click="$emit('cancel')" class="close-btn" type="button">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="form-container">
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="input-group">
          <label>用户名</label>
          <div class="input-wrapper">
            <input v-model="form.username" type="text" placeholder="请输入用户名" required />
          </div>
        </div>

        <div v-if="isRegister" class="input-group">
          <label>显示昵称</label>
          <div class="input-wrapper">
            <input v-model="form.nickname" type="text" placeholder="老师该如何称呼您？" required />
          </div>
        </div>

        <div class="input-group">
          <label>密码</label>
          <div class="input-wrapper">
            <input v-model="form.password" type="password" placeholder="请输入密码" required />
          </div>
        </div>

        <button type="submit" :disabled="loading" class="btn-primary">
          <span v-if="!loading">{{ isRegister ? '立即创建账号' : '登 录' }}</span>
          <span v-else class="loading-spinner">处理中...</span>
        </button>
      </form>

      <div class="footer">
        <div class="switch-box">
          <span>{{ isRegister ? '已经有账号了？' : '还没有账号？' }}</span>
          <a @click="isRegister = !isRegister" class="switch-link">
            {{ isRegister ? '去登录' : '立即注册' }}
          </a>
        </div>
        <button @click="$emit('cancel')" class="back-link" type="button">
          暂时返回引导页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';

// 声明接收父组件的事件
const emit = defineEmits(['login-success', 'cancel']);

const isRegister = ref(false);
const loading = ref(false);
const form = reactive({
  username: '',
  nickname: '',
  password: ''
});

const API_BASE = 'http://127.0.0.1:8000/auth';

const handleSubmit = async () => {
  if (isRegister.value && form.password.length < 5) {
    alert('密码长度不能少于 5 位');
    return;
  }
  if (isRegister.value && form.username.length < 8) {
    alert('账号长度不能少于 8 位');
    return;
  }
  loading.value = true;
  const endpoint = isRegister.value ? '/register' : '/login';

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(form)
    });

    const data = await response.json();

    if (response.ok) {
      if (isRegister.value) {
        alert('注册成功！快去登录吧');
        isRegister.value = false;
        form.password = '';
      } else {
        localStorage.setItem('user', JSON.stringify(data));
        emit('login-success', data);
      }
    } else {
      alert(data.detail || '验证失败，请重新检查');
    }
  } catch (error) {
    alert('无法连接到服务器，请确保后端服务已启动');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 核心：卡片化容器，去掉所有外边距 */
.login-card {
  background: white;
  width: 100%;
  max-width: 420px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 页眉部分：深色背景增强方块感 */
.header-section {
  background: #1e293b; /* 深蓝色/灰色背景 */
  padding: 2.5rem 2rem;
  text-align: center;
  position: relative;
  color: white;
}

.logo-placeholder {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

h2 {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #94a3b8;
  font-size: 0.85rem;
  line-height: 1.4;
}

/* 关闭按钮 */
.close-btn {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  color: rgba(255, 255, 255, 0.4);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

/* 表单主体 */
.form-container {
  padding: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.input-group label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.4rem;
}

.input-wrapper input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1.5px solid #f1f5f9;
  border-radius: 0.6rem;
  font-size: 0.95rem;
  transition: all 0.2s;
  background-color: #f8fafc;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #3b82f6;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.05);
}

/* 登录按钮：方正有力 */
.btn-primary {
  width: 100%;
  background-color: #2563eb;
  color: white;
  padding: 0.875rem;
  border: none;
  border-radius: 0.6rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 0.5rem;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.btn-primary:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 6px 15px rgba(37, 99, 235, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

/* 页脚链接 */
.footer {
  text-align: center;
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.switch-box {
  font-size: 0.85rem;
  color: #64748b;
}

.switch-link {
  color: #2563eb;
  font-weight: 700;
  cursor: pointer;
  margin-left: 0.4rem;
}

.back-link {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.75rem;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.back-link:hover {
  color: #64748b;
}
</style>