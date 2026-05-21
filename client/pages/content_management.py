import streamlit as st

def show_content_management():
    st.subheader("서약 문구 편집")
    st.text_area("문구 입력", value="여기에 서약서 내용을 작성하세요.", height=300)
    if st.button("저장"):
        st.success("저장되었습니다.")