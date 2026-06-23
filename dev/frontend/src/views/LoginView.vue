<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Dices, LogIn } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) return
  isLoading.value = true
  error.value = ''
  try {
    const success = await authStore.loginUser(username.value, password.value)
    if (success) {
      router.push('/courses')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div style="display: flex; justify-content: center; align-items: center; min-height: 70vh;">
    <div class="glass-card" style="width: 100%; max-width: 450px; padding: 2.5rem;">
      <div style="text-align: center; margin-bottom: 2rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; background: hsla(265, 80%, 65%, 0.15); width: 60px; height: 60px; border-radius: 50%; border: 1px solid var(--color-primary); margin-bottom: 1rem;">
          <Dices :size="32" style="color: var(--color-primary);" />
        </div>
        <h2 style="color: var(--text-bright); font-size: 1.8rem; font-weight: 700;">Lock & Spin 로그인</h2>
        <p class="text-muted" style="font-size: 0.9rem; margin-top: 0.4rem;">맞춤형 AI 여행 플랜을 완성해보세요</p>
      </div>

      <form @submit.prevent="handleLogin">
        <div style="margin-bottom: 1.2rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem;">아이디 (Username)</label>
          <input type="text" v-model="username" class="form-input" placeholder="아이디를 입력하세요" required style="width:100%;" />
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem;">비밀번호 (Password)</label>
          <input type="password" v-model="password" class="form-input" placeholder="비밀번호를 입력하세요" required style="width:100%;" />
        </div>

        <div v-if="error" style="color: hsl(0, 80%, 60%); font-size: 0.85rem; margin-bottom: 1.2rem; line-height: 1.4;">
          ⚠️ {{ error }}
        </div>

        <button type="submit" class="btn-primary" :disabled="isLoading || !username || !password" style="width: 100%; justify-content: center; padding: 0.8rem; font-size: 1rem; margin-bottom: 1.5rem;">
          <LogIn :size="18" />
          {{ isLoading ? '로그인 중...' : '로그인' }}
        </button>
      </form>

      <div style="text-align: center; font-size: 0.9rem; color: var(--text-muted);">
        아직 계정이 없으신가요? 
        <router-link to="/register" style="color: var(--color-primary); text-decoration: none; font-weight: 600; margin-left: 0.4rem;">
          회원가입
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-input {
  background: hsla(230, 15%, 8%, 0.6);
  border: 1px solid var(--border-muted);
  border-radius: 8px;
  padding: 0.8rem;
  color: var(--text-bright);
  font-size: 0.95rem;
  transition: border-color 0.2s;
}
.form-input:focus {
  border-color: var(--color-primary);
  outline: none;
}
</style>
