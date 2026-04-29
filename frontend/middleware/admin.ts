export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return
  const auth = useAuth()
  await auth.init()
  if (!auth.isLoggedIn.value) {
    return navigateTo(auth.buildLoginRedirect(to.fullPath), { replace: true })
  }
  if (!auth.isAdmin.value) {
    return navigateTo('/')
  }
})
