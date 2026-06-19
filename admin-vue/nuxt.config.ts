// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  ssr: false,
  app: {
    head: {
      title: 'KB Compliance Admin',
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
      link: [{ rel: 'icon', type: 'image/x-icon', href: '/icon_favicon.ico' }],
    },
  },
  modules: ['@nuxt/icon'],
  icon: {
    // 내부망(오프라인) 환경 대응: iconify API로 fallback하지 않고
    // 빌드 시점에 @iconify-json/lucide에서 아이콘을 서버 번들로 포함시킴
    provider: 'server',
    fallbackToApi: false,
  },
  css: ['~/assets/css/global.css'],
  devServer: {
    host: '0.0.0.0',
    port: 3000
  },
  vite: {
    optimizeDeps: {
      include: [
        '@vue/devtools-core',
        '@vue/devtools-kit',
      ]
    }
  }
})