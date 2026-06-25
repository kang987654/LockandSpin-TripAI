<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCourseStore } from '../stores/course'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const courseStore = useCourseStore()

const newCourseTitle = ref('')
const newCourseDestination = ref('')
const newCourseDuration = ref(2)
const newCourseDate = ref(new Date().toISOString().split('T')[0])
const newCourseTime = ref('09:00')
const newCourseTransport = ref('public')
const newCoursePreferences = ref('')

const realtimeKeywords = ref([])
let keywordTimeout = null

watch(newCoursePreferences, (newVal) => {
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
        newCourseTitle.value = res.data.title
      }
    } catch (e) {
      console.error(e)
    }
  }, 1000)
})

onMounted(() => {
  if (route.query.dest) newCourseDestination.value = route.query.dest
  if (route.query.start) newCourseDate.value = route.query.start
  if (route.query.days) newCourseDuration.value = Number(route.query.days)
  if (route.query.themes) newCoursePreferences.value = route.query.themes
  
  if (newCourseDestination.value) {
    newCourseTitle.value = `${newCourseDestination.value} 투어`
  }
})

const isCreating = ref(false)

const createCourse = async () => {
  isCreating.value = true
  try {
    const course = await courseStore.createCourse(
      newCourseTitle.value, 
      newCourseDestination.value, 
      newCourseDuration.value,
      newCourseDate.value,
      newCoursePreferences.value,
      newCourseTime.value,
      newCourseTransport.value
    )
    router.push(`/courses/${course.id}`)
  } catch (e) {
    alert('코스 생성 중 오류가 발생했습니다.')
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div style="max-width: 800px; margin: 0 auto;">
    <h2 style="color: var(--text-bright); margin-bottom: 2rem; text-align: center;">여행 코스 생성하기</h2>
    <div class="top-panels">
      
      <!-- Preference Panel -->
      <div class="glass-card">
        <h3 style="margin-bottom: 1rem; color: var(--text-bright);">🧬 내 취향 및 기피 태그 설정</h3>
        
        <!-- 동적 AI 테마 키워드로 인해 기존 고정 '선호 테마' 버튼은 삭제됨 -->

        <div style="margin-bottom: 1rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem;">선호 여행 페이스</label>
          <div style="display: flex; gap: 0.8rem;">
            <label v-for="pace in [{val:'slow', label:'느긋하게'}, {val:'medium', label:'적당히'}, {val:'fast', label:'빡빡하게'}]" :key="pace.val" class="pace-option" :class="{active: authStore.preferredPace === pace.val}" style="padding: 4px 12px; font-size: 0.8rem; border-radius: 99px;">
              <input type="radio" :value="pace.val" v-model="authStore.preferredPace" style="display:none;" />
              {{ pace.label }}
            </label>
          </div>
        </div>

        <div style="margin-bottom: 1rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem;">기피 카테고리 (Veto)</label>
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
            <label v-for="cat in ['restaurant', 'cafe', 'spot', 'activity', 'accommodation']" :key="cat" class="veto-chip" :class="{active: authStore.vetoCategories.includes(cat)}">
              <input type="checkbox" :value="cat" v-model="authStore.vetoCategories" style="display:none;" />
              {{ cat === 'spot' ? '명소' : cat === 'restaurant' ? '식당' : cat === 'cafe' ? '카페' : cat === 'accommodation' ? '숙박/숙소' : '액티비티' }} 🚫
            </label>
          </div>
        </div>

        <button class="btn-secondary" style="width: 100%; justify-content: center; padding: 0.6rem;" @click="authStore.savePreferences">
          취향 설정 저장
        </button>
      </div>

      <!-- Plan Creation -->
      <div class="glass-card">
        <h3 style="margin-bottom: 1rem; color: var(--text-bright);">✈️ 신규 여행 코스 생성</h3>
        
        <div style="margin-bottom: 0.8rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">여행 제목</label>
          <input type="text" v-model="newCourseTitle" class="form-input" />
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1.2rem;">
          <div>
            <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">여행 목적지</label>
            <select v-model="newCourseDestination" class="form-input" style="height: 38px;">
              <option value="랜덤">랜덤 🎲</option>
              <option value="서울">서울 🗼</option>
              <option value="강원도">강원도 🌊</option>
              <option value="제주도">제주도 🍊</option>
            </select>
          </div>
          <div>
            <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">기간 (일)</label>
            <input type="number" v-model="newCourseDuration" min="1" max="5" class="form-input" />
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1.2rem;">
          <div>
            <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">여행 시작 날짜</label>
            <input type="date" v-model="newCourseDate" class="form-input" style="height: 38px;" />
          </div>
          <div>
            <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">출발 시간</label>
            <input type="time" v-model="newCourseTime" class="form-input" style="height: 38px;" />
          </div>
        </div>

        <div style="margin-bottom: 1.2rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">이동 수단</label>
          <div style="display: flex; gap: 1rem;">
            <label style="color: var(--text-bright); font-size: 0.9rem;">
              <input type="radio" v-model="newCourseTransport" value="car" /> 자차
            </label>
            <label style="color: var(--text-bright); font-size: 0.9rem;">
              <input type="radio" v-model="newCourseTransport" value="public" /> 대중교통/도보
            </label>
          </div>
        </div>

        <div style="margin-bottom: 1.2rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">어떤 여행을 원하시나요? (자유입력)</label>
          <input type="text" v-model="newCoursePreferences" placeholder="예: 비 오는 날 실내 데이트, 동문시장 필수 방문" class="form-input" />
          <div v-if="realtimeKeywords.length" style="margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem; min-height: 24px;">
            <span v-for="tag in realtimeKeywords" :key="tag" style="font-size: 0.75rem; color: var(--color-primary); background: hsla(265, 80%, 65%, 0.1); padding: 2px 8px; border-radius: 99px;">
              #{{ tag }}
            </span>
            <span style="font-size: 0.75rem; color: #888; align-self: center; margin-left: 5px;">(AI 추천 키워드)</span>
          </div>
        </div>

        <button class="btn-primary" style="width: 100%; justify-content: center; padding: 0.7rem;" @click="createCourse" :disabled="isCreating">
          {{ isCreating ? 'AI가 일정을 분석하여 생성하고 있습니다...' : 'AI 슬롯 기반 최초 일정 추천받기' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.top-panels {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}
@media (min-width: 992px) {
  .top-panels {
    grid-template-columns: 1fr 1fr;
  }
}
.theme-chip, .veto-chip {
  padding: 4px 10px;
  border-radius: 99px;
  background: #f1f5f9;
  border: 1px solid var(--border-muted);
  color: var(--text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.theme-chip.active {
  background: hsla(265, 80%, 65%, 0.15);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.veto-chip.active {
  background: hsla(0, 80%, 60%, 0.1);
  border-color: hsl(0, 80%, 60%);
  color: hsl(0, 80%, 60%);
}
.pace-option {
  background: #f1f5f9;
  border: 1px solid var(--border-muted);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}
.pace-option.active {
  background: hsla(265, 80%, 65%, 0.15);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
