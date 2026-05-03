<template>
  <!-- Показываем shell только после auth.init() — иначе мелькает login,
       пока async middleware ещё ждёт ответа от /auth/me. -->
  <div v-if="initialized" class="app-shell">
    <ChatSidebar v-if="showSidebar" />
    <main class="main-area">
      <NuxtPage />
    </main>
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { init } = useTheme()
const { init: initPalette } = usePalette()
const { init: initSidebar } = useSidebar()
const { user, initialized, buildLoginRedirect } = useAuth()

useHead({
  titleTemplate: (title) => title ? `LegalBot AI | ${title}` : 'LegalBot AI',
})

onMounted(() => {
  init()
  initPalette()
  initSidebar()
})

const authRoutes = ['/auth/login', '/auth/register']
const showSidebar = computed(() => !authRoutes.includes(route.path))

// Любой переход user: <obj> → null (logout, протухший cookie из 401-хендлера)
// принудительно отправляет на login через router. Решает overlay-баг,
// когда middleware не срабатывает потому что navigation не было.
watch(user, (next, prev) => {
  if (!initialized.value) return
  if (prev && !next && !route.path.startsWith('/auth/')) {
    router.replace(buildLoginRedirect(route.fullPath))
  }
})
</script>

<style>
/* ─────────────────────────────────────────────────────────────
   LegalBot AI — Design Tokens
   Структура: [data-theme] задаёт светлую/тёмную базу;
              [data-palette] задаёт акцентный hue.
   Комбинация — независимая (4 темы × N палитр).
   ───────────────────────────────────────────────────────────── */

:root {
  /* Type scale */
  --font-display: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-sans:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono:    'JetBrains Mono', 'Fira Code', ui-monospace, monospace;

  /* Radii */
  --radius-xs:   4px;
  --radius-sm:   6px;
  --radius-md:   10px;
  --radius-lg:   14px;
  --radius-xl:   20px;
  --radius-full: 9999px;

  /* Motion */
  --ease-out:    cubic-bezier(0.2, 0.7, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.3, 0.64, 1);
  --t-fast:      120ms;
  --t-base:      180ms;
  --t-slow:      280ms;

  /* Default palette = navy */
  --brand-50:  #EAF1F9;
  --brand-100: #C8DCEE;
  --brand-200: #92BADD;
  --brand-300: #5C97CC;
  --brand-400: #3F7AB1;
  --brand-500: #1B3A5C;  /* primary */
  --brand-600: #163050;
  --brand-700: #112744;
  --brand-800: #0C1E36;
  --brand-900: #081628;
}

/* ─── PALETTES ─────────────────────────────────────────────── */

[data-palette="indigo"] {
  --brand-50:  #EEF2FF; --brand-100: #E0E7FF; --brand-200: #C7D2FE;
  --brand-300: #A5B4FC; --brand-400: #818CF8; --brand-500: #4F46E5;
  --brand-600: #4338CA; --brand-700: #3730A3; --brand-800: #312E81; --brand-900: #1E1B4B;
}

[data-palette="navy"] {
  --brand-50:  #EDF3FB; --brand-100: #CDDFF1; --brand-200: #9DBEE2;
  --brand-300: #6B9DD2; --brand-400: #467EB8; --brand-500: #2A4F82;
  --brand-600: #233F6B; --brand-700: #1B3155; --brand-800: #142340; --brand-900: #0C152A;
}

[data-palette="bordeaux"] {
  --brand-50:  #FBEBEB; --brand-100: #F5CECE; --brand-200: #E89E9E;
  --brand-300: #D86B6B; --brand-400: #BC4444; --brand-500: #7C1D1D;
  --brand-600: #6A1717; --brand-700: #561111; --brand-800: #410C0C; --brand-900: #2C0707;
}

[data-palette="emerald"] {
  --brand-50:  #E6F5EE; --brand-100: #BFE5D2; --brand-200: #82CDA8;
  --brand-300: #45B27D; --brand-400: #1F955F; --brand-500: #0E7C53;
  --brand-600: #0B6644; --brand-700: #084F35; --brand-800: #053926; --brand-900: #032217;
}

