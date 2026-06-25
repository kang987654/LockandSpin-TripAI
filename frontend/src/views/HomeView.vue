<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCourseStore } from '../stores/course'
import { MapPin, Calendar, Sparkles, Clock, Car } from 'lucide-vue-next'
import KoreaMapSelector from '../components/KoreaMapSelector.vue'
import FoodRecommendationWidget from '../components/FoodRecommendationWidget.vue'
import axios from 'axios'

const authStore = useAuthStore()
const courseStore = useCourseStore()
const router = useRouter()

const destination = ref('')
const courseTitle = ref('')
const startDate = ref(new Date().toISOString().split('T')[0])
const departureTime = ref('09:00')
const transportation = ref('public')
const durationDays = ref('2')
const coursePurpose = ref('')
const selectedThemes = ref([])
const realtimeKeywords = ref([])
let keywordTimeout = null

watch(coursePurpose, (newVal) => {
  clearTimeout(keywordTimeout)
  if (!newVal.trim()) {
    realtimeKeywords.value = []
    return
  }
  keywordTimeout = setTimeout(async () => {
    try {
      const res = await axios.post(`${authStore.API_BASE}/api/courses/extract_keywords/`, { query: newVal })
      realtimeKeywords.value = res.data.tags || []
      if (res.data.title) {
        courseTitle.value = res.data.title
      }
    } catch (e) {
      console.error(e)
    }
  }, 1000)
})
const isCreating = ref(false)

const REGIONS = [
  { id: 'seoul', name: '서울', icon: '🏙️' },
  { id: 'busan', name: '부산', icon: '🌊' },
  { id: 'jeju', name: '제주', icon: '🌴' },
  { id: 'gangneung', name: '강릉', icon: '🌅' },
  { id: 'gyeongju', name: '경주', icon: '🏯' },
  { id: 'jeonju', name: '전주', icon: '🏘️' },
  { id: 'yeosu', name: '여수', icon: '🌉' },
  { id: 'incheon', name: '인천', icon: '✈️' }
]

const THEMES = [
  "가성비", "럭셔리", "액티비티", "휴양/힐링", "자연친화", 
  "도시탐험", "로컬맛집", "카페투어", "예술/전시", "역사/문화"
]

const toggleTheme = (theme) => {
  if (selectedThemes.value.includes(theme)) {
    selectedThemes.value = selectedThemes.value.filter(t => t !== theme)
  } else {
    if (selectedThemes.value.length >= 3) {
      alert('테마는 최대 3개까지 선택 가능합니다.')
      return
    }
    selectedThemes.value.push(theme)
  }
}

const handleGenerate = async () => {
  if (!destination.value || !startDate.value) {
    alert('목적지와 출발일을 입력해주세요.')
    return
  }
  
  isCreating.value = true
  try {
    const title = courseTitle.value.trim() || `${destination.value} 투어`
    const course = await courseStore.createCourse(
      title,
      destination.value,
      Number(durationDays.value),
      startDate.value,
      coursePurpose.value,
      departureTime.value,
      transportation.value
    )
    router.push(`/courses/${course.id}`)
  } catch (error) {
    console.error('Course creation failed:', error)
    alert('코스 생성 중 오류가 발생했습니다.')
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="hero-container">
    <div class="hero-bg">
      <div class="hero-overlay"></div>
    </div>

    <div class="hero-content">
      <div class="text-center" style="margin-bottom: 3rem;">
        <h1 class="hero-title">
          당신만의 완벽한 <span class="text-gradient">AI 여행 코스</span>
        </h1>
        <p class="hero-subtitle">
          목적지와 취향을 알려주시면, 동행자와 함께 조율할 수 있는 초안을 만들어 드립니다.
        </p>
      </div>

      <div class="home-layout">
        <!-- Main Content -->
        <div class="glass-card creation-card">
        <h2 class="card-title">
          <Sparkles :size="20" style="color: var(--color-primary); margin-right: 0.5rem;" />
          새 코스 생성하기
        </h2>
        
        <form @submit.prevent="handleGenerate" class="creation-form">
          <!-- Row 1: 목적 및 테마 (Moved to Top) -->
          <div class="form-group" style="margin-top: 0; margin-bottom: 1.5rem;">
            <label>어떤 테마의 여행을 원하시나요? (목적을 자유롭게 적어주세요)</label>
            <div class="input-wrapper" style="margin-top: 0.5rem;">
              <Sparkles :size="18" class="input-icon" />
              <input v-model="coursePurpose" type="text" placeholder="예: 비오는 날 제주도 실내 데이트 코스" />
            </div>
            
            <!-- AI 동적 키워드 출력 -->
            <div v-if="realtimeKeywords.length" class="theme-pills" style="margin-top: 1rem;">
              <button 
                v-for="theme in realtimeKeywords" 
                :key="theme"
                type="button"
                class="theme-pill active"
              >
                #{{ theme }}
              </button>
              <span style="font-size: 0.8rem; color: var(--color-primary); align-self: center; margin-left: 0.5rem;">(AI 추천 키워드)</span>
            </div>
          </div>

          <div class="form-layout-split">
            <!-- Left Column: Title, Dates -->
            <div class="left-col">
              <div class="form-group" style="margin-top: 0;">
                <label>여행 제목 (선택)</label>
                <div class="input-wrapper">
                  <Sparkles :size="18" class="input-icon" />
                  <input v-model="courseTitle" type="text" />
                </div>
              </div>

              <div class="form-group" style="margin-top: 1.5rem;">
                <label>출발일</label>
                <div class="input-wrapper">
                  <Calendar :size="18" class="input-icon" />
                  <input v-model="startDate" type="date" required />
                </div>
              </div>

              <div class="form-group" style="margin-top: 1.5rem;">
                <label>여행 기간</label>
                <select v-model="durationDays" class="custom-select">
                  <option value="1">당일치기</option>
                  <option value="2">1박 2일</option>
                  <option value="3">2박 3일</option>
                  <option value="4">3박 4일</option>
                </select>
              </div>

              <div class="form-group" style="margin-top: 1.5rem;">
                <label>출발 시간</label>
                <div class="input-wrapper">
                  <Clock :size="18" class="input-icon" />
                  <input v-model="departureTime" type="time" required />
                </div>
              </div>

              <div class="form-group" style="margin-top: 1.5rem;">
                <label>이동 수단</label>
                <div style="display: flex; gap: 1.5rem; margin-top: 0.5rem;">
                  <label style="color: var(--text-muted); cursor: pointer;">
                    <input type="radio" v-model="transportation" value="car" /> 자차
                  </label>
                  <label style="color: var(--text-muted); cursor: pointer;">
                    <input type="radio" v-model="transportation" value="public" /> 대중교통/도보
                  </label>
                </div>
              </div>
            </div>

            <!-- Right Column: Map Selector -->
            <div class="right-col">
              <div class="form-group" style="height: 100%; margin-top: 0; display: flex; flex-direction: column;">
                <label>어디로 떠나시나요?</label>
                <div style="flex: 1; min-height: 0;">
                  <KoreaMapSelector v-model="destination" />
                </div>
              </div>
            </div>
          </div>
          
          <button type="submit" class="btn-primary submit-btn" :disabled="isCreating" style="margin-top: 1.5rem;">
            {{ isCreating ? '코스 생성 중...' : '코스 짜기 시작' }}
          </button>
        </form>
        </div>

        <!-- Sidebar (Food Widget) -->
        <div class="sidebar-container">
          <FoodRecommendationWidget />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* HomeView는 App.vue의 main-content 패딩을 무시하고 전체화면을 덮기 위해 네거티브 마진 사용 */
.hero-container {
  margin: -2rem -5%;
  min-height: calc(100vh - 70px);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: url('https://images.unsplash.com/photo-1628411848698-e3b3249a272a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqZWp1JTIwaXNsYW5kJTIwbGFuZHNjYXBlfGVufDF8fHx8MTc4MjA4OTQxNnww&ixlib=rb-4.1.0&q=80&w=1080');
  background-size: cover;
  background-position: center;
  z-index: 0;
}

.hero-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
}

.hero-content {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 1200px; /* Increased from 900px */
  padding: 0 1.5rem;
}

.home-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}



