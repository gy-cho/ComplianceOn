import streamlit as st
import base64
import os
from styles import get_coming_soon_style

def show_coming_soon(menu_name):
    
    get_coming_soon_style()

    def get_base64_gif(file_path):
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

    gif_filename = "assets/icon_waiting_80.gif"
    gif_base64 = get_base64_gif(gif_filename)

    # UI 구성
    if gif_base64:
        gif_html = f'<img src="data:image/gif;base64,{gif_base64}" class="gif-icon">'
    else:
        gif_html = '<div style="font-size:50px; margin-bottom:20px;">⏳</div>'

    st.markdown(f"""
        <div class="coming-soon-card">
            {gif_html}
            <div class="main-text">'{menu_name}' 페이지 준비중입니다.</div>
            <div class="sub-text">
                현재 페이지를 준비하고 있으니 조금만 기다려주세요.<br>
                감사합니다.
            </div>
        </div>
    """, unsafe_allow_html=True)

    