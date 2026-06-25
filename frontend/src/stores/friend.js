import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './auth'

export const useFriendStore = defineStore('friend', () => {
  const friends = ref([])
  const pendingReceived = ref([])
  const pendingSent = ref([])
  const searchResults = ref([])
  const authStore = useAuthStore()

  const fetchFriends = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/users/friends/', {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      friends.value = res.data.friends
      pendingReceived.value = res.data.pending_received
      pendingSent.value = res.data.pending_sent
    } catch (err) {
      console.error('Failed to fetch friends', err)
    }
  }

  const searchUsers = async (query) => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/users/search/?q=${query}`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      searchResults.value = res.data
    } catch (err) {
      console.error('Search failed', err)
    }
  }

  const sendRequest = async (userId) => {
    try {
      await axios.post('http://127.0.0.1:8000/api/users/friends/request/', { user_id: userId }, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      await fetchFriends()
    } catch (err) {
      console.error('Failed to send request', err)
      alert(err.response?.data?.error || 'Failed to send request')
    }
  }

  const acceptRequest = async (friendshipId) => {
    try {
      await axios.post('http://127.0.0.1:8000/api/users/friends/accept/', { friendship_id: friendshipId }, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      await fetchFriends()
    } catch (err) {
      console.error('Failed to accept request', err)
    }
  }

  const rejectRequest = async (friendshipId) => {
    try {
      await axios.post('http://127.0.0.1:8000/api/users/friends/reject/', { friendship_id: friendshipId }, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      await fetchFriends()
    } catch (err) {
      console.error('Failed to reject request', err)
    }
  }

  return {
    friends,
    pendingReceived,
    pendingSent,
    searchResults,
    fetchFriends,
    searchUsers,
    sendRequest,
    acceptRequest,
    rejectRequest
  }
})
