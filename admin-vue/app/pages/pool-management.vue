<template>
  <div class="page-wrapper">
    <div class="page-header">
      <span class="page-title">POOL 관리</span>
    </div>

    <div class="card card-has-head">
      <div class="card-section-head pool-tab-head">
        <button
          class="pool-tab"
          :class="{ active: activeTab === 'question' }"
          @click="activeTab = 'question'"
        >
          질문 POOL
        </button>
        <button
          class="pool-tab"
          :class="{ active: activeTab === 'image' }"
          @click="activeTab = 'image'"
        >
          이미지 POOL
        </button>
      </div>

      <!-- ══════════════════════════════════════════════════ QUESTION POOL -->
      <template v-if="activeTab === 'question'">
        <div class="row-center" style="gap: 10px; margin-bottom: 16px">
          <div class="input-icon-wrap" style="flex: 1">
            <Icon name="lucide:search" class="input-icon" />
            <input
              v-model="questionSearchText"
              class="form-input has-icon"
              placeholder="질문명, 질문 내용 검색"
            />
          </div>
          <button class="btn btn-primary" @click="openAddQuestionModal">
            <Icon name="lucide:plus" /> 질문 등록
          </button>
        </div>

        <div v-if="filteredQuestionPool.length === 0" class="info-box">
          {{ questionSearchText ? "검색 결과가 없습니다." : "등록된 질문이 존재하지 않습니다." }}
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table qstn-table">
            <colgroup>
              <col style="width: 90px" />
              <col style="width: 160px" />
              <col />
              <col style="width: 130px" />
            </colgroup>
            <thead>
              <tr>
                <th>질문 코드</th>
                <th>질문명</th>
                <th>질문 내용</th>
                <th>관리</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in filteredQuestionPool" :key="q.qstn_cd" class="qstn-row">
                <td>{{ q.qstn_cd }}</td>
                <td>{{ q.qstn_nm }}</td>
                <td class="qstn-cn-cell">{{ q.qstn_cn }}</td>
                <td>
                  <div class="row-center" style="gap: 6px">
                    <button class="btn btn-secondary btn-sm" @click="openEditQuestionModal(q)">
                      수정
                    </button>
                    <button class="btn btn-danger btn-sm" @click="openDeleteQuestionModal(q)">
                      삭제
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- ════════════════════════════════════════════════════ IMAGE POOL -->
      <template v-else>
        <div class="row-center" style="gap: 10px; margin-bottom: 16px">
          <div class="input-icon-wrap" style="flex: 2">
            <Icon name="lucide:search" class="input-icon" />
            <input
              v-model="imageSearchText"
              class="form-input has-icon"
              placeholder="파일명 검색"
            />
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            style="display: none"
            @change="onFileSelect"
          />
          <button
            class="btn btn-secondary file-select-btn"
            style="flex: 1"
            @click="fileInputRef?.click()"
          >
            <Icon name="lucide:paperclip" />
            <span class="file-select-text">{{ selectedFile ? selectedFile.name : "파일 선택" }}</span>
          </button>
          <button
            class="btn btn-primary"
            style="width: 90px; flex-shrink: 0"
            :disabled="!selectedFile || uploading"
            @click="handleUploadImage"
          >
            {{ uploading ? "업로드 중..." : "업로드" }}
          </button>
        </div>

        <div v-if="filteredImageList.length === 0" class="info-box">
          {{ imageSearchText ? "검색 결과가 없습니다." : "등록된 이미지가 존재하지 않습니다." }}
        </div>
        <div v-else class="image-pool-grid">
          <div
            v-for="img in filteredImageList"
            :key="img.img_flnm"
            class="image-pool-card"
            @click="openPreview(img)"
          >
            <div class="image-pool-thumb">
              <img :src="`${BASE_URL}/images/${img.img_flnm}`" :alt="img.img_flnm" />
            </div>
            <p class="image-pool-name" :title="img.img_flnm">{{ img.img_flnm }}</p>
            <button
              class="btn btn-danger btn-sm btn-full"
              @click.stop="openDeleteImageModal(img.img_flnm)"
            >
              삭제
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- ── Image Preview Modal ── -->
    <div
      v-if="previewImage"
      class="modal-overlay"
      @click.self="previewImage = null"
    >
      <div class="modal-box image-preview-box">
        <div class="modal-title image-preview-title">
          <span :title="previewImage.img_flnm">{{ previewImage.img_flnm }}</span>
          <button class="btn-icon" @click="previewImage = null">
            <Icon name="lucide:x" />
          </button>
        </div>
        <div class="image-preview-frame">
          <img :src="`${BASE_URL}/images/${previewImage.img_flnm}`" :alt="previewImage.img_flnm" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-danger" @click="openDeleteImageModal(previewImage.img_flnm)">
            삭제
          </button>
          <button class="btn btn-secondary" @click="previewImage = null">닫기</button>
        </div>
      </div>
    </div>

    <!-- ── Delete Question Confirm Modal ── -->
    <div
      v-if="showDeleteQuestionModal"
      class="modal-overlay"
      @click.self="showDeleteQuestionModal = false"
    >
      <div class="modal-box">
        <div class="modal-title">질문 삭제 확인</div>
        <p style="font-size: 14px; margin-bottom: 8px">
          <strong>[{{ deletingQuestion?.qstn_cd }}] {{ deletingQuestion?.qstn_nm }}</strong>
          질문을 정말 삭제하시겠습니까?
        </p>
        <p class="text-muted">삭제된 질문은 복구할 수 없습니다.</p>
        <p class="text-muted">이미 TASK에 사용 중인 질문은 삭제가 제한됩니다.</p>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="confirmDeleteQuestion">
            최종 확인 및 삭제
          </button>
          <button class="btn btn-secondary" @click="showDeleteQuestionModal = false">
            취소
          </button>
        </div>
      </div>
    </div>

    <!-- ── Delete Image Confirm Modal ── -->
    <div
      v-if="showDeleteImageModal"
      class="modal-overlay"
      @click.self="showDeleteImageModal = false"
    >
      <div class="modal-box">
        <div class="modal-title">이미지 삭제 확인</div>
        <p style="font-size: 14px; margin-bottom: 8px">
          <strong>{{ deletingImageFlnm }}</strong> 이미지를 정말 삭제하시겠습니까?
        </p>
        <p class="text-muted">삭제된 이미지는 복구할 수 없습니다.</p>
        <p class="text-muted">이미 TASK에 사용 중인 이미지는 삭제가 제한됩니다.</p>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="confirmDeleteImage">
            최종 확인 및 삭제
          </button>
          <button class="btn btn-secondary" @click="showDeleteImageModal = false">
            취소
          </button>
        </div>
      </div>
    </div>

    <!-- ── Add/Edit Question Modal ── -->
    <div
      v-if="showQuestionModal"
      class="modal-overlay"
      @click.self="closeQuestionModal"
    >
      <div class="modal-box question-modal-box">
        <div class="modal-title">
          {{ editingQuestion ? "질문 수정" : "질문 등록" }}
        </div>

        <div class="form-group">
          <label class="form-label">질문명 (필수)</label>
          <input v-model="questionForm.qstn_nm" class="form-input" placeholder="질문명을 입력하세요" />
        </div>
        <div class="form-group">
          <label class="form-label">질문 내용 (필수)</label>
          <textarea
            v-model="questionForm.qstn_cn"
            class="form-input question-textarea"
            placeholder="질문 내용을 입력하세요"
            rows="6"
          />
        </div>

        <div class="modal-footer">
          <button class="btn btn-primary" @click="handleSubmitQuestion">
            {{ editingQuestion ? "수정 완료" : "등록" }}
          </button>
          <button class="btn btn-secondary" @click="closeQuestionModal">취소</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  BASE_URL,
  fetchQuestionPool,
  addQuestion,
  updateQuestion,
  deleteQuestion,
  fetchTaskImages,
  uploadImage,
  deleteImage,
} from "~/utils/api";

