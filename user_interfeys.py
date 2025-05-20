import streamlit as st
from auth import show_auth_page
from ad_pan import get_all_fields
import sqlite3
import random
from urllib.parse import urlparse
from datetime import datetime
import ast 
import pandas as pd
import plotly.express as px
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import MinMaxScaler


def get_all_fields():
    conn = sqlite3.connect("learning_platform.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM fields")
    fields = c.fetchall()
    conn.close()
    return fields

def get_tests_by_field(field_id, limit=20):
    conn = sqlite3.connect("learning_platform.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, topic_id, question, options, answer 
        FROM tests 
        WHERE field_id = ? 
        ORDER BY RANDOM() 
        LIMIT ?
    """, (field_id, limit))
    tests = c.fetchall()
    conn.close()
    return tests

def insert_result(user_id, topic_id, correct_count, total_count):
    conn = sqlite3.connect("learning_platform.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO results (user_id, topic_id, correct_count, total_count, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, topic_id, correct_count, total_count, datetime.now()))
    conn.commit()
    conn.close()

def update_user_score(user_id, new_score):
    conn = sqlite3.connect("learning_platform.db")
    c = conn.cursor()
    c.execute("SELECT score FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    old_score = result[0] if result and result[0] is not None else 0
    total = old_score + new_score
    c.execute("UPDATE users SET score = ? WHERE id = ?", (total, user_id))
    conn.commit()
    conn.close()

def get_all_results():
    conn = sqlite3.connect("learning_platform.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, topic_id, correct_count, total_count FROM results")
    return cursor.fetchall()

def get_all_topics():
    conn = sqlite3.connect("learning_platform.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, field_id, difficulty FROM topics")
    return cursor.fetchall()


def show_test_page():
    st.title("👨‍🎓 Роҳнамои омӯзиши фардӣ")
    st.subheader(f"Хуш омадед, {st.session_state.username}!")

    # Sidebar selectbox yaratamiz
    page = st.sidebar.selectbox(
        "Меню интихоб кунед:",
        ("Тестсупорӣ", "🏆 Рейтинг", "📈 Натиҷаҳои шумо", "Ҷамъияти омӯзиш")
    )

    if page == "Тестсупорӣ":
        st.title("📘 Супоридани тест")

        fields = get_all_fields()
        field_names = [f[1] for f in fields]
        field_dict = {f[1]: f[0] for f in fields}

        selected_field_name = st.selectbox("Фанро интиҳоб кунед:", field_names)
        selected_field_id = field_dict[selected_field_name]

        # Testlarni bir marta olish
        if "test_data" not in st.session_state or st.session_state.get("current_field") != selected_field_name:
            all_tests = get_tests_by_field(selected_field_id)
            if not all_tests:
                st.warning("Барои ин фан тестҳо мавҷуд нест.")
                st.stop()

            st.session_state.test_data = random.sample(all_tests, min(20, len(all_tests)))
            st.session_state.current_field = selected_field_name

            # Javoblar uchun session_state ni boshlang‘ich holatga keltirish
            for test_id, topic_id, question, options, answer in st.session_state.test_data:
                key = f"answer_{test_id}"
                st.session_state[key] = None

        tests = st.session_state.test_data

        # Foydalanuvchi testlarni to‘ldiradi
        with st.form("test_form"):
            st.write("### Саволлҳои тестӣ:")
            for i, (test_id, topic_id, question, options, answer) in enumerate(tests):
                options_list = ast.literal_eval(options)
                key = f"answer_{test_id}"

                st.write(f"**{i+1}. {question}**")
                st.radio(
                    "Вариантнро интиҳоб намоед:",
                    options_list,
                    key=key,
                    index=0  # default value
                )
                st.markdown("---")

            submit = st.form_submit_button("✅ Супоридан")

        if submit:
            correct = 0
            for test_id, topic_id, question, options, answer in tests:
                user_ans = st.session_state.get(f"answer_{test_id}")
                if user_ans and user_ans.strip() == answer.strip():
                    correct += 1

            total = len(tests)
            score_10 = round((correct / total) * 10, 2)

            st.success(f"✅ Адади ҷавобҳои дуруст: {correct} / {total}")
            st.info(f"📊 Балл: {score_10} / 10")

            # Bazaga yozish
            topic_id_for_result = tests[0][1]
            insert_result(st.session_state.user_id, topic_id_for_result, correct, total)
            update_user_score(st.session_state.user_id, score_10)

            # Keyingi testlar uchun yangilanish
            del st.session_state.test_data

            # Model va tavsiyalar
            results = get_all_results()
            topics = get_all_topics()
            df_results = pd.DataFrame(results, columns=["user_id", "topic_id", "correct", "total"])
            df_topics = pd.DataFrame(topics, columns=["topic_id", "topic_name", "field_id", "difficulty"])

            df_results["score"] = df_results["correct"] / df_results["total"] * 10
            df = pd.merge(df_results, df_topics, on="topic_id")

            X = df[["difficulty"]]
            y = (df["score"] > 6.5).astype(int)

            if y.nunique() > 1:
                scaler = MinMaxScaler()
                X_scaled = scaler.fit_transform(X)

                model = MLPClassifier(hidden_layer_sizes=(5,), max_iter=500, random_state=42)
                model.fit(X_scaled, y)

                user_id = st.session_state.user_id
                user_topics = df[df["user_id"] == user_id]["topic_id"].unique()
                all_topic_ids = df_topics["topic_id"].unique()
                unseen_topic_ids = list(set(all_topic_ids) - set(user_topics))

                candidate_topics = df_topics[df_topics["topic_id"].isin(unseen_topic_ids)]
                X_candidates = scaler.transform(candidate_topics[["difficulty"]])
                y_pred = model.predict(X_candidates)
                recommended_topics = candidate_topics[y_pred == 0]

                if not recommended_topics.empty:
                    st.markdown("### 🧠 Мавзӯъҳои тавсияшӯда барои омӯзиши шумо:")
                    for name in recommended_topics["topic_name"].values[:5]:
                        st.markdown(f"🔹 **{name}**")
                else:
                    st.info("Ҳамаи мавзӯъҳо аз тарафи шумо хуб  омӯхта шудааст.")
            else:
                st.info("Барои тавсия додан маълумоти кофи нест")

            # Raqamli resurslar ko‘rsatish
            if not recommended_topics.empty:
                st.markdown("### 🧠 Мавзӯҳои тавсияшуда барои омӯхтан:")
                conn = sqlite3.connect("learning_platform.db")
                cur = conn.cursor()

                for _, row in recommended_topics.iterrows():
                    topic_name = row["topic_name"]
                    topic_id = row["topic_id"]

                    cur.execute("SELECT url FROM topic_resources WHERE topic_id = ?", (topic_id,))
                    resource_links = [r[0] for r in cur.fetchall()]

                    with st.expander(f"📌 {topic_name} — ресурсҳо"):
                        if resource_links:
                            for i, url in enumerate(resource_links, start=1):
                                st.markdown(f"[🔗 {url}]({url})", unsafe_allow_html=True)
                        else:
                            st.write("Ҳоло ресурҳо мавҷуд нест.")

                conn.close()
    elif page == "🏆 Рейтинг":
        st.markdown("---")
        st.subheader("🏆 Рейтинг – Беҳтарин 20 истифодабаранда")
        conn = sqlite3.connect("learning_platform.db") 
        cursor = conn.cursor()

        cursor.execute("SELECT username, score FROM users WHERE score IS NOT NULL ORDER BY score DESC LIMIT 20")
        top_users = cursor.fetchall()

        for i, (username, score) in enumerate(top_users, 1):
            st.markdown(f"**{i}. {username}** — {int(score)} балл")
        conn.close()
    elif page == "📈 Натиҷаҳои шумо":
        user_id = st.session_state.user_id

        conn = sqlite3.connect("learning_platform.db")
        cursor = conn.cursor()

        # Fan (field) bo‘yicha natijalarni olish
        cursor.execute("""
            SELECT f.name AS field, r.correct_count, r.total_count, r.timestamp
            FROM results r
            JOIN topics t ON r.topic_id = t.id
            JOIN fields f ON t.field_id = f.id
            WHERE r.user_id = ?
            ORDER BY r.timestamp ASC
        """, (user_id,))
        rows = cursor.fetchall()

        if rows:
            # DataFrame tayyorlash
            df = pd.DataFrame(rows, columns=["field", "correct", "total", "timestamp"])
            df["score_percent"] = (df["correct"] / df["total"]) * 100

            # Grafik chizish
            fig = px.line(
                df,
                x="timestamp",
                y="score_percent",
                color="field",  # Har bir fan o‘z rangida bo‘ladi
                title="🕒 Натиҷаҳои шумо дар давоми вақт",
                labels={"timestamp": "Сана", "score_percent": "Натиҷа (%)", "field": "Фан"},
                markers=True
            )

            fig.update_layout(legend_title_text='Фан', hovermode="x unified")
            fig.update_xaxes(tickformat="%d-%m-%Y", dtick="D1", tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ҳоло натиҷа мавҷуд нест.")
        conn.close()

                
        # 1. Flag uchun session_state boshlanishi
        if "show_community" not in st.session_state:
            st.session_state.show_community = False
    elif page == "Ҷамъияти омӯзиш":
        st.session_state.show_community = True

        # 3. Agar tugma bosilgan bo‘lsa, doimiy ko‘rsatish
        if st.session_state.show_community:
            st.markdown("---")
            st.subheader("🤝 Ҷамъияти омӯзиш")

            tab1, tab2 = st.tabs(["👥 Дӯстҳои ман", "➕ Иловаи дӯст"])
            user_id = st.session_state.user_id
            conn = sqlite3.connect("learning_platform.db")
            cursor = conn.cursor()

            with tab1:
                cursor.execute("""
                    SELECT u.username
                    FROM friends f
                    JOIN users u ON f.friend_id = u.id
                    WHERE f.user_id = ?
                """, (user_id,))
                friends = cursor.fetchall()

                if friends:
                    st.markdown("**дӯстҳои шумо:**")
                    for (friend_username,) in friends:
                        st.markdown(f"👤 {friend_username}")
                else:
                    st.info("Ҳоло дӯсти шумо мавҷуд нест.")

            with tab2:
                friend_username_input = st.text_input("Username-и дӯстатонро ворид намоед", key="friend_input")

                if st.button("➕ Иловаи дӯст", key="add_friend_button"):
                    if not friend_username_input.strip():
                        st.warning("Илтимос, Username-и дӯстатонро ворид намоед")
                    else:
                        cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (friend_username_input.strip(), user_id))
                        friend = cursor.fetchone()

                        if friend:
                            friend_id = friend[0]

                            cursor.execute("""
                                SELECT 1 FROM friends WHERE user_id = ? AND friend_id = ?
                            """, (user_id, friend_id))
                            already_friends = cursor.fetchone()

                            if already_friends:
                                st.warning("Ин истифодабаранда аллакай дӯсти шумо.")
                            else:
                                cursor.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
                                conn.commit()
                                st.success(f"✅ {friend_username_input.strip()} ба руйҳати дӯстон ворид карда шуд.")
                                #st.session_state.friend_input = ""  # Formani tozalash
                        else:
                            st.error("Ин хел username вуҷуд надорад")

            conn.close()