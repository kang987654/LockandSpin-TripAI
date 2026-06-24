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
          ${slot.place.place_url ? `<a href="${slot.place.place_url}" target="_blank" style="font-size:11px; color:#aa3bff; font-weight:bold; text-decoration:none;">지도 보기 ↗</a>` : ''}
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
  const myMemberInfo = members.value.find(m => m.username === authStore.currentUser?.username)
  return myMemberInfo && myMemberInfo.role === 'owner'
})

// 마운트 시 멤버 로드 추가
watch(() => courseStore.activeCourse, async (newVal) => {
  if (newVal && members.value.length === 0) {
    await fetchMembers()
  }
})

const saveCourse = async () => {
  if (!authStore.isLoggedIn) {
    if (confirm('코스를 저장하려면 로그인이 필요합니다. 로그인 화면으로 이동하시겠습니까?')) {
      router.push(`/login?redirect=/courses/${courseStore.activeCourse.id}`)
    }
    return
  }

  // 익명으로 생성된 코스를 로그인한 유저가 처음 저장(Claim)할 때
  if (!courseStore.activeCourse.user) {
    try {
      await axios.post(`${authStore.API_BASE}/api/courses/${courseStore.activeCourse.id}/claim/`, {}, authStore.getHeaders())
      courseStore.activeCourse.user = { id: authStore.currentUser?.id, username: authStore.currentUser?.username }
      courseStore.activeCourse.status = 'saved'
    } catch (err) {
      console.error('Failed to claim course:', err)
      alert(err.response?.data?.error || '일정 저장에 실패했습니다.')
    }
    return
  }

  try {
    await axios.post(`${authStore.API_BASE}/api/courses/${courseStore.activeCourse.id}/save_course/`, {}, authStore.getHeaders())
    courseStore.activeCourse.status = 'saved'
  } catch (err) {
    console.error('Failed to save course:', err)
    alert('일정 저장에 실패했습니다.')
  }
}

const isEvaluating = ref(false)
const evaluateCourseComment = async () => {
  isEvaluating.value = true
  try {
    await courseStore.evaluateCourse()
  } catch (e) {
    alert('평가 중 오류가 발생했습니다.')
  } finally {
    isEvaluating.value = false
  }
}

const swapTargetPlaceId = ref(null)
const swapDaySeq = ref('') // "day_seq" format

const openSwap = (kPlace) => {
  swapTargetPlaceId.value = kPlace.id;
  const compSlots = getCompatibleSlots(kPlace.category);
  if (compSlots.length === 1) {
    swapDaySeq.value = `${compSlots[0].day_number}_${compSlots[0].sequence}`;
  } else {
    swapDaySeq.value = '';
  }
}

const handleSwap = async (placeId) => {
  if (!swapDaySeq.value) {
    alert('어떤 일정으로 교체할지 선택해주세요.');
    return;
  }
  const [day, seq] = swapDaySeq.value.split('_').map(Number);
  await courseStore.swapKeptPlace(courseStore.activeCourse.id, placeId, day, seq);
  swapTargetPlaceId.value = null;
  swapDaySeq.value = '';
}

const isExcluded = (placeId) => {
  return courseStore.activeCourse?.excluded_places?.some(ep => ep.id === placeId)
}

const getCompatibleSlots = (category) => {
  const comp = [];
  Object.keys(slotsByDay.value).forEach(day => {
    slotsByDay.value[day].forEach(slot => {
      let isCompatible = false;
      if (slot.sequence === 1 && (category === 'spot' || category === 'activity')) isCompatible = true;
      if (slot.sequence === 2 && category === 'restaurant') isCompatible = true;
      if (slot.sequence === 3 && category === 'cafe') isCompatible = true;
      if (slot.sequence === 4 && category === 'restaurant') isCompatible = true;
      
      if (isCompatible) {
        comp.push({
          day_number: slot.day_number,
          sequence: slot.sequence,
          place_name: slot.place.name,
          label: `Day ${slot.day_number} - ${getSeqLabel(slot.sequence)} (${slot.place.name})`
        });
      }
    });
  });
  return comp;
}

