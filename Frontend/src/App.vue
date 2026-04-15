<template>
  <div class="min-h-screen w-full bg-white font-sans antialiased relative">

    <template v-if="showGuide">
      <Guide
        :currentUser="currentUser"
        @enter="enterApp"
        @open-login="showLoginModal = true"
        @logout="logout"
        @go-admin="goToAdmin"
        @go-profile="handleGoProfile"
      />
    </template>

    <template v-else-if="showAdminPage && currentUser?.role === 'admin'">
          <AdminManager
            :currentUser="currentUser"
            @exit="handleExitAdmin"
          />
        </template>

    <template v-else-if="showProfilePage && currentUser">
      <ProfileManager
        :currentUser="currentUser"
        @exit="handleExitProfile"
        @logout="logout"
        @update-user="handleUpdateUser"
      />
    </template>

    <template v-else-if="currentUser">
      <div class="flex h-screen w-full overflow-hidden">
        <aside class="w-72 bg-[#202123] p-4 flex flex-col shrink-0 text-gray-200 z-20 shadow-xl">
          <div class="flex items-center gap-3 mb-8 border-b border-white/10 pb-4">
            <span class="text-3xl">📜</span>
            <h1 class="text-xl font-bold tracking-tight text-white">初中历史助手</h1>
          </div>

          <button @click="startNewChat"
                  class="border border-white/20 rounded-lg p-3 hover:bg-white/10 transition flex items-center gap-3 w-full mb-6 text-sm active:scale-95">
            <span class="text-lg">+</span>
            <span>开启新对话</span>
          </button>

          <div class="flex-1 overflow-y-auto space-y-2 pr-2 scrollbar-thin">
            <div class="text-xs text-gray-500 font-bold px-3 py-1 uppercase tracking-wider mb-2">历史记录</div>
            <div v-if="sessionList.length === 0" class="px-3 py-4 text-xs text-gray-600 text-center italic">暂无历史对话</div>
            <div v-for="session in sessionList" :key="session.id"
                 @click="loadSession(session.id)"
                 class="group relative px-3 py-3 text-sm rounded-md cursor-pointer transition-all duration-200 border-l-4"
                 :class="currentSessionId === session.id ? 'bg-[#343541] text-white border-blue-500' : 'hover:bg-[#2A2B32] text-gray-400 border-transparent'">
              <div class="flex flex-col pr-14">
                <input v-if="editingSessionId === session.id"
                       v-model="editingTitle"
                       @click.stop
                       @keyup.enter="saveTitle(session)"
                       @blur="saveTitle(session)"
                       v-focus
                       class="bg-gray-700 text-white text-xs px-2 py-0.5 rounded outline-none border border-blue-500 w-full" />

                <template v-else>
                  <div class="font-medium truncate">{{ session.title || '历史对话' }}</div>
                  <div class="text-[10px] opacity-30 mt-1">{{ formatDate(session.updated_at) }}</div>
                </template>
              </div>

              <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">

                <button @click.stop="startEditTitle(session)"
                        class="p-1.5 rounded-md hover:bg-gray-700 text-gray-500 hover:text-blue-400 transition-colors"
                        title="重命名">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>

                <button @click.stop="handleDelete(session.id)"
                        class="p-1.5 rounded-md hover:bg-gray-700 text-gray-500 hover:text-red-500 transition-colors"
                        title="删除">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <div class="border-t border-white/10 pt-4 mt-auto">
            <div class="flex items-center gap-2 px-2 mb-4">
              <div :class="['w-7 h-7 rounded flex items-center justify-center text-[10px] font-bold shadow-sm',
                            currentUser.role === 'admin' ? 'bg-amber-500' : 'bg-blue-500']">
                {{ currentUser.nickname[0] }}
              </div>
              <div class="flex flex-col">
                <span class="text-xs text-gray-200 font-medium truncate w-24">{{ currentUser.nickname }}</span>
                <span v-if="currentUser.role === 'admin'" class="text-[8px] bg-amber-500/20 text-amber-400 px-1 rounded w-fit border border-amber-500/30">ADMIN</span>
              </div>
            </div>

            <div class="flex items-center gap-2 px-2">
              <button @click="handleGoProfile"
                      class="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-md bg-white/5 hover:bg-white/10 text-gray-300 text-[10px] transition-all border border-white/5">
                <span>⚙️</span> 管理
              </button>
              <button @click="logout(false)"
                      class="flex-1 py-1.5 rounded-md text-[10px] text-gray-500 hover:text-red-400 transition-colors border border-transparent hover:border-red-400/20">
                <span>🚪</span> 退出
              </button>
            </div>
          </div>
        </aside>

        <main class="flex-1 flex flex-col h-full bg-gray-50 relative overflow-hidden">
          <header class="h-16 flex items-center justify-between px-6 bg-white border-b border-gray-100 shrink-0 shadow-sm z-10">
            <div class="text-sm font-medium text-gray-600">{{ currentSessionId ? `会话ID: ${currentSessionId.toString().slice(0,8)}...` : '等待开始' }}</div>
            <div class="flex items-center gap-2.5">
              <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
              <span class="text-sm text-emerald-700 font-medium tracking-tight">AI 历史老师已就绪</span>
            </div>
          </header>

          <div ref="scrollContainer" class="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 bg-gray-50 scroll-smooth">
            <div class="h-4"></div>
            <div v-for="(msg, index) in messages" :key="index" :class="['flex w-full animate-fade-in', msg.role === 'user' ? 'justify-end' : 'justify-start']">
              <div :class="['flex gap-3.5 max-w-[85%] md:max-w-[75%]', msg.role === 'user' ? 'flex-row-reverse' : 'flex-row']">
                <div :class="['w-9 h-9 rounded-full flex items-center justify-center shrink-0 shadow-md mt-0.5', msg.role === 'user' ? 'bg-blue-600' : 'bg-emerald-600']">
                  <span class="text-white font-bold text-xs">{{ msg.role === 'user' ? '你' : '师' }}</span>
                </div>
                <div :class="['px-4 py-3 rounded-2xl shadow-sm leading-relaxed border', msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none border-blue-500' : 'bg-white text-gray-800 rounded-bl-none border-gray-100']">
                  <div class="whitespace-pre-wrap text-[15px] leading-6">{{ msg.content }}</div>
                </div>
              </div>
            </div>
            <div v-if="isStreaming && messages[messages.length-1]?.role === 'user'" class="flex justify-start pl-12">
              <div class="p-3 rounded-xl bg-white shadow-sm border border-gray-100 flex gap-1.5">
                <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
                <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
              </div>
            </div>
            <div class="h-32"></div>
          </div>

          <footer class="absolute bottom-0 left-0 right-0 p-6 md:p-10 bg-gradient-to-t from-gray-50 via-gray-50 to-transparent">
            <div class="max-w-4xl mx-auto relative">
              <textarea v-model="userInput" @keyup.enter.exact.prevent="sendMessage" rows="1" placeholder="输入问题..." class="w-full bg-white border border-gray-200 rounded-2xl p-4 pr-16 focus:ring-4 focus:ring-blue-100 shadow-xl transition-all resize-none"></textarea>
              <button @click="sendMessage" :disabled="loading || !userInput.trim()" class="absolute right-3 bottom-3 p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-lg active:scale-95">
                <svg class="h-5 w-5 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </footer>
        </main>
      </div>
    </template>

    <div v-if="showLoginModal" class="fixed inset-0 z-[1000] flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
      <div class="relative w-full max-w-md animate-fade-in overflow-hidden rounded-2xl shadow-2xl">
    <Login @login-success="onLoginSuccess" @cancel="showLoginModal = false" />
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import Login from './components/Login.vue';
import Guide from './components/Guide.vue';
import AdminManager from './components/AdminManager.vue';
import ProfileManager from './components/ProfileManager.vue';

