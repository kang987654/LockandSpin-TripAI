import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import CourseListView from '../views/CourseListView.vue'
import CourseDetailView from '../views/CourseDetailView.vue'
import CommunityListView from '../views/CommunityListView.vue'
import CommunityCreateView from '../views/CommunityCreateView.vue'
import CommunityDetailView from '../views/CommunityDetailView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/ProfileView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/courses',
      name: 'courses',
      component: CourseListView,
      meta: { requiresAuth: true }
    },
    {
      path: '/courses/:id',
      name: 'course-detail',
      component: CourseDetailView,
      meta: { requiresAuth: true }
    },
    {
      path: '/community',
      name: 'community',
      component: CommunityListView
    },
    {
      path: '/community/write',
      name: 'community-write',
      component: CommunityCreateView,
      meta: { requiresAuth: true }
    },
    {
      path: '/community/:id',
      name: 'community-detail',
      component: CommunityDetailView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation Guard for Authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // If token exists but currentUser is null (refresh page etc.), fetch details
  if (authStore.token && !authStore.currentUser) {
    await authStore.fetchPreferences()
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if ((to.name === 'login' || to.name === 'register') && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
