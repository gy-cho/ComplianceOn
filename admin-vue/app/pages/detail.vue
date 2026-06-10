<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <span class="page-title">사원 상세 답변 내역</span>
      <button class="btn btn-secondary" @click="goBack">목록으로</button>
    </div>

    <!-- Employee info card -->
    <div class="card">
      <div class="card-section-title">
        ■ {{ empNm }} ({{ empNo }}) 상세 정보
      </div>

      <div v-if="loading" class="spinner-wrap">상세 데이터를 불러오는 중...</div>

      <div v-else-if="!detailData.length" class="info-box" style="background:#ffebee; border-color:#ffcdd2; color:#c62828">
        데이터를 조회할 수 없습니다. 다시 시도해 주세요.
      </div>

      <div v-else class="qa-list">
        <div
          v-for="(item, idx) in detailData"
          :key="idx"
          class="qa-card"
          :style="{ backgroundColor: bgColor(item.emp_ans_yn), borderColor: '#E0E0E0' }"
        >
          <div class="qa-question">
            Q{{ idx + 1 }}. {{ item.qstn_cn || '질문 내용이 없습니다.' }}
          </div>
          <div class="qa-answer" :style="{ color: ansColor(item.emp_ans_yn) }">
            {{ ansDisplay(item.emp_ans_yn) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchEmpDetailAnswers } from '~/utils/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()

const taskId = Number(route.query.task_id)
const appSeq = Number(route.query.app_seq)
const empNo = String(route.query.emp_no ?? '')
const empNm = String(route.query.emp_nm ?? '')

const detailData = ref<any[]>([])
const loading = ref(true)

function bgColor(val: string) {
  if (val === 'Y') return '#F1F8E9'
  if (val === 'N') return '#FFEBEE'
  return '#FAFAFA'
}

function ansColor(val: string) {
  if (val === 'Y') return '#4CAF50'
  if (val === 'N') return '#FF4B4B'
  return '#999'
}

function ansDisplay(val: string) {
  if (val === 'Y') return '🟢 준수 (Y)'
  if (val === 'N') return '🔴 미준수 (N)'
  return `⚪ ${val}`
}

function goBack() {
  router.push('/dashboard')
}

onMounted(async () => {
  if (taskId && appSeq && empNo) {
    detailData.value = await fetchEmpDetailAnswers(taskId, appSeq, empNo)
  }
  loading.value = false
})
</script>

<style scoped>
.qa-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
}

.qa-card {
  border: 1px solid #E0E0E0;
  border-radius: 8px;
  padding: 16px;
}

.qa-question {
  font-weight: 600;
  font-size: 14px;
  color: #424242;
  margin-bottom: 10px;
}

.qa-answer {
  font-weight: 800;
  font-size: 15px;
}
</style>
