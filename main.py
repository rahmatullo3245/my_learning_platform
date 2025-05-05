import streamlit as st
import sqlite3
import hashlib
from auth import show_auth_page
from ad_pan import show_admin_dashboard
from user_interfeys import show_test_page

def init_db():
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""
            INSERT INTO users (name, username, password, role, score)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin", hashed_pw, "admin", 0))
    
    conn.commit()
    conn.close()


def main():
    #st.set_page_config(page_title="Платформаи омӯзиши ҳушманд", layout="wide")
    init_db()
    #show_auth_page()
    
    if 'user_id' not in st.session_state:
        show_auth_page()
    else:
        if st.session_state.is_admin:
            show_admin_dashboard()
        else:
            if st.session_state.user_id:
                show_test_page()
        
        if st.sidebar.button("Баромад"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
