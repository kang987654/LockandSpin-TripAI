<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const region = ref('')
const travelDate = ref('')
const preferences = ref('')

const loading = ref(false)
const results = ref<any>(null)
const error = ref('')

const search = async () => {
  if (!region.value.trim() || !travelDate.value || !preferences.value.trim()) {
    error.value = '모든 항목(장소, 날짜, 정보)을 입력해주세요.'
    return
  }
  
  loading.value = true
  error.value = ''
  results.value = null
  
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/recommend/', {
      region: region.value,
      date: travelDate.value,
      query: preferences.value
    })
    results.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || '추천 정보를 불러오는 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 w-full font-sans text-slate-800 flex flex-col items-center">
    <div class="w-full max-w-5xl mx-auto px-4 py-12 flex flex-col items-center">
      
      <!-- 헤더 -->
      <div class="text-center animate-fade-in-up mb-10 mt-8">
        <h1 class="text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 mb-4 animate-pulse-slow">
          AI 트래블 & 데이트 플래너
        </h1>
        <p class="text-lg text-slate-500">
          원하는 장소, 날짜, 그리고 어떤 여행을 하고 싶은지 자유롭게 적어주세요.
        </p>
      </div>

      <!-- 검색 폼 (분리형) -->
      <div class="w-full max-w-3xl animate-fade-in-up bg-white/70 backdrop-blur-md rounded-3xl p-8 shadow-xl ring-1 ring-indigo-100 mb-10" style="animation-delay: 0.1s;">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <!-- 장소 입력 -->
          <div class="flex flex-col">
            <label class="text-sm font-bold text-indigo-800 mb-2">📍 장소 (어디로 가시나요?)</label>
            <input 
              v-model="region"
              type="text" 
              class="px-4 py-3 rounded-xl bg-white border border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all placeholder-slate-400"
              placeholder="예: 홍대, 성수, 해운대"
            />
          </div>
          <!-- 날짜 입력 -->
          <div class="flex flex-col">
            <label class="text-sm font-bold text-indigo-800 mb-2">📅 날짜 (언제 가시나요?)</label>
            <input 
              v-model="travelDate"
              type="date" 
              class="px-4 py-3 rounded-xl bg-white border border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-slate-700"
            />
          </div>
        </div>

        <!-- 선호 정보 입력 -->
        <div class="flex flex-col mb-6">
          <label class="text-sm font-bold text-indigo-800 mb-2">✨ 원하는 여행/데이트 정보</label>
          <textarea 
            v-model="preferences"
            rows="3"
            class="px-4 py-3 rounded-xl bg-white border border-slate-200 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all resize-none placeholder-slate-400"
            placeholder="예: 비가 와서 실내 데이트를 하고 싶어. 맛있는 디저트가 있는 조용한 카페랑 귀여운 팝업스토어를 추천해줘."
          ></textarea>
        </div>

        <button 
          @click="search" 
          :disabled="loading"
          class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-indigo-500/30 text-lg flex justify-center items-center gap-2"
        >
          <span v-if="loading" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            AI가 맞춤 코스를 찾고 있어요...
          </span>
          <span v-else>맞춤 코스 추천받기</span>
        </button>
      </div>

      <!-- 에러 메시지 -->
      <div v-if="error" class="mb-8 p-4 bg-red-50 text-red-600 rounded-xl animate-fade-in-up w-full max-w-3xl border border-red-100 flex items-center gap-3 font-medium">
        ⚠️ {{ error }}
      </div>

      <!-- 결과 영역 -->
      <div v-if="results && !loading" class="w-full max-w-5xl animate-fade-in-up" style="animation-delay: 0.2s;">
        <div class="text-center mb-10">
          <span class="inline-block py-1.5 px-4 rounded-full bg-indigo-100 text-indigo-700 font-bold text-sm mb-4 shadow-sm">
            AI 분석 완료 ✨
          </span>
          <h2 class="text-3xl font-extrabold text-slate-800">
            <span class="text-blue-600">{{ results.region }}</span> 추천 코스
          </h2>
          <p class="text-slate-500 mt-2 font-medium">추천 기준 날짜: {{ results.travel_date }}</p>
        </div>

        <div class="grid lg:grid-cols-2 gap-10">
          
          <!-- 트랙 A: 고정 장소 -->
          <div v-if="results.recommendations?.fixed?.length > 0" class="bg-white/40 p-6 rounded-3xl">
            <h3 class="text-xl font-bold flex items-center gap-2 mb-6 border-b border-indigo-100 pb-3 text-indigo-900">
              <span class="text-2xl">☕</span> 핫플레이스 (DB 기반 3점 이상)
            </h3>
            <div class="space-y-5">
              <div v-for="(place, idx) in results.recommendations.fixed" :key="idx" 
                   class="bg-white rounded-2xl p-5 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-indigo-50 group">
                <div class="flex gap-4">
                  <div class="w-28 h-28 rounded-xl overflow-hidden bg-slate-100 shrink-0 shadow-inner">
                    <img v-if="place.image_url" :src="place.image_url" class="w-full h-full object-cover group-hover:scale-110 transition duration-500"/>
                    <div v-else class="w-full h-full flex items-center justify-center text-slate-300 text-sm font-medium">No Image</div>
                  </div>
                  <div class="flex-1 flex flex-col justify-between">
                    <div>
                      <div class="flex justify-between items-start mb-1">
                        <h4 class="font-bold text-lg text-slate-800 group-hover:text-indigo-600 transition">{{ place.name }}</h4>
                        <span class="text-xs font-bold bg-blue-50 text-blue-600 px-2 py-1 rounded-md">{{ place.category }}</span>
                      </div>
                      <div class="flex flex-wrap gap-1 mt-2">
                        <span v-for="tag in place.tags" :key="tag" class="text-xs text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full font-medium">#{{ tag }}</span>
                      </div>
                    </div>
                    <a :href="place.link" target="_blank" class="inline-block mt-3 text-sm text-indigo-500 font-bold hover:text-indigo-700 flex items-center gap-1">
                      카카오맵 상세 보기 <span class="text-lg leading-none">→</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 트랙 B: 일시적 행사 -->
          <div v-if="results.recommendations?.temporary?.length > 0" class="bg-indigo-50/50 p-6 rounded-3xl">
            <h3 class="text-xl font-bold flex items-center gap-2 mb-6 border-b border-indigo-100 pb-3 text-indigo-900">
              <span class="text-2xl">🎟️</span> 실시간 행사 & 팝업 (네이버 검색)
            </h3>
            <div class="space-y-5">
              <div v-for="(event, idx) in results.recommendations.temporary" :key="idx" 
                   class="bg-gradient-to-br from-indigo-600 to-blue-700 rounded-2xl p-6 shadow-lg hover:shadow-indigo-500/40 transition-all duration-300 transform hover:-translate-y-1 text-white relative overflow-hidden group">
                <div class="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-white opacity-10 rounded-full blur-2xl group-hover:scale-150 transition duration-700"></div>
                <div class="relative z-10 flex gap-4">
                  <div class="flex-1">
                    <div class="flex justify-between items-start mb-2">
                      <h4 class="font-bold text-xl leading-snug">{{ event.name }}</h4>
                    </div>
                    <p class="text-indigo-200 text-sm font-medium mb-4">{{ event.category }}</p>
                    <div class="inline-block bg-black/20 backdrop-blur-md border border-white/10 rounded-xl px-4 py-2 text-sm font-medium mb-4 shadow-inner">
                      📅 {{ event.dates }}
                    </div>
                    <div>
                      <a :href="event.link" target="_blank" class="inline-block text-sm bg-white text-indigo-700 font-bold px-5 py-2.5 rounded-xl hover:bg-indigo-50 transition transform active:scale-95 shadow-md">네이버 상세 정보 →</a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
        
        <div v-if="results.recommendations?.fixed?.length === 0 && results.recommendations?.temporary?.length === 0" class="text-center py-16 bg-white/50 rounded-3xl mt-6 border border-slate-100">
          <span class="text-4xl mb-4 block">😢</span>
          <p class="text-lg text-slate-600 font-medium">조건에 맞는 장소나 행사를 찾지 못했어요.</p>
          <p class="text-slate-500 mt-2">검색어의 분위기나 종류를 조금 바꿔보시는 건 어떨까요?</p>
        </div>
      </div>
      
    </div>
  </div>
</template>
