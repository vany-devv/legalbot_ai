export default defineNuxtRouteMiddleware(async (to) => {
  // SSR отключён (nuxt.config.ts: ssr: false), middleware всегда на клиенте.
  const auth = useAuth()
  const isPublicAuthRoute = to.path === '/auth/login' || to.path === '/auth/register'

  await auth.init()

  if (!auth.isLoggedIn.value && !isPublicAuthRoute) {
    return navigateTo(auth.buildLoginRedirect(to.fullPath), { replace: true })
  }

  if (auth.isLoggedIn.value && isPublicAuthRoute) {
    return navigateTo(auth.resolvePostAuthRedirect(to.query.next), { replace: true })
  }
})
