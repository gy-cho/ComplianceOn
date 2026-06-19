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
    <div class="card card-has-head">
      <div class="card-section-head">준법 항목 및 적용일 선택</div>
      <div class="row-center">
        <div style="flex: 3">
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
        <div
          class="metric-card"
          :class="{ active: statusFilter === '전체' }"
          @click="statusFilter = '전체'"
        >
          <div class="metric-label">대상자 총원</div>
          <div class="metric-value">{{ totalCount }}명</div>
          <div class="metric-sub">전체 대상자 보기</div>
        </div>
        <div
          class="metric-card"
          :class="{ active: statusFilter === '완료' }"
          @click="statusFilter = '완료'"
        >
          <div class="metric-label">답변 완료</div>
          <div class="metric-value completed">{{ doneCount }}명</div>
          <div class="metric-sub completed">
            완료자 보기 (오늘 +{{ todayDone }}명)
          </div>
        </div>
        <div
          class="metric-card"
          :class="{ active: statusFilter === '미완료' }"
          @click="statusFilter = '미완료'"
        >
          <div class="metric-label">미답변</div>
          <div class="metric-value pending">{{ pendingCount }}명</div>
          <div class="metric-sub pending">미답변자 보기</div>
        </div>
      </div>
    </template>

    <!-- Card 2: Table -->
    <div
      v-if="selectedTaskId && selectedAppSeq !== null && !loading"
      class="card"
    >
      <div class="row-center" style="margin-bottom: 16px">
        <div class="input-icon-wrap" style="flex: 3">
          <Icon name="lucide:search" class="input-icon" />
          <input
            v-model="searchText"
            class="form-input has-icon"
            placeholder="직원명, 직원번호 입력"
          />
        </div>
        <div style="flex: 1">
          <select v-model="statusFilter" class="form-select">
            <option>답변여부 전체</option>
            <option>완료</option>
            <option>미완료</option>
          </select>
        </div>
        <div style="flex: 1">
          <select v-model="agreeFilter" class="form-select">
            <option>정상답변여부 전체</option>
            <option>정상</option>
            <option>비정상</option>
          </select>
        </div>
        <button class="btn btn-reset" @click="resetSearch">
          <Icon name="lucide:x" /> 초기화
        </button>
        <button
          class="btn btn-excel"
          :disabled="filteredAnswers.length === 0"
          @click="downloadExcel"
        >
          <Icon name="lucide:download" />
          엑셀 다운로드
        </button>
      </div>

      <template v-if="filteredAnswers.length > 0">
        <div class="table-wrapper">
          <table class="data-table">
            <colgroup>
              <col style="width: 110px" />
              <col style="width: 100px" />
              <col style="width: auto" />
              <col style="width: 130px" />
              <col style="width: 100px" />
              <col style="width: 100px" />
              <col style="width: 200px" />
            </colgroup>
            <thead>
              <tr>
                <th>직원명</th>
                <th>직원번호</th>
                <th>준법명</th>
                <th>IP 주소</th>
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
                <td>{{ row.emp_nm }}</td>
                <td>{{ row.emp_no }}</td>
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
                        : 'badge badge-warning'
                    "
                  >
                    {{ isAnswered(row) ? "완료" : "미완료" }}
                  </span>
                </td>
                <td>
                  <span
                    v-if="isAnswered(row)"
                    :class="
                      isAgreed(row) ? 'badge badge-info' : 'badge badge-error'
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
import * as XLSX from "xlsx";

definePageMeta({ middleware: "auth" });

const router = useRouter();
const { showToast } = useToast();

const taskList = ref<any[]>([]);
const selectedTaskId = ref<number | null>(null);
const selectedAppSeq = ref<number | null>(null);
const answers = ref<any[]>([]);
const loading = ref(false);
const statusFilter = ref("답변여부 전체");
const agreeFilter = ref("정상답변여부 전체");
const searchText = ref("");

const today = new Date().toISOString().split("T")[0];

const currentTask = computed(() =>
  taskList.value.find((t) => t.task_id === selectedTaskId.value),
);

const appSeqOptions = computed(() => {
  const dt = currentTask.value?.task_app_dt;
  if (!dt || dt.length === 0) return [];
  const opts = [{ seq: 0, label: "답변여부 전체" }];
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
  if (agreeFilter.value === "정상")
    data = data.filter((r) => isAnswered(r) && isAgreed(r));
  else if (agreeFilter.value === "비정상")
    data = data.filter((r) => isAnswered(r) && !isAgreed(r));
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

function resetSearch() {
  searchText.value = "";
  statusFilter.value = "답변여부 전체";
  agreeFilter.value = "정상답변여부 전체";
}

function handleRowClick(row: any) {
  if (currentTask.value.task_type === "ETHICS") {
    return;
  }

  if (!isAnswered(row)) {
    showToast("warning", "해당 직원은 아직 답변을 완료하지 않았습니다.");
    return;
  }
  router.push({
    path: "/answer-detail",
    query: {
      task_id: String(row.task_id ?? selectedTaskId.value),
      app_seq: String(row.app_seq ?? selectedAppSeq.value),
      emp_no: String(row.emp_no),
      emp_nm: String(row.emp_nm),
    },
  });
}

function downloadExcel() {
  const rows = filteredAnswers.value.map((row) => ({
    직원명: row.emp_nm,
    직원번호: row.emp_no,
    준법명: `${row.task_nm}(${row.app_seq}회차) - ${row.task_app_dt}`,
    "IP 주소": row.ip || "-",
    답변여부: isAnswered(row) ? "완료" : "미완료",
    정상답변여부: isAnswered(row) ? (isAgreed(row) ? "정상" : "비정상") : "-",
    답변일시: row.ans_dt || "-",
  }));

  const worksheet = XLSX.utils.json_to_sheet(rows);
  worksheet["!cols"] = [
    { wch: 12 },
    { wch: 12 },
    { wch: 35 },
    { wch: 16 },
    { wch: 10 },
    { wch: 12 },
    { wch: 20 },
  ];
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "현황조회");

  const taskNm = currentTask.value?.task_nm ?? "현황조회";
  const dateStr = new Date().toISOString().split("T")[0];
  XLSX.writeFile(workbook, `${taskNm}_${dateStr}.xlsx`);
}

onMounted(loadTasks);
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
</style>