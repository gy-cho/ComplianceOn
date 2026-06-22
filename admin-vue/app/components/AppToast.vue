<template>
  <Transition name="toast-fade">
    <div
      v-if="toast.visible"
      class="toast-wrap"
      :class="[`toast-${toast.type}`, { copied }]"
      @click="handleCopy"
    >
      <Icon :name="copied ? 'lucide:check' : (iconMap[toast.type] || 'lucide:info')" class="toast-icon" />
      <span class="toast-msg">{{ copied ? '복사되었습니다' : toast.message }}</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
const { toast } = useToast()
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | null = null

const iconMap: Record<string, string> = {
  success: 'lucide:check-circle',
  error: 'lucide:alert-circle',
  warning: 'lucide:alert-triangle',
  info: 'lucide:info',
}

async function handleCopy() {
  const text = toast.value.message
  const ok = await copyText(text)
  if (ok) {
    copied.value = true
    if (copiedTimer) clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => {
      copied.value = false
    }, 1200)
  }
}

async function copyText(text: string): Promise<boolean> {
  // 1. 표준 Clipboard API (HTTPS 또는 localhost에서만 동작)
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // 폴백으로 진행
    }
  }

  // 2. 폴백: 숨겨진 textarea + execCommand('copy')
  //    (HTTP 환경이나 Clipboard API 미지원 브라우저 대응)
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    textarea.style.top = '0'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    const success = document.execCommand('copy')
    document.body.removeChild(textarea)
    return success
  } catch {
    return false
  }
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
  align-items: flex-start;
  gap: 8px;
  padding: 12px 22px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  min-width: 260px;
  max-width: min(480px, calc(100vw - 40px));
  pointer-events: auto;
  cursor: pointer;
  white-space: normal;
  word-break: break-word;
  transition: filter 0.15s ease;
}

.toast-wrap:hover {
  filter: brightness(1.05);
}

.toast-wrap:active {
  filter: brightness(0.95);
}

.toast-success { background: #00C851; color: #fff; }
.toast-error   { background: #ff4444; color: #fff; }
.toast-warning { background: #ffbb33; color: #333; }
.toast-info    { background: #33b5e5; color: #fff; }

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
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