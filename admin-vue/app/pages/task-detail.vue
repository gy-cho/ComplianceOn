<template>
  <div class="page-wrapper">
    <div v-if="loading" class="spinner-wrap">TASK 정보를 불러오는 중...</div>

    <template v-else-if="!selectedTask">
      <div class="info-box" style="background: #ffebee; border-color: #ffcdd2; color: #c62828">
        TASK 정보를 조회할 수 없습니다.
      </div>
    </template>

    <template v-else>
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
              style="max-width: 100%; border: 1px solid #e2e8f0; border-radius: 6px;"
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
        <button class="btn btn-danger" @click="showDeleteModal = true">삭제</button>
        <button class="btn btn-secondary" @click="router.push('/task-management')">
          목록으로
        </button>
      </div>

      <!-- ── Delete Confirm Modal ── -->
      <div
        v-if="showDeleteModal"
        class="modal-overlay"
        @click.self="showDeleteModal = false"
      >
        <div class="modal-box">
          <div class="modal-title">TASK 삭제 확인</div>
          <p style="font-size: 14px; margin-bottom: 8px">
            <strong>{{ selectedTask?.task_nm }}</strong> TASK를 정말
            삭제하시겠습니까?
          </p>
          <p class="text-muted">삭제된 TASK는 복구할 수 없습니다.</p>
          <p class="text-muted">
            이미 직원 답변이 등록된 TASK는 삭제가 제한됩니다.
          </p>
          <div class="modal-footer">
            <button class="btn btn-primary" @click="confirmDelete">
              최종 확인 및 삭제
            </button>
            <button class="btn btn-secondary" @click="showDeleteModal = false">
              취소
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  BASE_URL,
  fetchComplianceTasks,
  fetchTaskDates,
  fetchTaskImages,
  fetchQuestionPool,
  fetchTaskQuestions,
  updateComplianceTask,
  deleteComplianceTask,
} from "~/utils/api";
import { useTaskDates, tomorrowStr } from "~/composables/useTaskDates";

definePageMeta({ middleware: "auth" });

const { showToast } = useToast();
const route = useRoute();
const router = useRouter();

const taskId = Number(route.query.task_id);

const loading = ref(true);
const selectedTask = ref<any>(null);
const showDeleteModal = ref(false);

const { tempDates, pickedDate, usedDates, loadUsedDates, addDate, removeDate } =
  useTaskDates();

const form = ref({
  task_nm: "",
  task_type: "ETHICS",
  pbls_yn: "Y",
  img_flnm: null as string | null,
});

const imageList = ref<any[]>([]);
const questionPool = ref<any[]>([]);
const detailQuestions = ref<any[]>([]);

const otherUsedDates = computed(() =>
  usedDates.value.filter((d) => !tempDates.value.includes(d)),
);

function typeLabel(type: string) {
  return type === "ETHICS"
    ? "윤리강령"
    : type === "SELF_CHECK"
      ? "자가점검"
      : type;
}

async function loadTask() {
  loading.value = true;
  if (!taskId) {
    loading.value = false;
    return;
  }
  const { status, data } = await fetchComplianceTasks();
  const task = status === 200 ? data.find((t: any) => t.task_id === taskId) : null;
  if (!task) {
    loading.value = false;
    return;
  }

  selectedTask.value = task;
  showDeleteModal.value = false;
  form.value = {
    task_nm: task.task_nm,
    task_type: task.task_type,
    pbls_yn: task.pbls_yn,
    img_flnm: task.img_flnm ?? null,
  };

  const dates = await fetchTaskDates(task.task_id);
  tempDates.value = dates.map((d: any) => d.task_app_dt);
  pickedDate.value = tomorrowStr();
  await loadUsedDates(tempDates.value);

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

  loading.value = false;
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
    router.push("/task-management");
  } else {
    showToast("error", "수정 요청 처리 중 에러가 발생했습니다.");
  }
}

async function confirmDelete() {
  const status = await deleteComplianceTask(selectedTask.value.task_id);
  showDeleteModal.value = false;
  if (status === 200) {
    showToast("success", "해당 관리 TASK가 삭제되었습니다.");
    router.push("/task-management");
  } else if (status === 409) {
    showToast("error", "이미 답변이 등록된 TASK는 삭제할 수 없습니다.");
  } else {
    showToast("error", "삭제 요청 처리 중 에러가 발생했습니다.");
  }
}

onMounted(loadTask);
</script>

<style scoped>
.row-center {
  margin: 12px 0;
}
</style>