// --- 状态变量 ---
const currentUser = ref(null);
const showGuide = ref(false);
const userInput = ref('');
const loading = ref(false);
const isStreaming = ref(false);
const scrollContainer = ref(null);
const currentSessionId = ref('');
const sessionList = ref([]);
const messages = ref([]);
const showLoginModal = ref(false);
const API_BASE = 'http://127.0.0.1:8000';
const showAdminPage = ref(false); // 控制管理页面的显示
const showProfilePage = ref(false); // 新增状态
const editingSessionId = ref(null); // 当前正在编辑标题的会话ID
const editingTitle = ref('');       // 临时存放编辑中的标题内容

// --- 初始化与生命周期 ---
onMounted(() => {
  const savedUser = localStorage.getItem('user');
  if (savedUser) {
    currentUser.value = JSON.parse(savedUser);
    fetchSessions();
    startNewChat();
    // 已登录用户进入后依然先看引导页封面
    showGuide.value = true;
  } else {
    // 未登录用户显然必须看引导页
    showGuide.value = true;
  }
});

const onLoginSuccess = (userData) => {
  currentUser.value = userData;
  showLoginModal.value = false; // 登录成功关闭弹窗
  fetchSessions();
  startNewChat();
  // 登录成功后依然留在 Guide 页面，等待用户点击“开始探索”
};

// 自动聚焦指令
const vFocus = {
  mounted: (el) => el.focus()
};

const startEditTitle = (session) => {
  editingSessionId.value = session.id;
  editingTitle.value = session.title || '历史对话';
};

const saveTitle = async (session) => {
  // 如果当前没在编辑这个 session，直接返回
  if (editingSessionId.value !== session.id) return;

  const trimmedTitle = editingTitle.value.trim();

  // 如果内容没变，直接取消编辑模式即可，不发请求
  if (trimmedTitle === session.title) {
    editingSessionId.value = null;
    return;
  }

  try {
    const response = await fetch(`http://127.0.0.1:8000/sessions/${session.id}/title`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: trimmedTitle })
    });

    if (response.ok) {
      session.title = trimmedTitle; // 成功后更新本地显示
    } else {
      alert("更新标题失败");
    }
  } catch (error) {
    console.error("请求出错:", error);
  } finally {
    editingSessionId.value = null; // 无论如何都关闭编辑框
  }
};

