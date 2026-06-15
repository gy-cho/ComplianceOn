<template>
  <div class="auth-layout">
    <slot />
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #2f3443 0%, #1e222f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
