<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import { User, Mail, Settings, Save, FolderHeart, BookOpen, MessageSquare } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

// 활동 내역 상태값
const activeTab = ref('courses')
const myCourses = ref([])
const myArticles = ref([])
const myComments = ref([])
const isActivityLoading = ref(false)

const fetchMyActivity = async () => {
  if (!authStore.token) return
  isActivityLoading.value = true
  try {
    const [coursesRes, articlesRes, commentsRes] = await Promise.all([
      axios.get(`${authStore.API_BASE}/api/courses/`, authStore.getHeaders()),
      axios.get(`${authStore.API_BASE}/api/community/articles/?my=true`, authStore.getHeaders()),
      axios.get(`${authStore.API_BASE}/api/community/comments/?my=true`, authStore.getHeaders())
    ])
    myCourses.value = coursesRes.data
    myArticles.value = articlesRes.data
    myComments.value = commentsRes.data
  } catch (err) {
    console.error('Failed to load my activities:', err)
  } finally {
    isActivityLoading.value = false
  }
}

onMounted(async () => {
  if (authStore.isLoggedIn) {
    await authStore.fetchPreferences()
    await fetchMyActivity()
  }
})
</script>

<template>
  <div style="max-width: 800px; margin: 2rem auto;">
    <div v-if="authStore.currentUser" class="glass-card" style="margin-bottom: 2rem;">
      <div style="display: flex; align-items: center; gap: 1.5rem; border-bottom: 1px solid var(--border-muted); padding-bottom: 1.5rem; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; justify-content: center; background: hsla(265, 80%, 65%, 0.15); width: 70px; height: 70px; border-radius: 50%; border: 2px solid var(--color-primary);">
          <User :size="36" style="color: var(--color-primary);" />
        </div>
        <div>
          <h2 style="color: var(--text-bright); font-size: 1.8rem; font-weight: 700; margin-bottom: 0.3rem;">
            {{ authStore.currentUser.username }}
          </h2>
          <p style="color: var(--text-muted); font-size: 0.95rem; display: flex; align-items: center; gap: 0.4rem;">
            <Mail :size="16" />
            {{ authStore.currentUser.email }}
          </p>
        </div>
      </div>

      <!-- Preference Settings -->
      <div>
        <h3 style="margin-bottom: 1.5rem; color: var(--text-bright); display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;">
          <Settings :size="20" style="color: var(--color-accent);" />
          🧬 내 여행 성향 및 기피 필터 설정
        </h3>

        <!-- Theme Chips -->
        <div style="margin-bottom: 1.5rem;">
          <label style="display: block; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.6rem; font-weight: 600;">선호 테마</label>
          <div style="display: flex; flex-wrap: wrap; gap: 0.6rem;">
            <label v-for="theme in ['healing', 'nature', 'food', 'activity', 'culture', 'traditional']" :key="theme" class="theme-chip" :class="{active: authStore.preferredThemes.includes(theme)}">
              <input type="checkbox" :value="theme" v-model="authStore.preferredThemes" style="display:none;" />
              #{{ theme === 'healing' ? '힐링' : theme === 'nature' ? '자연' : theme === 'food' ? '맛집' : theme === 'activity' ? '액티비티' : theme === 'culture' ? '문화/역사' : '전통' }}
            </label>
          </div>
          <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.4rem;">선택한 테마의 장소가 추천될 확률이 높아집니다.</p>
        </div>

        <!-- Pace Selector -->
        <div style="margin-bottom: 1.5rem;">
          <label style="display: block; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.6rem; font-weight: 600;">선호 여행 페이스</label>
          <div style="display: flex; gap: 1rem;">
            <label v-for="pace in [{val:'slow', label:'느긋하게'}, {val:'medium', label:'적당히'}, {val:'fast', label:'빡빡하게'}]" :key="pace.val" class="pace-option" :class="{active: authStore.preferredPace === pace.val}">
              <input type="radio" :value="pace.val" v-model="authStore.preferredPace" style="display:none;" />
              {{ pace.label }}
            </label>
          </div>
        </div>

        <!-- Veto Chips -->
        <div style="margin-bottom: 2rem;">
          <label style="display: block; font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.6rem; font-weight: 600;">기피 카테고리 (추천 제외)</label>
          <div style="display: flex; flex-wrap: wrap; gap: 0.6rem;">
            <label v-for="cat in ['restaurant', 'cafe', 'spot', 'activity']" :key="cat" class="veto-chip" :class="{active: authStore.vetoCategories.includes(cat)}">
              <input type="checkbox" :value="cat" v-model="authStore.vetoCategories" style="display:none;" />
              {{ cat === 'spot' ? '관광지' : cat === 'restaurant' ? '음식점' : cat === 'cafe' ? '카페' : '액티비티' }} 제외
            </label>
          </div>
          <p style="font-size: 0.75rem; color: hsl(0, 80%, 65%); margin-top: 0.4rem;">선택한 종류의 장소는 일정 추천 및 Re-spin 후보지에서 원천 배제됩니다.</p>
        </div>

        <button class="btn-primary" style="width: 100%; justify-content: center; padding: 0.8rem; font-size: 1rem; margin-bottom: 2rem;" @click="authStore.savePreferences">
          <Save :size="18" />
          성향 설정 저장하기
        </button>

        <!-- User Activities Logs -->
        <div style="margin-top: 3rem; border-top: 1px solid var(--border-muted); padding-top: 2rem;">
          <h3 style="margin-bottom: 1.5rem; color: var(--text-bright); display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;">
            📁 나의 활동 내역
          </h3>

          <!-- Tab Buttons -->
          <div style="display: flex; gap: 0.5rem; border-bottom: 1px solid var(--border-muted); padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
            <button v-for="tab in [{id:'courses', label:'내 여행 코스', icon:FolderHeart}, {id:'articles', label:'작성한 게시글', icon:BookOpen}, {id:'comments', label:'작성한 댓글', icon:MessageSquare}]" 
                    :key="tab.id" 
                    class="tab-btn" 
                    :class="{active: activeTab === tab.id}" 
                    @click="activeTab = tab.id"
                    type="button">
              <component :is="tab.icon" :size="16" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Activity Contents -->
          <div v-if="isActivityLoading" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            활동 정보를 불러오는 중...
          </div>
          <div v-else>
            <!-- 1. Courses List -->
            <div v-if="activeTab === 'courses'">
              <div v-if="myCourses.length === 0" class="no-activity">생성하거나 초대받은 여행 코스가 없습니다.</div>
              <div v-else class="activity-list">
                <div v-for="c in myCourses" :key="c.id" class="activity-item" @click="router.push(`/courses/${c.id}`)">
                  <div>
                    <h4 style="color: var(--text-bright); margin-bottom: 0.2rem; font-size: 1rem; text-align: left;">{{ c.title }}</h4>
                    <p style="font-size: 0.8rem; color: var(--text-muted); text-align: left; margin: 0;">목적지: {{ c.destination }} | 기간: {{ c.duration_days }}일간</p>
                  </div>
                  <span style="font-size: 0.75rem; color: var(--color-accent); font-weight: bold;">이동하기 ➔</span>
                </div>
              </div>
            </div>

            <!-- 2. Articles List -->
            <div v-if="activeTab === 'articles'">
              <div v-if="myArticles.length === 0" class="no-activity">작성한 커뮤니티 게시글이 없습니다.</div>
              <div v-else class="activity-list">
                <div v-for="a in myArticles" :key="a.id" class="activity-item" @click="router.push(`/community/${a.id}`)">
                  <div>
                    <h4 style="color: var(--text-bright); margin-bottom: 0.2rem; font-size: 1rem; text-align: left;">{{ a.title }}</h4>
                    <p style="font-size: 0.8rem; color: var(--text-muted); text-align: left; margin: 0;">작성일: {{ new Date(a.created_at).toLocaleDateString() }} | 댓글 수: {{ a.comment_count }}</p>
                  </div>
                  <span style="font-size: 0.75rem; color: var(--color-accent); font-weight: bold;">읽어보기 ➔</span>
                </div>
              </div>
            </div>

            <!-- 3. Comments List -->
            <div v-if="activeTab === 'comments'">
              <div v-if="myComments.length === 0" class="no-activity">작성한 댓글이 없습니다.</div>
              <div v-else class="activity-list">
                <div v-for="co in myComments" :key="co.id" class="activity-item" @click="router.push(`/community/${co.article}`)">
                  <div style="flex: 1; text-align: left;">
                    <p style="color: var(--text-bright); font-size: 0.95rem; margin-bottom: 0.3rem; font-weight: 500;">
                      &ldquo;{{ co.content }}&rdquo;
                    </p>
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin: 0;">
                      원문: <span style="color: var(--color-primary); font-weight: 600;">{{ co.article_title || '게시글' }}</span> | 작성일: {{ new Date(co.created_at).toLocaleDateString() }}
                    </p>
                  </div>
                  <span style="font-size: 0.75rem; color: var(--color-accent); font-weight: bold;">본문 보기 ➔</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="glass-card" style="text-align: center; padding: 4rem; color: var(--text-muted);">
      프로필 정보를 불러오는 중...
    </div>
  </div>
