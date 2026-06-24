import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const isLoggedIn = ref(!!token.value)
  const isLoggingIn = ref(false)

  const preferredThemes = ref(['healing', 'nature'])
  const preferredPace = ref('medium')
  const vetoCategories = ref([])
  const currentUser = ref(null)

  const getHeaders = () => ({
    headers: { Authorization: `Bearer ${token.value}` }
  })

  const loginUser = async (username, password) => {
    isLoggingIn.value = true
    try {
      const res = await axios.post(`${API_BASE}/api/auth/login/`, {
        username,
        password
      })
      token.value = res.data.access
      localStorage.setItem('token', token.value)
      isLoggedIn.value = true
      await fetchPreferences()
      return true
    } catch (err) {
      console.error('Login failed:', err)
      throw err
    } finally {
      isLoggingIn.value = false
    }
  }

  const registerUser = async (username, email, password) => {
    isLoggingIn.value = true
    try {
      await axios.post(`${API_BASE}/api/auth/register/`, {
        username,
        email,
        password
      })
      return await loginUser(username, password)
    } catch (err) {
      console.error('Registration failed:', err)
      throw err
    } finally {
      isLoggingIn.value = false
    }
  }

  const loginDemoUser = async () => {
    isLoggingIn.value = true
    const demoCredentials = {
      username: 'traveler_demo',
      email: 'demo@example.com',
      password: 'Password123!'
    }

    try {
      await loginUser(demoCredentials.username, demoCredentials.password)
    } catch (err) {
      try {
        await axios.post(`${API_BASE}/api/auth/register/`, demoCredentials)
        await loginUser(demoCredentials.username, demoCredentials.password)
      } catch (regErr) {
        console.error('Demo auth failed:', regErr)
      }
    } finally {
      isLoggingIn.value = false
    }
  }

  const logout = () => {
    token.value = ''
    localStorage.removeItem('token')
    isLoggedIn.value = false
    currentUser.value = null
  }

  const fetchPreferences = async () => {
    if (!token.value) return
    try {
      const res = await axios.get(`${API_BASE}/api/user/preference/`, getHeaders())
      preferredThemes.value = res.data.preferred_themes
      preferredPace.value = res.data.preferred_pace
      vetoCategories.value = res.data.veto_categories
      currentUser.value = {
        username: res.data.username,
        email: res.data.email
      }
    } catch (err) {
      console.error('Fetch preference failed:', err)
    }
  }

  const savePreferences = async () => {
    try {
      await axios.put(`${API_BASE}/api/user/preference/`, {
        preferred_themes: preferredThemes.value,
        preferred_pace: preferredPace.value,
        veto_categories: vetoCategories.value
      }, getHeaders())
      alert('선호 성향이 반영되었습니다! 다음 Re-spin 추천 시 반영됩니다.')
    } catch (err) {
      console.error('Save preference failed:', err)
    }
  }

  return { 
    API_BASE,
    token, isLoggedIn, isLoggingIn, currentUser,
    preferredThemes, preferredPace, vetoCategories, 
    loginUser, registerUser, loginDemoUser, logout, fetchPreferences, savePreferences, getHeaders 
  }
})
