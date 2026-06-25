<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h3>친구 관리 및 초대</h3>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="tabs">
        <button :class="{ active: currentTab === 'search' }" @click="currentTab = 'search'">사용자 검색</button>
        <button :class="{ active: currentTab === 'friends' }" @click="currentTab = 'friends'">내 친구</button>
        <button :class="{ active: currentTab === 'requests' }" @click="currentTab = 'requests'">
          받은 요청
          <span v-if="friendStore.pendingReceived.length > 0" class="badge">{{ friendStore.pendingReceived.length }}</span>
        </button>
      </div>

      <div class="tab-content" v-if="currentTab === 'search'">
        <div class="search-bar">
          <input type="text" v-model="searchQuery" @keyup.enter="search" placeholder="이메일 또는 이름으로 검색..." />
          <button @click="search">검색</button>
        </div>
        <ul class="user-list">
          <li v-for="user in friendStore.searchResults" :key="user.id">
            <div class="user-info">
              <div class="avatar">{{ user.username.charAt(0).toUpperCase() }}</div>
              <div>
                <span class="name">{{ user.username }}</span>
                <span class="email">{{ user.email }}</span>
              </div>
            </div>
            <button class="action-btn" :class="{ disabled: isRequestSent(user.id) }" :disabled="isRequestSent(user.id)" @click="friendStore.sendRequest(user.id)">
              {{ isRequestSent(user.id) ? '요청 완료' : '요청 보내기' }}
            </button>
          </li>
          <li v-if="friendStore.searchResults.length === 0" class="empty-state">검색 결과가 없습니다.</li>
        </ul>
      </div>

      <div class="tab-content" v-if="currentTab === 'friends'">
        <ul class="user-list">
          <li v-for="friendship in friendStore.friends" :key="friendship.id">
            <div class="user-info">
              <div class="avatar">{{ getFriend(friendship).username.charAt(0).toUpperCase() }}</div>
              <div>
                <span class="name">{{ getFriend(friendship).username }}</span>
                <span class="email">{{ getFriend(friendship).email }}</span>
              </div>
            </div>
            <button v-if="showInvite" class="action-btn primary" @click="inviteToCourse(getFriend(friendship).email)">코스 초대</button>
          </li>
          <li v-if="friendStore.friends.length === 0" class="empty-state">아직 등록된 친구가 없습니다.</li>
        </ul>
      </div>

      <div class="tab-content" v-if="currentTab === 'requests'">
        <ul class="user-list">
          <li v-for="req in friendStore.pendingReceived" :key="req.id">
            <div class="user-info">
              <div class="avatar">{{ req.from_user.username.charAt(0).toUpperCase() }}</div>
              <div>
                <span class="name">{{ req.from_user.username }}</span>
                <span class="email">{{ req.from_user.email }}</span>
              </div>
            </div>
            <div class="actions">
              <button class="action-btn primary" @click="friendStore.acceptRequest(req.id)">수락</button>
              <button class="action-btn danger" @click="friendStore.rejectRequest(req.id)">거절</button>
            </div>
          </li>
          <li v-if="friendStore.pendingReceived.length === 0" class="empty-state">받은 친구 요청이 없습니다.</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFriendStore } from '../stores/friend'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const props = defineProps({
  isOpen: Boolean,
  showInvite: Boolean,
  courseId: Number
})

const emit = defineEmits(['close', 'invited'])

const friendStore = useFriendStore()
const authStore = useAuthStore()
const currentTab = ref('friends')
const searchQuery = ref('')

onMounted(() => {
  friendStore.fetchFriends()
})

const close = () => {
  emit('close')
}

const search = () => {
  if (searchQuery.value.trim()) {
    friendStore.searchUsers(searchQuery.value)
  }
}

const getFriend = (friendship) => {
  return friendship.from_user.email === authStore.currentUser?.email ? friendship.to_user : friendship.from_user
}

const isRequestSent = (userId) => {
  return friendStore.pendingSent.some(req => req.to_user.id === userId) || friendStore.friends.some(f => getFriend(f).id === userId)
}

const inviteToCourse = async (email) => {
  try {
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
    await axios.post(`${API_BASE}/api/courses/${props.courseId}/members/`, { email }, authStore.getHeaders())
    alert('친구를 코스에 초대했습니다!')
    emit('invited')
    close()
  } catch (err) {
    alert(err.response?.data?.email || err.response?.data?.detail || '초대에 실패했습니다.')
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  width: 90%;
  max-width: 500px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #888;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}

.tabs button {
  flex: 1;
  padding: 15px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-weight: 500;
  color: #666;
  position: relative;
}

.tabs button.active {
  color: #007bff;
  border-bottom-color: #007bff;
}

.badge {
  background: #ff4757;
  color: white;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 5px;
}

.tab-content {
  padding: 20px;
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.search-bar button {
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.user-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.user-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.name {
  display: block;
  font-weight: 600;
  color: #333;
}

.email {
  display: block;
  font-size: 0.8rem;
  color: #888;
}

.actions {
  display: flex;
  gap: 5px;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.action-btn.primary {
  background: #007bff;
  color: white;
  border: none;
}

.action-btn.disabled {
  background: #f1f5f9;
  color: #94a3b8;
  border: 1px solid #e2e8f0;
  cursor: not-allowed;
}

.action-btn.danger {
  background: #ff4757;
  color: white;
  border: none;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 30px 0;
  background: transparent !important;
}
</style>