.hero-title {
  font-size: 2.8rem;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 1rem;
  letter-spacing: -0.05em;
  text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.text-gradient {
  background: linear-gradient(135deg, #a78bfa, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 1.15rem;
  color: #f8fafc;
  font-weight: 500;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.creation-card {
  flex: 2; /* takes more space */
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255,255,255,0.5);
}

.sidebar-container {
  flex: 1;
  min-width: 300px;
  max-width: 350px;
}

.text-center {
  text-align: center;
}

.card-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text-bright);
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-muted);
}

.creation-form {
  display: flex;
  flex-direction: column;
}

.form-layout-split {
  display: flex;
  gap: 2rem;
}

.left-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.right-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}

@media (max-width: 992px) {
  .home-layout {
    flex-direction: column;
  }
  
  .sidebar-container {
    max-width: 100%;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .form-layout-split {
    flex-direction: column;
  }
}

.form-group {
  margin-top: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.5rem;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.input-wrapper input {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 1px solid var(--border-muted);
  border-radius: 12px;
  background: #f8fafc;
  font-size: 1rem;
  font-family: inherit;
  font-weight: 500;
  color: var(--text-bright);
  transition: all 0.2s;
}

.region-selector {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin-top: 1rem;
}

.region-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  padding: 0.8rem 0;
  background: #f8fafc;
  border: 1px solid var(--border-muted);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.region-btn:hover {
  background: rgba(139, 92, 246, 0.05);
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.region-btn.active {
  background: rgba(139, 92, 246, 0.1);
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 700;
}

.r-icon {
  font-size: 1.5rem;
}

.r-name {
  font-size: 0.9rem;
  color: var(--text-main);
}
.region-btn.active .r-name {
  color: var(--color-primary);
}

.input-wrapper input:focus {
  background: #ffffff;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.submit-btn {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
  justify-content: center;
  margin-top: 0.5rem;
}

.form-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.flex-1 {
  flex: 1;
  min-width: 150px;
}

.custom-select {
  width: 100%;
  padding: 1rem 1rem 1rem 1rem;
  border: 1px solid var(--border-muted);
  border-radius: 12px;
  background: #f8fafc;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-bright);
  outline: none;
  cursor: pointer;
}

.theme-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 0.3rem;
}

.theme-pill {
  padding: 0.5rem 1rem;
  border-radius: 99px;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-pill:hover {
  background: #e2e8f0;
}

.theme-pill.active {
  background: var(--color-primary);
  color: #ffffff;
  border-color: var(--color-primary-dark);
  box-shadow: 0 4px 10px rgba(139, 92, 246, 0.3);
}
</style>
