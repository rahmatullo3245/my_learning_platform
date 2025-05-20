import streamlit as st
import sqlite3
import hashlib
# Database bilan bog'lanish
def get_db_connection():
    conn = sqlite3.connect('learning_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

# Parolni hash qilish
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Foydalanuvchini ro'yxatdan o'tkazish
def register_user(name, username, password, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
            (name, username, hashed_password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Foydalanuvchini tekshirish
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user


# Asosiy ilova
def show_auth_page():
    st.set_page_config(page_title="Роҳнамои омӯзиши фардӣ", page_icon="📚")
    
    # Session stateda foydalanuvchi ma'lumotlarini saqlash
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Agar foydalanuvchi login qilmagan bo'lsa
    if not st.session_state.user:
        st.title("Хуш омадед ба Роҳнамои омӯзиши фардӣ!")
        
        # Tablar yaratish
        tab1, tab2 = st.tabs(["🔐 Даромад", "📝 Регистратсия"])
        
        with tab1:
            st.subheader("Даромад ба платформа")
            username = st.text_input("Номи истифодабаранда", key="login_username")
            password = st.text_input("Парол", type="password", key="login_password")
            
            if st.button("Даромадан", key="login_button"):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = dict(user)
                    st.session_state.user_id = user[0]  # <--- ID ni saqlaymiz
                    st.session_state.username = user[1]
                    st.session_state.is_admin = user[4] is not None and user[4].lower() == 'admin'

                    if st.session_state.is_admin:
                        st.success("Шумо хамчун админ ба плптформа ворид шудед.")
                    else:
                        st.success("Шумо хамчун истифодабаранда ба платформа ворид шудед.")
                    st.rerun()
                else:
                    st.error("Логин ё пароли нодуруст ворид кардед.")


        
        with tab2:
            st.subheader("Сохтани хисоби нав")
            name = st.text_input("Исми пурраатон", key="reg_name")
            username = st.text_input("Номи истифодабаранда", key="reg_username")
            password = st.text_input("Парол", type="password", key="reg_password")
            confirm_password = st.text_input("Паролро тасдиқ намоед", type="password", key="reg_confirm")
            
            if st.button("Аз рӯйҳат гузарӣ", key="reg_button"):
                if not name or not username or not password:
                    st.error("Илтимос ҳамаи майдонҳоро пурра намоед")
                elif password != confirm_password:
                    st.error("Паролҳо мувофиқ нашуд")
                elif len(password) < 6:
                    st.error("Парол на кам аз 6 рамз бошад")
                else:
                    if register_user(name, username, password):
                        # Avtomatik login qilish
                        user = authenticate_user(username, password)
                        if user:
                            st.session_state.user = dict(user)
                            st.session_state.user_id = user[0]
                            st.session_state.username = user[1]
                            st.session_state.is_admin = user[4] is not None and user[4].lower() == 'admin'
                            st.success("Ҳисоб бо муваффақият сохта шуд ва шумо ба платформа ворид шудед.")
                            st.rerun()
                        else:
                            st.warning("Муаммо дар доҳилшавӣ бори дигар кӯшиш намоед.")
                    else:
                        st.error("Ин номи истифодабаранда аллакай мавҷуд")

    
    # Agar foydalanuvchi login qilgan bo'lsa
    else:
        st.sidebar.title(f"👤 {st.session_state.user['name']}")
        st.sidebar.write(f"Role: {st.session_state.user['role']}")
        st.sidebar.write(f"Score: {st.session_state.user['score']}")
        
        if st.sidebar.button("Баромад"):
            st.session_state.user = None
            st.rerun()
        
        # Asosiy kontent
        st.title(f"Хуш омадед, {st.session_state.user['name']}!")
        st.write("Саҳифаи асосӣ")
        
        '''# Foydalanuvchi roliga qarab turli funksiyalar
        if st.session_state.user['role'] == 'admin':
            st.warning("Шумо хамчун администратор ба платформа ворид шудед")
            # Admin funksiyalari qo'shishingiz mumkin'''

if __name__ == "__main__":
    main()
