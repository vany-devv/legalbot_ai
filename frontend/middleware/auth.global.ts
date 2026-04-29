export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuth()
  const isPublicAuthRoute = to.path === '/auth/login' || to.path === '/auth/register'

  if (import.meta.server) {
    if (!auth.hasStoredToken() && !isPublicAuthRoute) {
      return navigateTo(auth.buildLoginRedirect(to.fullPath), { replace: true })
    }
    return
  }

  await auth.init()

  if (!auth.isLoggedIn.value && !isPublicAuthRoute) {
    return navigateTo(auth.buildLoginRedirect(to.fullPath), { replace: true })
  }

  if (auth.isLoggedIn.value && isPublicAuthRoute) {
    return navigateTo(auth.resolvePostAuthRedirect(to.query.next), { replace: true })
  }
})
