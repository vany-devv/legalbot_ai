// https://nuxt.com/docs/api/configuration/nuxt-config
const apiTarget = process.env.API_URL ?? 'http://localhost:8080'
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss', '@nuxtjs/google-fonts'],
  googleFonts: {
    families: {
      Inter: [400, 500, 600, 700],
      Manrope: [500, 600, 700, 800],
      'JetBrains Mono': [400, 500],
    },
    display: 'swap',
    download: true,
    preload: true,
    inject: true,
    overwriting: true,
  },
  devtools: { enabled: false },
  future: { compatibilityVersion: 4 },
  // Compat 4 changes srcDir to './app' by default — pin to root so
  // frontend/middleware/, frontend/plugins/, frontend/composables/ are scanned.
  srcDir: '.',
  dir: {
    pages: 'pages',
    layouts: 'layouts',
    middleware: 'middleware',
    plugins: 'plugins',
  },
  app: {
    // Глобальные page/layout transitions — стили определены в app.vue.
    pageTransition: { name: 'page-fade', mode: 'out-in' },
    layoutTransition: { name: 'layout-fade', mode: 'out-in' },
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
          innerHTML: `(function(){try{var t=localStorage.getItem('lb-theme');if(t==='light'){document.documentElement.setAttribute('data-theme','light');}else if(!t&&window.matchMedia('(prefers-color-scheme:light)').matches){document.documentElement.setAttribute('data-theme','light');}var p=localStorage.getItem('lb-palette');if(p&&['indigo','navy','bordeaux','emerald','graphite'].indexOf(p)>=0){document.documentElement.setAttribute('data-palette',p);}}catch(e){}})();`,
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


