<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <span class="page-title">준법 관리 대상 직원 목록</span>
      <div class="row-center">
        <button class="btn btn-excel" @click="downloadEmployeeTemplate">
          <Icon name="lucide:file-down" /> 양식 다운로드
        </button>
        <button class="btn btn-excel" @click="triggerFileSelect">
          <Icon name="lucide:upload" /> 엑셀 업로드
        </button>
        <input
          ref="fileInputRef"
          type="file"
          accept=".xlsx,.xls"
          style="display: none"
          @change="handleFileSelected"
        />
        <button class="btn btn-primary" @click="showAddModal = true">
          직원 등록
        </button>
        <button class="btn btn-danger" @click="handleDeleteSelected">
          선택 삭제
        </button>
      </div>
    </div>

    <!-- Employee Table -->
    <div v-if="employees.length === 0" class="info-box">
      등록된 관리 대상 직원이 없습니다. 신규 직원을 등록해 주세요.
    </div>
    <div v-else class="card">
      <div class="row-center" style="margin-bottom: 16px">
        <div class="input-icon-wrap" style="flex: 1">
          <Icon name="lucide:search" class="input-icon" />
          <input
            v-model="searchText"
            class="form-input has-icon"
            placeholder="직원명, 직원번호, IP 주소 검색"
          />
        </div>
        <button class="btn btn-reset" @click="resetSearch">
          <Icon name="lucide:x" /> 초기화
        </button>
      </div>

      <div v-if="filteredEmployees.length === 0" class="info-box">
        검색 결과가 없습니다.
      </div>
      <div v-else class="table-wrapper">
        <table class="data-table">
          <colgroup>
            <col style="width: 40px" />
            <col />
            <col style="width: 30%" />
            <col style="width: 30%" />
          </colgroup>
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th>직원번호</th>
              <th>직원명</th>
              <th>IP 주소</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="emp in filteredEmployees" :key="emp.emp_no">
              <td>
                <input
                  type="checkbox"
                  :value="emp.emp_no"
                  v-model="selectedEmpNos"
                />
              </td>
              <td>{{ emp.emp_no }}</td>
              <td>{{ emp.emp_nm }}</td>
              <td>{{ emp.ip }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Add Employee Modal ── -->
    <div
      v-if="showAddModal"
      class="modal-overlay"
      @click.self="showAddModal = false"
    >
      <div class="modal-box">
        <div class="modal-title">직원 등록</div>
        <p style="font-size: 13px; color: #555; margin-bottom: 16px">
          새로운 준법 관리 대상 직원 정보를 입력하세요.
        </p>
        <div class="form-group">
          <label class="form-label">직원번호</label>
          <input
            v-model="addForm.emp_no"
            class="form-input"
            placeholder="예: D260101"
          />
        </div>
        <div class="form-group">
          <label class="form-label">직원명</label>
          <input
            v-model="addForm.emp_nm"
            class="form-input"
            placeholder="예: 홍길동"
          />
        </div>
        <div class="form-group">
          <label class="form-label">IP 주소</label>
          <input
            v-model="addForm.ip"
            class="form-input"
            placeholder="예: 10.211.X.X"
          />
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="handleAdd">등록</button>
          <button class="btn btn-secondary" @click="closeAddModal">닫기</button>
        </div>
      </div>
    </div>

    <!-- ── Delete Confirm Modal ── -->
    <div
      v-if="showDeleteModal"
      class="modal-overlay"
      @click.self="showDeleteModal = false"
    >
      <div class="modal-box">
        <div class="modal-title">직원 삭제 확인</div>
        <p style="font-size: 14px; margin-bottom: 8px">
          선택한 <strong>{{ selectedEmpNos.length }}명</strong>의 직원을 정말
          삭제하시겠습니까?
        </p>
        <p class="text-muted">
          삭제된 직원은 준법 TASK 대상자 목록에서 제외됩니다.
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

    <!-- ── Excel Upload Result Modal ── -->
    <div
      v-if="showUploadErrorModal"
      class="modal-overlay"
      @click.self="showUploadErrorModal = false"
    >
      <div class="modal-box" style="width: 520px">
        <div class="modal-title">엑셀 업로드 실패</div>
        <p style="font-size: 14px; margin-bottom: 12px">
          {{ uploadErrorMessage }}
        </p>
        <div
          class="table-wrapper"
          style="max-height: 280px; overflow-y: auto"
        >
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 50px">No</th>
                <th>오류 내용</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(err, i) in uploadErrors" :key="i">
                <td>{{ i + 1 }}</td>
                <td>{{ err }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-secondary"
            style="flex: none; width: 100%"
            @click="showUploadErrorModal = false"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  fetchAllEmployees,
  addNewEmployee,
  deleteEmployees,
  downloadEmployeeTemplate,
  uploadEmployees,
} from "~/utils/api";

definePageMeta({ middleware: "auth" });

const { showToast } = useToast();

const employees = ref<any[]>([]);
const selectedEmpNos = ref<string[]>([]);
const showAddModal = ref(false);
const showDeleteModal = ref(false);
const searchText = ref("");

const fileInputRef = ref<HTMLInputElement | null>(null);
const showUploadErrorModal = ref(false);
const uploadErrorMessage = ref("");
const uploadErrors = ref<string[]>([]);

const addForm = ref({ emp_no: "", emp_nm: "", ip: "" });

const filteredEmployees = computed(() => {
  if (!searchText.value.trim()) return employees.value;
  const s = searchText.value.toLowerCase();
  return employees.value.filter(
    (e) =>
      String(e.emp_nm ?? "").toLowerCase().includes(s) ||
      String(e.emp_no ?? "").toLowerCase().includes(s) ||
      String(e.ip ?? "").toLowerCase().includes(s),
  );
});

const isAllSelected = computed(() => {
  if (filteredEmployees.value.length === 0) return false;
  return filteredEmployees.value.every((e) =>
    selectedEmpNos.value.includes(e.emp_no),
  );
});

function toggleSelectAll() {
  if (isAllSelected.value) {
    const filteredNos = new Set(
      filteredEmployees.value.map((e) => e.emp_no),
    );
    selectedEmpNos.value = selectedEmpNos.value.filter(
      (no) => !filteredNos.has(no),
    );
  } else {
    const merged = new Set(selectedEmpNos.value);
    filteredEmployees.value.forEach((e) => merged.add(e.emp_no));
    selectedEmpNos.value = Array.from(merged);
  }
}

async function loadEmployees() {
  employees.value = await fetchAllEmployees();
}

function resetSearch() {
  searchText.value = "";
}

function triggerFileSelect() {
  fileInputRef.value?.click();
}

async function handleFileSelected(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = ""; // 같은 파일 재선택 시에도 change가 다시 발생하도록 초기화
  if (!file) return;

  const { status, data } = await uploadEmployees(file);
  const body = data as any;

  // 검증 실패: status 값과 무관하게 errors 배열이 내려오면 그 내용으로 모달 표시
  if (Array.isArray(body?.errors) && body.errors.length > 0) {
    uploadErrorMessage.value =
      body?.message ?? "엑셀 검증 중 오류가 발견되어 전체 등록이 취소되었습니다.";
    uploadErrors.value = body.errors;
    showUploadErrorModal.value = true;
    return;
  }

  if (status === 200 || status === 201) {
    showToast(
      "success",
      body?.message ?? "엑셀 파일을 통해 직원이 일괄 등록되었습니다.",
    );
    await loadEmployees();
    return;
  }

  showToast("error", body?.message ?? "엑셀 업로드 처리 중 오류가 발생했습니다.");
}

function closeAddModal() {
  showAddModal.value = false;
  addForm.value = { emp_no: "", emp_nm: "", ip: "" };
}

async function handleAdd() {
  if (
    !addForm.value.emp_no.trim() ||
    !addForm.value.emp_nm.trim() ||
    !addForm.value.ip.trim()
  ) {
    showToast("error", "모든 필드를 정확히 입력해 주세요.");
    return;
  }
  const { status, data } = await addNewEmployee(
    addForm.value.emp_no,
    addForm.value.emp_nm,
    addForm.value.ip,
  );
  if (status === 200 || status === 201) {
    showToast(
      "success",
      data?.message ??
        `${addForm.value.emp_nm} 직원이 성공적으로 등록되었습니다.`,
    );
    closeAddModal();
    await loadEmployees();
  } else {
    showToast("error", `등록 실패: ${data?.message ?? "통신 오류"}`);
  }
}

function handleDeleteSelected() {
  if (selectedEmpNos.value.length === 0) {
    showToast("warning", "삭제할 직원을 먼저 체크해 주세요.");
    return;
  }
  showDeleteModal.value = true;
}

async function confirmDelete() {
  const { status, data } = await deleteEmployees(selectedEmpNos.value);
  if (status === 200) {
    showToast("success", "선택한 직원 정보가 정상적으로 삭제되었습니다.");
    selectedEmpNos.value = [];
    showDeleteModal.value = false;
    await loadEmployees();
  } else {
    showToast("error", `삭제 처리 실패: ${data?.message ?? "오류 발생"}`);
  }
}

onMounted(loadEmployees);
</script>