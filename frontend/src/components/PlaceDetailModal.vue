<script setup>
import { ref } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  place: Object
})

const emit = defineEmits(['close'])

const closeModal = () => {
  emit('close')
}

// Generate a simple youtube search URL
const getYoutubeUrl = (placeName) => {
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(placeName + ' 브이로그 리뷰')}`
}
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content glass-card">
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
          <h2 style="color: var(--text-bright); margin: 0;">{{ place?.name }} 상세 정보</h2>
          <button @click="closeModal" style="background: none; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer;">×</button>
        </div>

        <p style="color: var(--text-muted); margin-bottom: 1rem;">📍 {{ place?.address }}</p>
        
        <div style="font-size: 0.85rem; color: var(--color-success); margin-bottom: 1rem;">
          <span v-for="theme in place?.themes" :key="theme" style="margin-right: 0.3rem;">#{{ theme }}</span>
        </div>

        <p style="color: var(--text-bright); line-height: 1.5; margin-bottom: 2rem;">
          {{ place?.description }}
        </p>

        <div style="display: flex; gap: 1rem;">
          <a :href="getYoutubeUrl(place?.name)" target="_blank" rel="noopener noreferrer" style="flex: 1; text-decoration: none;">
            <button class="btn-primary" style="width: 100%; display: flex; justify-content: center; gap: 0.5rem;">
              📺 유튜브 리뷰 검색
            </button>
          </a>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 500px;
  padding: 2rem;
  border-radius: 12px;
}
</style>
