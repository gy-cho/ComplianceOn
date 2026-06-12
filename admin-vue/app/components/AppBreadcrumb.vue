<template>
  <div class="breadcrumb-bar">
    <nav class="breadcrumb">
      <NuxtLink to="/dashboard" class="breadcrumb-item breadcrumb-home">
        <Icon name="lucide:home" />
      </NuxtLink>
      <template v-for="(crumb, i) in crumbs" :key="crumb.path">
        <Icon name="lucide:chevron-right" class="breadcrumb-sep" />
        <NuxtLink
          v-if="i < crumbs.length - 1"
          :to="crumb.path"
          class="breadcrumb-item"
        >
          {{ crumb.label }}
        </NuxtLink>
        <span v-else class="breadcrumb-item current">{{ crumb.label }}</span>
      </template>
    </nav>
  </div>
</template>

<script setup lang="ts">
const route = useRoute();

const routeMap: Record<string, string> = {
  "/dashboard": "현황 조회",
  "/detail": "사원 상세 답변 내역",
  "/employee-management": "직원 관리",
  "/task-management": "준법 TASK",
};

const crumbs = computed(() => {
  const path = route.path;
  const items: { path: string; label: string }[] = [];

  // Detail page is a child of dashboard
  if (path === "/detail") {
    items.push({ path: "/dashboard", label: "현황 조회" });
    items.push({ path, label: `답변 상세` });
  } else {
    const label = routeMap[path] ?? path.replace("/", "");
    items.push({ path, label });
  }

  return items;
});
</script>

<style scoped>
.breadcrumb-bar {
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
  padding: 12px 28px;
  margin: -28px -28px 24px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-muted);
}

.breadcrumb-home {
  display: inline-flex;
  align-items: center;
  color: var(--text-muted);
  transition: color 0.15s;
  font-size: 15px;
}

.breadcrumb-home:hover {
  color: var(--text-primary);
}

.breadcrumb-sep {
  font-size: 12px;
  color: #c0c0c0;
  flex-shrink: 0;
}

.breadcrumb-item {
  text-decoration: none;
  color: var(--text-muted);
  transition: color 0.15s;
  white-space: nowrap;
}

.breadcrumb-item:hover:not(.current) {
  color: var(--text-primary);
}

.breadcrumb-item.current {
  color: var(--text-primary);
  font-weight: 500;
}
</style>
