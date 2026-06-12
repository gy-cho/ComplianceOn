<template>
  <aside class="sidebar">
    <div class="sidebar-top">
      <div class="logo-area">
        <img src="/kbds_logo.png" alt="KBDS" class="logo-img" />
      </div>

      <nav class="nav-menu">
        <button
          v-for="item in menuItems"
          :key="item.path"
          class="nav-btn"
          :class="{ active: isActive(item.path) }"
          @click="navigateTo(item.path)"
        >
          <span class="nav-icon">
            <Icon :name="item.icon" />
          </span>
          {{ item.label }}
        </button>
      </nav>
    </div>

    <div class="sidebar-bottom">
      <button class="nav-btn logout-btn" @click="logout">
        <span class="nav-icon">
          <Icon name="lucide:log-out" />
        </span>
        로그아웃
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
const route = useRoute();
const router = useRouter();
const loggedIn = useCookie("kb_logged_in");

const menuItems = [
  { path: "/dashboard", icon: "lucide:layout-grid", label: "현황 조회" },
  { path: "/employee-management", icon: "lucide:users", label: "직원 관리" },
  { path: "/task-management", icon: "lucide:shield-check", label: "준법 TASK" },
];

function isActive(path: string) {
  return route.path === path;
}

function logout() {
  loggedIn.value = null;
  router.push("/");
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 200;
}

.sidebar-top {
  overflow-y: auto;
}

.logo-area {
  padding: 18px 20px 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  max-width: 160px;
  max-height: 52px;
  object-fit: contain;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 10px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #444;
  cursor: pointer;
  text-align: left;
  transition:
    background 0.18s,
    color 0.18s;
}

.nav-btn:hover {
  background: #f5f5f5;
}

.nav-btn.active {
  background: #ffbc00;
  color: #222;
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-bottom {
  padding: 10px 10px 20px;
  border-top: 1px solid #f0f0f0;
}

.logout-btn {
  color: #888;
}

.logout-btn:hover {
  background: #fff0f0;
  color: #c00;
}
</style>
