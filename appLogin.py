import streamlit as st
import mysql.connector

# DB 연결 설정 (주어진 정보 사용)
config = {
    "host": "localhost",
    "port": 3306,
    "user": "skn14",
    "password": "skn14",
    "database": "users"
}

# DB 연결 함수
def connect_db():
    return mysql.connector.connect(**config)

# 인증 함수 정의
def authenticate(user_id, user_pw):
    conn = connect_db()
    cursor = conn.cursor()
    query = '''
        SELECT * FROM user_list WHERE user_id = %s AND user_pw = %s
    '''
    cursor.execute(query, (user_id, user_pw))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

# Streamlit UI
st.title("로그인 페이지")

with st.form("login_form"):
    user_id = st.text_input("아이디")
    print(user_id, type(user_id))
    user_pw = st.text_input("비밀번호", type="password")
    submit_button = st.form_submit_button("로그인")

if submit_button:
    if authenticate(user_id, user_pw):
        st.success("로그인 성공!")
    else:
        st.error("아이디 또는 비밀번호가 잘못되었습니다.")