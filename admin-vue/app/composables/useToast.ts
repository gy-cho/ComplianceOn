export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastState {
  visible: boolean
  type: ToastType
  message: string
}

let _timer: ReturnType<typeof setTimeout> | null = null

export function useToast() {
  const toast = useState<ToastState>('app-toast', () => ({
    visible: false,
    type: 'success',
    message: '',
  }))

  function showToast(type: ToastType, message: string, duration = 3000) {
    if (_timer) clearTimeout(_timer)
    toast.value = { visible: true, type, message }
    _timer = setTimeout(() => {
      toast.value = { ...toast.value, visible: false }
    }, duration)
  }

  return { toast: readonly(toast), showToast }
}
