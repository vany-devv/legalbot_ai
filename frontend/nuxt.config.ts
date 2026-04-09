// https://nuxt.com/docs/api/configuration/nuxt-config
const apiTarget = process.env.API_URL ?? 'http://localhost:8080'
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
  devtools: { enabled: false },
  future: { compatibilityVersion: 4 },
  app: {
    head: {
      title: 'LegalBot AI',
      titleTemplate: '%s — LegalBot AI',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Юридический ИИ-ассистент' },
        { name: 'theme-color', content: '#6366f1' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon-black.svg' },
      ],
      script: [
        {
          // Anti-FOUC: apply saved theme before first paint
          innerHTML: `(function(){try{var t=localStorage.getItem('lb-theme');if(t==='light'){document.documentElement.setAttribute('data-theme','light');}else if(!t&&window.matchMedia('(prefers-color-scheme:light)').matches){document.documentElement.setAttribute('data-theme','light');}}catch(e){}})();`,
        },
      ],
    },
  },
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


