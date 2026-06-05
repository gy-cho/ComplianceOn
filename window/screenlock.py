import sys
import os

# =========================================================================
# 💡 [리눅스 X11 폰트 버그 방어막 및 크래시 방지 우회]
# =========================================================================
IS_LINUX = sys.platform.startswith('linux')
if IS_LINUX:
    os.environ["QT_X11_NO_MITSHM"] = "1"
    os.environ["GDK_CORE_DEVICE_EVENTS"] = "1"
    UI_FONT = "fixed"  # 리눅스 테스트 환경용 비트맵 폰트
else:
    UI_FONT = "Malgun Gothic"

import tkinter as tk
import socket
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
import ctypes
from io import BytesIO

# =========================================================================
# 📌 [서버 및 환경 설정]
# =========================================================================
BASE_URL = "http://192.168.62.94:8080"

# 📌 마스터 데이터 및 상태 인스턴스 정의
emp_no_str = "D230057"        # 테스트 사번
task_id_str = ""
app_seq_str = ""
emp_name_str = "홍길동"        
date_str = "2026년 6월"
task_type_str = ""           # API에서 받아올 현재 태스크 타입 보관

# 자가점검(SELF_CHECK)용 유저 답변 저장 딕셔너리 {qstn_cd: "Y" 또는 "N"}
user_answers = {}

