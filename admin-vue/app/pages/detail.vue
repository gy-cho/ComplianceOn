<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <span class="page-title">{{ empNm }} ({{ empNo }}) 답변 상세 내역</span>
      <button class="btn btn-secondary" @click="goBack">목록으로</button>
    </div>

    <!-- Employee info card -->
    <div>
      <div v-if="loading" class="spinner-wrap">
        상세 데이터를 불러오는 중...
      </div>

      <div
        v-else-if="!detailData.length"
        class="info-box"
        style="background: #ffebee; border-color: #ffcdd2; color: #c62828"
      >
        데이터를 조회할 수 없습니다. 다시 시도해 주세요.
      </div>

      <div v-else class="qa-list">
        <div
          v-for="(item, idx) in detailData"
          :key="idx"
          class="qa-card"
          :class="{
            'comply-card': item.emp_ans_yn === 'Y',
            'non-comply-card': item.emp_ans_yn === 'N',
          }"
        >
          <!-- Top Section (Classification and Title) -->
          <div class="qa-top">
            <span class="qa-category">[{{ item.qstn_nm }}]</span>
            <div class="qa-question-row">
              <span class="qa-num">Q{{ idx + 1 }}.</span>
              <div class="qa-question-text">
                {{ item.qstn_cn || "질문 내용이 없습니다." }}
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="qa-divider"></div>

          <!-- Bottom Section (Comply / Non-comply Status) -->
          <div class="qa-bottom">
            <span
              class="qa-status-badge"
              :class="{
                comply: item.emp_ans_yn === 'Y',
                'non-comply': item.emp_ans_yn === 'N',
                unknown: item.emp_ans_yn !== 'Y' && item.emp_ans_yn !== 'N',
              }"
            >
              {{
                item.emp_ans_yn === "Y"
                  ? "준수"
                  : item.emp_ans_yn === "N"
                    ? "미준수"
                    : item.emp_ans_yn
              }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchEmpDetailAnswers } from "~/utils/api";

definePageMeta({ middleware: "auth" });

const route = useRoute();
const router = useRouter();

const taskId = Number(route.query.task_id);
const appSeq = Number(route.query.app_seq);
const empNo = String(route.query.emp_no ?? "");
const empNm = String(route.query.emp_nm ?? "");

const detailData = ref<any[]>([]);
const loading = ref(true);

function goBack() {
  router.push("/dashboard");
}

onMounted(async () => {
  if (taskId && appSeq && empNo) {
    detailData.value = await fetchEmpDetailAnswers(taskId, appSeq, empNo);
  }
  loading.value = false;
});
</script>

<style scoped>
.qa-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.qa-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.qa-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.qa-card.comply-card {
  border-color: #c8e6c9;
  background-color: #fcfdfc;
}

.qa-card.non-comply-card {
  border-color: #ffcdd2;
  background-color: #fffdfd;
}

.qa-top {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qa-category {
  font-size: 14px;
  font-weight: 500;
  color: #888888;
}

.qa-question-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.qa-num {
  font-weight: 700;
  font-family: "KBFGDisplay", sans-serif;
  color: #1a1a1a;
  flex-shrink: 0;
}

.qa-question-text {
  font-size: 16px;
  color: #1a1a1a;
}

.qa-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 12px 0;
}

.qa-bottom {
  display: flex;
  justify-content: flex-end;
}

/* Compliance status badges */
.qa-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 16px;
  border-radius: 12px;
  font-size: 12px;
  white-space: nowrap;
}

.qa-status-badge.comply {
  background-color: #e8f5e9;
  color: #388e3c;
}

.qa-status-badge.non-comply {
  background-color: #ffebee;
  color: #d32f2f;
}

.qa-status-badge.unknown {
  background-color: #f5f5f5;
  color: #757575;
}
</style>
