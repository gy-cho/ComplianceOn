import tkinter as tk
import socket
from tkinter import messagebox
import requests

def on_agree():
# 1. 서버로 보낼 데이터 준비
    url = "http://127.0.0.1:8000/submit-consent"  # 나중에 미니PC IP로 변경
    # 1. 호스트 이름과 IP 주소 추출
    hostname = socket.gethostname()
    internal_ip = socket.gethostbyname(hostname)

    # 2. 페이로드 구성
    payload = {
        "emp_no": "2026002",
        "emp_name": "홍길동",
        "pc_name": hostname,
        "user_ip": internal_ip  # 👈 여기에 추출한 IP를 쏙 넣어줍니다!
    }

    try:
        # 2. 서버로 동의 내역 전송 (타임아웃 3초 설정)
        response = requests.post(url, json=payload, timeout=3)
        
        # 3. 전송 결과에 따른 처리
        if response.status_code == 200:
            res_data = response.json()
            # 서버에서 보내준 메세지를 그대로 팝업에 노출
            messagebox.showinfo("알림", res_data["message"])
            root.destroy()  # 성공했을 때만 창 닫기
        elif response.status_code == 409:
            res_data = response.json()
            # 서버에서 보내준 메세지를 그대로 팝업에 노출
            messagebox.showinfo("알림", res_data["message"])
            root.destroy()  # 성공했을 때만 창 닫기
        else:
            messagebox.showerror("오류", f"서버 응답 에러: {response.status_code}\n전산팀에 문의하세요.")
            
    except requests.exceptions.RequestException as e:
        # 서버가 꺼져있거나 네트워크 연결이 안 될 경우
        messagebox.showerror("네트워크 오류", "서버와 통신할 수 없습니다.\n네트워크 상태를 확인해 주세요.")
        print(f"Error: {e}")

def check():
    # 체크박스 상태에 따라 버튼 활성화/비활성화
    if agreement_var.get():
        submit_btn.config(state=tk.NORMAL, bg="#004C98", fg="white") # 활성화 시 색상 변경
    else:
        submit_btn.config(state=tk.DISABLED, bg="#cccccc")

root = tk.Tk()
root.title("사내 준법 서약 시스템")

# 1. 전체 화면 설정
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)  # 항상 최상단 노출
root.configure(background='white') # 바탕색 흰색

# 2. 닫기 버튼(X) 및 Alt+F4 무력화 (동의 버튼으로만 종료 가능)
root.protocol("WM_DELETE_WINDOW", lambda: None)

# 화면 중앙 배치를 위한 프레임
frame = tk.Frame(root, bg="white")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

# 디자인 구성 요소
title_label = tk.Label(
    frame, 
    text="준법 및 보안 준수 서약서", 
    font=("Malgun Gothic", 24, "bold"), 
    bg="white", 
    fg="#333333"
)
title_label.pack(pady=(0, 20))

# 서약 내용 (간략 예시)
content_text = (
    "1. 본인은 회사의 보안 규정을 철저히 준수하겠습니다.\n"
    "2. 사내 정보를 외부에 유출하지 않으며, 승인되지 않은 SW를 사용하지 않겠습니다.\n"
    "3. 준법 교육 내용을 숙지하였으며 이를 위반 시 책임을 지겠습니다."
)
content_label = tk.Label(
    frame, 
    text=content_text, 
    font=("Malgun Gothic", 12), 
    bg="#f5f5f5", 
    justify=tk.LEFT, 
    padx=20, 
    pady=20,
    wraplength=600
)
content_label.pack(pady=20)

# 3. 체크박스 및 동의 버튼 디자인
agreement_var = tk.IntVar()
check_btn = tk.Checkbutton(
    frame, 
    text="위 내용을 모두 숙지하였으며 이에 동의합니다.", 
    variable=agreement_var, 
    command=check,
    font=("Malgun Gothic", 11),
    bg="white",
    activebackground="white"
)
check_btn.pack(pady=10)

submit_btn = tk.Button(
    frame, 
    text="확인 및 업무 시작", 
    command=on_agree, 
    state=tk.DISABLED, # 기본값은 비활성화
    font=("Malgun Gothic", 12, "bold"),
    bg="#cccccc", 
    fg="white",
    width=20,
    height=2,
    relief=tk.FLAT
)
submit_btn.pack(pady=20)

# (테스트용) Esc 키를 누르면 종료되도록 설정 (실제 배포 시에는 삭제하세요)
root.bind("<Escape>", lambda e: root.destroy())

root.mainloop()