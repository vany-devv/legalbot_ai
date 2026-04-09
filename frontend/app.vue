<template>
  <div class="app-shell">
    <ChatSidebar v-if="showSidebar" />
    <main class="main-area">
      <NuxtPage />
    </main>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { init } = useTheme()
const { init: initAuth } = useAuth()
const { init: initSidebar } = useSidebar()

useHead({
  titleTemplate: (title) => title ? `LegalBot AI | ${title}` : 'LegalBot AI',
})

onMounted(() => {
  init()
  initAuth()
  initSidebar()
})

const authRoutes = ['/auth/login', '/auth/register']
const showSidebar = computed(() => !authRoutes.includes(route.path))
</script>

<style>
/* ─── CSS Design Tokens ─── */
:root,
[data-theme="dark"] {
  --bg-primary:        #1e1f22;
  --bg-secondary:      #26272b;
  --bg-tertiary:       #2e3035;
  --bg-hover:          #35373e;
  --bg-chat:           #1e1f22;
  --bg-input:          #2b2d31;
  --bg-user-msg:       #2b2d31;
  --bg-assistant-msg:  transparent;
  --bg-citation:       #26272b;
  --bg-sidebar:        #16171a;
  --border:            #3a3c42;
  --border-light:      #2e3035;
  --text-primary:      #f0f1f4;
  --text-secondary:    #9ea3b2;
  --text-tertiary:     #6b7080;
  --accent:            #6366f1;
  --accent-hover:      #818cf8;
  --accent-subtle:     rgba(99, 102, 241, 0.15);
  --danger:            #ef4444;
  --success:           #22c55e;
  --shadow:            0 1px 3px rgba(0, 0, 0, 0.4);
  --radius-sm:         8px;
  --radius-md:         12px;
  --radius-lg:         16px;
  --radius-full:       9999px;
  color-scheme: dark;
}

[data-theme="light"] {
  --bg-primary:        #ffffff;
  --bg-secondary:      #f7f7fb;
  --bg-tertiary:       #ededf5;
  --bg-hover:          #e4e4ef;
  --bg-chat:           #ffffff;
  --bg-input:          #f4f4fa;
  --bg-user-msg:       #eeeef8;
  --bg-assistant-msg:  transparent;
  --bg-citation:       #f7f7fb;
  --bg-sidebar:        #f2f2f8;
  --border:            #dddde8;
  --border-light:      #e8e8f2;
  --text-primary:      #0f0f1a;
  --text-secondary:    #5a5a78;
  --text-tertiary:     #9595ac;
  --accent:            #4f46e5;
  --accent-hover:      #4338ca;
  --accent-subtle:     rgba(79, 70, 229, 0.1);
  --danger:            #dc2626;
  --success:           #16a34a;
  --shadow:            0 1px 3px rgba(0, 0, 0, 0.08);
  --radius-sm:         8px;
  --radius-md:         12px;
  --radius-lg:         16px;
  --radius-full:       9999px;
  color-scheme: light;
}

/* ─── Disable all transitions during theme switch ─── */
html.no-transition * {
  transition: none !important;
}

/* ─── Global Reset ─── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #__nuxt { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; text-decoration: none; }
button { font: inherit; }
input, textarea { font: inherit; }

/* ─── App Shell ─── */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.main-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }
</style>
