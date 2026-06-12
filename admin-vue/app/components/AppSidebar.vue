<template>
  <aside class="sidebar">
    <div class="sidebar-top">
      <div class="logo-area">
        <img src="/kbds_logo_white.svg" alt="KBDS" class="logo-img" />
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
  if (path === "/dashboard") {
    return route.path === "/dashboard" || route.path === "/detail";
  }
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
  background: #1e222f; /* Deep dark navy */
  border-right: 1px solid #151821;
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
  padding: 24px 20px;
  border-bottom: 1px solid #282d3f;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  max-width: 160px;
  max-height: 50px;
  object-fit: contain;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 0; /* Align buttons directly to the left edge */
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-left: 3px solid transparent;
  border-radius: 0;
  font-size: 14px;
  font-weight: 500;
  color: #98a2b3; /* Muted gray/silver */
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

.nav-btn:hover .nav-icon {
  color: #ffffff;
}

.nav-btn.active {
  background: #252a37; /* Solid charcoal slate-blue highlight */
  color: #ffbc00; /* KB Yellow Positive */
  border-left-color: #ffbc00; /* KB Yellow Positive left border */
}

.nav-btn.active .nav-icon {
  color: #ffbc00;
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: inherit;
}

.sidebar-bottom {
  padding: 12px 0;
  border-top: 1px solid #282d3f;
}

.logout-btn {
  color: #98a2b3;
}

.logout-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  color: #ff5252;
}
</style>
