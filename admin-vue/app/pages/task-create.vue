<template>
  <div class="page-wrapper">
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
            style="max-width: 100%; border: 1px solid #e2e8f0; border-radius: 6px;"
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
              :disabled="
                !form.selected_qstn_cds.includes(q.qstn_cd) &&
                form.selected_qstn_cds.length >= 3
              "
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
          선택됨: {{ form.selected_qstn_cds.length }}개 (최대 3개)
        </p>
      </template>
    </div>

    <!-- Action buttons -->
    <div class="btns-area">
      <button class="btn btn-primary" @click="handleCreate">등록</button>
      <button class="btn btn-secondary" @click="router.push('/task-management')">
        취소
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  BASE_URL,
  fetchTaskImages,
  fetchQuestionPool,
  createComplianceTask,
} from "~/utils/api";
import { useTaskDates, tomorrowStr } from "~/composables/useTaskDates";

definePageMeta({ middleware: "auth" });

const { showToast } = useToast();
const router = useRouter();

const { tempDates, pickedDate, usedDates, loadUsedDates, addDate, removeDate } =
  useTaskDates();

const form = ref({
  task_nm: "",
  task_type: "ETHICS",
  pbls_yn: "Y",
  img_flnm: null as string | null,
  selected_qstn_cds: [] as string[],
});

const imageList = ref<any[]>([]);
const questionPool = ref<any[]>([]);
const qSearch = ref("");

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

async function init() {
  tempDates.value = [];
  pickedDate.value = tomorrowStr();
  await loadUsedDates();
  imageList.value = await fetchTaskImages();
  if (imageList.value.length > 0)
    form.value.img_flnm = imageList.value[0].img_flnm;
  questionPool.value = await fetchQuestionPool();
  qSearch.value = "";
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
  if (
    form.value.task_type === "SELF_CHECK" &&
    form.value.selected_qstn_cds.length > 3
  ) {
    showToast("error", "질문 문항은 최대 3개까지만 선택할 수 있습니다.");
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
    router.push("/task-management");
  } else {
    showToast("error", "서버 저장 처리 중 통신 오류가 발생했습니다.");
  }
}

onMounted(init);
</script>

<style scoped>
.row-center {
  margin: 12px 0;
}
</style>