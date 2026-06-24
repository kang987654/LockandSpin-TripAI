<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const articles = ref([])

onMounted(async () => {
  try {
    const res = await axios.get(`${authStore.API_BASE}/api/community/articles/`, authStore.getHeaders())
    articles.value = res.data
  } catch (e) {
    console.error(e)
  }
})
</script>

<template>
  <div>
    <div class="glass-card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h2 style="color: var(--text-bright);">여행 커뮤니티</h2>
        <button class="btn-primary" @click="router.push('/community/write')">✏️ 글 작성하기</button>
      </div>

      <div v-if="articles.length === 0" style="color: var(--text-muted); text-align: center; padding: 2rem;">
        첫 번째 게시글을 작성해 보세요!
      </div>

      <div class="articles-grid">
        <div v-for="article in articles" :key="article.id" class="glass-card article-item" @click="router.push(`/community/${article.id}`)">
          <h4 style="color: var(--text-bright); margin-bottom: 0.5rem;">{{ article.title }}</h4>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.5rem;">
            작성자: {{ article.user?.username }} | 댓글 수: {{ article.comment_count }}
          </p>
          <div v-if="article.course" style="font-size: 0.8rem; color: var(--color-primary);">
            🔗 연동된 코스: {{ article.course_title || '상세 보기' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}
.article-item {
  margin-bottom: 0;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.article-item:hover {
  transform: translateY(-4px);
}
</style>
