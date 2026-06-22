<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useCourseStore } from '../stores/course'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'
import PlaceDetailModal from '../components/PlaceDetailModal.vue'

const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()

const kakaoKey = ref('')
const map = ref(null)
const markers = ref([])
const activeInfowindows = ref([])
const pathPolyline = ref(null)
const isMapLoaded = ref(false)
const hasCenteredOnce = ref(false)

const selectedPlace = ref(null)
const isModalOpen = ref(false)

onMounted(async () => {
  await courseStore.loadCourse(route.params.id)
  
  // 백엔드 API로부터 카카오 API Key 동적 취득
  try {
    const res = await axios.get(`${authStore.API_BASE}/api/config/`, authStore.getHeaders())
    kakaoKey.value = res.data.kakao_javascript_key
  } catch (err) {
    console.error('Failed to load Kakao API key:', err)
  }

  if (kakaoKey.value) {
    await loadKakaoMapScript(kakaoKey.value)
    initMap()
  }
})

const loadKakaoMapScript = (appKey) => {
  return new Promise((resolve) => {
    if (window.kakao && window.kakao.maps) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=${appKey}`
    script.onload = () => {
      window.kakao.maps.load(() => resolve())
    }
    document.head.appendChild(script)
  })
}

const initMap = () => {
  const container = document.getElementById('map')
  if (!container || !window.kakao || !window.kakao.maps) return
  const options = { center: new window.kakao.maps.LatLng(37.5665, 126.9780), level: 5 }
  map.value = new window.kakao.maps.Map(container, options)
  isMapLoaded.value = true
  updateMapRoute()
}

const updateMapRoute = () => {
  if (!isMapLoaded.value || !map.value || !courseStore.activeCourse?.slots) return

  markers.value.forEach(m => m.setMap(null))
  markers.value = []
  activeInfowindows.value.forEach(iw => iw.close())
  activeInfowindows.value = []
  if (pathPolyline.value) { pathPolyline.value.setMap(null); pathPolyline.value = null }

  const allSlots = [...courseStore.activeCourse.slots].sort((a, b) => {
    if (a.day_number !== b.day_number) return a.day_number - b.day_number
    return a.sequence - b.sequence
  })

  if (allSlots.length > 0 && !hasCenteredOnce.value) {
    map.value.setCenter(new window.kakao.maps.LatLng(allSlots[0].place.latitude, allSlots[0].place.longitude))
    hasCenteredOnce.value = true
  }

  allSlots.forEach((slot) => {
    const position = new window.kakao.maps.LatLng(slot.place.latitude, slot.place.longitude)
    
    let markerImage = null
    if (window.kakao && window.kakao.maps && window.kakao.maps.MarkerImage) {
      const imageSize = new window.kakao.maps.Size(24, 35)
      // locked면 별표 마커, unlocked면 기본 마커 사용
      markerImage = new window.kakao.maps.MarkerImage(
        slot.is_locked 
          ? 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/markerStar.png' 
          : 'https://t1.daumcdn.net/mapjsapi/images/2x/marker.png',
        imageSize
      )
    }

    const marker = new window.kakao.maps.Marker({
      position,
      map: map.value,
      title: `${slot.day_number}일차 [${slot.sequence}] ${slot.place.name}`,
      image: markerImage
    })

    // 마커 클릭 시 정보창(InfoWindow) 제공
    const iwContent = `
      <div style="padding:10px; min-width:180px; color:#111; font-family:sans-serif; text-align:left;">
        <h5 style="margin:0 0 4px 0; font-size:11px; color:var(--color-primary, #8b5cf6);">Day ${slot.day_number} - 일정 ${slot.sequence}</h5>
        <h4 style="margin:0 0 6px 0; font-size:13px; font-weight:700;">${slot.place.name}</h4>
        <p style="margin:0 0 6px 0; font-size:11px; color:#555; line-height:1.3;">${slot.place.address}</p>
        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #eee; padding-top:6px;">
          <span style="font-size:10px; font-weight:600; padding:2px 6px; border-radius:4px; background:${slot.is_locked ? '#d1fae5' : '#f3f4f6'}; color:${slot.is_locked ? '#065f46' : '#374151'};">
            ${slot.is_locked ? '🔒 고정됨' : '🔓 미고정'}
          </span>
        </div>
      </div>
    `
    const infowindow = new window.kakao.maps.InfoWindow({
      content: iwContent,
      removable: true
    })

    window.kakao.maps.event.addListener(marker, 'click', () => {
      activeInfowindows.value.forEach(iw => iw.close())
      infowindow.open(map.value, marker)
      activeInfowindows.value = [infowindow]
    })

    markers.value.push(marker)
  })

  // 폴리라인: 전체 경로를 순서대로 실선 연결
  const linePath = allSlots.map(s => new window.kakao.maps.LatLng(s.place.latitude, s.place.longitude))
  if (linePath.length > 1) {
    pathPolyline.value = new window.kakao.maps.Polyline({
      path: linePath,
      strokeWeight: 4,
      strokeColor: '#aa3bff',
      strokeOpacity: 0.8,
      strokeStyle: 'solid'
    })
    pathPolyline.value.setMap(map.value)
  }

  if (allSlots.length > 0) {
    const bounds = new window.kakao.maps.LatLngBounds()
    allSlots.forEach(s => bounds.extend(new window.kakao.maps.LatLng(s.place.latitude, s.place.longitude)))
    map.value.setBounds(bounds)
  }
}

watch(() => courseStore.activeCourse, () => updateMapRoute(), { deep: true })

const slotsByDay = computed(() => {
  if (!courseStore.activeCourse?.slots) return {}
  const groups = {}
  courseStore.activeCourse.slots.forEach(slot => {
    if (!groups[slot.day_number]) groups[slot.day_number] = []
    groups[slot.day_number].push(slot)
  })
  Object.values(groups).forEach(g => g.sort((a, b) => a.sequence - b.sequence))
  return groups
})

const getSeqLabel = (seq) => ['오전 명소 ☀️', '점심 식사 🍲', '오후 카페 ☕️', '저녁 식사 🍖'][seq - 1] || '일정'

const openPlaceModal = (place) => {
  selectedPlace.value = place
  isModalOpen.value = true
}

// 소셜 스핀 공동 편집 멤버 상태 및 메소드
const members = ref([])
const inviteEmail = ref('')
const isInviting = ref(false)

const fetchMembers = async () => {
  try {
    const res = await axios.get(`${authStore.API_BASE}/api/courses/${route.params.id}/members/`, authStore.getHeaders())
    members.value = res.data
  } catch (err) {
    console.error('Failed to fetch course members:', err)
  }
}

const inviteMember = async () => {
  if (!inviteEmail.value.trim()) return
  isInviting.value = true
  try {
    await axios.post(`${authStore.API_BASE}/api/courses/${route.params.id}/members/`, {
      email: inviteEmail.value,
      role: 'editor'
    }, authStore.getHeaders())
    inviteEmail.value = ''
    alert('동행자가 성공적으로 초대되었습니다!')
    await fetchMembers()
  } catch (err) {
    console.error('Failed to invite member:', err)
    const errMsg = err.response?.data?.email || err.response?.data?.detail || '초대에 실패했습니다.'
    alert(Array.isArray(errMsg) ? errMsg[0] : errMsg)
  } finally {
    isInviting.value = false
  }
}

const removeMember = async (userId) => {
  if (!confirm('이 동행자를 그룹에서 제외하시겠습니까?')) return
  try {
    await axios.delete(`${authStore.API_BASE}/api/courses/${route.params.id}/members/${userId}/`, authStore.getHeaders())
    alert('제외되었습니다.')
    await fetchMembers()
  } catch (err) {
    console.error('Failed to remove member:', err)
    alert(err.response?.data?.detail || '동행자 제외에 실패했습니다.')
  }
}

const isCourseOwner = computed(() => {
  const myMemberInfo = members.value.find(m => m.username === 'traveler_demo')
  return myMemberInfo && myMemberInfo.role === 'owner'
})

// 마운트 시 멤버 로드 추가
watch(() => courseStore.activeCourse, async (newVal) => {
  if (newVal && members.value.length === 0) {
    await fetchMembers()
  }
})
</script>

<template>
  <div v-if="courseStore.activeCourse" class="glass-card" style="margin-bottom: 2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-muted); padding-bottom: 1rem; margin-bottom: 1.5rem;">
      <div>
        <h2 style="color: var(--text-bright);">{{ courseStore.activeCourse.title }}</h2>
        <p class="text-muted">목적지: {{ courseStore.activeCourse.destination }} | {{ courseStore.activeCourse.duration_days }}일간</p>
      </div>
      <button class="btn-primary" :disabled="courseStore.isSpinning" @click="courseStore.triggerRespin" style="padding: 0.9rem 2.2rem; font-size: 1.05rem;">
        <span style="font-size: 1.2rem;">🔄</span> {{ courseStore.isSpinning ? '슬롯 재조합 중...' : 'Re-spin!' }}
      </button>
    </div>

    <div class="planner-layout">
      <!-- Left side: Slots -->
      <div class="slots-container">
        <div v-for="(slots, day) in slotsByDay" :key="day" style="margin-bottom: 2.5rem;">
          <h3 style="color: var(--color-accent); margin-bottom: 1rem;">Day {{ day }}</h3>
          <div class="slot-board">
            <div v-for="slot in slots" :key="slot.sequence" class="slot-card" :class="{ locked: slot.is_locked, 'spinning-anim': courseStore.spinningSlots[`${slot.day_number}_${slot.sequence}`] }" @click="openPlaceModal(slot.place)">
              <div class="lock-toggle" @click.stop="courseStore.toggleLock(slot)">
                {{ slot.is_locked ? '🔒' : '🔓' }}
              </div>
              <div style="font-size: 0.8rem; font-weight: 600; color: var(--color-accent); text-transform: uppercase; margin-bottom: 0.5rem;">
                {{ getSeqLabel(slot.sequence) }}
              </div>
              <h4 style="font-size: 1.2rem; font-weight: 700; color: var(--text-bright); margin-bottom: 0.4rem;">
                {{ slot.place.name }}
              </h4>
              <p style="font-size: 0.8rem; color: var(--color-success); margin-bottom: 0.4rem;">📍 {{ slot.place.address }}</p>
              <p style="font-size: 0.85rem; color: var(--text-muted);">{{ slot.place.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side: Map & Social Spin -->
      <div class="map-section">
        <h3 style="color: var(--text-bright); margin-bottom: 1rem;">🗺️ 지도 시각화</h3>
        <div id="map" class="map-container" style="background-color: hsl(230, 20%, 10%); margin-top: 0; margin-bottom: 1.5rem;"></div>

        <!-- Social Spin Member Management Panel -->
        <div class="glass-card" style="padding: 1.5rem; background: hsla(230, 20%, 10%, 0.5); border: 1px solid var(--border-muted);">
          <h3 style="color: var(--text-bright); font-size: 1.15rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
            👥 소셜 스핀 공동 편집자
          </h3>
          
          <!-- Member List -->
          <div style="display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1.2rem;">
            <div v-for="member in members" :key="member.user_id" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.8rem; background: hsla(230, 15%, 8%, 0.4); border-radius: 8px; border: 1px solid var(--border-muted);">
              <div>
                <span style="color: var(--text-bright); font-weight: 600; font-size: 0.9rem;">{{ member.username }}</span>
                <span class="badge-role" :class="member.role" style="margin-left: 0.5rem; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                  {{ member.role === 'owner' ? '소유자' : '편집자' }}
                </span>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.15rem;">{{ member.email }}</div>
              </div>
              <button v-if="isCourseOwner && member.role !== 'owner'" @click="removeMember(member.user_id)" style="background: none; border: none; color: hsl(0, 80%, 60%); cursor: pointer; font-size: 1rem; padding: 4px;" title="동행자 제외">
                ❌
              </button>
            </div>
          </div>

          <!-- Invite Form -->
          <div v-if="isCourseOwner || members.some(m => m.username === 'traveler_demo' && m.role === 'editor')" style="display: flex; gap: 0.5rem;">
            <input type="email" v-model="inviteEmail" placeholder="초대할 동행자 이메일 입력" @keyup.enter="inviteMember" style="flex: 1; padding: 0.5rem 0.8rem; background: hsla(230, 15%, 8%, 0.6); border: 1px solid var(--border-muted); border-radius: 99px; color: var(--text-bright); font-size: 0.85rem;" />
            <button class="btn-primary" @click="inviteMember" :disabled="isInviting || !inviteEmail" style="padding: 0.5rem 1.2rem; font-size: 0.85rem;">
              {{ isInviting ? '초대 중...' : '초대' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <PlaceDetailModal :isOpen="isModalOpen" :place="selectedPlace" @close="isModalOpen = false" />
  </div>
</template>

<style scoped>
.planner-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2.5rem;
}
@media (min-width: 992px) {
  .planner-layout {
    grid-template-columns: 1fr 1fr;
  }
}
.map-section {
  position: sticky;
  top: 100px;
  height: max-content;
}
.badge-role.owner {
  background: hsla(265, 80%, 65%, 0.15);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
.badge-role.editor {
  background: hsla(190, 90%, 50%, 0.15);
  color: var(--color-accent);
  border: 1px solid var(--color-accent);
}
</style>
