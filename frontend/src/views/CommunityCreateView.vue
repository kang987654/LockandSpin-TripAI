<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const title = ref('')
const content = ref('')
const selectedCourse = ref('')
const myCourses = ref([])

onMounted(async () => {
  try {
    const res = await axios.get(`${authStore.API_BASE}/api/courses/`, authStore.getHeaders())
    myCourses.value = res.data
  } catch (e) {
    console.error(e)
  }
})

const submitArticle = async () => {
  try {
    const data = {
      title: title.value,
      content: content.value,
      course: selectedCourse.value || null
    }
    const res = await axios.post(`${authStore.API_BASE}/api/community/articles/`, data, authStore.getHeaders())
    router.push(`/community/${res.data.id}`)
  } catch (e) {
    alert('게시글 작성 중 오류가 발생했습니다.')
  }
}
</script>

<template>
  <div>
    <div class="glass-card">
      <h2 style="color: var(--text-bright); margin-bottom: 2rem;">새 게시글 작성</h2>
      
      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">제목</label>
        <input type="text" v-model="title" class="form-input" placeholder="제목을 입력하세요" />
      </div>

      <div style="margin-bottom: 1.5rem;">
        <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">내용</label>
        <textarea v-model="content" class="form-input" rows="8" placeholder="내용을 입력하세요"></textarea>
      </div>

      <div style="margin-bottom: 2rem;">
        <label style="display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.3rem;">연동할 여행 코스 (선택)</label>
        <select v-model="selectedCourse" class="form-input">
          <option value="">-- 연동하지 않음 --</option>
          <option v-for="c in myCourses" :key="c.id" :value="c.id">
            {{ c.title }} ({{ c.destination }})
          </option>
        </select>
      </div>

      <div style="display: flex; gap: 1rem; justify-content: flex-end;">
        <button class="btn-secondary" @click="router.push('/community')">취소</button>
        <button class="btn-primary" @click="submitArticle" :disabled="!title || !content">작성 완료</button>
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
