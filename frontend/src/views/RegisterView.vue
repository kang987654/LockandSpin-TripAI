<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Dices, UserPlus } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const isLoading = ref(false)

const handleRegister = async () => {
  if (!username.value || !email.value || !password.value) return
  if (password.value !== confirmPassword.value) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  
  isLoading.value = true
  error.value = ''
  try {
    const success = await authStore.registerUser(username.value, email.value, password.value)
    if (success) {
      const redirect = route.query.redirect || '/courses'
      router.push(redirect)
    }
  } catch (err) {
    const errData = err.response?.data
    if (errData && typeof errData === 'object') {
      const keys = Object.keys(errData)
      error.value = errData[keys[0]][0] || '회원가입에 실패했습니다.'
    } else {
      error.value = '회원가입에 실패했습니다. 입력값을 확인해주세요.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div style="display: flex; justify-content: center; align-items: center; min-height: 80vh;">
    <div class="glass-card" style="width: 100%; max-width: 480px; padding: 2.5rem;">
      <div style="text-align: center; margin-bottom: 2rem;">
        <div style="display: inline-flex; align-items: center; justify-content: center; background: hsla(190, 90%, 50%, 0.15); width: 60px; height: 60px; border-radius: 50%; border: 1px solid var(--color-accent); margin-bottom: 1rem;">
          <Dices :size="32" style="color: var(--color-accent);" />
        </div>
        <h2 style="color: var(--text-bright); font-size: 1.8rem; font-weight: 700;">Lock & Spin 회원가입</h2>
        <p class="text-muted" style="font-size: 0.9rem; margin-top: 0.4rem;">새로운 계정을 생성하고 여행 일정을 꾸려보세요</p>
      </div>

      <form @submit.prevent="handleRegister">
        <div style="margin-bottom: 1.1rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">사용자명 (ID / Username)</label>
          <input type="text" v-model="username" class="form-input" placeholder="아이디를 입력하세요" required style="width:100%;" />
        </div>

        <div style="margin-bottom: 1.1rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">이메일 (Email)</label>
          <input type="email" v-model="email" class="form-input" placeholder="이메일을 입력하세요" required style="width:100%;" />
        </div>

        <div style="margin-bottom: 1.1rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">비밀번호 (Password)</label>
          <input type="password" v-model="password" class="form-input" placeholder="비밀번호를 입력하세요" required style="width:100%;" />
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">비밀번호 확인 (Confirm Password)</label>
          <input type="password" v-model="confirmPassword" class="form-input" placeholder="비밀번호를 한번 더 입력하세요" required style="width:100%;" />
        </div>

        <div v-if="error" style="color: hsl(0, 80%, 60%); font-size: 0.85rem; margin-bottom: 1.2rem; line-height: 1.4;">
          ⚠️ {{ error }}
        </div>

        <button type="submit" class="btn-primary" :disabled="isLoading || !username || !email || !password || !confirmPassword" style="width: 100%; justify-content: center; padding: 0.8rem; font-size: 1rem; margin-bottom: 1.5rem;">
          <UserPlus :size="18" />
          {{ isLoading ? '가입 중...' : '회원가입 완료' }}
        </button>
      </form>

      <div style="text-align: center; font-size: 0.9rem; color: var(--text-muted);">
        이미 계정이 있으신가요? 
        <router-link :to="{ path: '/login', query: route.query }" style="color: var(--color-primary); text-decoration: none; font-weight: 600; margin-left: 0.4rem;">
          로그인
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-input {
  width: 100%;
  background: #ffffff;
  border: 1px solid var(--border-muted);
  border-radius: 8px;
  padding: 0.8rem;
  color: var(--text-main);
  font-size: 0.95rem;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}
</style>
