<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const article = ref(null)
const newComment = ref('')

const fetchArticle = async () => {
  try {
    const res = await axios.get(`${authStore.API_BASE}/api/community/articles/${route.params.id}/`, authStore.getHeaders())
    article.value = res.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchArticle()
})

const submitComment = async () => {
  if (!newComment.value.trim()) return
  try {
    await axios.post(`${authStore.API_BASE}/api/community/articles/${route.params.id}/comments/`, {
      content: newComment.value
    }, authStore.getHeaders())
    newComment.value = ''
    fetchArticle()
  } catch (e) {
    alert('댓글 작성 중 오류가 발생했습니다.')
  }
}
</script>

<template>
  <div>
    <div v-if="article" class="glass-card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-muted); padding-bottom: 1.5rem;">
        <div>
          <h2 style="color: var(--text-bright); margin-bottom: 0.5rem;">{{ article.title }}</h2>
          <p style="color: var(--text-muted); font-size: 0.9rem;">
            작성자: {{ article.user?.username }} | 작성일: {{ new Date(article.created_at).toLocaleString() }}
          </p>
        </div>
        <button class="btn-secondary" @click="router.push('/community')">목록으로</button>
      </div>

      <div v-if="article.course" style="margin-bottom: 2rem; padding: 1rem; background: hsla(265, 90%, 65%, 0.1); border-radius: 8px; border: 1px solid var(--color-primary); cursor: pointer;" @click="router.push(`/courses/${article.course}`)">
        <h4 style="color: var(--color-primary); margin-bottom: 0.3rem;">🔗 연동된 여행 코스 보러가기</h4>
        <p style="color: var(--text-bright); font-size: 0.9rem; margin: 0;">&ldquo;{{ article.course_title || '상세 일정' }}&rdquo; 보러 가기 (여기를 클릭하세요)</p>
      </div>

      <div style="color: var(--text-bright); line-height: 1.6; margin-bottom: 3rem; white-space: pre-wrap;">
        {{ article.content }}
      </div>

      <hr style="border: 0; border-top: 1px solid var(--border-muted); margin-bottom: 2rem;" />

      <h3 style="color: var(--text-bright); margin-bottom: 1.5rem;">댓글 ({{ article.comments?.length || 0 }})</h3>

      <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
        <input type="text" v-model="newComment" class="form-input" placeholder="댓글을 남겨보세요..." @keyup.enter="submitComment" style="flex: 1;" />
        <button class="btn-primary" @click="submitComment" :disabled="!newComment">등록</button>
      </div>

      <div v-if="article.comments && article.comments.length > 0">
        <div v-for="comment in article.comments" :key="comment.id" style="padding: 1rem; background: var(--bg-app); border-radius: 8px; margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <strong style="color: var(--text-bright);">{{ comment.user?.username }}</strong>
            <span style="color: var(--text-muted); font-size: 0.8rem;">{{ new Date(comment.created_at).toLocaleString() }}</span>
          </div>
          <p style="color: var(--text-main); margin: 0;">{{ comment.content }}</p>
        </div>
      </div>
    </div>
    <div v-else style="text-align: center; color: var(--text-muted); padding: 4rem;">
      게시글을 불러오는 중...
    </div>
  </div>
</template>

<style scoped>
.form-input {
  flex: 1;
  background: hsla(230, 15%, 8%, 0.6);
  border: 1px solid var(--border-muted);
  border-radius: 8px;
  padding: 0.8rem;
  color: var(--text-bright);
  font-size: 0.95rem;
}
</style>
