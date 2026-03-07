<template>
  <aside class="sidebar">
    <div class="sidebar-top">
      <button class="new-chat-btn" @click="handleNewChat">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Новый чат
      </button>
    </div>

    <div class="sidebar-conversations">
      <div
        v-for="conv in conversations"
        :key="conv.id"
        class="conv-item"
        :class="{ active: conv.id === currentConversationId }"
        @click="handleOpen(conv.id)"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span class="conv-title">{{ conv.title }}</span>
      </div>
      <div v-if="!conversations.length" class="conv-empty">
        Нет диалогов
      </div>
    </div>

    <div class="sidebar-bottom">
      <NuxtLink to="/settings" class="sidebar-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        Настройки
      </NuxtLink>
      <NuxtLink to="/subscription" class="sidebar-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        Подписка
      </NuxtLink>
      <ThemeToggle />
      <template v-if="isLoggedIn">
        <div class="sidebar-user">
          <span class="user-email">{{ user?.email }}</span>
          <button class="logout-btn" @click="logout">Выйти</button>
        </div>
      </template>
      <NuxtLink v-else to="/auth/login" class="sidebar-link login-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
        Войти
      </NuxtLink>
    </div>
  </aside>
</template>

<script setup lang="ts">
const { conversations, currentConversationId, newChat, loadConversations } = useChat()
const { user, isLoggedIn, logout, init } = useAuth()
const router = useRouter()

onMounted(async () => {
  init()
  await loadConversations()
})

function handleNewChat() {
  newChat()
  router.push('/')
}

function handleOpen(id: string) {
  router.push(`/chat/${id}`)
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
}

.sidebar-top {
  padding: 12px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.new-chat-btn:hover { background: var(--bg-hover); }

.sidebar-conversations {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  transition: background 0.12s, color 0.12s;
}
.conv-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.conv-item.active { background: var(--accent-subtle); color: var(--text-primary); }

.conv-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-empty {
  padding: 16px 10px;
  font-size: 13px;
  color: var(--text-tertiary);
  text-align: center;
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
  transition: background 0.12s, color 0.12s;
}
.sidebar-link:hover { background: var(--bg-hover); color: var(--text-primary); }

.sidebar-user {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
}
.user-email {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 13px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
}
.logout-btn:hover { color: var(--danger); background: var(--bg-hover); }
</style>
