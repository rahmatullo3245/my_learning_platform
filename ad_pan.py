import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import json
import uuid
# funksiya baroi ilova kardani fanho
def add_field(name, description, user_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO fields (name, description, created_by, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, description, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.success("Фан бо  муваффақият илова карда шуд.")
        return True
    except sqlite3.IntegrityError:
        st.error("Ин фан аллакай мавҷуд!")
        return False
    finally:
        conn.close()
# funksiya baroi ilova kardani mavzuho
def add_topic(field_id, name, difficulty_level, resource_urls):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        # 1. Mavzuni qo‘shish
        c.execute("""
            INSERT INTO topics (name, field_id, difficulty)
            VALUES (?, ?, ?)
        """, (name, field_id, difficulty_level))
        topic_id = c.lastrowid

        # 2. Resurslarni qo‘shish
        for url in resource_urls:
            if url.strip():  # bo‘sh emasligini tekshir
                c.execute("""
                    INSERT INTO topic_resources (topic_id, url)
                    VALUES (?, ?)
                """, (topic_id, url.strip()))

        conn.commit()
        st.success("Мавзӯъ ва ресурсҳо бомуваффақият илова карда шуд.")
        return True
    except sqlite3.Error as e:
        st.error(f"Хато: {e}")
        return False
    finally:
        conn.close()

# funksiya baroi ilova kardani testho
def add_test(field_id, topic_id, question, options, answer, user_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        options_json = json.dumps(options)
        c.execute("""
            INSERT INTO tests (field_id, topic_id, question, options, answer, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (field_id, topic_id, question, options_json, answer, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.success("Тест бомуваффақият илова карда шуд.")
        return True
    except sqlite3.Error:
        st.error("Дар вақти иловаи тест хатогӣ рӯх дод.")
        return False
    finally:
        conn.close()
# funksiya baroi giriftani fanhoi mavjudbuda dar baza
def get_all_fields():
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("SELECT id, name, description FROM fields")
    fields = c.fetchall()
    conn.close()
    return fields
#funksiya baroi giriftani mavzuho az rui fanho dar baza mavjudbuda
def get_topics_by_field(field_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, name, difficulty 
        FROM topics 
        WHERE field_id=?
    """, (field_id,))
    topics = c.fetchall()
    conn.close()
    return topics

# funksiya baroi nishon dodani paneli admin dar main.py davat karda meshavad
def show_admin_dashboard():
    st.subheader("⚙️ Панели админ")
    
    tab1, tab2, tab3 = st.tabs(["Иловаи фан", "Иловаи мавзӯъ", "Иловаи тест"])
    
    with tab1:
        #baroi toza kardani forma
        if st.session_state.get("clear_field_form"):
            st.session_state["field_name"] = ""
            st.session_state["field_description"] = ""
            st.session_state["clear_field_form"] = False
            #baroi sohtani forma
        with st.form("add_field_form"):
            name = st.text_input("Номи фан", key="field_name")
            description = st.text_area("Тавсиф", key="field_description")
            if st.form_submit_button("Иловаи фан"):
                add_field(name, description, st.session_state.user_id)
                st.session_state["clear_field_form"] = True  
                st.rerun()
     #baroi toza kardani forma 
    if st.session_state.get("clear_topic_form_tab2"):
        st.session_state["tab2_topic_name"] = ""
        st.session_state["tab2_difficulty_level"] = 1  # default value
        st.session_state["tab2_resource_1"] = ""
        st.session_state["tab2_resource_2"] = ""
        st.session_state["tab2_resource_3"] = ""
        st.session_state["clear_topic_form_tab2"] = False
    with tab2:
        fields = get_all_fields()
        if not fields:
            st.warning("Аввал фанҳо илова кунед!")
        else:
            with st.form("add_topic_form"):
                field = st.selectbox(
                    "Интихоби фан",
                    fields,
                    format_func=lambda x: x[1],
                    key="tab2_field_select"
                )
                st.text_input("Номи мавзӯъ", key="tab2_topic_name")
                st.select_slider("Сатҳи душворӣ", options=list(range(1, 11)), key="tab2_difficulty_level")

                st.markdown("#### 📎 Ресурсҳо барои мавзӯъ (YouTube, сайт ва ҳ.к.):")
                st.text_input("Ресурс 1 (URL):", key="tab2_resource_1")
                st.text_input("Ресурс 2 (URL):", key="tab2_resource_2")
                st.text_input("Ресурс 3 (URL):", key="tab2_resource_3")

                if st.form_submit_button("Иловаи мавзӯъ"):
                    resource_urls = [
                        st.session_state["tab2_resource_1"],
                        st.session_state["tab2_resource_2"],
                        st.session_state["tab2_resource_3"]
                    ]
                    success = add_topic(
                        st.session_state["tab2_field_select"][0],
                        st.session_state["tab2_topic_name"],
                        st.session_state["tab2_difficulty_level"],
                        resource_urls
                    )
                    if success:
                        #  Tozalash flagi faollashtiriladi
                        st.session_state["clear_topic_form_tab2"] = True
                        st.rerun()

     #baroi sohtani forma
        
    with tab3:
            fields = get_all_fields()
            if not fields:
                st.warning("Аввал фанҳо илова кунед!")
            else:
                field = st.selectbox(
                    "Интихоби фан",
                    fields,
                    format_func=lambda x: x[1],
                    key="test_fan_select"
                )
                topics = get_topics_by_field(field[0])
                if not topics:
                    st.warning("Аввал мавзӯъҳо илова кунед!")
                else:
                    #  Formani tozalash flagi bo‘lsa, inputlarni tozalaymiz (BEFORE widgets)
                    if st.session_state.get("clear_test_form", False):
                        st.session_state["question_text"] = ""
                        for i in range(4):
                            st.session_state[f"variant_{i}"] = ""
                        st.session_state["clear_test_form"] = False  # endi yana ishlamasin

                    with st.form("add_test_form"):
                        topic = st.selectbox(
                            "Интихоби мавзӯъ",
                            topics,
                            format_func=lambda x: x[1]
                        )

                        question = st.text_input("Савол", key="question_text")

                        st.write("Вариантҳо:")
                        options = []
                        columns = st.columns(2)
                        for i in range(4):
                            with columns[i % 2]:
                                options.append(st.text_input(f"Вариант {i + 1}", key=f"variant_{i}"))

                        # Selectbox faqat 4 ta to‘liq variant bo‘lsa chiqadi
                        correct_answer = None
                        if all(options):
                            correct_answer = st.selectbox("Ҷавоби дуруст", options, index=None, placeholder="Ҷавоби дуруст")

                        submitted = st.form_submit_button("Иловаи тест")

                        if submitted:
                            if not question.strip():
                                st.error("Саволро ворид намоед!")
                            elif not all(options):
                                st.error("Ҳамаи варианҳоро доҳил кунед!")
                            elif correct_answer is None:
                                st.error("Ҷавоби дурустро интихоб намоед!")
                            else:
                                add_test(field[0], topic[0], question.strip(), options, correct_answer, st.session_state.user_id)
                                st.success("Тест бомуваффақият илова шуд.")

                                # Belgilaymizki: keyingi rerun da formani tozalash kerak
                                st.session_state["clear_test_form"] = True
                                st.rerun()
