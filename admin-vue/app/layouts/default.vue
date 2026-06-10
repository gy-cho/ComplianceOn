<template>
  <div class="admin-layout">
    <AppSidebar />
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #EEF0F5;
}

.main-content {
  margin-left: 220px;
  flex: 1;
  padding: 28px 28px 40px;
  min-height: 100vh;
  overflow-x: hidden;
}
</style>
