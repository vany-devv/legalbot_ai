export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return
  const { isAdmin, isLoggedIn } = useAuth()
  if (!isLoggedIn.value || !isAdmin.value) {
    return navigateTo('/')
  }
})
