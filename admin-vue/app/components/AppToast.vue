<template>
  <Transition name="toast-fade">
    <div v-if="toast.visible" class="toast-wrap" :class="`toast-${toast.type}`">
      <span class="toast-icon">{{ iconMap[toast.type] }}</span>
      <span class="toast-msg">{{ toast.message }}</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
const { toast } = useToast()

const iconMap = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
}
</script>

<style scoped>
.toast-wrap {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  min-width: 260px;
  max-width: 480px;
  pointer-events: none;
  white-space: nowrap;
}

.toast-success { background: #00C851; color: #fff; }
.toast-error   { background: #ff4444; color: #fff; }
.toast-warning { background: #ffbb33; color: #333; }
.toast-info    { background: #33b5e5; color: #fff; }

.toast-icon {
  font-size: 15px;
  font-weight: 700;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(16px);
}
</style>
