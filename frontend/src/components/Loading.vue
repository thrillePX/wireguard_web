<template>
  <Transition name="fade">
    <div v-if="show" :class="['loading-overlay', { 'inline': inline }]">
      <div class="spinner-container">
        <div class="spinner"></div>
        <p v-if="text" class="loading-text">{{ text }}</p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  text: { type: String, default: '' },
  inline: { type: Boolean, default: false }
})
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-overlay.inline {
  position: absolute;
  background: rgba(0, 0, 0, 0.3);
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.inline .spinner {
  width: 24px;
  height: 24px;
  border-width: 3px;
  border-color: var(--border-color);
  border-top-color: var(--accent-color);
}

.loading-text {
  color: white;
  font-size: 14px;
  margin: 0;
}

.inline .loading-text {
  color: var(--text-primary);
  font-size: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
