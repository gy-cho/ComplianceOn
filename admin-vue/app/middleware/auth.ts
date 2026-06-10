export default defineNuxtRouteMiddleware((to) => {
  const loggedIn = useCookie('kb_logged_in')

  if (loggedIn.value !== 'true' && to.path !== '/') {
    return navigateTo('/')
  }

  if (loggedIn.value === 'true' && to.path === '/') {
    return navigateTo('/dashboard')
  }
})
