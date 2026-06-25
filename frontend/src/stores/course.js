import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './auth'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'

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

  const createCourse = async (title, destination, duration, travelDate, preferences, departureTime, transportation) => {
    try {
      const res = await axios.post(`${API_BASE}/api/courses/`, {
        title: title,
        destination: destination,
        duration_days: duration,
        start_date: travelDate || new Date().toISOString().split('T')[0],
        departure_time: departureTime || '09:00',
        transportation: transportation || 'public',
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

  const triggerRespin = async (target_day = null) => {
    if (!activeCourse.value) return
    isSpinning.value = true

    activeCourse.value.slots.forEach(slot => {
      if (!slot.is_locked && (!target_day || slot.day_number === target_day)) {
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
        target_day: target_day,
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
    if (ws) {
      ws.onclose = null // Prevent old socket from triggering reconnect loop
      ws.close()
    }
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
      } else if (message.event === 'spin_update') {
        if (isSpinning.value) return // 내가 돌린 스핀이면 API 응답으로 처리되므로 무시
        
        const data = message.data
        if (activeCourse.value && activeCourse.value.slots) {
          const slot = activeCourse.value.slots.find(
            s => s.day_number === data.day_number && s.sequence === data.sequence
          )
          if (slot) {
            // 다른 사람의 스핀으로 인해 변경된 경우 애니메이션 트리거
            spinningSlots.value[`${data.day_number}_${data.sequence}`] = true
            setTimeout(() => {
              slot.place = data.place
              spinningSlots.value[`${data.day_number}_${data.sequence}`] = false
            }, 1200) // 애니메이션 지속 시간 후 데이터 갱신
          }
        }
      } else if (message.event === 'course_changed') {
        if (activeCourse.value) {
          loadCourse(activeCourse.value.id)
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

  const evaluateCourse = async () => {
    if (!activeCourse.value) return
    try {
      const res = await axios.post(`${API_BASE}/api/courses/${activeCourse.value.id}/generate_ai_comment/`, {}, authStore.getHeaders())
      activeCourse.value = res.data
      return res.data
    } catch (err) {
      console.error('Evaluate course failed:', err)
      throw err
    }
  }

  const keepPlace = async (courseId, placeId, dayNumber, sequence) => {
    try {
      await axios.post(`${API_BASE}/api/courses/${courseId}/keep_place/`, { place_id: placeId }, authStore.getHeaders())
      // 킵할 때는 다른 마음에 드는 슬롯이 변경되지 않도록 자동 리스핀을 호출하지 않습니다.
    } catch (err) {
      console.error('Keep place failed:', err)
    }
  }

  const excludePlace = async (courseId, placeId, dayNumber, sequence) => {
    try {
      await axios.post(`${API_BASE}/api/courses/${courseId}/exclude_place/`, { place_id: placeId }, authStore.getHeaders())
      // 제외할 때도 자동 리스핀을 막아, 사용자가 원하는 타이밍에 수동으로 리스핀하도록 합니다.
    } catch (err) {
      console.error('Exclude place failed:', err)
    }
  }

  const swapKeptPlace = async (courseId, placeId, dayNumber, sequence) => {
    try {
      await axios.post(`${API_BASE}/api/courses/${courseId}/swap_kept_place/`, {
        place_id: placeId,
        day_number: dayNumber,
        sequence: sequence
      }, authStore.getHeaders())
    } catch (err) {
      console.error('Swap kept place failed:', err)
    }
  }

  const removeKeptPlace = async (courseId, placeId) => {
    try {
      await axios.delete(`${API_BASE}/api/courses/${courseId}/remove_kept_place/${placeId}/`, authStore.getHeaders())
    } catch (err) {
      console.error('Remove kept place failed:', err)
    }
  }

  const swapSlotSequence = async (courseId, dayNumber, seq1, seq2) => {
    try {
      await axios.post(`${API_BASE}/api/courses/${courseId}/swap_slot_sequence/`, {
        day_number: dayNumber,
        seq1: seq1,
        seq2: seq2
      }, authStore.getHeaders())
    } catch (err) {
      console.error('Swap slot sequence failed:', err)
    }
  }

  const addSlot = async (courseId, dayNumber, category) => {
    try {
      await axios.post(`${API_BASE}/api/courses/${courseId}/add_slot/`, {
        day_number: dayNumber,
        category: category
      }, authStore.getHeaders())
      await loadCourse(courseId)
    } catch (err) {
      console.error('Add slot failed:', err)
    }
  }

  const deleteSlot = async (courseId, dayNumber, sequence) => {
    try {
      await axios.post(`${API_BASE}/api/courses/${courseId}/delete_slot/`, {
        day_number: dayNumber,
        sequence: sequence
      }, authStore.getHeaders())
      await loadCourse(courseId)
    } catch (err) {
      console.error('Delete slot failed:', err)
    }
  }

  return {
    activeCourse, coursesList, isSpinning, spinningSlots,
    fetchCourses, loadCourse, createCourse, triggerRespin, toggleLock, evaluateCourse, connectWebSocket, keepPlace, excludePlace, swapKeptPlace, removeKeptPlace, swapSlotSequence, addSlot, deleteSlot
  }
})
