<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCourseStore } from '../stores/course'

const router = useRouter()
const authStore = useAuthStore()
const courseStore = useCourseStore()

const newCourseTitle = ref('서울 힐링 감성 투어')
const newCourseDestination = ref('랜덤')
const newCourseDuration = ref(2)

const searchQuery = ref('')
const filterDestination = ref('')

onMounted(() => {
  courseStore.fetchCourses()
})

const createCourse = async () => {
  try {
    const course = await courseStore.createCourse(
      newCourseTitle.value, 
      newCourseDestination.value, 
      newCourseDuration.value
    )
    router.push(`/courses/${course.id}`)
  } catch (e) {
    alert('코스 생성 중 오류가 발생했습니다.')
  }
}

const filteredCourses = computed(() => {
  let list = courseStore.coursesList
  if (filterDestination.value) {
    list = list.filter(c => c.destination.includes(filterDestination.value))
  }
  if (searchQuery.value) {
    list = list.filter(c => c.title.toLowerCase().includes(searchQuery.value.toLowerCase()))
  }
  // 정렬 (최신순)
  return list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

const currentPage = ref(1)
const itemsPerPage = 12

const totalPages = computed(() => Math.ceil(filteredCourses.value.length / itemsPerPage) || 1)
const paginatedCourses = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredCourses.value.slice(start, start + itemsPerPage)
})
</script>

<template>
  <div>
    <div class="top-panels">
      
      <!-- Preference Panel -->
      <div class="glass-card">
        <h3 style="margin-bottom: 1rem; color: var(--text-bright);">🧬 내 취향 및 기피 태그 설정</h3>
        
        <div style="margin-bottom: 1rem;">
          <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem;">선호 테마</label>
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
            <label v-for="theme in ['healing', 'nature', 'food', 'activity', 'culture', 'traditional']" :key="theme" class="theme-chip" :class="{active: authStore.preferredThemes.includes(theme)}">
              <input type="checkbox" :value="theme" v-model="authStore.preferredThemes" style="display:none;" />
              #{{ theme === 'healing' ? '힐링' : theme === 'nature' ? '자연' : theme === 'food' ? '맛집' : theme === 'activity' ? '액티비티' : theme === 'culture' ? '문화/역사' : '전통' }}
            </label>
          </div>
        </div>

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
            <label v-for="cat in ['restaurant', 'cafe', 'spot', 'activity']" :key="cat" class="veto-chip" :class="{active: authStore.vetoCategories.includes(cat)}">
              <input type="checkbox" :value="cat" v-model="authStore.vetoCategories" style="display:none;" />
              {{ cat === 'spot' ? '관광지' : cat === 'restaurant' ? '음식점' : cat === 'cafe' ? '카페' : '액티비티' }} 제외
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

        <button class="btn-primary" style="width: 100%; justify-content: center; padding: 0.7rem;" @click="createCourse">
          AI 슬롯 기반 최초 일정 추천받기
        </button>
      </div>
    </div>

    <div class="glass-card">
      <h3 style="margin-bottom: 1rem; color: var(--text-bright);">목록 및 필터링</h3>
      <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
        <input type="text" v-model="searchQuery" placeholder="여행 제목 검색" class="form-input" style="max-width: 200px;" />
        <select v-model="filterDestination" class="form-input" style="max-width: 150px;">
          <option value="">모든 지역</option>
          <option value="서울">서울</option>
          <option value="강원도">강원도</option>
          <option value="제주도">제주도</option>
        </select>
      </div>

      <div class="courses-grid">
        <div v-for="course in paginatedCourses" :key="course.id" class="glass-card course-item" @click="router.push(`/courses/${course.id}`)">
          <h4 style="color: var(--text-bright);">{{ course.title }}</h4>
          <p class="text-muted" style="margin: 0; font-size: 0.9rem;">목적지: {{ course.destination }} | {{ course.duration_days }}일간 | 생성일: {{ new Date(course.created_at).toLocaleDateString() }}</p>
        </div>
      </div>

      <div style="display: flex; justify-content: center; align-items: center; gap: 1rem; margin-top: 2rem;">
        <button class="btn-secondary" style="padding: 0.5rem 1rem;" :disabled="currentPage === 1" @click="currentPage--">이전</button>
        <span style="color: var(--text-bright); font-weight: bold;">{{ currentPage }} / {{ totalPages }}</span>
        <button class="btn-secondary" style="padding: 0.5rem 1rem;" :disabled="currentPage === totalPages" @click="currentPage++">다음</button>
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
.courses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}
.course-item {
  margin-bottom: 0;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.course-item:hover {
  transform: translateY(-4px);
}
.theme-chip, .veto-chip {
  cursor: pointer;
  background: hsla(230, 15%, 18%, 0.6);
  border: 1px solid var(--border-muted);
  color: var(--text-muted);
  padding: 4px 12px;
  border-radius: 99px;
  font-size: 0.8rem;
  transition: all 0.2s;
  user-select: none;
}
.theme-chip.active {
  background: hsla(265, 80%, 65%, 0.15);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.veto-chip.active {
  background: hsla(0, 80%, 60%, 0.15);
  border-color: hsl(0, 80%, 60%);
  color: hsl(0, 80%, 60%);
}
.pace-option {
  cursor: pointer;
  background: hsla(230, 15%, 18%, 0.6);
  border: 1px solid var(--border-muted);
  color: var(--text-muted);
  transition: all 0.2s;
  user-select: none;
}
.pace-option.active {
  background: hsla(190, 90%, 50%, 0.15);
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.form-input {
  width: 100%;
  background: hsla(230, 15%, 8%, 0.6);
  border: 1px solid var(--border-muted);
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  color: var(--text-bright);
  font-size: 0.9rem;
}
</style>
