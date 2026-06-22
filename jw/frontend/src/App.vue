<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { Dices, User, LogOut } from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <div class="header-glass">
    <div class="brand-title">
      <router-link to="/" style="text-decoration: none; color: inherit; display: flex; align-items: center; gap: 0.6rem;">
        <Dices :size="24" style="color: var(--color-primary);" />
        <span>Lock & Spin</span>
        <span class="badge-logo">Custom Travel Planner</span>
      </router-link>
    </div>
    
    <nav class="nav-links">
      <router-link to="/courses" class="nav-link">여행 코스</router-link>
      <router-link to="/community" class="nav-link">커뮤니티</router-link>
    </nav>

    <div class="user-status" style="display: flex; align-items: center; gap: 1rem;">
      <div v-if="authStore.isLoggedIn" style="display: flex; align-items: center; gap: 1rem;">
        <router-link to="/profile" class="nav-link" style="margin: 0; display: flex; align-items: center; gap: 0.4rem; color: var(--text-bright);">
          <User :size="18" style="color: var(--color-accent);" />
          <span>{{ authStore.currentUser?.username || '프로필' }}</span>
        </router-link>
        <button @click="handleLogout" style="background: none; border: none; color: var(--text-muted); cursor: pointer; display: flex; align-items: center; gap: 0.3rem; font-weight: 600; padding: 0;" title="로그아웃">
          <LogOut :size="16" />
          <span style="font-size: 0.9rem;">로그아웃</span>
        </button>
      </div>
      <div v-else style="display: flex; gap: 0.8rem;">
        <router-link to="/login">
          <button class="btn-secondary" style="padding: 0.4rem 1.2rem; font-size: 0.85rem;">로그인</button>
        </router-link>
        <router-link to="/register">
          <button class="btn-primary" style="padding: 0.4rem 1.2rem; font-size: 0.85rem;">회원가입</button>
        </router-link>
      </div>
    </div>
  </div>

  <div class="main-content">
    <router-view></router-view>
  </div>
</template>

<style>
.nav-links {
  display: flex;
  gap: 1.5rem;
  margin: 0 2rem;
}
.nav-link {
  color: var(--text-bright);
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}
.nav-link:hover, .nav-link.router-link-active {
  color: var(--color-primary);
}
.main-content {
  padding: 2rem 5%;
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}
</style>