definePageMeta({ middleware: "auth" });

const { showToast } = useToast();

const activeTab = ref<"question" | "image">("question");

// ── Question Pool ──────────────────────────────────────────────
const questionPool = ref<any[]>([]);
const questionSearchText = ref("");
const showQuestionModal = ref(false);
const editingQuestion = ref<any | null>(null);
const questionForm = ref({ qstn_nm: "", qstn_cn: "" });

const filteredQuestionPool = computed(() => {
  const s = questionSearchText.value.trim().toLowerCase();
  if (!s) return questionPool.value;
  return questionPool.value.filter(
    (q) =>
      String(q.qstn_nm ?? "").toLowerCase().includes(s) ||
      String(q.qstn_cn ?? "").toLowerCase().includes(s),
  );
});

async function loadQuestionPool() {
  questionPool.value = await fetchQuestionPool();
}

function openAddQuestionModal() {
  editingQuestion.value = null;
  questionForm.value = { qstn_nm: "", qstn_cn: "" };
  showQuestionModal.value = true;
}

function openEditQuestionModal(q: any) {
  editingQuestion.value = q;
  questionForm.value = {
    qstn_nm: q.qstn_nm ?? "",
    qstn_cn: q.qstn_cn ?? "",
  };
  showQuestionModal.value = true;
}

function closeQuestionModal() {
  showQuestionModal.value = false;
  editingQuestion.value = null;
}

async function handleSubmitQuestion() {
  const { qstn_nm, qstn_cn } = questionForm.value;
  if (!qstn_nm.trim()) {
    showToast("error", "질문명을 입력하세요.");
    return;
  }
  if (!qstn_cn.trim()) {
    showToast("error", "질문 내용을 입력하세요.");
    return;
  }

  if (editingQuestion.value) {
    const { status, data } = await updateQuestion(
      editingQuestion.value.qstn_cd,
      qstn_nm.trim(),
      qstn_cn.trim(),
    );
    if (status === 200) {
      showToast("success", data?.message ?? "질문이 수정되었습니다.");
      closeQuestionModal();
      await loadQuestionPool();
    } else {
      showToast(
        "error",
        data?.message ?? "수정에 실패했습니다. 이미 TASK에 사용 중인 질문일 수 있습니다.",
      );
    }
  } else {
    const { status, data } = await addQuestion(qstn_nm.trim(), qstn_cn.trim());
    if (status === 201) {
      showToast("success", data?.message ?? "질문이 등록되었습니다.");
      closeQuestionModal();
      await loadQuestionPool();
    } else {
      showToast("error", data?.message ?? "질문 등록에 실패했습니다.");
    }
  }
}

