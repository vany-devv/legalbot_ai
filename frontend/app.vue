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

onMounted(() => init())

const authRoutes = ['/auth/login', '/auth/register']
const showSidebar = computed(() => !authRoutes.includes(route.path))
</script>

<style>
/* ─── CSS Variables ─── */
:root,
[data-theme="dark"] {
  --bg-primary: #0a0a0a;
  --bg-secondary: #141414;
  --bg-tertiary: #1a1a1a;
  --bg-hover: #222222;
  --bg-chat: #0a0a0a;
  --bg-input: #1a1a1a;
  --bg-user-msg: #1a1a1a;
  --bg-assistant-msg: transparent;
  --bg-citation: #141414;
  --bg-sidebar: #0f0f0f;
  --border: #262626;
  --border-light: #1f1f1f;
  --text-primary: #f5f5f5;
  --text-secondary: #a0a0a0;
  --text-tertiary: #666666;
  --accent: #7c6aef;
  --accent-hover: #8f7ff2;
  --accent-subtle: rgba(124, 106, 239, 0.12);
  --danger: #ef4444;
  --success: #22c55e;
  --shadow: 0 1px 3px rgba(0,0,0,0.4);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;
  color-scheme: dark;
}

[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f7f7f8;
  --bg-tertiary: #efefef;
  --bg-hover: #e8e8e8;
  --bg-chat: #ffffff;
  --bg-input: #f7f7f8;
  --bg-user-msg: #f0f0f1;
  --bg-assistant-msg: transparent;
  --bg-citation: #f7f7f8;
  --bg-sidebar: #f7f7f8;
  --border: #e0e0e0;
  --border-light: #ebebeb;
  --text-primary: #111111;
  --text-secondary: #6b6b6b;
  --text-tertiary: #999999;
  --accent: #6b54d9;
  --accent-hover: #5a45c4;
  --accent-subtle: rgba(107, 84, 217, 0.08);
  --danger: #dc2626;
  --success: #16a34a;
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;
  color-scheme: light;
}

/* ─── Global Reset ─── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #__nuxt { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, Oxygen, Ubuntu, sans-serif;
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
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }
</style>
