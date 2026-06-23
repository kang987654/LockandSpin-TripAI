import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './auth'

const API_BASE = 'http://localhost:8000'
const WS_BASE = 'ws://localhost:8000'

export const useCourseStore = defineStore('course', () => {
  const authStore = useAuthStore()
  const activeCourse = ref(null)
  const coursesList = ref([])
  const isSpinning = ref(false)
  const spinningSlots = ref({})

  let ws = null

  const fetchCourses = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/courses/`, authStore.getHeaders())
      coursesList.value = res.data
    } catch (err) {
      console.error('Fetch courses failed:', err)
    }
  }

  const loadCourse = async (courseId) => {
    try {
      const res = await axios.get(`${API_BASE}/api/courses/${courseId}/`, authStore.getHeaders())
      activeCourse.value = res.data
      connectWebSocket(courseId)
    } catch (err) {
      console.error('Load course failed:', err)
    }
  }

  const createCourse = async (title, destination, duration, travelDate, preferences) => {
    try {
      const res = await axios.post(`${API_BASE}/api/courses/`, {
        title: title,
        destination: destination,
        duration_days: duration,
        start_date: travelDate || new Date().toISOString().split('T')[0],
        preferences: preferences || ''
      }, authStore.getHeaders())
      activeCourse.value = res.data
      await fetchCourses()
      connectWebSocket(res.data.id)
      return res.data
    } catch (err) {
      console.error('Create course failed:', err)
      throw err
    }
  }

  const triggerRespin = async () => {
    if (!activeCourse.value) return
    isSpinning.value = true

    activeCourse.value.slots.forEach(slot => {
      if (!slot.is_locked) {
        spinningSlots.value[`${slot.day_number}_${slot.sequence}`] = true
      }
    })

    const requestSlots = activeCourse.value.slots.map(s => ({
      day_number: s.day_number,
      sequence: s.sequence,
      is_locked: s.is_locked,
      place_id: s.place.id
    }))

    try {
      await new Promise(resolve => setTimeout(resolve, 1200))
      const res = await axios.post(`${API_BASE}/api/courses/${activeCourse.value.id}/spin/`, {
        slots: requestSlots
      }, authStore.getHeaders())
      activeCourse.value = res.data
    } catch (err) {
      console.error('Re-spin failed:', err)
    } finally {
      isSpinning.value = false
      spinningSlots.value = {}
    }
  }

  const toggleLock = (slot) => {
    const newLockState = !slot.is_locked
    slot.is_locked = newLockState

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        event: 'toggle_lock',
        data: {
          day_number: slot.day_number,
          sequence: slot.sequence,
          is_locked: newLockState
        }
      }))
    }
  }

  const connectWebSocket = (courseId) => {
    if (ws) ws.close()
    ws = new WebSocket(`${WS_BASE}/ws/courses/${courseId}/`)

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.event === 'toggle_lock') {
        const data = message.data
        if (activeCourse.value && activeCourse.value.slots) {
          const slot = activeCourse.value.slots.find(
            s => s.day_number === data.day_number && s.sequence === data.sequence
          )
          if (slot) {
            slot.is_locked = data.is_locked
          }
        }
      }
    }

    ws.onclose = () => {
      console.log('WS Connection closed. Reconnecting in 3s...')
      setTimeout(() => {
        if (activeCourse.value && activeCourse.value.id === courseId) {
          connectWebSocket(courseId)
        }
      }, 3000)
    }
  }

  return {
    activeCourse, coursesList, isSpinning, spinningSlots,
    fetchCourses, loadCourse, createCourse, triggerRespin, toggleLock
  }
})
