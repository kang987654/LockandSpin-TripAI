<script setup>
import { useAuthStore } from '../stores/auth'
const authStore = useAuthStore()
</script>

<template>
  <div style="text-align: center; margin-top: 4rem;">
    <h1 style="color: var(--text-bright); font-size: 2.5rem; margin-bottom: 1rem;">
      당신만의 맞춤형 AI 여행 플래너
    </h1>
    <p class="text-muted" style="font-size: 1.2rem; margin-bottom: 2rem;">
      Lock & Spin 기능으로 원하는 장소는 고정하고, 나머지는 새롭게 추천받으세요.
    </p>
    
    <div class="glass-card" style="max-width: 600px; margin: 0 auto; padding: 2rem;">
      <h3 style="margin-bottom: 1rem; color: var(--text-bright);">✈️ 신규 여행 코스 생성하러 가기</h3>
      <router-link to="/courses" style="text-decoration: none;">
        <button class="btn-primary" style="width: 100%; padding: 1rem; font-size: 1.1rem;">
          코스 짜기 시작
        </button>
      </router-link>
    </div>
  </div>
</template>
