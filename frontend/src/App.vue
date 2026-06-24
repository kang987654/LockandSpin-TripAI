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
        <span class="badge-logo">TripAI</span>
      </router-link>
    </div>
    
    <div class="right-nav-group">
      <nav class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="active">홈</router-link>
        <router-link to="/courses" class="nav-link" active-class="active">나의 코스</router-link>
        <router-link to="/community" class="nav-link" active-class="active">커뮤니티</router-link>
      </nav>

      <div class="divider"></div>

      <div class="user-status">
        <template v-if="authStore.isLoggedIn">
          <router-link to="/profile" class="nav-link" active-class="active" style="display: flex; align-items: center; gap: 0.4rem;">
            <User :size="16" style="color: var(--color-accent);" />
            <span>{{ authStore.currentUser?.username || '프로필' }}</span>
          </router-link>
          <button @click="handleLogout" class="logout-btn" title="로그아웃">
            <LogOut :size="16" />
            <span>로그아웃</span>
          </button>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link">로그인</router-link>
          <router-link to="/register">
            <button class="btn-primary" style="padding: 0.5rem 1.2rem; font-size: 0.85rem;">시작하기</button>
          </router-link>
        </template>
      </div>
    </div>
  </div>

  <div class="main-content">
    <router-view></router-view>
  </div>
</template>

<style>
.header-glass {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2.5rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border-muted);
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.right-nav-group {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.user-status {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.nav-link {
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: color 0.2s;
}

.nav-link:hover {
  color: var(--text-main);
}

.nav-link.active {
  color: var(--color-primary);
}

.divider {
  width: 1px;
  height: 20px;
  background-color: var(--border-muted);
  margin: 0 0.5rem;
}

.logout-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0;
  transition: color 0.2s;
}

.logout-btn:hover {
  color: #ef4444;
}

.main-content {
  width: 100%;
  flex-grow: 1;
}
</style>
