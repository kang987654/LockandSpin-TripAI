<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { Utensils, MapPin, Search, Sparkles } from 'lucide-vue-next'

const authStore = useAuthStore()

const region = ref('')
const preference = ref('')
const isLoading = ref(false)
const result = ref(null)
const error = ref('')

const fetchRecommendation = async () => {
  if (!region.value.trim() || !preference.value.trim()) {
    error.value = '지역과 먹고 싶은 음식을 모두 입력해주세요!'
    return
  }
  
  isLoading.value = true
  error.value = ''
  result.value = null
  
  try {
    const res = await axios.post(`${authStore.API_BASE}/api/recommendations/food/`, {
      region: region.value,
      preference: preference.value
    })
    
    if (res.data.error) {
      error.value = '추천을 불러오는 중 문제가 발생했습니다.'
    } else {
      result.value = res.data
    }
  } catch (err) {
    console.error(err)
    error.value = '서버 통신 중 오류가 발생했습니다.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="food-widget">
    <div class="widget-header">
      <Utensils :size="20" style="color: var(--color-primary);" />
      <h3>오늘 뭐 먹지?</h3>
    </div>
    
    <div class="widget-body">
      <p class="widget-desc">AI가 딱 맞는 밥 메뉴를 골라드려요!</p>
      
      <form @submit.prevent="fetchRecommendation" class="food-form">
        <div class="input-group">
          <MapPin :size="16" class="icon" />
          <input v-model="region" type="text" placeholder="어디서 드시나요? (예: 강남역)" required />
        </div>
        
        <div class="input-group">
          <Sparkles :size="16" class="icon" />
          <input v-model="preference" type="text" placeholder="어떤 기분인가요? (예: 비오는데 국물)" required />
        </div>
        
        <button type="submit" class="btn-primary search-btn" :disabled="isLoading">
          <span v-if="isLoading">추천 중...</span>
          <span v-else><Search :size="16" style="margin-right: 4px;"/> 메뉴 추천받기</span>
        </button>
      </form>
      
      <div v-if="error" class="error-msg">
        {{ error }}
      </div>
      
      <div v-if="result && result.place" class="result-card">
        <div class="result-header">
          <span class="category-badge">{{ result.ai_analysis.category }}</span>
        </div>
        
        <div class="place-info">
          <div v-if="result.place.image_url" class="place-img">
            <img :src="result.place.image_url" alt="식당 이미지" />
          </div>
          <div v-else class="place-img-placeholder">
            🍽️
          </div>
          
          <div class="place-details">
            <h4 class="place-name">{{ result.place.name }}</h4>
            <p class="place-address">{{ result.place.address }}</p>
            <a v-if="result.place.place_url" :href="result.place.place_url" target="_blank" class="place-link">지도에서 보기 &rarr;</a>
          </div>
        </div>
        
        <div class="ai-message">
          <Sparkles :size="14" class="ai-icon" />
          <p>{{ result.ai_analysis.recommend_message }}</p>
        </div>
      </div>
      
      <div v-else-if="result && !result.place" class="error-msg">
        조건에 맞는 식당을 근처에서 찾지 못했어요 😢 다른 지역이나 메뉴로 시도해 보세요.
      </div>
    </div>
  </div>
</template>

<style scoped>
.food-widget {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.widget-header {
  padding: 1.2rem 1.5rem;
  background: linear-gradient(to right, #f8fafc, #f1f5f9);
  border-bottom: 1px solid var(--border-muted);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.widget-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-bright);
}

.widget-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.widget-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
}

.food-form {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.input-group {
  position: relative;
}

.input-group .icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.input-group input {
  width: 100%;
  padding: 0.8rem 1rem 0.8rem 2.5rem;
  border: 1px solid var(--border-muted);
  border-radius: 12px;
  background: #f8fafc;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.input-group input:focus {
  background: #fff;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  outline: none;
}

.search-btn {
  width: 100%;
  padding: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.95rem;
}

.error-msg {
  color: #ef4444;
  font-size: 0.85rem;
  text-align: center;
  background: #fef2f2;
  padding: 0.8rem;
  border-radius: 8px;
}

.result-card {
  margin-top: 0.5rem;
  background: #fff;
  border: 1px solid var(--border-muted);
  border-radius: 16px;
  padding: 1.2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.result-header {
  margin-bottom: 1rem;
}

.category-badge {
  background: rgba(139, 92, 246, 0.1);
  color: var(--color-primary);
  padding: 0.3rem 0.8rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 700;
}

.place-info {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.place-img, .place-img-placeholder {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  flex-shrink: 0;
  overflow: hidden;
}

.place-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.place-img-placeholder {
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.place-details {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.place-name {
  margin: 0 0 0.3rem 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-bright);
}

.place-address {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.3;
}

.place-link {
  display: inline-block;
  margin-top: 0.4rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-primary);
  text-decoration: none;
}

.place-link:hover {
  text-decoration: underline;
}

.ai-message {
  background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
}

.ai-icon {
  color: #0d9488;
  flex-shrink: 0;
  margin-top: 2px;
}

.ai-message p {
  margin: 0;
  font-size: 0.9rem;
  color: #115e59;
  line-height: 1.4;
  font-weight: 600;
}
</style>
