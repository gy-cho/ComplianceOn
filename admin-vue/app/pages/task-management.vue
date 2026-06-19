<template>
  <div class="page-wrapper">
    <div class="page-header">
      <span class="page-title">준법 TASK 현황 목록</span>
      <button class="btn btn-primary" @click="router.push('/task-create')">
        TASK 등록
      </button>
    </div>

    <div v-if="taskList.length === 0" class="info-box">
      등록된 준법 관리 TASK 항목이 존재하지 않습니다.
    </div>
    <div v-else class="card">
      <div class="row-center" style="margin-bottom: 16px">
        <div class="input-icon-wrap" style="flex: 2">
          <Icon name="lucide:search" class="input-icon" />
          <input
            v-model="searchText"
            class="form-input has-icon"
            placeholder="TASK 명 검색"
          />
        </div>
        <div style="flex: 1">
          <select v-model="typeFilter" class="form-select">
            <option value="ALL">TASK유형 전체</option>
            <option value="ETHICS">윤리강령</option>
            <option value="SELF_CHECK">자가점검</option>
          </select>
        </div>
        <div style="flex: 1">
          <select v-model="statusFilter" class="form-select">
            <option value="ALL">게시여부 전체</option>
            <option value="Y">게시중</option>
            <option value="N">미게시</option>
          </select>
        </div>
      </div>

      <div v-if="filteredTasks.length === 0" class="info-box">
        검색 결과가 없습니다.
      </div>
      <div v-else class="table-wrapper">
        <table class="data-table">
          <colgroup>
            <col />
            <col style="width: 30%" />
            <col style="width: 30%" />
          </colgroup>
          <thead>
            <tr>
              <th>TASK 명</th>
              <th>TASK 유형</th>
              <th>게시여부</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in filteredTasks"
              :key="t.task_id"
              class="row-hover"
              style="cursor: pointer"
              @click="router.push(`/task-detail?task_id=${t.task_id}`)"
            >
              <td>{{ t.task_nm }}</td>
              <td>{{ typeLabel(t.task_type) }}</td>
              <td>
                <span
                  :class="
                    t.pbls_yn === 'Y'
                      ? 'badge badge-success'
                      : 'badge badge-gray'
                  "
                >
                  {{ t.pbls_yn === "Y" ? "게시중" : "미게시" }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchComplianceTasks } from "~/utils/api";

definePageMeta({ middleware: "auth" });

const router = useRouter();
const taskList = ref<any[]>([]);
const searchText = ref("");
const statusFilter = ref("ALL");
const typeFilter = ref("ALL");

const filteredTasks = computed(() => {
  let result = taskList.value;
  if (typeFilter.value !== "ALL") {
    result = result.filter((t) => t.task_type === typeFilter.value);
  }
  if (statusFilter.value !== "ALL") {
    result = result.filter((t) => t.pbls_yn === statusFilter.value);
  }
  if (searchText.value.trim()) {
    const s = searchText.value.toLowerCase();
    result = result.filter((t) =>
      String(t.task_nm ?? "").toLowerCase().includes(s),
    );
  }
  return result;
});

function typeLabel(type: string) {
  return type === "ETHICS"
    ? "윤리강령"
    : type === "SELF_CHECK"
      ? "자가점검"
      : type;
}

async function loadList() {
  const { status, data } = await fetchComplianceTasks();
  if (status === 200) taskList.value = data;
}

// 등록/상세 화면에서 돌아올 때마다 최신 목록을 다시 조회
onMounted(loadList);
onActivated(loadList);
</script>