// 退出登录
const handleLogout = () => {
  localStorage.removeItem('user');
  currentUser.value = null;
  showAdminPage.value = false;
  showGuide.value = true;
};

const handleEnterApp = () => {
  if (!currentUser.value) {
    showLoginModal.value = true; // 没登录点击“开始”弹窗
  } else {
    showGuide.value = false; // 已登录进入主界面
  }
};

// 进入管理模式
const handleGoAdmin = () => {
  if (currentUser.value?.role === 'admin') {
    showGuide.value = false;
    showAdminPage.value = true;
  }
};

const enterApp = () => {
  if (!currentUser.value) {
    showLoginModal.value = true; // 未登录点击探索，唤起登录
  } else {
    showGuide.value = false; // 已登录点击探索，进入主界面
  }
};

const logout = (force = false) => {
// 如果不是强制退出（比如用户点侧边栏按钮），则询问
  // 如果是强制退出（比如修改密码成功），则直接跳过 confirm
  if (!force && currentUser.value) {
    if (!confirm("您确定要退出登录吗？")) {
      return;
    }
  }
  // 执行真正的清理逻辑
  localStorage.removeItem('user');
  currentUser.value = null;
  // 核心：立即切回引导页
  showGuide.value = true;
  showProfilePage.value = false;
  showAdminPage.value = false;
  // 重置聊天相关的临时状态（可选）
  messages.value = [];
  currentSessionId.value = null;
};

// 从管理模式返回
const handleExitAdmin = () => {
  showAdminPage.value = false;
  showGuide.value = true; // 返回引导页封面
};

// --- 会话逻辑 ---
const fetchSessions = async () => {
  if (!currentUser.value) return;
  try {
    const res = await fetch(`${API_BASE}/sessions/${currentUser.value.id}`);
    if (res.ok) sessionList.value = await res.json();
  } catch (e) {
    console.error("加载列表失败", e);
  }
};

const startNewChat = () => {
  currentSessionId.value = '';
  messages.value = [{
    role: 'assistant',
    content: `你好，${currentUser.value ? currentUser.value.nickname : '同学'}！我是你的历史助教。想了解秦皇汉武，还是唐宗宋祖？`
  }];
};

const loadSession = async (sid) => {
  if (loading.value) return;
  currentSessionId.value = sid;
  try {
    const res = await fetch(`${API_BASE}/history/${sid}`);
    if (res.ok) {
      messages.value = await res.json();
      scrollToBottom();
    }
  } catch (e) {
    console.error("历史加载失败", e);
  }
};

const handleDelete = async (sid) => {
  if (!confirm("确定要删除这段历史吗？此操作不可撤销。")) return;
  try {
    const res = await fetch(`${API_BASE}/sessions/${sid}`, { method: 'DELETE' });
    if (res.ok) {
      if (currentSessionId.value === sid) startNewChat();
      await fetchSessions();
    }
  } catch (error) {
    alert("网络请求失败");
  }
};

const goToAdmin = () => {
  if (currentUser.value?.role === 'admin') {
    showGuide.value = false;      // 关闭引导页
    showAdminPage.value = true;   // 开启管理页
  } else {
    alert("权限不足");
  }
};

// 处理点击侧边栏“管理”的事件
const handleGoProfile = () => {
  console.log("接收到进入个人中心的信号");
  showProfilePage.value = true;
  showGuide.value = false;      // 🚩 必须关闭引导页，否则引导页层级高会挡住后面
  showAdminPage.value = false;
};

// 处理从个人中心返回
const handleExitProfile = () => {
  showProfilePage.value = false;
};

// --- 消息处理 ---
const sendMessage = async () => {
  const content = userInput.value.trim();
  if (!content || loading.value) return;

  if (!currentSessionId.value) {
    currentSessionId.value = crypto.randomUUID();
  }

  messages.value.push({ role: 'user', content });
  userInput.value = '';
  loading.value = true;
  await scrollToBottom();

  const aiMsgObj = { role: 'assistant', content: '' };
  messages.value.push(aiMsgObj);
  const aiIndex = messages.value.length - 1;

  try {
    const response = await fetch(`${API_BASE}/chat_stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: content,
        session_id: currentSessionId.value,
        user_id: currentUser.value.id
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    isStreaming.value = true;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      messages.value[aiIndex].content += decoder.decode(value, { stream: true });
      scrollToBottom();
    }
    fetchSessions();
  } catch (error) {
    messages.value[aiIndex].content = "⚠️ 连接超时，请检查后端服务。";
  } finally {
    loading.value = false;
    isStreaming.value = false;
  }
};

const scrollToBottom = async () => {
  await nextTick();
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
};
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar { width: 4px; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 10px; }
.animate-fade-in { animation: fadeIn 0.3s ease-in-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>