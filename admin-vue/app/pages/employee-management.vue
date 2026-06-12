<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <span class="page-title">준법 관리 대상 직원 목록</span>
      <div class="row-center">
        <button class="btn btn-primary" @click="showAddModal = true">
          직원 등록
        </button>
        <button class="btn btn-danger" @click="handleDeleteSelected">
          선택 삭제
        </button>
      </div>
    </div>

    <!-- Employee Table -->
    <div class="card">
      <template v-if="employees.length > 0">
        <div class="table-wrapper">
          <table class="data-table">
            <colgroup>
              <col style="width: 40px" />
              <col />
              <col style="width: 30%" />
              <col style="width: 30%" />
            </colgroup>
            <thead>
              <tr>
                <th>선택</th>
                <th>직원번호</th>
                <th>직원명</th>
                <th>IP 주소</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="emp in employees" :key="emp.emp_no">
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
      </template>
      <div v-else class="info-box">
        등록된 관리 대상 직원이 없습니다. 신규 직원을 추가해 주세요.
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
  </div>
</template>

<script setup lang="ts">
import {
  fetchAllEmployees,
  addNewEmployee,
  deleteEmployees,
} from "~/utils/api";

definePageMeta({ middleware: "auth" });

const { showToast } = useToast();

const employees = ref<any[]>([]);
const selectedEmpNos = ref<string[]>([]);
const showAddModal = ref(false);
const showDeleteModal = ref(false);

const addForm = ref({ emp_no: "", emp_nm: "", ip: "" });

async function loadEmployees() {
  employees.value = await fetchAllEmployees();
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