</template>

<style scoped>
.theme-chip, .veto-chip, .pace-option {
  cursor: pointer;
  background: hsla(230, 15%, 18%, 0.6);
  border: 1px solid var(--border-muted);
  color: var(--text-muted);
  padding: 8px 16px;
  border-radius: 99px;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s;
  user-select: none;
}
.theme-chip:hover, .veto-chip:hover, .pace-option:hover {
  border-color: var(--text-main);
  background: hsla(230, 15%, 22%, 0.8);
}
.theme-chip.active {
  background: hsla(265, 80%, 65%, 0.15);
  border-color: var(--color-primary);
  color: var(--color-primary);
  box-shadow: 0 0 10px hsla(265, 80%, 65%, 0.2);
}
.veto-chip.active {
  background: hsla(0, 80%, 60%, 0.15);
  border-color: hsl(0, 80%, 60%);
  color: hsl(0, 80%, 60%);
  box-shadow: 0 0 10px hsla(0, 80%, 60%, 0.2);
}
.pace-option.active {
  background: hsla(190, 90%, 50%, 0.15);
  border-color: var(--color-accent);
  color: var(--color-accent);
  box-shadow: 0 0 10px hsla(190, 90%, 50%, 0.2);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  color: var(--text-muted);
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  cursor: pointer;
  font-size: 0.9rem;
  border-radius: 8px;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: var(--text-bright);
  background: hsla(230, 15%, 20%, 0.4);
}
.tab-btn.active {
  color: var(--color-primary);
  background: hsla(265, 80%, 65%, 0.1);
}
.no-activity {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  background: hsla(230, 15%, 8%, 0.2);
  border-radius: 8px;
  border: 1px dashed var(--border-muted);
}
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}
.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.2rem;
  background: hsla(230, 15%, 8%, 0.4);
  border: 1px solid var(--border-muted);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.activity-item:hover {
  border-color: var(--color-primary);
  background: hsla(230, 15%, 12%, 0.6);
  transform: translateX(4px);
}
</style>
