import streamlit as st
import time

def show_toast(msg_type, message, duration=3):
    colors = {
        "success": "#00C851",
        "error": "#ff4444",
        "warning": "#ffbb33"
    }
    bg_color = colors.get(msg_type, "#333")
    t_id = f"t_{int(time.time() * 1000)}"

    # 핵심: container 자체에 display: none을 주어 레이아웃 공간을 물리적으로 삭제
    # 그 안의 요소만 fixed로 공중에 띄움
    toast_html = f"""
        <div style="display: none;"></div>
        <div id="{t_id}" class="custom-toast-msg">
            {message}
        </div>
        <style>
            #{t_id} {{
                position: fixed;
                bottom: 50px;
                left: 50%;
                transform: translateX(-50%);
                background-color: {bg_color};
                color: white;
                padding: 14px 28px;
                border-radius: 10px;
                z-index: 1000001;
                font-weight: bold;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                pointer-events: none;
                animation: fade_{t_id} {duration}s ease-in-out forwards;
                white-space: nowrap;
            }}
            @keyframes fade_{t_id} {{
                0% {{ opacity: 0; bottom: 20px; }}
                15% {{ opacity: 1; bottom: 50px; }}
                85% {{ opacity: 1; bottom: 50px; }}
                100% {{ opacity: 0; bottom: 20px; }}
            }}
        </style>
    """
    st.markdown(toast_html, unsafe_allow_html=True)