const showDeleteQuestionModal = ref(false);
const deletingQuestion = ref<any | null>(null);

function openDeleteQuestionModal(q: any) {
  deletingQuestion.value = q;
  showDeleteQuestionModal.value = true;
}

async function confirmDeleteQuestion() {
  if (!deletingQuestion.value) return;
  const { status, data } = await deleteQuestion(deletingQuestion.value.qstn_cd);
  showDeleteQuestionModal.value = false;
  if (status === 200) {
    showToast("success", data?.message ?? "삭제되었습니다.");
    await loadQuestionPool();
  } else {
    showToast(
      "error",
      data?.message ?? "삭제에 실패했습니다. 이미 TASK에 사용 중인 질문일 수 있습니다.",
    );
  }
}

// ── Image Pool ─────────────────────────────────────────────────
const imageList = ref<any[]>([]);
const imageSearchText = ref("");
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const previewImage = ref<any | null>(null);

const filteredImageList = computed(() => {
  const s = imageSearchText.value.trim().toLowerCase();
  if (!s) return imageList.value;
  return imageList.value.filter((img) =>
    String(img.img_flnm ?? "").toLowerCase().includes(s),
  );
});

const showDeleteImageModal = ref(false);
const deletingImageFlnm = ref<string>("");

function openPreview(img: any) {
  previewImage.value = img;
}

function openDeleteImageModal(imgFlnm: string) {
  deletingImageFlnm.value = imgFlnm;
  showDeleteImageModal.value = true;
}

async function confirmDeleteImage() {
  if (!deletingImageFlnm.value) return;
  const { status, data } = await deleteImage(deletingImageFlnm.value);
  showDeleteImageModal.value = false;
  if (status === 200) {
    showToast("success", data?.message ?? "삭제되었습니다.");
    previewImage.value = null;
    await loadImageList();
  } else {
    showToast(
      "error",
      data?.message ?? "삭제에 실패했습니다. 이미 TASK에 사용 중인 이미지일 수 있습니다.",
    );
  }
}

async function loadImageList() {
  imageList.value = await fetchTaskImages();
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  selectedFile.value = target.files?.[0] ?? null;
}

async function handleUploadImage() {
  if (!selectedFile.value) return;
  uploading.value = true;
  const { status, data } = await uploadImage(selectedFile.value);
  uploading.value = false;
  if (status === 201) {
    showToast("success", data?.message ?? "이미지가 업로드되었습니다.");
    selectedFile.value = null;
    if (fileInputRef.value) fileInputRef.value.value = "";
    await loadImageList();
  } else {
    showToast("error", data?.message ?? "이미지 업로드에 실패했습니다.");
  }
}

onMounted(async () => {
  await Promise.all([loadQuestionPool(), loadImageList()]);
});
</script>

<style scoped>
/* card-section-head의 기본 좌측 강조 바는 탭마다 개별로 그리므로 제거 */
.pool-tab-head::before {
  display: none;
}

.pool-tab-head {
  align-items: stretch;
  gap: 4px;
  padding: 0;
}

.pool-tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  background: transparent;
  border: none;
  font-family: "KBFGDisplay", sans-serif;
  font-size: 15px;
  color: #b7b2a6;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.pool-tab:first-child {
  border-top-left-radius: 9px;
}

.pool-tab::before {
  content: "";
  display: block;
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background-color: #e6dfc4;
  flex-shrink: 0;
  transition: background-color 0.2s ease;
}

.pool-tab:hover {
  color: #3b3730;
}

.pool-tab.active {
  background: var(--bg-card);
  color: #3b3730;
  font-weight: 700;
}

.pool-tab.active::before {
  background-color: var(--kb-yellow);
}

.image-pool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.image-pool-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.image-pool-card:hover {
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
  border-color: var(--kb-yellow);
}

.image-pool-thumb {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-pool-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-pool-name {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Image Preview Modal ── */
.image-preview-box {
  width: 90vw;
  max-width: 960px;
}

.image-preview-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.image-preview-title span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-preview-frame {
  width: 100%;
  max-height: 80vh;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-frame img {
  width: 100%;
  height: auto;
  max-height: 80vh;
  object-fit: contain;
}

.file-select-btn {
  justify-content: flex-start;
  overflow: hidden;
}

.file-select-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Question Add/Edit Modal ── */
.question-modal-box {
  width: 520px;
}

.question-textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.5;
  font-family: inherit;
}

.qstn-table {
  table-layout: fixed;
}

.qstn-row td {
  vertical-align: top;
}

.qstn-cn-cell {
  line-height: 1.5;
  word-break: break-word;
}
</style>