<template>
  <div class="fixed inset-0 z-[100] bg-slate-50 flex items-center justify-center p-4 sm:p-6">
    <div class="absolute inset-0 bg-grid-slate-200 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10"></div>

    <div class="w-full max-w-2xl bg-white rounded-3xl shadow-2xl shadow-slate-200/50 overflow-hidden border border-slate-100 animate-fade-in">
      <div class="flex flex-col md:flex-row h-full">

        <div class="md:w-1/3 bg-slate-900 p-8 text-white flex flex-col items-center justify-center text-center">
          <div class="relative group">
            <div class="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center text-4xl font-bold shadow-xl mb-4 transform group-hover:rotate-6 transition-transform">
              {{ currentUser?.nickname?.charAt(0) }}
            </div>
            <div class="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 border-4 border-slate-900 rounded-full"></div>
          </div>
          <h2 class="text-xl font-bold truncate w-full">{{ currentUser?.nickname }}</h2>
          <p class="text-slate-400 text-xs mt-1 uppercase tracking-widest">{{ currentUser?.role }}</p>

          <button @click="$emit('exit')" class="mt-8 flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors">
            <span>←</span> 返回系统
          </button>
        </div>

        <div class="flex-1 p-8 overflow-y-auto max-h-[85vh]">
          <div class="mb-6">
            <h3 class="text-2xl font-bold text-slate-800">个人设置</h3>
            <p class="text-slate-500 text-sm mt-1">更新您的个人资料与安全选项</p>
          </div>

          <div class="space-y-5">
            <div class="space-y-1">
              <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">登录账号</label>
              <div class="px-4 py-2.5 bg-slate-50 border border-slate-100 rounded-xl text-slate-500 font-mono text-sm cursor-not-allowed">
                @ {{ currentUser?.username }}
              </div>
            </div>

            <div class="space-y-1">
              <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">显示昵称</label>
              <input
                v-model="form.nickname"
                type="text"
                class="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all"
              />
            </div>

            <div class="h-px bg-slate-100 my-2"></div>

            <div class="space-y-4">
              <h4 class="text-sm font-bold text-slate-700 flex items-center gap-2">
                <span class="text-lg">🔒</span> 修改密码 <span class="text-[10px] font-normal text-slate-400">(不修改请留空)</span>
              </h4>

              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">当前密码</label>
                <input
                  v-model="form.oldPassword"
                  type="password"
                  placeholder="验证旧身份"
                  class="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all"
                />
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">新密码</label>
                  <input
                    v-model="form.newPassword"
                    type="password"
                    class="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all"
                  />
                </div>
                <div class="space-y-1">
                  <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">确认新密码</label>
                  <input
                    v-model="form.confirmPassword"
                    type="password"
                    class="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all"
                  />
                </div>
              </div>
            </div>

            <div class="pt-6 flex flex-col gap-3">
              <button
                @click="handleSave"
                :disabled="isSaving"
                class="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-xl font-bold shadow-lg shadow-blue-500/30 transition-all flex items-center justify-center gap-2"
              >
                <span v-if="isSaving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                {{ isSaving ? '提交保存' : '保存更改' }}
              </button>
              <button @click="$emit('exit')" class="w-full py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl font-bold transition-all">
                取消
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';

const props = defineProps({
  currentUser: { type: Object, required: true }
});

const emit = defineEmits(['exit', 'update-user', 'logout']);

const isSaving = ref(false);
const form = reactive({
  nickname: props.currentUser?.nickname || '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const handleSave = async () => {
  // 1. 基础校验
  if (!form.nickname.trim()) return alert("昵称不能为空");

  // 2. 密码校验逻辑
  if (form.newPassword || form.oldPassword) {
    if (!form.oldPassword) return alert("修改密码需要填写当前密码");
    if (form.newPassword.length < 6) return alert("新密码长度不能少于6位");
    if (form.newPassword !== form.confirmPassword) return alert("两次输入的新密码不一致");
  }

  isSaving.value = true;

  try {
    // 🚩 对接后端 API
    const response = await fetch(`http://127.0.0.1:8000/admin/users/${props.currentUser.id}/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nickname: form.nickname,
        old_password: form.oldPassword || null,
        new_password: form.newPassword || null
      })
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "更新失败");


    alert("更新成功！" + (form.newPassword ? "请使用新密码重新登录。" : ""));

      alert("个人资料更新成功，请重新登录以生效！");

          // 触发父组件 App.vue 的 logout 函数
          // 传入 false 表示强制静默退出（不弹出 confirm 确认框）
          emit('logout', true);
  } catch (error) {
    alert(error.message);
  } finally {
    isSaving.value = false;
  }
};
</script>