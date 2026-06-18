<template>
  <div class="page-wrapper">
    <div class="page-header">
      <span class="page-title">POOL 관리</span>
    </div>

    <div class="card card-has-head">
      <div class="card-section-head">
        <div class="row-center" style="gap: 4px">
          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'question' }"
            @click="activeTab = 'question'"
          >
            질문 POOL
          </button>
          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'image' }"
            @click="activeTab = 'image'"
          >
            이미지 POOL
          </button>
        </div>
      </div>

      <!-- ══════════════════════════════════════════════════ QUESTION POOL -->
      <template v-if="activeTab === 'question'">
        <div class="row-center" style="gap: 10px; margin-bottom: 16px">
          <input
            v-model="newQuestionNm"
            class="form-input"
            placeholder="새 질문 내용을 입력하세요"
            style="flex: 1"
            @keyup.enter="handleAddQuestion"
          />
          <button class="btn btn-primary" style="width: 100px" @click="handleAddQuestion">
            등록
          </button>
        </div>

        <div v-if="questionPool.length === 0" class="info-box">
          등록된 질문이 존재하지 않습니다.
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table">
            <colgroup>
              <col style="width: 120px" />
              <col />
              <col style="width: 90px" />
            </colgroup>
            <thead>
              <tr>
                <th>질문 코드</th>
                <th>질문 내용</th>
                <th>삭제</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in questionPool" :key="q.qstn_cd">
                <td>{{ q.qstn_cd }}</td>
                <td>{{ q.qstn_nm }}</td>
                <td>
                  <button class="btn btn-danger btn-sm" @click="handleDeleteQuestion(q.qstn_cd)">
                    삭제
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- ════════════════════════════════════════════════════ IMAGE POOL -->
      <template v-else>
        <div class="row-center" style="gap: 10px; margin-bottom: 16px">
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="form-input"
            style="flex: 1"
            @change="onFileSelect"
          />
          <button
            class="btn btn-primary"
            style="width: 100px"
            :disabled="!selectedFile || uploading"
            @click="handleUploadImage"
          >
            {{ uploading ? "업로드 중..." : "업로드" }}
          </button>
        </div>

        <div v-if="imageList.length === 0" class="info-box">
          등록된 이미지가 존재하지 않습니다.
        </div>
        <div v-else class="image-pool-grid">
          <div v-for="img in imageList" :key="img.img_flnm" class="image-pool-card">
            <div class="image-pool-thumb">
              <img :src="`${BASE_URL}/images/${img.img_flnm}`" :alt="img.img_flnm" />
            </div>
            <p class="image-pool-name" :title="img.img_flnm">{{ img.img_flnm }}</p>
            <button class="btn btn-danger btn-sm btn-full" @click="handleDeleteImage(img.img_flnm)">
              삭제
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  BASE_URL,
  fetchQuestionPool,
  addQuestion,
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
const newQuestionNm = ref("");

async function loadQuestionPool() {
  questionPool.value = await fetchQuestionPool();
}

async function handleAddQuestion() {
  if (!newQuestionNm.value.trim()) {
    showToast("error", "질문 내용을 입력하세요.");
    return;
  }
  const status = await addQuestion(newQuestionNm.value.trim());
  if (status === 200) {
    showToast("success", "질문이 등록되었습니다.");
    newQuestionNm.value = "";
    await loadQuestionPool();
  } else {
    showToast("error", "질문 등록에 실패했습니다.");
  }
}

async function handleDeleteQuestion(qstnCd: string) {
  const status = await deleteQuestion(qstnCd);
  if (status === 200) {
    showToast("success", "삭제되었습니다.");
    await loadQuestionPool();
  } else {
    showToast("error", "삭제에 실패했습니다. 이미 TASK에 사용 중인 질문일 수 있습니다.");
  }
}

// ── Image Pool ─────────────────────────────────────────────────
const imageList = ref<any[]>([]);
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

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
  const { status } = await uploadImage(selectedFile.value);
  uploading.value = false;
  if (status === 200) {
    showToast("success", "이미지가 업로드되었습니다.");
    selectedFile.value = null;
    if (fileInputRef.value) fileInputRef.value.value = "";
    await loadImageList();
  } else {
    showToast("error", "이미지 업로드에 실패했습니다.");
  }
}

async function handleDeleteImage(imgFlnm: string) {
  const status = await deleteImage(imgFlnm);
  if (status === 200) {
    showToast("success", "삭제되었습니다.");
    await loadImageList();
  } else {
    showToast("error", "삭제에 실패했습니다. 이미 TASK에 사용 중인 이미지일 수 있습니다.");
  }
}

onMounted(async () => {
  await Promise.all([loadQuestionPool(), loadImageList()]);
});
</script>

<style scoped>
.nav-tab-btn {
  padding: 8px 18px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-tab-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-primary);
}

.nav-tab-btn.active {
  background: var(--kb-yellow);
  color: #333;
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
  transition: box-shadow 0.2s;
}

.image-pool-card:hover {
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
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
</style>