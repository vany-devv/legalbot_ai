<template>
  <div class="app">
    <header class="header">
      <div class="brand">LegalBot</div>
      <nav class="nav">
        <NuxtLink to="/ingest" class="nav-link">Ingest</NuxtLink>
        <NuxtLink to="/search" class="nav-link">Search</NuxtLink>
        <NuxtLink to="/answer" class="nav-link">Answer</NuxtLink>
      </nav>
    </header>
    <main class="container">
      <NuxtPage />
    </main>
  </div>
  
</template>

<style>
:root {
  color-scheme: dark;
}
html, body, #__nuxt { height: 100%; }
body { margin: 0; }
.app {
  min-height: 100%;
  background: #0b0d12;
  color: #e6e8ec;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
}
.header {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid #1b1f2a;
  background: rgba(11, 13, 18, 0.8);
  backdrop-filter: blur(8px);
}
.brand {
  font-weight: 700;
  letter-spacing: 0.5px;
}
.nav { display: flex; gap: 12px; }
.nav-link {
  color: #9ab5ff;
  text-decoration: none;
  padding: 6px 10px;
  border-radius: 8px;
}
.nav-link.router-link-active {
  background: #122042;
  color: #cfe0ff;
}
.container {
  max-width: 980px;
  margin: 24px auto;
  padding: 0 16px;
}

label { font-weight: 600; color: #cbd5e1; }
input, textarea, select {
  width: 100%;
  padding: 10px 12px;
  box-sizing: border-box;
  border-radius: 10px;
  border: 1px solid #1f2937;
  background: #0f131a;
  color: #e6e8ec;
}
button {
  padding: 10px 14px;
  cursor: pointer;
  border: 1px solid #20355b;
  background: linear-gradient(180deg, #163059, #0f1e3d);
  color: #d6e1ff;
  border-radius: 10px;
}
button:disabled { opacity: 0.6; cursor: not-allowed; }
.card {
  border: 1px solid #1b2230;
  background: #0d1117;
  border-radius: 12px;
  padding: 14px;
}
.muted { color: #9aa4b2; }
.row { display:flex; gap: 12px; align-items: center; }
.gap { display:flex; gap: 8px; }
.spacer { height: 12px; }
.list { display: grid; gap: 10px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
</style>