def fetch_task_and_init():
    """프로그램 시작 시 서버에서 오늘의 태스크를 조회하고 타입에 맞는 화면을 띄우는 함수"""
    global task_id_str, app_seq_str, task_type_str, tk_image, canvas
    
    results = []
    get_task_url = f"{BASE_URL}/get-task-qstn?emp_no={emp_no_str}"
    
    try:
        response = requests.get(get_task_url, timeout=3)
        if response.status_code == 200:
            results = response.json()
        else:
            raise Exception(f"API 응답 에러 (HTTP {response.status_code})")
    except Exception as e:
        messagebox.showerror("시스템 오류", f"서버와 통신할 수 없습니다.\n네트워크 상태를 확인해 주세요.\n\n에러: {e}")
        root.destroy()
        exit()
        
    if not results:
        # 할당된 작업이 없는 상황도 비정상 구동으로 간주하고 안전 종료 처리
        messagebox.showinfo("알림", "오늘 참여해야 할 준법 서약 또는 자가점검 내역이 없습니다.")
        root.destroy()
        exit()
        
    # 첫 번째 활성화된 태스크 정보 매핑
    task_data = results[0]
    task_id_str = str(task_data.get("task_id"))   
    app_seq_str = str(task_data.get("app_seq"))   
    task_type_str = task_data.get("task_type", "ETHICS")
    
    if task_type_str == "ETHICS":
        draw_ethics_ui(task_data)
    elif task_type_str == "SELF_CHECK":
        draw_self_check_ui(task_data)


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
            bg_image = Image.open("윤리강령_1.png")
        except:
            # 🌟 로컬 대체 이미지마저 로드 실패 시 무한 루프나 화면 먹통을 막기 위해 팝업 후 즉시 종료
            messagebox.showerror("오류", "서약서 이미지를 서버 및 로컬에서 모두 가져올 수 없어 프로그램을 종료합니다.")
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
# 📌 [타입 B] 자가점검 설문지 화면 (Modern 엔터프라이즈 스타일)
# =========================================================================
def draw_self_check_ui(task_data):
    global canvas, submit_btn
    
    root.configure(background='#F5F7FA')
    
    box_width = int(screen_width * 0.65)
    box_height = int(screen_height * 0.85)
    
    canvas = tk.Canvas(root, width=box_width, height=box_height, bd=0, highlightthickness=1, highlightbackground="#E4E7ED", bg='#FFFFFF')
    canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    # 상단 타이틀 영역
    if IS_LINUX:
        title_lbl = tk.Label(canvas, text=task_data.get("task_nm", "임직원 자가점검"), font=(UI_FONT, 18, "bold"), fg="#1F2D3D", bg="#FFFFFF")
        canvas.create_window(box_width * 0.5, 45, window=title_lbl, anchor=tk.CENTER)
        
        sub_lbl = tk.Label(canvas, text="임직원의 안전한 업무 환경을 위해 하단 자가점검 항목에 성실히 답변 바랍니다.", font=(UI_FONT, 10), fg="#718096", bg="#FFFFFF")
        canvas.create_window(box_width * 0.5, 85, window=sub_lbl, anchor=tk.CENTER)
    else:
        canvas.create_text(box_width * 0.5, 55, text=task_data.get("task_nm", "임직원 자가점검"), font=(UI_FONT, 22, "bold"), fill="#1F2D3D")
        canvas.create_text(box_width * 0.5, 95, text="임직원의 안전한 업무 환경을 위해 하단 자가점검 항목에 성실히 답변 바랍니다.", font=(UI_FONT, 11), fill="#718096")
    
    canvas.create_line(40, 130, box_width - 40, 130, fill="#E2E8F0", width=2)
    
    qstn_list = task_data.get("qstn_list", [])
    start_y = 170
    y_gap = 120  
    
    # 문항 리스트 바인딩 및 라벨 가공
    for idx, qstn in enumerate(qstn_list):
        q_cd = qstn.get("qstn_cd")
        q_title = qstn.get("qstn_nm")
        q_content = qstn.get("qstn_cn") 
        
        current_y = start_y + (idx * y_gap)
        
        lbl_num = tk.Label(canvas, text=f"문항 {idx+1:02d}", font=(UI_FONT, 10, "bold"), fg="#3182CE", bg="#FFFFFF")
        canvas.create_window(55, current_y, window=lbl_num, anchor=tk.W)
        
        lbl_title = tk.Label(canvas, text=q_title, font=(UI_FONT, 12, "bold"), fg="#2D3748", bg="#FFFFFF")
        canvas.create_window(125, current_y, window=lbl_title, anchor=tk.W)
        
        lbl_content = tk.Label(canvas, text=q_content, font=(UI_FONT, 10), fg="#4A5568", bg="#FFFFFF", justify=tk.LEFT)
        canvas.create_window(55, current_y + 35, window=lbl_content, anchor=tk.W)
        
        user_answers[q_cd] = tk.StringVar(value="")
        
        r_yes = tk.Radiobutton(
            canvas, text=" 예 (Yes)", variable=user_answers[q_cd], value="Y", 
            bg="white", activebackground="white", selectcolor="white",
            font=(UI_FONT, 11, "bold"), fg="#2D3748", activeforeground="#3182CE",
            command=check_self_check_complete
        )
        r_no = tk.Radiobutton(
            canvas, text=" 아니오 (No)", variable=user_answers[q_cd], value="N", 
            bg="white", activebackground="white", selectcolor="white",
            font=(UI_FONT, 11, "bold"), fg="#E53E3E", activeforeground="#E53E3E",
            command=check_self_check_complete
        )
        
        canvas.create_window(box_width - 240, current_y + 15, window=r_yes, anchor=tk.W)
        canvas.create_window(box_width - 130, current_y + 15, window=r_no, anchor=tk.W)
        
        canvas.create_line(40, current_y + 75, box_width - 40, current_y + 75, fill="#EDF2F7", width=1)

    # 최종 제출 버튼
    submit_btn = tk.Button(
        canvas, text="점검 완료 및 서약 데이터 전송", command=on_agree, state=tk.DISABLED,
        font=(UI_FONT, 12, "bold"), bg="#E2E8F0", fg="#A0AEC0", 
        width=32, height=1, relief=tk.FLAT, bd=0, cursor="hand2"
    )
    canvas.create_window(box_width * 0.5, box_height - 65, window=submit_btn, anchor=tk.CENTER)


