export const BASE_URL = "http://10.201.106.35:8080";
// export const BASE_URL = "http://127.0.0.1:8080";

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE_URL}${path}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function post<T>(
  path: string,
  body?: unknown,
): Promise<{ status: number; data: T | null }> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => null);
    return { status: res.status, data };
  } catch (e: any) {
    return { status: 500, data: null };
  }
}

// ── Answers ──────────────────────────────────────────────────────────────────

export async function fetchEmpAnswers(taskId?: number, appSeq?: number) {
  const params = new URLSearchParams();
  if (taskId != null) params.set("task_id", String(taskId));
  if (appSeq != null) params.set("app_seq", String(appSeq));
  const q = params.toString() ? `?${params.toString()}` : "";
  const data = await get<any[]>(`/get-all-answers${q}`);
  return Array.isArray(data) ? data : [];
}

export async function fetchEmpDetailAnswers(
  taskId: number,
  appSeq: number,
  empNo: string,
) {
  const params = new URLSearchParams({
    task_id: String(taskId),
    app_seq: String(appSeq),
    emp_no: empNo,
  });
  const data = await get<any[]>(`/get-emp-detail-answers?${params.toString()}`);
  return Array.isArray(data) ? data : [];
}

// ── Employees ─────────────────────────────────────────────────────────────────

export async function fetchAllEmployees() {
  const data = await get<any[]>("/get-all-employees");
  return Array.isArray(data) ? data : [];
}

export async function addNewEmployee(empNo: string, empNm: string, ip: string) {
  return post<any>("/add-employee", { emp_no: empNo, emp_nm: empNm, ip });
}

export async function deleteEmployees(empNos: string[]) {
  return post<any>("/delete-employees", { emp_nos: empNos });
}

export function downloadEmployeeTemplate() {
  window.open(`${BASE_URL}/download-employee-template`, "_blank");
}

export async function uploadEmployees(file: File) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/upload-employees`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json().catch(() => null);
    return { status: res.status, data };
  } catch {
    return { status: 500, data: null };
  }
}

// ── Compliance Tasks ──────────────────────────────────────────────────────────

export async function fetchComplianceTasks() {
  try {
    const res = await fetch(`${BASE_URL}/get-compliance-tasks`);
    const data = await res.json().catch(() => []);
    return { status: res.status, data: Array.isArray(data) ? data : [] };
  } catch {
    return { status: 500, data: [] as any[] };
  }
}

export async function createComplianceTask(payload: any) {
  const { status } = await post<any>("/create-compliance-task", payload);
  return status;
}

export async function updateComplianceTask(payload: any) {
  const { status } = await post<any>("/update-compliance-task", payload);
  return status;
}

export async function deleteComplianceTask(taskId: number) {
  const { status } = await post<any>(
    `/delete-compliance-task?taskId=${taskId}`,
  );
  return status;
}

// ── Questions ─────────────────────────────────────────────────────────────────

export async function fetchQuestionPool() {
  const data = await get<any[]>("/get-question-pool");
  return Array.isArray(data) ? data : [];
}

export async function fetchTaskQuestions(taskId: number) {
  const data = await get<string[]>(`/get-task-questions?taskId=${taskId}`);
  return Array.isArray(data) ? data : [];
}

// ── Dates ─────────────────────────────────────────────────────────────────────

export async function fetchAllUsedDates() {
  const data = await get<string[]>("/get-all-used-dates");
  return Array.isArray(data) ? data : [];
}

export async function fetchTaskDates(taskId: number) {
  const data = await get<any[]>(`/get-task-dates?taskId=${taskId}`);
  return Array.isArray(data) ? data : [];
}

// ── Images ────────────────────────────────────────────────────────────────────

export async function fetchTaskImages() {
  const data = await get<any[]>("/get-img-pool");
  return Array.isArray(data) ? data : [];
}

export async function uploadImage(file: File): Promise<{ status: number; data: any }> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE_URL}/upload-image`, {
      method: 'POST',
      body: formData, // Content-Type 헤더는 지정하지 않음 (브라우저가 자동 설정)
    })
    const data = await res.json().catch(() => null)
    return { status: res.status, data }
  } catch {
    return { status: 500, data: null }
  }
}

export async function deleteImage(imgFlnm: string) {
  return post<any>('/delete-image', { img_flnm: imgFlnm })
}


// ── Question Pool ──────────────────────────────────────────────────────────

export async function addQuestion(qstnNm: string, qstnCn: string) {
  return post<any>('/add-question', { qstn_nm: qstnNm, qstn_cn: qstnCn })
}

export async function updateQuestion(qstnCd: string, qstnNm: string, qstnCn: string) {
  return post<any>('/update-question', {
    qstn_cd: qstnCd,
    qstn_nm: qstnNm,
    qstn_cn: qstnCn,
  })
}

export async function deleteQuestion(qstnCd: string) {
  return post<any>('/delete-question', { qstn_cd: qstnCd })
}