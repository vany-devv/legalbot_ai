// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: false },
  future: { compatibilityVersion: 4 },
  nitro: {
    routeRules: {
      '/api/**': {
        proxy: 'http://localhost:8000/**',
      },
    },
  },
  runtimeConfig: {
    public: {
      apiBase: '/api',
    },
  },
})