</script>

<template>
  <div v-if="courseStore.activeCourse" class="glass-card" style="margin-bottom: 2rem;">

    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-muted); padding-bottom: 1rem; margin-bottom: 1.5rem;">
      <div>
        <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">
          <h2 style="color: var(--text-bright); margin: 0;">{{ courseStore.activeCourse.title }}</h2>
          <span v-if="courseStore.activeCourse.status === 'draft'" style="background: var(--color-accent); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">임시저장</span>
          <span v-else style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">저장됨</span>
        </div>
        <p class="text-muted" style="margin: 0;">목적지: {{ courseStore.activeCourse.destination }} | {{ courseStore.activeCourse.duration_days }}일간</p>
      </div>
      <div style="display: flex; gap: 1rem;">
        <button class="btn-primary" :disabled="courseStore.isSpinning || courseStore.activeCourse.status === 'saved'" @click="courseStore.triggerRespin" style="padding: 0.9rem 2.2rem; font-size: 1.05rem;">
          <span style="font-size: 1.2rem;">🔄</span> {{ courseStore.isSpinning ? '슬롯 재조합 중...' : (courseStore.activeCourse.status === 'saved' ? '확정된 일정' : 'Re-spin!') }}
        </button>
        <button v-if="courseStore.activeCourse.status === 'draft' && (!courseStore.activeCourse.user || isCourseOwner)" class="btn-secondary" style="border-color: #10b981; color: #10b981; padding: 0.9rem 1.5rem; font-size: 1.05rem;" @click="saveCourse">
          💾 일정 확정 및 저장하기
        </button>
      </div>
    </div>

    <div class="planner-layout">
      <!-- Left side: Slots -->
      <div class="slots-container">
        <div v-for="(slots, day) in slotsByDay" :key="day" style="margin-bottom: 2.5rem;">
          <h3 style="color: var(--color-primary); margin-bottom: 1.5rem; font-weight: 800; font-size: 1.4rem;">Day {{ day }}</h3>
          <div class="slot-board">
            <div v-for="slot in slots" :key="slot.sequence" class="timeline-item">
              <!-- Timeline Dot -->
              <div class="timeline-dot">
                <div class="timeline-dot-inner"></div>
              </div>
              
              <!-- Slot Card -->
              <div class="slot-card-light" :class="{ locked: slot.is_locked, 'spinning-anim': courseStore.spinningSlots[`${slot.day_number}_${slot.sequence}`] }" :style="{ opacity: isExcluded(slot.place.id) ? 0.4 : 1, filter: isExcluded(slot.place.id) ? 'grayscale(100%)' : 'none' }" @click="openPlaceModal(slot.place)">
                
                <div v-if="isExcluded(slot.place.id)" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.7); color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: bold; font-size: 1.2rem; z-index: 10; pointer-events: none;">
                  🚫 제외됨
                </div>

                <div style="display: flex; justify-content: space-between; margin-bottom: 0.6rem;">
                  <span style="font-size: 0.8rem; font-weight: 800; color: var(--color-accent); text-transform: uppercase;">{{ getSeqLabel(slot.sequence) }}</span>
                  <button class="btn-lock" :class="{ 'is-locked': slot.is_locked }" @click.stop="courseStore.toggleLock(slot)">
                    {{ slot.is_locked ? '🔒 결정됨' : '🔓 이걸로 결정!' }}
                  </button>
                </div>

                <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                  <!-- Image placeholder -->
                  <div style="width: 80px; height: 80px; border-radius: 8px; background: linear-gradient(135deg, #e0e7ff 0%, #dbeafe 100%); flex-shrink: 0; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 1.5rem;">{{ slot.category === 'restaurant' ? '🍽️' : slot.category === 'cafe' ? '☕' : '🏞️' }}</span>
                  </div>
                  <div style="flex: 1;">
                    <h4 style="font-size: 1.15rem; font-weight: 800; margin: 0 0 0.2rem 0; color: var(--text-bright);">{{ slot.place.name }}</h4>
                    <p style="font-size: 0.8rem; color: var(--color-success); margin: 0 0 0.3rem 0; font-weight: 600;">📍 {{ slot.place.address }}</p>
                    <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4;">
                      {{ slot.place.description }}
                    </p>
                  </div>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 0.5rem; border-top: 1px solid var(--border-muted); padding-top: 0.8rem;">
                  <a v-if="slot.place.place_url" :href="slot.place.place_url" target="_blank" @click.stop style="font-size: 0.8rem; color: var(--text-muted); text-decoration: underline; margin-right: auto; padding-top: 6px;" :style="{ pointerEvents: isExcluded(slot.place.id) ? 'none' : 'auto' }">지도 보기 ↗</a>
                  <button @click.stop="courseStore.excludePlace(courseStore.activeCourse.id, slot.place.id, slot.day_number, slot.sequence)" class="btn-exclude" :disabled="isExcluded(slot.place.id)">{{ isExcluded(slot.place.id) ? '🚫 제외됨' : '🚫 제외하기' }}</button>
                  <button @click.stop="courseStore.keepPlace(courseStore.activeCourse.id, slot.place.id, slot.day_number, slot.sequence)" class="btn-keep" :disabled="isExcluded(slot.place.id)">📦 킵하기</button>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side: Map & Panels -->
      <div class="map-section">
        <div id="map" class="map-container"></div>

        <!-- Floating Panel: Top Right (AI Comment & Social Spin) -->
        <div class="floating-panel-top-right">
          <!-- AI Comment Box -->
          <div v-if="courseStore.activeCourse.ai_comment" style="background: rgba(255,255,255,0.95); backdrop-filter: blur(8px); padding: 1.2rem; border-radius: 12px; border: 1px solid var(--border-muted); box-shadow: 0 4px 20px rgba(0,0,0,0.08); display: flex; flex-direction: column; gap: 0.8rem;">
            <div style="display: flex; gap: 0.8rem; align-items: flex-start;">
              <div style="font-size: 1.5rem;">✨</div>
              <div style="flex: 1;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--color-primary); font-size: 0.95rem; font-weight: 800;">AI 여행 플래너의 조언</h4>
                <p style="margin: 0; color: var(--text-normal); font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; max-height: 400px; overflow-y: auto; padding-right: 0.5rem; text-align: left;">
{{ courseStore.activeCourse.ai_comment }}
                </p>
              </div>
            </div>
            <button class="btn-exclude" style="align-self: flex-end; padding: 4px 10px; font-size: 0.75rem;" @click="evaluateCourseComment" :disabled="isEvaluating">
              {{ isEvaluating ? '평가 중...' : '💡 다시 평가받기' }}
            </button>
          </div>

          <!-- Social Spin Member Management Panel -->
          <div style="background: rgba(255,255,255,0.95); backdrop-filter: blur(8px); padding: 1.2rem; border-radius: 12px; border: 1px solid var(--border-muted); box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <h3 style="color: var(--text-bright); font-size: 0.95rem; margin-bottom: 0.8rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem;">
              👥 소셜 스핀 멤버
            </h3>
            <div style="display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem;">
              <div v-for="member in members" :key="member.user_id" style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem; background: #f8fafc; border-radius: 6px; border: 1px solid var(--border-muted);">
                <div>
                  <span style="color: var(--text-bright); font-weight: 700; font-size: 0.85rem;">{{ member.username }}</span>
                  <span class="badge-role" :class="member.role" style="margin-left: 0.4rem; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: 700;">
                    {{ member.role === 'owner' ? '소유자' : '편집자' }}
                  </span>
                </div>
                <button v-if="isCourseOwner && member.role !== 'owner'" @click="removeMember(member.user_id)" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem; padding: 2px;" title="동행자 제외">❌</button>
              </div>
            </div>
            <div v-if="isCourseOwner || members.some(m => m.username === authStore.currentUser?.username && m.role === 'editor')" style="display: flex; gap: 0.4rem;">
              <input type="email" v-model="inviteEmail" placeholder="초대 이메일" @keyup.enter="inviteMember" style="flex: 1; padding: 6px 10px; background: #f8fafc; border: 1px solid var(--border-muted); border-radius: 6px; color: var(--text-bright); font-size: 0.8rem;" />
              <button class="btn-keep" style="padding: 6px 10px;" @click="inviteMember" :disabled="isInviting || !inviteEmail">
                {{ isInviting ? '...' : '초대' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Floating Panel: Bottom (Kept Places) -->
        <div class="floating-panel-bottom" v-if="courseStore.activeCourse.kept_places && courseStore.activeCourse.kept_places.length > 0">
          <div class="kept-glass-panel">
            <h3 style="color: var(--text-bright); font-size: 1rem; margin-bottom: 0.8rem; font-weight: 800;">📦 보관된 장소 목록</h3>
            <div style="display: flex; gap: 1rem; overflow-x: auto; padding-bottom: 0.5rem; scroll-snap-type: x mandatory;">
              <div v-for="kPlace in courseStore.activeCourse.kept_places" :key="kPlace.id" style="background: white; border: 1px solid var(--border-muted); border-radius: 12px; padding: 1rem; min-width: 260px; max-width: 260px; flex-shrink: 0; scroll-snap-align: start; box-shadow: 0 4px 12px rgba(0,0,0,0.04); position: relative;">
                <h4 style="margin: 0 0 0.3rem 0; color: var(--text-bright); font-size: 1rem; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ kPlace.name }}</h4>
                <p style="margin: 0 0 0.8rem 0; color: var(--color-success); font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">📍 {{ kPlace.address }}</p>
                
                <div v-if="swapTargetPlaceId === kPlace.id" style="display: flex; flex-direction: column; gap: 0.5rem; background: #f8fafc; padding: 0.8rem; border-radius: 8px;">
                  <label style="font-size: 0.75rem; color: var(--text-normal); font-weight: 600;">어느 일정과 교체할까요?</label>
                  <select v-model="swapDaySeq" style="padding: 6px; border-radius: 4px; background: white; color: var(--text-bright); border: 1px solid var(--border-muted); font-size: 0.8rem;">
                    <option disabled value="">선택</option>
                    <option v-for="slot in getCompatibleSlots(kPlace.category)" :key="'opt_'+slot.day_number+'_'+slot.sequence" :value="`${slot.day_number}_${slot.sequence}`">{{ slot.label }}</option>
                  </select>
                  <div style="display: flex; gap: 0.4rem; justify-content: flex-end; margin-top: 0.4rem;">
                    <button class="btn-exclude" style="padding: 4px 8px; font-size: 0.75rem;" @click="swapTargetPlaceId = null">취소</button>
                    <button class="btn-keep" style="padding: 4px 8px; font-size: 0.75rem;" @click="handleSwap(kPlace.id)">교체 확정</button>
                  </div>
                </div>
                <div v-else style="display: flex; gap: 0.4rem;">
                  <button class="btn-keep" style="padding: 6px; font-size: 0.75rem; flex: 1;" @click="openSwap(kPlace)">🔄 교체</button>
                  <button class="btn-exclude" style="padding: 6px; font-size: 0.75rem; flex: 1; border-color: #ef4444; color: #ef4444;" @click="courseStore.removeKeptPlace(courseStore.activeCourse.id, kPlace.id)">🗑️ 삭제</button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <PlaceDetailModal :isOpen="isModalOpen" :place="selectedPlace" @close="isModalOpen = false" />
  </div>
</template>

<style scoped>
.planner-layout {
  display: flex;
  height: calc(100vh - 180px); /* 헤더 등을 제외한 나머지 높이 꽉 채우기 */
  min-height: 600px;
  position: relative;
  background-color: var(--bg-color);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-muted);
}

.slots-container {
  width: 450px;
  min-width: 450px;
  height: 100%;
  overflow-y: auto;
  background-color: #f8fafc;
  border-right: 1px solid var(--border-muted);
  padding: 1.5rem;
  z-index: 10;
  box-shadow: 2px 0 15px rgba(0, 0, 0, 0.03);
}

.map-section {
  flex: 1;
  position: relative;
  height: 100%;
  background-color: #e2e8f0; /* Map placeholder color */
}

.map-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* Floating Panels */
.floating-panel-top-right {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 320px;
  pointer-events: none; /* 패널 외 빈 공간 지도 클릭 허용 */
}
.floating-panel-top-right > * {
  pointer-events: auto; /* 패널 내용물은 클릭 허용 */
}

.floating-panel-bottom {
  position: absolute;
  bottom: 20px;
  right: 20px;
  left: 20px;
  z-index: 20;
  pointer-events: none;
}
.floating-panel-bottom > * {
  pointer-events: auto;
}

/* Slot Card & Timeline Design */
.slot-board {
  display: flex;
  flex-direction: column;
  gap: 0; /* 선 연결을 위해 마진 제거, 패딩으로 조절 */
}

.timeline-item {
  display: flex;
  gap: 1rem;
  position: relative;
  padding-bottom: 2rem;
}

/* 타임라인 세로선 */
.timeline-item::before {
  content: '';
  position: absolute;
  top: 30px;
  bottom: -10px;
  left: 19px; /* 점 중앙에 맞춤 */
  width: 2px;
  background-color: var(--border-muted);
  z-index: 1;
}
/* 마지막 요소는 선을 긋지 않음 */
.timeline-item:last-child::before {
  display: none;
}

/* 타임라인 점(Dot) */
.timeline-dot {
  width: 40px;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding-top: 10px;
  position: relative;
  z-index: 2;
}
.timeline-dot-inner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: var(--bg-card);
  border: 3px solid var(--color-primary);
}

