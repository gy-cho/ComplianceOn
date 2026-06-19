import { fetchAllUsedDates } from "~/utils/api";

export function todayStr() {
  return new Date().toISOString().split("T")[0];
}

export function tomorrowStr() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().split("T")[0];
}

/**
 * TASK 적용일 추가/삭제 공통 로직.
 * create-task.vue, task-detail.vue 양쪽에서 동일하게 사용한다.
 */
export function useTaskDates() {
  const { showToast } = useToast();

  const tempDates = ref<string[]>([]);
  const pickedDate = ref(tomorrowStr());
  const usedDates = ref<string[]>([]);

  async function loadUsedDates(excludeDates: string[] = []) {
    const allUsed = await fetchAllUsedDates();
    usedDates.value = allUsed.filter((d: string) => !excludeDates.includes(d));
  }

  function addDate() {
    const d = pickedDate.value;
    if (!d) return;
    if (d < tomorrowStr()) {
      showToast("error", "오늘 이전 날짜는 추가할 수 없습니다.");
      return;
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

  return {
    tempDates,
    pickedDate,
    usedDates,
    loadUsedDates,
    addDate,
    removeDate,
  };
}