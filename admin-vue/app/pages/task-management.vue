<template>
  <div class="page-wrapper">
    <!-- ═══════════════════════════════════════════════════════ LIST MODE -->
    <template v-if="mode === 'list'">
      <div class="page-header">
        <span class="page-title">준법 TASK 현황 목록</span>
        <button class="btn btn-primary" @click="openCreate">TASK 등록</button>
      </div>

      <div v-if="taskList.length === 0" class="info-box">
        등록된 준법 관리 TASK 항목이 존재하지 않습니다.
      </div>
      <div v-else class="card">
        <div class="table-wrapper">
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
                v-for="t in taskList"
                :key="t.task_id"
                class="row-hover"
                style="cursor: pointer"
                @click="openDetail(t)"
              >
                <td>{{ t.task_nm }}</td>
                <td>
                  {{ typeLabel(t.task_type) }}
                </td>
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
    </template>

    <!-- ═══════════════════════════════════════════════════════ CREATE MODE -->
    <template v-else-if="mode === 'create'">
      <div class="page-header">
        <span class="page-title">새 TASK 등록</span>
      </div>

      <!-- Basic Info -->
      <div class="card card-has-head">
        <div class="card-section-head">기본 정보 및 정책 설정</div>
        <div class="form-group">
          <label class="form-label">TASK 명</label>
          <input
            v-model="form.task_nm"
            class="form-input"
            placeholder="예: 2026년 하반기 정보보안 서약 관리"
          />
        </div>
        <div class="row">
          <div class="col-1">
            <label class="form-label">TASK 유형 선택</label>
            <select v-model="form.task_type" class="form-select">
              <option value="ETHICS">윤리강령</option>
              <option value="SELF_CHECK">자가점검</option>
            </select>
          </div>
          <div class="col-1">
            <label class="form-label">즉시 게시 여부</label>
            <div class="radio-group" style="padding-top: 8px">
              <label class="radio-label">
                <input type="radio" v-model="form.pbls_yn" value="Y" /> 게시
              </label>
              <label class="radio-label">
                <input type="radio" v-model="form.pbls_yn" value="N" /> 미게시
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Dates -->
      <div class="card card-has-head">
        <div class="card-section-head">TASK 적용일 설정</div>
        <div v-if="usedDates.length > 0" class="warning-box">
          <p class="warning-line">
            <Icon name="lucide:alert-triangle" />
            선택 불가 안내: 다음 날짜들은 이미 다른 TASK에서 사용 중입니다.
          </p>
          <p style="padding-left: 20px">{{ usedDates.join(", ") }}</p>
        </div>
        <p v-else class="text-muted mb-8">
          TASK를 배포하거나 강제 노출할 날짜를 추가하세요.
        </p>
        <div class="row-center">
          <input
            type="date"
            v-model="pickedDate"
            :min="tomorrowStr()"
            style="flex: 1"
          />
          <button class="btn btn-secondary" @click="addDate">
            <Icon name="lucide:plus" /> 날짜 추가
          </button>
        </div>
        <div v-if="tempDates.length > 0" class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 40px">삭제</th>
                <th>선택된 적용일</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, i) in tempDates" :key="d">
                <td>
                  <input
                    type="checkbox"
                    :id="`del-c-${i}`"
                    :disabled="d < tomorrowStr()"
                    @change="removeDate(i)"
                  />
                </td>
                <td>{{ d }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="info-box">
          선택된 적용일이 없습니다. 날짜를 추가해 주세요.
        </div>
      </div>

      <!-- Content -->
      <div class="card card-has-head">
        <div class="card-section-head">상세 본문 및 문항 매핑 설정</div>

        <!-- ETHICS: image select -->
        <template v-if="form.task_type === 'ETHICS'">
          <div v-if="imageList.length > 0" class="form-group">
            <label class="form-label">서약 내용 이미지 등록 (필수)</label>
            <select v-model="form.img_flnm" class="form-select">
              <option
                v-for="img in imageList"
                :key="img.img_flnm"
                :value="img.img_flnm"
              >
                {{ img.img_flnm }}
              </option>
            </select>
          </div>
          <div v-else class="warning-box">
            서버에서 조회된 이미지 데이터가 없습니다.
          </div>
          <div v-if="form.img_flnm" class="form-group">
            <label class="form-label">이미지 미리보기</label>
            <img
              :src="`${BASE_URL}/images/${form.img_flnm}`"
              :alt="form.img_flnm"
              style="max-width:100%; border:1px solid #e2e8f0; border-radius:6px;"
            />
          </div>
        </template>

        <!-- SELF_CHECK: question multiselect -->
        <template v-else-if="form.task_type === 'SELF_CHECK'">
          <label class="form-label">점검 문항 선택</label>
          <div class="question-select-wrapper">
            <div class="question-select-search">
              <input
                v-model="qSearch"
                class="form-input"
                placeholder="문항 검색..."
                style="font-size: 13px; padding: 6px 10px"
              />
            </div>
            <label
              v-for="q in filteredQuestions"
              :key="q.qstn_cd"
              class="question-option"
            >
              <input
                type="checkbox"
                :value="q.qstn_cd"
                v-model="form.selected_qstn_cds"
              />
              <span class="question-option-text">
                [{{ q.qstn_cd }}] {{ q.qstn_nm }} - {{ q.qstn_cn }}
              </span>
            </label>
            <div
              v-if="filteredQuestions.length === 0"
              class="question-option text-muted"
            >
              검색 결과 없음
            </div>
          </div>
          <p class="text-muted mt-8">
            선택됨: {{ form.selected_qstn_cds.length }}개
          </p>
        </template>
      </div>

      <!-- Action buttons -->
      <div class="btns-area">
        <button class="btn btn-primary" @click="handleCreate">등록</button>
        <button class="btn btn-secondary" @click="mode = 'list'">취소</button>
      </div>
    </template>

    <!-- ═══════════════════════════════════════════════════════ DETAIL MODE -->
    <template v-else-if="mode === 'detail' && selectedTask">
      <div class="page-header">
        <span class="page-title">TASK 상세 정보</span>
      </div>

      <!-- Basic Info -->
      <div class="card card-has-head">
        <div class="card-section-head">기본 정보 및 정책 설정</div>
        <div class="form-group">
          <label class="form-label">TASK 명</label>
          <input v-model="form.task_nm" class="form-input" />
        </div>
        <div class="row">
          <div class="col-1">
            <label class="form-label">TASK 유형</label>
            <input
              :value="typeLabel(selectedTask.task_type)"
              class="form-input"
              disabled
            />
          </div>
          <div class="col-1">
            <label class="form-label">게시 여부 전환</label>
            <div class="radio-group" style="padding-top: 8px">
              <label class="radio-label">
                <input type="radio" v-model="form.pbls_yn" value="Y" /> 게시
              </label>
              <label class="radio-label">
                <input type="radio" v-model="form.pbls_yn" value="N" /> 미게시
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Dates -->
      <div class="card card-has-head">
        <div class="card-section-head">TASK 적용일 편집</div>
        <div v-if="otherUsedDates.length > 0" class="warning-box">
          <p class="warning-line">
            <Icon name="lucide:alert-triangle" />
            선택 불가 안내: 다음 날짜들은 다른 TASK에서 사용 중입니다.
          </p>
          <p style="padding-left: 20px">{{ otherUsedDates.join(", ") }}</p>
        </div>
        <p v-else class="text-muted mb-8">
          날짜 추가 또는 체크 해제로 삭제 처리가 가능합니다.
        </p>
        <div class="row-center">
          <input
            type="date"
            v-model="pickedDate"
            :min="tomorrowStr()"
            style="flex: 1"
          />
          <button class="btn btn-secondary" @click="addDate">
            <Icon name="lucide:plus" /> 날짜 추가
          </button>
        </div>
        <div v-if="tempDates.length > 0" class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 40px">삭제</th>
                <th>선택된 적용일</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(d, i) in tempDates" :key="d">
                <td>
                  <input
                    type="checkbox"
                    :disabled="d < tomorrowStr()"
                    @change="removeDate(i)"
                  />
                </td>
                <td>{{ d }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="info-box mt-8">
          할당된 적용일이 없습니다. 날짜를 할당해 주세요.
        </div>
      </div>

      <!-- Content -->
      <div class="card card-has-head">
        <div class="card-section-head">상세 본문 및 문항 매핑 현황</div>

        <!-- ETHICS: image view-only -->
        <template v-if="selectedTask.task_type === 'ETHICS'">
          <div v-if="imageList.length > 0" class="form-group">
            <label class="form-label">서약 내용 이미지 수정 (필수)</label>
            <select v-model="form.img_flnm" class="form-select">
              <option
                v-for="img in imageList"
                :key="img.img_flnm"
                :value="img.img_flnm"
              >
                {{ img.img_flnm }}
              </option>
            </select>
          </div>
          <div v-else class="warning-box">
            서버에서 조회된 이미지 데이터가 없습니다.
          </div>
          <div v-if="form.img_flnm" class="form-group">
            <label class="form-label">이미지 미리보기</label>
            <img
              :src="`${BASE_URL}/images/${form.img_flnm}`"
              :alt="form.img_flnm"
              style="
                max-width: 100%;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
              "
            />
          </div>
        </template>

        <!-- SELF_CHECK: read-only questions -->
        <template v-else-if="selectedTask.task_type === 'SELF_CHECK'">
          <p class="text-muted mb-8">
            본 준법 자가점검 TASK에 포함되어 있는 질문 문항 목록입니다.
          </p>
          <div v-if="detailQuestions.length > 0" class="table-wrapper">
            <table class="data-table">
              <colgroup>
                <col style="width: 10%" />
                <col style="width: 20%" />
                <col />
              </colgroup>
              <thead>
                <tr>
                  <th>질문 코드</th>
                  <th>질문 분류</th>
                  <th>질문 상세 내용</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="q in detailQuestions" :key="q.qstn_cd">
                  <td>{{ q.qstn_cd }}</td>
                  <td>{{ q.qstn_nm }}</td>
                  <td>{{ q.qstn_cn }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="info-box">매핑된 질문 문항이 없습니다.</div>
        </template>
      </div>

      <!-- Action buttons -->
      <div class="btns-area">
        <button class="btn btn-primary" @click="handleUpdate">저장</button>
        <button class="btn btn-danger" @click="handleDelete">삭제</button>
        <button class="btn btn-secondary" @click="mode = 'list'">
          목록으로
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  BASE_URL,
  fetchComplianceTasks,
  fetchTaskDates,
  fetchAllUsedDates,
  fetchTaskImages,
  fetchQuestionPool,
  fetchTaskQuestions,
  createComplianceTask,
  updateComplianceTask,
  deleteComplianceTask,
} from "~/utils/api";

definePageMeta({ middleware: "auth" });

const { showToast } = useToast();

type Mode = "list" | "create" | "detail";
const mode = ref<Mode>("list");
const taskList = ref<any[]>([]);
const selectedTask = ref<any>(null);

// Shared form state
const form = ref({
  task_nm: "",
  task_type: "ETHICS",
  pbls_yn: "Y",
  img_flnm: null as string | null,
  selected_qstn_cds: [] as string[],
});

const tempDates = ref<string[]>([]);
const pickedDate = ref(tomorrowStr());
const usedDates = ref<string[]>([]);
const imageList = ref<any[]>([]);
const questionPool = ref<any[]>([]);
const detailQuestions = ref<any[]>([]);
const qSearch = ref("");

const otherUsedDates = computed(() =>
  usedDates.value.filter((d) => !tempDates.value.includes(d)),
);

const filteredQuestions = computed(() => {
  if (!qSearch.value) return questionPool.value;
  const s = qSearch.value.toLowerCase();
  return questionPool.value.filter(
    (q) =>
      q.qstn_nm?.toLowerCase().includes(s) ||
      q.qstn_cn?.toLowerCase().includes(s) ||
      q.qstn_cd?.toLowerCase().includes(s),
  );
});

function todayStr() {
  return new Date().toISOString().split("T")[0];
}

function tomorrowStr() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().split('T')[0]
}

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

async function openCreate() {
  form.value = {
    task_nm: "",
    task_type: "ETHICS",
    pbls_yn: "Y",
    img_flnm: null,
    selected_qstn_cds: [],
  };
  tempDates.value = [];
  pickedDate.value = tomorrowStr();
  usedDates.value = await fetchAllUsedDates();
  imageList.value = await fetchTaskImages();
  if (imageList.value.length > 0)
    form.value.img_flnm = imageList.value[0].img_flnm;
  questionPool.value = await fetchQuestionPool();
  qSearch.value = "";
  mode.value = "create";
}

async function openDetail(task: any) {
  selectedTask.value = task;
  form.value = {
    task_nm: task.task_nm,
    task_type: task.task_type,
    pbls_yn: task.pbls_yn,
    img_flnm: task.img_flnm ?? null,
    selected_qstn_cds: [],
  };
  const dates = await fetchTaskDates(task.task_id);
  tempDates.value = dates.map((d: any) => d.task_app_dt);
  pickedDate.value = tomorrowStr();
  const allUsed = await fetchAllUsedDates();
  usedDates.value = allUsed.filter((d) => !tempDates.value.includes(d));
  imageList.value = await fetchTaskImages();
  if (task.task_type === "ETHICS" && imageList.value.length > 0) {
    const saved = task.img_flnm;
    form.value.img_flnm = imageList.value.some((i) => i.img_flnm === saved)
      ? saved
      : imageList.value[0].img_flnm;
  }
  if (task.task_type === "SELF_CHECK") {
    const mappedCds = await fetchTaskQuestions(task.task_id);
    questionPool.value = await fetchQuestionPool();
    detailQuestions.value = questionPool.value.filter((q) =>
      mappedCds.includes(q.qstn_cd),
    );
  }
  mode.value = "detail";
}

function addDate() {
  const d = pickedDate.value;
  if (!d) return;
  if (d < tomorrowStr()) {
    showToast('error', '오늘 이전 날짜는 추가할 수 없습니다.')
    return
  }
  if (usedDates.value.includes(d) && !tempDates.value.includes(d)) {
    showToast("error", "이미 다른 TASK에서 사용 중인 날짜입니다.");
    return;
  }
  if (tempDates.value.includes(d)) {
    showToast("warning", "이미 현재 목록에 추가된 날짜입니다.");
    return;
  }
  tempDates.value.push(d);
}

function removeDate(index: number) {
  const d = tempDates.value[index];
  if (d < tomorrowStr()) {
    showToast("warning", "오늘 이전 날짜는 삭제할 수 없습니다.");
    return;
  }
  tempDates.value.splice(index, 1);
}

async function handleCreate() {
  if (!form.value.task_nm.trim()) {
    showToast("error", "TASK 명을 입력해 주세요.");
    return;
  }
  if (tempDates.value.length === 0) {
    showToast("error", "최소 1개 이상의 적용 날짜를 추가하셔야 합니다.");
    return;
  }
  if (form.value.task_type === "ETHICS" && !form.value.img_flnm) {
    showToast("error", "서약 이미지를 선택해야 합니다.");
    return;
  }
  if (
    form.value.task_type === "SELF_CHECK" &&
    form.value.selected_qstn_cds.length === 0
  ) {
    showToast("error", "최소 1개 이상의 질문 문항을 매핑해야 합니다.");
    return;
  }
  const payload = {
    task_nm: form.value.task_nm,
    task_type: form.value.task_type,
    task_cn: null,
    rcrn_yn: "N",
    pbls_yn: form.value.pbls_yn,
    img_flnm: form.value.task_type === "ETHICS" ? form.value.img_flnm : null,
    selected_qstn_cds:
      form.value.task_type === "SELF_CHECK" ? form.value.selected_qstn_cds : [],
    app_dates: tempDates.value,
    emp_no: "admin",
  };
  const status = await createComplianceTask(payload);
  if (status === 200) {
    showToast("success", "새로운 준법 제어 TASK가 DB에 등록되었습니다.");
    await loadList();
    mode.value = "list";
  } else {
    showToast("error", "서버 저장 처리 중 통신 오류가 발생했습니다.");
  }
}

async function handleUpdate() {
  if (tempDates.value.length === 0) {
    showToast("error", "최소 하나 이상의 적용 날짜가 유지되어야 합니다.");
    return;
  }
  if (!form.value.task_nm.trim()) {
    showToast("error", "TASK 명은 비워둘 수 없습니다.");
    return;
  }
  if (selectedTask.value?.task_type === "ETHICS" && !form.value.img_flnm) {
    showToast("error", "서약 이미지를 선택해야 합니다.");
    return;
  }
  const payload = {
    task_id: Number(selectedTask.value.task_id),
    task_nm: form.value.task_nm,
    task_cn: null,
    pbls_yn: form.value.pbls_yn,
    img_flnm:
      selectedTask.value.task_type === "ETHICS" ? form.value.img_flnm : null,
    app_dates: tempDates.value,
    emp_no: "admin",
  };
  const status = await updateComplianceTask(payload);
  if (status === 200) {
    showToast("success", "준법 제어 변경사항이 갱신되었습니다.");
    await loadList();
    mode.value = "list";
  } else {
    showToast("error", "수정 요청 처리 중 에러가 발생했습니다.");
  }
}

async function handleDelete() {
  const status = await deleteComplianceTask(selectedTask.value.task_id);
  if (status === 200) {
    showToast("success", "해당 관리 TASK가 삭제되었습니다.");
    await loadList();
    mode.value = "list";
  } else {
    showToast("error", "삭제 요청 처리 중 에러가 발생했습니다.");
  }
}

onMounted(loadList);
</script>

<style scoped>
.row-center {
  margin: 12px 0;
}
</style>
