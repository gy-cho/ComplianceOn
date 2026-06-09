import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
from io import BytesIO
import winreg

# =========================================================================
# 📌 [서버 및 환경 설정]
# =========================================================================
BASE_URL = "http://10.201.2.93:8080"
# BASE_URL = "http://127.0.0.1:8080"

UI_FONT = "Malgun Gothic"

# 📌 마스터 데이터 및 상태 인스턴스 정의
emp_no_str = ""        # 테스트 사번
task_id_str = ""
app_seq_str = ""
emp_name_str = "홍길동"        
date_str = "2026년 6월"
task_type_str = ""           # API에서 받아올 현재 태스크 타입 보관

# 자가점검(SELF_CHECK)용 데이터 핸들러 
user_answers = {}            # 유저 답변 저장 {qstn_cd: "Y" 또는 "N"}
standard_answers = {}        # 🌟 [추가] 서버 기준 정상 응답 보관 {qstn_cd: "Y" 또는 "N"}

def fetch_task_and_init():
    """서버에서 데이터를 조회하여 성공하면 데이터를 반환, 실패하면 None 반환"""
    global task_id_str, app_seq_str, task_type_str, standard_answers
    
    get_task_url = f"{BASE_URL}/get-task-qstn?emp_no={emp_no_str}"
    
    try:
        response = requests.get(get_task_url, timeout=3)
        if response.status_code != 200:
            return None # 실패 시 None 리턴
            
        results = response.json()
        if not results:
            return None # 데이터 없으면 None 리턴
            
        # 첫 번째 태스크 정보 매핑
        task_data = results[0]
        task_id_str = str(task_data.get("task_id"))   
        app_seq_str = str(task_data.get("app_seq"))   
        task_type_str = task_data.get("task_type", "ETHICS")
        
        # 정상응답 캐싱
        if task_type_str == "SELF_CHECK" and "qstn_list" in task_data:
            for qstn in task_data.get("qstn_list", []):
                q_cd = qstn.get("qstn_cd")
                standard_answers[q_cd] = qstn.get("qstn_std_ans_yn", "Y")
        
        return task_data # 성공 시 데이터 전달
        
    except Exception:
        return None # 통신 에러 시 None 리턴


