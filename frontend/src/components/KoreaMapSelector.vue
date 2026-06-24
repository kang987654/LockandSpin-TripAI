<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const regions = [
  { id: 'seoul', name: '서울', top: '22%', left: '42%', pos: 'left' },
  { id: 'gyeonggi', name: '경기', top: '27%', left: '44%', pos: 'right' },
  { id: 'gangwon', name: '강원', top: '18%', left: '59%', pos: 'right' },
  { id: 'chungbuk', name: '충북', top: '38%', left: '52%', pos: 'right' },
  { id: 'chungnam', name: '충남', top: '42%', left: '38%', pos: 'left' },
  { id: 'daejeon', name: '대전', top: '46%', left: '45%', pos: 'bottom' },
  { id: 'gyeongbuk', name: '경북', top: '44%', left: '67%', pos: 'right' },
  { id: 'jeonbuk', name: '전북', top: '55%', left: '41%', pos: 'left' },
  { id: 'daegu', name: '대구', top: '55%', left: '62%', pos: 'top' },
  { id: 'gyeongnam', name: '경남', top: '63%', left: '56%', pos: 'left' },
  { id: 'ulsan', name: '울산', top: '59%', left: '69%', pos: 'right' },
  { id: 'gwangju', name: '광주', top: '66%', left: '36%', pos: 'left' },
  { id: 'jeonnam', name: '전남', top: '73%', left: '33%', pos: 'bottom' },
  { id: 'busan', name: '부산', top: '66%', left: '68%', pos: 'right' },
  { id: 'jeju', name: '제주', top: '97%', left: '31%', pos: 'bottom' }
]

const selectRegion = (name) => {
  emit('update:modelValue', name)
}
</script>

<template>
  <div class="korea-map-container">
    <div class="map-background">
      <!-- 배경으로 사용할 대한민국 지도 이미지 -->
      <img src="../assets/korea-map.svg" alt="Korea Map" class="map-img" style="opacity: 0.2;"/>
      
      <!-- 지역 버튼들 -->
      <button 
        v-for="region in regions" 
        :key="region.id"
        type="button"
        class="map-marker"
        :class="{ active: modelValue === region.name }"
        :style="{ top: region.top, left: region.left }"
        @click="selectRegion(region.name)"
      >
        <span class="marker-dot"></span>
        <span class="marker-label" :class="`label-${region.pos}`">{{ region.name }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.korea-map-container {
  width: 100%;
  height: 100%;
  min-height: 350px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid var(--border-muted);
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.map-background {
  position: relative;
  width: 100%;
  max-width: 320px;
  aspect-ratio: 1 / 1;
}

.map-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.map-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  background: none;
  border: none;
  cursor: pointer;
  z-index: 10;
  padding: 0;
  width: 12px;
  height: 12px;
  display: block;
}

.marker-dot {
  width: 12px;
  height: 12px;
  background: var(--border-muted);
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s;
  display: block;
}

.marker-label {
  position: absolute;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255,255,255,0.8);
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
  white-space: nowrap;
  pointer-events: none;
}

/* 위치 지정 */
.label-top {
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
}
.label-bottom {
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
}
.label-left {
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
}
.label-right {
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
}

.map-marker:hover .marker-dot {
  background: var(--color-primary);
  transform: scale(1.2);
}

.map-marker:hover .marker-label {
  color: var(--color-primary);
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.map-marker.active .marker-dot {
  background: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2);
  transform: scale(1.2);
}

.map-marker.active .marker-label {
  color: white;
  background: var(--color-primary);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.map-marker:hover .marker-label {
  color: var(--color-primary);
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.map-marker.active .marker-dot {
  background: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2);
  transform: scale(1.2);
}

.map-marker.active .marker-label {
  color: white;
  background: var(--color-primary);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}
</style>
