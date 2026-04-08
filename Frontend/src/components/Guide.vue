<template>
  <div class="guide-fullscreen-wrapper">
    <div class="bg-overlay"></div>

    <nav class="absolute top-0 right-0 z-[100] p-8">
      <div v-if="currentUser" class="flex items-center gap-4 bg-black/40 backdrop-blur-md px-5 py-2.5 rounded-full border border-white/20 shadow-2xl">
        <div :class="['w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-inner',
                      currentUser.role === 'admin' ? 'bg-amber-500' : 'bg-blue-600']">
          {{ currentUser.nickname[0] }}
        </div>
        <div class="flex flex-col">
          <span class="text-white text-sm font-semibold">你好，{{ currentUser.nickname }}</span>
          <span class="text-[10px] text-gray-400 leading-none">AI 助手已就绪</span>
        </div>
        <div class="w-px h-4 bg-white/10 mx-1"></div>
        <button @click.stop="$emit('logout')" class="text-xs text-gray-300 hover:text-red-400 transition-colors px-2">退出</button>
      </div>

      <button v-else @click.stop="$emit('open-login')"
              class="group flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-7 py-2.5 rounded-full text-sm font-bold shadow-xl transition-all active:scale-95 relative z-[110]">
        <span>点击登录</span>
        <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l4-4m0 0l-4-4m4 4H7" />
        </svg>
      </button>
    </nav>

    <div class="content-container animate-slide-up">
      <header class="guide-header">
        <span class="logo-icon">📜</span>
        <span class="logo-text">初中历史智能实验室</span>
      </header>

      <section class="main-hero">
        <h1 class="hero-title">
          融合 <span class="highlight">RAG</span> 技术，<br/>
          重塑历史教学新范式
        </h1>
        <p class="hero-subtitle">
          基于检索增强生成（Retrieval-Augmented Generation）技术，深度整合初中历史权威教材与海量史料数据。
          我们不只是在对话，而是在精准、可靠的知识库支撑下，为您提供逻辑严密、史实准确的教学辅助服务。
        </p>

        <div class="features-horizontal">
          <div class="f-card">
            <div class="f-num">01</div>
            <div class="f-content">
              <h3>史料库精准对齐</h3>
              <p>拒绝AI幻觉，所有回答均可溯源至大纲考点。</p>
            </div>
          </div>
          <div class="f-card">
            <div class="f-num">02</div>
            <div class="f-content">
              <h3>深度教学辅助</h3>
              <p>一键生成课纲、故事脚本或多维史实对比。</p>
            </div>
          </div>
          <div class="f-card">
            <div class="f-num">03</div>
            <div class="f-content">
              <h3>智能化存档</h3>
              <p>基于 MySQL 的持久化存储，珍贵灵感永不丢失。</p>
            </div>
          </div>
        </div>
      </section>

      <footer class="guide-footer">
        <div class="flex flex-wrap items-center gap-4">
          <button @click="$emit('enter')" class="explore-btn">
            <span>立即开启探索</span>
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>

          <button v-if="currentUser?.role === 'admin'"
                  @click="$emit('go-admin')"
                  class="admin-btn">
            <span>🛠️ 管理对话</span>
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </button>
        </div>

        <div class="footer-note">当前版本：v1.2.0 | DeepSeek 核心驱动</div>
      </footer>
    </div>
  </div>
</template>

<script setup>
// 确保定义了这些 Emits，否则父组件 App.vue 接收不到信号
defineProps(['nickname', 'currentUser']);
defineEmits(['enter', 'open-login', 'logout', 'go-admin']);
</script>

<style scoped>
.guide-fullscreen-wrapper {
/* 🚩 修改：去掉 position: absolute 或 fixed */
  position: relative;
  width: 100%;
  /* 🚩 确保它能撑开高度 */
  min-height: 100vh;

  background-image: url('../assets/guide-bg.png');
  background-size: cover;
  background-position: center;
  background-attachment: fixed; /* 背景不动，文字动，这才是高级感 */

  /* 🚩 确保没有东西拦截滚动 */
  overflow: visible;
}

.bg-overlay {
  position: fixed; /* 固定在屏幕，不随内容走 */
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    75deg,
    rgba(0,0,0,0.95) 0%,
    rgba(0,0,0,0.7) 50%,
    rgba(0,0,0,0.4) 100%
  );
  pointer-events: none; /* 👈 极其重要：允许点击穿透 */
}

.content-container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 1200px;
  min-height: 100vh;
  margin: 0 auto;
  padding: 8rem 2rem 4rem; /* 增加顶部 padding 避免挡住 nav */
  display: flex;
  flex-direction: column;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 4rem;
}
.logo-icon { font-size: 2.5rem; }
.logo-text { font-size: 1.25rem; font-weight: 600; letter-spacing: 2px; color: #cbd5e1; }

.main-hero { max-width: 850px; flex: 1; }
.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 2rem;
}
.highlight { color: #3b82f6; text-shadow: 0 0 20px rgba(59, 130, 246, 0.4); }
.hero-subtitle { font-size: 1.15rem; line-height: 1.8; color: #94a3b8; margin-bottom: 4rem; }

.features-horizontal {
  display: grid;
  grid-template-cols: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 6rem;
}
.f-card {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-left: 2px solid #3b82f6;
  backdrop-filter: blur(8px);
}
.f-num { font-size: 1.2rem; font-weight: 800; color: #3b82f6; }
.f-content h3 { font-size: 1rem; margin-bottom: 0.5rem; color: #f1f5f9; }
.f-content p { font-size: 0.85rem; color: #64748b; line-height: 1.5; }

.guide-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 4rem;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.explore-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  height: 3.5rem; /* 固定高度 */
  padding: 0 2.5rem;
  background: #3b82f6; /* 蓝色 */
  border: none;
  border-radius: 9999px;
  color: white;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}
.admin-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  height: 3.5rem; /* 与探索按钮高度一致 */
  padding: 0 2.5rem;
  background: #f59e0b; /* amber-500 金色 */
  border: none;
  border-radius: 9999px;
  color: white;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
}

.admin-btn:hover {
  background: #d97706; /* amber-600 */
  transform: translateY(-2px); /* 统一向上微弹动画 */
  box-shadow: 0 6px 25px rgba(245, 158, 11, 0.4);
}

.admin-btn:active {
  transform: translateY(0);
}
.explore-btn:hover {
  background: #2563eb;
  transform: translateX(8px);
}
.footer-note { font-size: 0.8rem; color: #475569; }

.animate-slide-up { animation: slideUp 0.8s ease-out; }
@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式调整：手机端上下堆叠 */
@media (max-width: 640px) {
  .flex-wrap {
    flex-direction: column;
    align-items: stretch;
  }
  .explore-btn, .admin-btn {
    justify-content: center;
    width: 100%;
  }
}
</style>