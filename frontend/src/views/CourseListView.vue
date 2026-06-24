<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCourseStore } from '../stores/course'
import { MapPin, Calendar, Plus, Trash2 } from 'lucide-vue-next'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const courseStore = useCourseStore()

const searchQuery = ref('')
const filterDestination = ref('')
const filterStatus = ref('')

onMounted(() => {
  courseStore.fetchCourses()
})

const deleteCourse = async (courseId, event) => {
  event.stopPropagation()
  if (!confirm('정말 이 코스를 삭제하시겠습니까?')) return
  try {
    await axios.delete(`${authStore.API_BASE}/api/courses/${courseId}/`, authStore.getHeaders())
    courseStore.coursesList = courseStore.coursesList.filter(c => c.id !== courseId)
    alert('코스가 삭제되었습니다.')
  } catch (err) {
    console.error('Delete course failed:', err)
    alert('코스 삭제 중 오류가 발생했습니다.')
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
  if (filterStatus.value) {
    list = list.filter(c => c.status === filterStatus.value)
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

// Helper functions for mock data
const getStatusLabel = (status) => {
  if (status === 'draft') return { text: '계획 중', class: 'badge-planning' }
  return { text: '생성 완료', class: 'badge-upcoming' }
}

const getRandomImage = (id) => {
  const images = [
    'https://images.unsplash.com/photo-1628411848698-e3b3249a272a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800',
    'https://images.unsplash.com/photo-1541055575455-df3a497caa48?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800',
    'https://images.unsplash.com/photo-1730263640693-74af4e1def6d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800'
  ];
  return images[id % images.length];
}
</script>

<template>
  <div class="my-plans-container">
    <div class="header-area">
      <div>
        <h1 class="page-title">나의 코스</h1>
        <p class="page-subtitle">AI와 함께 계획한 모든 여행 코스를 이곳에서 관리하세요.</p>
      </div>
      <button class="btn-primary" @click="router.push('/')">
        <Plus :size="18" /> 새 코스 생성
      </button>
    </div>

    <!-- Filters -->
    <div class="filter-area">
      <input type="text" v-model="searchQuery" placeholder="여행 제목 검색" class="form-input" style="max-width: 250px;" />
      <select v-model="filterDestination" class="form-input" style="max-width: 150px;">
        <option value="">모든 지역</option>
        <option value="서울">서울</option>
        <option value="강원도">강원도</option>
        <option value="제주도">제주도</option>
        <option value="부산">부산</option>
      </select>
      <select v-model="filterStatus" class="form-input" style="max-width: 150px;">
        <option value="">모든 상태</option>
        <option value="saved">생성 완료</option>
        <option value="draft">계획 중</option>
      </select>
    </div>

    <!-- Grid -->
    <div v-if="paginatedCourses.length > 0" class="courses-grid">
      <div v-for="course in paginatedCourses" :key="course.id" class="course-card group" @click="router.push(`/courses/${course.id}`)">
        <div class="card-image-wrap">
          <img :src="getRandomImage(course.id)" alt="Course cover" class="card-image" />
          <div class="image-overlay"></div>
          <div class="card-badges">
            <span :class="['status-badge', getStatusLabel(course.status).class]">
              {{ getStatusLabel(course.status).text }}
            </span>
          </div>
          <button @click="(e) => deleteCourse(course.id, e)" class="delete-btn" title="일정 삭제">
            <Trash2 :size="18" />
          </button>
        </div>
        
        <div class="card-content">
          <h3 class="card-title">{{ course.title }}</h3>
          
          <div class="info-list">
            <div class="info-item">
              <MapPin :size="14" class="info-icon" />
              <span>{{ course.destination }}</span>
            </div>
            <div class="info-item">
              <Calendar :size="14" class="info-icon" />
              <span>생성: {{ new Date(course.created_at).toLocaleDateString() }} ({{ course.duration_days }}일간)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      조건에 맞는 코스가 없습니다.
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="totalPages > 1">
      <button class="btn-secondary" :disabled="currentPage === 1" @click="currentPage--">이전</button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <button class="btn-secondary" :disabled="currentPage === totalPages" @click="currentPage++">다음</button>
    </div>
  </div>
</template>

<style scoped>
.my-plans-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 0;
}

.header-area {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title {
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--text-bright);
  margin: 0 0 0.5rem 0;
}

.page-subtitle {
  color: var(--text-muted);
  margin: 0;
  font-size: 1.05rem;
}

.filter-area {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.form-input {
  width: 100%;
  background: #ffffff;
  border: 1px solid var(--border-muted);
  border-radius: 12px;
  padding: 0.7rem 1rem;
  color: var(--text-main);
  font-size: 0.95rem;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  outline: none;
  transition: all 0.2s;
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.courses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
}

.course-card {
  background: #ffffff;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid var(--border-muted);
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  flex-direction: column;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0,0,0,0.08);
  border-color: #cbd5e1;
}

.card-image-wrap {
  height: 200px;
  position: relative;
  overflow: hidden;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.course-card:hover .card-image {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(15, 23, 42, 0.6), transparent);
}

.card-badges {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  display: flex;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  backdrop-filter: blur(4px);
}

.badge-upcoming {
  background: rgba(59, 130, 246, 0.9);
}

.badge-planning {
  background: rgba(245, 158, 11, 0.9);
}

.delete-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0,0,0,0.4);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background 0.2s;
  backdrop-filter: blur(4px);
}

.course-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.9);
}

.card-content {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-bright);
  margin: 0 0 1rem 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.info-item {
  display: flex;
  align-items: center;
  color: var(--text-muted);
  font-size: 0.9rem;
  font-weight: 500;
}

.info-icon {
  margin-right: 0.5rem;
  color: #94a3b8;
}

.empty-state {
  text-align: center;
  padding: 5rem 0;
  color: var(--text-muted);
  font-size: 1.1rem;
  background: #ffffff;
  border-radius: 16px;
  border: 1px dashed var(--border-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-top: 3rem;
}

.page-info {
  color: var(--text-bright);
  font-weight: 700;
  font-size: 1.1rem;
}
</style>