def check_self_check_complete():
    """자가점검 항목 중 누락된 답변이 없는지 체크하여 버튼을 활성화하는 함수"""
    all_answered = True
    for val in user_answers.values():
        if val.get() == "":  
            all_answered = False
            break
            
    if all_answered:
        submit_btn.config(state=tk.NORMAL, bg="#2B6CB0", fg="#FFFFFF", relief=tk.RAISED) 
    else:
        submit_btn.config(state=tk.DISABLED, bg="#E2E8F0", fg="#A0AEC0", relief=tk.FLAT)


# =========================================================================
# 📌 [오류 발생 시 프로세스 강제 종료 로직 전면 보완 적용 구역]
# =========================================================================
def on_agree():
    submit_url = f"{BASE_URL}/submit-compliance" 
    
    payload = {
        "task_id": int(task_id_str) if task_id_str.isdigit() else None,        
        "app_seq": int(app_seq_str) if app_seq_str.isdigit() else None,        
        "emp_no": emp_no_str,
        "emp_main_ans_yn": "Y",  
        "emp_ans_agr_yn": "Y",   
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
        # 🌟 서버 측 검증 에러 및 500 내부 에러 발생 시 처리
        elif response.status_code in [400, 404, 500]:
            res_data = response.json()
            messagebox.showwarning("제출 실패", f"서버가 처리를 거부했습니다.\n\n사유: {res_data.get('message', '알 수 없는 요류')}")
            root.destroy()  # 💡 팝업창 확인 누른 후 프로그램 자동 폭파
            exit()
        else:
            messagebox.showerror("오류", f"정의되지 않은 서버 응답 에러가 발생했습니다.\nStatus Code: {response.status_code}")
            root.destroy()
            exit()
    except Exception as e:
        # 🌟 전송 중 타임아웃, 사내 서브넷 끊김 등 세션 유실 예외 처리
        messagebox.showerror("네트워크 오류", f"서버에 서약 데이터를 전송하지 못했습니다.\n네트워크 연결 상태를 재확인해 주세요.\n\n에러: {e}")
        root.destroy()  # 💡 팝업창 확인 누른 후 프로그램 자동 폭파
        exit()


def setup_ethics_elements(width, height):
    """기존 윤리강령 화면 렌더링용 서브 컴포넌트 설정"""
    global submit_btn, agreement_var
    TARGET_X = width * 0.50
    agreement_var = tk.IntVar()
    
    check_btn = tk.Checkbutton(
        canvas, text="본인은 상기의 '윤리강령' 내용을 확인하였으며, 이를 준수할 것을 다짐합니다.", 
        variable=agreement_var, command=check_ethics_complete, font=(UI_FONT, 12, "bold"),
        bg="#F4F4F2", activebackground="#F4F4F2", bd=0
    )
    canvas.create_window(TARGET_X, height * 0.83, window=check_btn, anchor=tk.CENTER)
    canvas.create_text(TARGET_X, height * 0.86, text=date_str, font=(UI_FONT, 12, "bold"), fill="#333333", anchor=tk.CENTER)
    canvas.create_text(TARGET_X, height * 0.88, text=f"직원번호 : {emp_no_str}       서명 : {emp_name_str}", font=(UI_FONT, 12, "bold"), fill="#333333", anchor=tk.CENTER)

    submit_btn = tk.Button(
        canvas, text="확인 및 업무 시작", command=on_agree, state=tk.DISABLED,
        font=(UI_FONT, 12, "bold"), bg="#cccccc", fg="white", width=24, height=1, relief=tk.SOLID, bd=1
    )
    canvas.create_window(TARGET_X, height * 0.92, window=submit_btn, anchor=tk.CENTER)

def check_ethics_complete():
    if agreement_var.get(): submit_btn.config(state=tk.NORMAL, bg="#FFBC00", fg="#111111")
    else: submit_btn.config(state=tk.DISABLED, bg="#cccccc", fg="white")


# =========================================================================
# 시스템 윈도우 생성 및 메인루프 기동
# =========================================================================
try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
except: pass

root = tk.Tk()
root.title("사내 준법 서약 시스템")
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(background='black') 
root.protocol("WM_DELETE_WINDOW", lambda: None)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.after(100, fetch_task_and_init)
root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()