// https://nuxt.com/docs/api/configuration/nuxt-config
const apiTarget = process.env.API_URL ?? 'http://localhost:8080'
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
  devtools: { enabled: false },
  future: { compatibilityVersion: 4 },
  nitro: {
    routeRules: {
      '/api/**': { proxy: `${apiTarget}/api/**` },
    },
  },
  runtimeConfig: {
    public: {
      apiBase: '/api',
    },
  },
})