[data-palette="graphite"] {
  --brand-50:  #F1F2F5; --brand-100: #DADCE3; --brand-200: #B0B5C2;
  --brand-300: #848B9D; --brand-400: #5E647A; --brand-500: #353B50;
  --brand-600: #2A2F40; --brand-700: #20242F; --brand-800: #161821; --brand-900: #0C0D14;
}

/* ─── DARK THEME (default) ─────────────────────────────────── */

:root,
[data-theme="dark"] {
  --bg-canvas:    #22252E;   /* Notion-like, мягче чем #1e1f22 */
  --bg-panel:     #2A2D37;
  --bg-raised:    #34374A;
  --bg-hover:     #3D4153;
  --bg-sidebar:   #1E2027;
  --bg-input:     #2A2D37;
  --bg-citation:  #2A2D37;
  --bg-overlay:   rgba(20, 22, 28, 0.6);

  --border:       #3A3D4A;
  --border-faint: #2E3140;
  --border-strong:#4A4E5E;

  --text-primary:   #E8EAF0;
  --text-secondary: #A8AEC0;
  --text-tertiary:  #6F7689;

  /* Accent — на тёмном фоне используем ярче brand-300/200 */
  --accent:         var(--brand-300);
  --accent-hover:   var(--brand-200);
  --accent-subtle:  color-mix(in oklab, var(--brand-300) 16%, transparent);
  --accent-on:      #ffffff;

  --danger:   #E5484D;
  --warning:  #FFB224;
  --success:  #46A758;
  --info:     #8DA9D6;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.35);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.45);

  color-scheme: dark;
}

/* ─── LIGHT THEME ──────────────────────────────────────────── */

[data-theme="light"] {
  --bg-canvas:    #FAFAF7;   /* Тёплая бумага, не чисто-белый */
  --bg-panel:     #FFFFFF;
  --bg-raised:    #F1F1ED;
  --bg-hover:     #ECECE7;
  --bg-sidebar:   #F4F4F0;
  --bg-input:     #FFFFFF;
  --bg-citation:  #F7F7F3;
  --bg-overlay:   rgba(20, 22, 28, 0.4);

  --border:       #E2E2DA;
  --border-faint: #ECECE5;
  --border-strong:#CFCFC4;

  --text-primary:   #1A1D24;
  --text-secondary: #4F5563;
  --text-tertiary:  #8A8F9C;

  /* На светлом — насыщенный brand-500 */
  --accent:         var(--brand-500);
  --accent-hover:   var(--brand-600);
  --accent-subtle:  color-mix(in oklab, var(--brand-500) 10%, transparent);
  --accent-on:      #FFFFFF;

  --danger:   #C62828;
  --warning:  #B45309;
  --success:  #2E7D32;
  --info:     #1B3A5C;

  --shadow-sm: 0 1px 2px rgba(20, 22, 28, 0.05);
  --shadow-md: 0 4px 12px rgba(20, 22, 28, 0.08);
  --shadow-lg: 0 12px 32px rgba(20, 22, 28, 0.12);

  color-scheme: light;
}

/* ─── BACK-COMPAT aliases (старые токены имени *-primary/*-secondary) ── */
:root,
[data-theme="dark"],
[data-theme="light"] {
  --bg-primary:        var(--bg-canvas);
  --bg-secondary:      var(--bg-panel);
  --bg-tertiary:       var(--bg-raised);
  --bg-chat:           var(--bg-canvas);
  --bg-user-msg:       var(--bg-panel);
  --bg-assistant-msg:  transparent;
  --border-light:      var(--border-faint);
}

/* ─── No-transition during theme/palette switch ─── */
html.no-transition * {
  transition: none !important;
  animation-duration: 0ms !important;
}

/* ─── Global Reset ─── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #__nuxt { height: 100%; }
body {
  font-family: var(--font-sans);
  background: var(--bg-canvas);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  font-feature-settings: 'cv11', 'ss01', 'ss03';
}
h1, h2, h3, .display { font-family: var(--font-display); letter-spacing: -0.012em; }
a { color: inherit; text-decoration: none; }
button { font: inherit; }
input, textarea { font: inherit; }

/* ─── App Shell ─── */
.app-shell { display: flex; height: 100vh; overflow: hidden; }
.main-area { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }
</style>