.slot-card-light {
  flex: 1;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-muted);
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  padding: 1.2rem;
  transition: all 0.3s;
  position: relative;
}
.slot-card-light:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}
.slot-card-light.locked {
  border-color: var(--color-primary);
  background-color: #f5f3ff;
}

/* Action Buttons (Light Theme) */
.btn-keep {
  background-color: #06b6d4;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}
.btn-keep:hover:not(:disabled) { background-color: #0891b2; }
.btn-keep:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-exclude {
  background-color: transparent;
  color: #64748b;
  border: 1px solid #cbd5e1;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}
.btn-exclude:hover:not(:disabled) { background-color: #f1f5f9; color: #ef4444; border-color: #ef4444; }
.btn-exclude:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-lock {
  background-color: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}
.btn-lock.is-locked {
  background-color: var(--color-primary);
  color: white;
}
.btn-lock:hover { background-color: var(--color-primary); color: white; }

/* Kept Places Glass Panel */
.kept-glass-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.4);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.08);
  padding: 1.5rem;
}

.badge-role.owner {
  background: #f3e8ff;
  color: #7e22ce;
  border: 1px solid #d8b4fe;
}
.badge-role.editor {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #7dd3fc;
}

@keyframes flip-spin {
  0% { transform: perspective(600px) rotateX(0deg); opacity: 1; }
  50% { transform: perspective(600px) rotateX(180deg); opacity: 0.4; }
  100% { transform: perspective(600px) rotateX(360deg); opacity: 1; }
}
.spinning-anim {
  animation: flip-spin 0.4s ease-in-out infinite;
  background-color: #f1f5f9 !important;
  box-shadow: 0 0 20px #cbd5e1;
  pointer-events: none;
}
</style>