# =========================================================================
# 📌 [타입 A] 윤리강령 서약서 화면 
# =========================================================================
def draw_ethics_ui(task_data):
    global tk_image, canvas
    img_filename = task_data.get("img_flnm", "TEST_1.png")
    image_url = f"{BASE_URL}/images/{img_filename}"
    
    try:
        img_response = requests.get(image_url, timeout=3)
        if img_response.status_code == 200:
            bg_image = Image.open(BytesIO(img_response.content))
        else: raise Exception()
    except:
        try: 
            bg_image = Image.open("TEST_1.png")
        except:
            root.destroy()
            exit()

    new_width = int(bg_image.size[0] * (screen_height / bg_image.size[1]))
    resized_image = bg_image.resize((new_width, screen_height), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(resized_image)

    canvas = tk.Canvas(root, width=new_width, height=screen_height, bd=0, highlightthickness=0, bg='white')
    canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

    setup_ethics_elements(new_width, screen_height)


# =========================================================================
# 📌 [타입 B] 자가점검 설문지 화면
# =========================================================================
def draw_self_check_ui(task_data):
    global canvas, submit_btn, tk_image
    
    root.configure(background='#F4F4F4') 
    
    try:
        bg_image = Image.open("img_self_check_bg.png")
    except Exception as e:
        messagebox.showerror("오류", f"자가점검 배경 이미지(img_self_check_bg.png)를 찾을 수 없습니다.\n에러: {e}")
        root.destroy()
        exit()
        
    box_height = int(screen_height * 0.95) 
    box_width = int(bg_image.size[0] * (box_height / bg_image.size[1]))
    
    resized_image = bg_image.resize((box_width, box_height), Image.Resampling.LANCZOS)
    tk_image = ImageTk.PhotoImage(resized_image)
    
    canvas = tk.Canvas(root, width=box_width, height=box_height, bd=0, highlightthickness=0, bg='#FFFFFF')
    canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
    
    qstn_list = task_data.get("qstn_list", [])[:3]
    
    scale_ratio = box_height / bg_image.size[1]
    
    start_y = int(410 * scale_ratio)  
    y_gap = int(90 * scale_ratio)    
    
    text_left_x = int(90 * scale_ratio)       
    radio_yes_x = box_width - int(200 * scale_ratio) 
    radio_no_x = box_width - int(140 * scale_ratio)  
    line_padding = int(100 * scale_ratio)      
    
    for idx, qstn in enumerate(qstn_list):
        q_cd = qstn.get("qstn_cd")
        q_title = qstn.get("qstn_nm", "")
        q_content = qstn.get("qstn_cn", "")
        
        current_y = start_y + (idx * y_gap)
        
        display_title = f"{idx+1:02d}. {q_title}" if q_title else f"{idx+1:02d}. 자가점검 항목"
        lbl_title = tk.Label(canvas, text=display_title, font=(UI_FONT, 11, "bold"), fg="#2D3748", bg="#FFFFFF")
        canvas.create_window(text_left_x, current_y, window=lbl_title, anchor=tk.W)
        
        # 현재 설문 내용이 들어가는 라벨 수정
        lbl_content = tk.Label(
            canvas, 
            text=q_content, 
            font=(UI_FONT, 10), 
            fg="#5A6A85", 
            bg="#FFFFFF", 
            justify=tk.LEFT,
            wraplength=int(box_width * 0.75)  # 🌟 추가: 버튼 침범 방지를 위해 너비 제한
        )
        canvas.create_window(text_left_x, current_y + int(16 * scale_ratio), window=lbl_content, anchor=tk.NW) # 🌟 anchor를 NW로 변경
        
        user_answers[q_cd] = tk.StringVar(value="")
        
        r_yes = tk.Radiobutton(
            canvas, text=" 예", variable=user_answers[q_cd], value="Y", 
            bg="white", activebackground="white", selectcolor="white",
            font=(UI_FONT, 10, "bold"), fg="#2D3748", activeforeground="#FFBC00",
            command=check_self_check_complete
        )
        r_no = tk.Radiobutton(
            canvas, text=" 아니오", variable=user_answers[q_cd], value="N", 
            bg="white", activebackground="white", selectcolor="white",
            font=(UI_FONT, 10, "bold"), fg="#E53E3E", activeforeground="#E53E3E",
            command=check_self_check_complete
        )
        
        canvas.create_window(radio_yes_x, current_y + int(12 * scale_ratio), window=r_yes, anchor=tk.W)
        canvas.create_window(radio_no_x, current_y + int(12 * scale_ratio), window=r_no, anchor=tk.W)
        
        canvas.create_line(line_padding, current_y + int(65 * scale_ratio), box_width - line_padding, current_y + int(65 * scale_ratio), fill="#F1F3F5", width=1)

    btn_x = box_width - int(173 * scale_ratio)
    btn_y = box_height - int(56 * scale_ratio)
    
    # 둥근 버튼 좌표 계산
    btn_w, btn_h = 200, 56 # 기존 버튼 크기에 맞춰 설정
    btn_x1 = btn_x - (btn_w / 2)
    btn_y1 = btn_y - (btn_h / 2)
    btn_x2 = btn_x + (btn_w / 2)
    btn_y2 = btn_y + (btn_h / 2)

    # 둥근 사각형 생성 (처음에는 비활성 색상 #D1D5DB)
    submit_btn = create_round_rect(canvas, btn_x1, btn_y1, btn_x2, btn_y2, radius=15, fill="#D1D5DB", outline="")
    
    # 버튼 텍스트 추가
    btn_label = canvas.create_text(btn_x, btn_y, text="제출(확인)", fill="#9CA3AF", font=(UI_FONT, 12, "bold"))
    
    # 상태 관리 전역 변수 설정
    global submit_btn_state
    submit_btn_state = "disabled"

    def on_btn_click(event):
        if submit_btn_state == "normal":
            on_agree()
            
    canvas.tag_bind(submit_btn, "<Button-1>", on_btn_click)
    canvas.tag_bind(btn_label, "<Button-1>", on_btn_click)


def check_self_check_complete():
    """자가점검 항목 중 누락된 답변이 없는지 체크하여 버튼 상태 업데이트"""
    global submit_btn_state, btn_label
    all_answered = True
    for val in user_answers.values():
        if val.get() == "":
            all_answered = False
            break
            
    if all_answered:
        submit_btn_state = "normal"
        # 활성화 시 색상: 노란색 배경, 검정색 글씨
        canvas.itemconfig(submit_btn, fill="#FFBC00")
        canvas.itemconfig(btn_label, fill="#FFFFFF")
    else:
        submit_btn_state = "disabled"
        # 비활성화 시 색상: 회색 배경, 회색 글씨
        canvas.itemconfig(submit_btn, fill="#D1D5DB")
        canvas.itemconfig(btn_label, fill="#9CA3AF")


# =========================================================================
# 📌 [비즈니스 요건 수정 반영 구역] 검증 및 emp_ans_agr_yn 유동 분기 처리
# =========================================================================
def on_agree():
    submit_url = f"{BASE_URL}/submit-compliance" 
    
    # 1. 🌟 [정상응답 준수 여부 사전 검증]
    is_all_correct = True
    if task_type_str == "SELF_CHECK":
        for q_cd, var in user_answers.items():
            user_ans = var.get()
            correct_ans = standard_answers.get(q_cd, "Y")
            if user_ans != correct_ans:
                is_all_correct = False
                break
        
        # 2. 🌟 정상응답이 아닌 항목이 있을 경우 재확인 팝업 가로채기
        if not is_all_correct:
            confirm = messagebox.askyesno(
                "자가점검 재확인", 
                "보안 지침에 위배되는 답변 항목이 존재합니다.\n"
                "이대로 점검 결과를 제출하시겠습니까?"
            )
            if not confirm:
                return  # '아니오' 누르면 함수 탈출하여 화면 유지 (제출 유보)

    # 3. 🌟 검증 결과에 따라 emp_ans_agr_yn 플래그 가변 세팅
    # 모두 정상응답 시 "Y", 하나라도 오답(미흡) 선택 후 강제 진행 시 "N"
    final_agr_yn = "Y" if is_all_correct else "N"

    payload = {
        "task_id": int(task_id_str) if task_id_str.isdigit() else None,        
        "app_seq": int(app_seq_str) if app_seq_str.isdigit() else None,        
        "emp_no": emp_no_str,
        "emp_main_ans_yn": "Y",  
        "emp_ans_agr_yn": final_agr_yn,  # 💡 변수 대입
        "answers": []
    }

    if task_type_str == "SELF_CHECK":
        payload["answers"] = [
            {"qstn_cd": q_cd, "emp_ans_yn": var.get()} for q_cd, var in user_answers.items()
        ]
    else:
        payload["answers"] = []

    try:
        response = requests.post(submit_url, json=payload, timeout=3)
        if response.status_code == 200:
            res_data = response.json()
            messagebox.showinfo("알림", res_data.get("message", "준법 프로그램 수행 기록이 정상적으로 저장되었습니다."))
            root.destroy()
            exit()
        elif response.status_code in [400, 404, 500]:
            res_data = response.json()
            messagebox.showwarning("제출 실패", f"{res_data.get('message', '알 수 없는 오류')}")
            root.destroy()
            exit()
        else:
            messagebox.showerror("오류", f"정의되지 않은 서버 응답 에러가 발생했습니다.\nStatus Code: {response.status_code}")
            root.destroy()
            exit()
    except Exception as e:
        messagebox.showerror("네트워크 오류", f"서버에 서약 데이터를 전송하지 못했습니다.\n네트워크 연결 상태를 재확인해 주세요.\n\n에러: {e}")
        root.destroy()
        exit()


def setup_ethics_elements(width, height):
    """기존 윤리강령 화면 렌더링용 서브 컴포넌트 설정"""
    global submit_btn, agreement_var
    TARGET_X = width * 0.50
    agreement_var = tk.IntVar()
    
    check_btn = tk.Checkbutton(
        canvas, text="본인은 상기의 '윤리강령' 내용을 확인하였으며, 이를 준수할 것을 다짐합니다.", 
        variable=agreement_var, command=check_ethics_complete, font=(UI_FONT, 12, "bold"),
        bg="#FFFFFF", activebackground="#FFFFFF", bd=0
    )
    canvas.create_window(TARGET_X, height * 0.83, window=check_btn, anchor=tk.CENTER)
    canvas.create_text(TARGET_X, height * 0.86, text=date_str, font=(UI_FONT, 12, "bold"), fill="#333333", anchor=tk.CENTER)
    canvas.create_text(TARGET_X, height * 0.88, text=f"직원번호 : {emp_no_str}       서명 : {emp_name_str}", font=(UI_FONT, 12, "bold"), fill="#333333", anchor=tk.CENTER)

    # 둥근 버튼 그리기
    btn_w, btn_h = 240, 40
    btn_x1 = TARGET_X - (btn_w / 2)
    btn_y1 = height * 0.92 - (btn_h / 2)
    btn_x2 = TARGET_X + (btn_w / 2)
    btn_y2 = height * 0.92 + (btn_h / 2)
    
    # 둥근 사각형 생성 (처음에는 비활성 색상 #cccccc)
    submit_btn = create_round_rect(canvas, btn_x1, btn_y1, btn_x2, btn_y2, radius=20, fill="#cccccc", outline="")
    # 텍스트 추가
    label_id = canvas.create_text(TARGET_X, height * 0.92, text="확인 및 업무 시작", fill="white", font=(UI_FONT, 12, "bold"))
    
    # 클릭 이벤트 연결 (비활성화 상태일 때는 반응 없음)
    def on_btn_click(event):
        if submit_btn_state == "normal":
            on_agree()
            
    canvas.tag_bind(submit_btn, "<Button-1>", on_btn_click)
    canvas.tag_bind(label_id, "<Button-1>", on_btn_click)
    
    # 상태를 관리할 전역 변수 설정
    global submit_btn_state, submit_btn_label
    submit_btn_state = "disabled"
    submit_btn_label = label_id

def check_ethics_complete():
    global submit_btn_state
    if agreement_var.get():
        submit_btn_state = "normal"
        canvas.itemconfig(submit_btn, fill="#FFBC00") # 활성 색상
    else:
        submit_btn_state = "disabled"
        canvas.itemconfig(submit_btn, fill="#cccccc") # 비활성 색상

def create_round_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    # 둥근 사각형 그리기 로직
    points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
              x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2,
              x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius,
              x1, y1+radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

def get_auth_id():
    """
    레지스트리 HKEY_LOCAL_MACHINE\SOFTWARE\Geni\Genian 경로에서 
    AuthID 값을 가져오는 함수
    """
    # 레지스트리 경로
    key_path = r"SOFTWARE\Geni\Genian"
    
    try:
        # HKEY_LOCAL_MACHINE에서 키 열기 (읽기 권한)
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        
        # AuthID 값 가져오기
        value, reg_type = winreg.QueryValueEx(key, "AuthID")
        
        # 사용 완료 후 키 닫기
        winreg.CloseKey(key)
        
        return value
        
    except FileNotFoundError:
        print("오류: 해당 레지스트리 경로를 찾을 수 없습니다.")
        return None
    except OSError:
        print("오류: 레지스트리 값을 읽는 중 문제가 발생했습니다 (권한 문제 등).")
        return None
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return None

# =========================================================================
# 시스템 윈도우 생성 및 메인루프 기동
# =========================================================================
root = tk.Tk()
root.withdraw() # 🌟 창을 숨깁니다 (사용자 눈에 안 보임)

# 1. 사번 가져오기
auth_id = get_auth_id()
if auth_id:
    emp_no_str = auth_id
else :
    print("사번 가져오기 실패!")
    root.destroy()
    exit()

# 2. 화면 크기를 구합니다
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 3. 데이터를 조회합니다
task_data = fetch_task_and_init()

# 4. 데이터가 없으면 즉시 종료
if task_data is None:
    root.destroy()
    exit()

# 5. 데이터가 있을 때만 화면을 표시하고 설정을 적용합니다
root.deiconify() # 🌟 숨겨져 있던 창을 화면에 나타냅니다
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)

# 6. UI 그리기 (이제 screen_height를 그대로 사용할 수 있습니다)
if task_type_str == "ETHICS":
    draw_ethics_ui(task_data)
elif task_type_str == "SELF_CHECK":
    draw_self_check_ui(task_data)

root.mainloop()