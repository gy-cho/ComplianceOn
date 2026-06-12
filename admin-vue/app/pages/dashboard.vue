<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <span class="page-title">현황 조회</span>
      <button class="btn btn-secondary" @click="refresh">
        <Icon name="lucide:rotate-cw" />
        새로고침
      </button>
    </div>

    <!-- Card 1: Task + AppSeq selection -->
    <div class="card">
      <div class="card-section-title">■ 준법 항목 및 적용일 선택</div>
      <div class="row" style="gap: 12px">
        <div style="flex: 2.5">
          <select
            v-model="selectedTaskId"
            class="form-select"
            :disabled="taskList.length === 0"
            @change="onTaskChange"
          >
            <option v-if="taskList.length === 0" :value="null">
              등록된 준법 항목이 없습니다.
            </option>
            <option v-for="t in taskList" :key="t.task_id" :value="t.task_id">
              {{ t.task_nm }}
            </option>
          </select>
        </div>
        <div style="flex: 1">
          <template v-if="appSeqOptions.length > 0">
            <select
              v-model="selectedAppSeq"
              class="form-select"
              @change="onSeqChange"
            >
              <option
                v-for="opt in appSeqOptions"
                :key="opt.seq"
                :value="opt.seq"
              >
                {{ opt.label }}
              </option>
            </select>
          </template>
          <div v-else class="info-box" style="padding: 8px 12px">
            할당된 적용일 없음
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="spinner-wrap">데이터를 불러오는 중...</div>

    <template
      v-else-if="
        selectedTaskId && selectedAppSeq !== null && answers.length > 0
      "
    >
      <!-- Stats Cards -->
      <div class="stats-row">
        <div class="metric-card">
          <div class="metric-label">대상자 총원</div>
          <div class="metric-value">{{ totalCount }} 명</div>
          <div class="metric-sub">DB 등록 기준</div>
          <button
            class="btn btn-secondary btn-sm mt-8"
            @click="statusFilter = '전체'"
          >
            전체 대상자 보기
          </button>
        </div>
        <div class="metric-card">
          <div class="metric-label">답변 완료</div>
          <div class="metric-value yellow">{{ doneCount }} 명</div>
          <div class="metric-sub green">(오늘 +{{ todayDone }}명 완료)</div>
          <button
            class="btn btn-secondary btn-sm mt-8"
            @click="statusFilter = '완료'"
          >
            답변 완료자 보기
          </button>
        </div>
        <div class="metric-card">
          <div class="metric-label">미답변(진행중)</div>
          <div class="metric-value red">{{ pendingCount }} 명</div>
          <div class="metric-sub">미답변자 {{ pendingCount }}명</div>
          <button
            class="btn btn-secondary btn-sm mt-8"
            @click="statusFilter = '미완료'"
          >
            미답변자 보기
          </button>
        </div>
      </div>
    </template>

    <!-- Card 2: Table -->
    <div
      v-if="selectedTaskId && selectedAppSeq !== null && !loading"
      class="card"
    >
      <div class="row-center" style="gap: 12px; margin-bottom: 14px">
        <input
          v-model="searchText"
          class="form-input"
          placeholder="이름, 사원번호 입력"
          style="flex: 3.6"
        />
        <select v-model="statusFilter" class="form-select" style="flex: 1">
          <option>전체</option>
          <option>완료</option>
          <option>미완료</option>
        </select>
      </div>

      <template v-if="filteredAnswers.length > 0">
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>이름</th>
                <th>준법명</th>
                <th>IP</th>
                <th>답변여부</th>
                <th>정상답변여부</th>
                <th>답변일시</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in filteredAnswers"
                :key="`${row.emp_no}-${row.app_seq}`"
                class="row-hover"
                :class="{ clickable: isAnswered(row) }"
                @click="handleRowClick(row)"
                :title="isAnswered(row) ? '클릭하여 상세 보기' : ''"
              >
                <td>{{ row.emp_nm }} ({{ row.emp_no }})</td>
                <td>
                  {{ row.task_nm }}({{ row.app_seq }}회차) -
                  {{ row.task_app_dt }}
                </td>
                <td>{{ row.ip || "-" }}</td>
                <td>
                  <span
                    :class="
                      isAnswered(row)
                        ? 'badge badge-success'
                        : 'badge badge-error'
                    "
                  >
                    {{ isAnswered(row) ? "완료" : "미완료" }}
                  </span>
                </td>
                <td>
                  <span
                    v-if="isAnswered(row)"
                    :class="
                      isAgreed(row)
                        ? 'badge badge-success'
                        : 'badge badge-error'
                    "
                  >
                    {{ isAgreed(row) ? "정상" : "비정상" }}
                  </span>
                  <span v-else class="text-muted">-</span>
                </td>
                <td>{{ row.ans_dt || "-" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <div v-else class="info-box mt-8">
        {{
          answers.length === 0
            ? "선택된 준법 항목에 해당하는 답변 로그 데이터가 존재하지 않습니다."
            : "검색 조건에 해당하는 결과가 없습니다."
        }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchEmpAnswers, fetchComplianceTasks } from "~/utils/api";

definePageMeta({ middleware: "auth" });

const router = useRouter();
const { showToast } = useToast();

const taskList = ref<any[]>([]);
const selectedTaskId = ref<number | null>(null);
const selectedAppSeq = ref<number | null>(null);
const answers = ref<any[]>([]);
const loading = ref(false);
const statusFilter = ref("전체");
const searchText = ref("");

const today = new Date().toISOString().split("T")[0];

const currentTask = computed(() =>
  taskList.value.find((t) => t.task_id === selectedTaskId.value),
);

const appSeqOptions = computed(() => {
  const dt = currentTask.value?.task_app_dt;
  if (!dt || dt.length === 0) return [];
  const opts = [{ seq: 0, label: "전체" }];
  const sorted = [...dt].sort((a, b) => a.app_seq - b.app_seq);
  for (const d of sorted) {
    opts.push({ seq: d.app_seq, label: `${d.task_app_dt} (${d.app_seq}회차)` });
  }
  return opts;
});

const totalCount = computed(() => answers.value.length);
const doneCount = computed(() => answers.value.filter(isAnswered).length);
const pendingCount = computed(
  () => answers.value.filter((r) => !isAnswered(r)).length,
);
const todayDone = computed(
  () =>
    answers.value.filter(
      (r) => isAnswered(r) && (r.ans_dt ?? "").includes(today),
    ).length,
);

const filteredAnswers = computed(() => {
  let data = [...answers.value];
  if (statusFilter.value === "완료") data = data.filter(isAnswered);
  else if (statusFilter.value === "미완료")
    data = data.filter((r) => !isAnswered(r));
  if (searchText.value) {
    const s = searchText.value.toLowerCase();
    data = data.filter(
      (r) =>
        String(r.emp_nm).toLowerCase().includes(s) ||
        String(r.emp_no).toLowerCase().includes(s),
    );
  }
  return data;
});

function isAnswered(row: any) {
  return row.emp_main_ans_yn === "Y" || row.emp_main_ans_yn === true;
}

function isAgreed(row: any) {
  return row.emp_ans_agr_yn === "Y" || row.emp_ans_agr_yn === true;
}

async function loadTasks() {
  const { status, data } = await fetchComplianceTasks();
  if (status === 200 && data.length > 0) {
    taskList.value = data;
    selectedTaskId.value = data[0].task_id;
    const dt = data[0].task_app_dt;
    if (dt && dt.length > 0) {
      selectedAppSeq.value = 0;
      await loadAnswers();
    }
  }
}

async function loadAnswers() {
  if (!selectedTaskId.value) return;
  loading.value = true;
  answers.value = await fetchEmpAnswers(
    selectedTaskId.value,
    selectedAppSeq.value ?? undefined,
  );
  loading.value = false;
}

async function onTaskChange() {
  selectedAppSeq.value = appSeqOptions.value[0]?.seq ?? null;
  answers.value = [];
  if (selectedAppSeq.value !== null) await loadAnswers();
}

async function onSeqChange() {
  answers.value = [];
  await loadAnswers();
}

async function refresh() {
  answers.value = [];
  await loadAnswers();
  showToast("success", "데이터가 새로고침 되었습니다!");
}

function handleRowClick(row: any) {
  if (currentTask.value.task_type === "ETHICS") {
    return;
  }

  if (!isAnswered(row)) {
    showToast("info", "해당 사원은 아직 답변을 완료하지 않았습니다.");
    return;
  }
  router.push({
    path: "/detail",
    query: {
      task_id: String(row.task_id ?? selectedTaskId.value),
      app_seq: String(row.app_seq ?? selectedAppSeq.value),
      emp_no: String(row.emp_no),
      emp_nm: String(row.emp_nm),
    },
  });
}

onMounted(loadTasks);
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
</style>
