import streamlit as st
import sqlite3
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import json

# ====== Database Functions ======
def init_db():
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            registration_date TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            difficulty_level INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""
            INSERT INTO users (username, password, registration_date, is_admin)
            VALUES (?, ?, ?, ?)
        """, ("admin", hashed_pw, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
    
    conn.commit()
    conn.close()

# ====== Main Functions ======
def register_user(username, password):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        c.execute("""
            INSERT INTO users (username, password, registration_date, is_admin)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_pw, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0))
        conn.commit()
        st.success("Истифодабаранда бомуваффақият ба қайд гирифта шуд .")
        return True
    except sqlite3.IntegrityError:
        st.error("Истифодабаранда аллакай мавҷуд!")
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("""
        SELECT id, username, is_admin 
        FROM users 
        WHERE username=? AND password=?
    """, (username, hashed_pw))
    user = c.fetchone()
    conn.close()
    
    if user:
        st.success("Тизимга муваффақиятли кирилди.")
    else:
        st.error("Нотўғри логин ёки парол!")
    
    return user

def add_field(name, description, user_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO fields (name, description, created_by, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, description, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.success("Фан муваффақиятли равишда қўшилди.")
        return True
    except sqlite3.IntegrityError:
        st.error("Фан аллақачон мавжуд!")
        return False
    finally:
        conn.close()

def add_topic(field_id, name, description, difficulty_level, user_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO topics (field_id, name, description, difficulty_level, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (field_id, name, description, difficulty_level, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.success("Мавзу муваффақиятли равишда қўшилди.")
        return True
    except sqlite3.Error:
        st.error("Мавзу қўшишда хато.")
        return False
    finally:
        conn.close()

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
        st.success("Тест муваффақиятли равишда қўшилди.")
        return True
    except sqlite3.Error:
        st.error("Тест қўшишда хато.")
        return False
    finally:
        conn.close()

def get_all_fields():
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("SELECT id, name, description FROM fields")
    fields = c.fetchall()
    conn.close()
    return fields

def get_topics_by_field(field_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, name, difficulty_level 
        FROM topics 
        WHERE field_id=?
    """, (field_id,))
    topics = c.fetchall()
    conn.close()
    return topics

def get_tests_by_topic(topic_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, question, options, answer 
        FROM tests 
        WHERE topic_id=?
    """, (topic_id,))
    tests = []
    for row in c.fetchall():
        tests.append({
            'id': row[0],
            'question': row[1],
            'options': json.loads(row[2]),
            'answer': row[3]
        })
    conn.close()
    return tests

def save_test_result(user_id, test_id, score):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO test_results (user_id, test_id, score, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, test_id, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_user_scores(user_id):
    conn = sqlite3.connect('learning_platform.db')
    try:
        df = pd.read_sql("""
            SELECT t.field_id, f.name as field_name, tr.score, tr.timestamp 
            FROM test_results tr
            JOIN tests t ON tr.test_id = t.id
            JOIN fields f ON t.field_id = f.id
            WHERE tr.user_id = ?
            ORDER BY tr.timestamp
        """, conn, params=(user_id,))
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()

def get_friends(user_id):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.username 
        FROM friends f
        JOIN users u ON f.friend_id = u.id
        WHERE f.user_id = ?
    """, (user_id,))
    friends = c.fetchall()
    conn.close()
    return friends

def add_friend(user_id, friend_username):
    conn = sqlite3.connect('learning_platform.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM users WHERE username=?", (friend_username,))
        friend = c.fetchone()
        if not friend:
            st.error("Дӯст топилмади!")
            return False
        
        c.execute("""
            INSERT INTO friends (user_id, friend_id, timestamp)
            VALUES (?, ?, ?)
        """, (user_id, friend[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.success("Дӯст муваффақиятли равишда қўшилди.")
        return True
    except sqlite3.Error:
        st.error("Дўстни қўшишда хато.")
        return False
    finally:
        conn.close()

# ====== Recommendation System ======
class LearningRecommender:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)
        self.fields = self.load_fields()
        self.topics = self.load_topics()
    
    def load_fields(self):
        conn = sqlite3.connect('learning_platform.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM fields")
        fields = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        return fields
    
    def load_topics(self):
        conn = sqlite3.connect('learning_platform.db')
        c = conn.cursor()
        c.execute("SELECT id, field_id, name, difficulty_level FROM topics")
        topics = {}
        for row in c.fetchall():
            if row[1] not in topics:
                topics[row[1]] = []
            topics[row[1]].append({
                'id': row[0],
                'name': row[2],
                'level': row[3]
            })
        conn.close()
        return topics
    
    def train_model(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
    
    def recommend_fields(self, answers):
        X = np.array(answers).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict_proba(X_scaled)[0]
        sorted_indices = np.argsort(probabilities)[::-1]
        field_ids = list(self.fields.keys())
        return [(self.fields[field_ids[i]], round(probabilities[i]*100, 1)) for i in sorted_indices]
    
    def recommend_topics(self, field_id, score):
        if field_id not in self.topics:
            return []
        
        if score < 40:
            return [t for t in self.topics[field_id] if t['level'] == 1]
        elif score < 70:
            return [t for t in self.topics[field_id] if t['level'] == 2]
        else:
            return [t for t in self.topics[field_id] if t['level'] == 3]

# ====== User Interface ======
def show_auth_page():
    st.title("🔐 Платформаи омӯзиши индивидуалӣ")
    
    tab1, tab2 = st.tabs(["Даромад", "Бақайдгирӣ"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Номи корбар")
            password = st.text_input("Рамз", type="password")
            
            if st.form_submit_button("Даромад"):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.is_admin = user[2]
                    st.rerun()
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Номи нави корбар")
            new_password = st.text_input("Рамзи нав", type="password")
            
            if st.form_submit_button("Бақайдгирӣ"):
                if register_user(new_username, new_password):
                    st.rerun()

def show_questionnaire():
    st.subheader("🧠 Пурсиши равоншиносӣ")
    
    questions = [
        "Ҳал кардани масъалаҳои мураккаб ба шумо чӣ қадар маъқул аст? (1-10)",
        "Ба фанҳои техникӣ чӣ қадар шавқ доред? (1-10)",
        "Афкори абстрактӣ ба шумо чӣ қадар осон аст? (1-10)",
        "Иҷодкорӣ дар омӯзиш барои шумо чӣ қадар муҳим аст? (1-10)",
        "Огоҳиҳои амалӣ нисбат ба назария чӣ қадар бартарӣ доранд? (1-10)"
    ]
    
    answers = []
    for i, question in enumerate(questions):
        answers.append(st.slider(question, 1, 10, 5, key=f"s_{i}"))
    
    if st.button("Гирифтани тавсияҳо"):
        if 'recommender' not in st.session_state:
            st.session_state.recommender = LearningRecommender()
            X_train = np.random.randint(1, 11, size=(100, 5))
            y_train = np.random.choice(list(st.session_state.recommender.fields.keys()), size=100)
            st.session_state.recommender.train_model(X_train, y_train)
        
        recommendations = st.session_state.recommender.recommend_fields(answers)
        st.session_state.recommendations = recommendations[:3]
        st.rerun()

def show_field_tests(field_id):
    topics = get_topics_by_field(field_id)
    if not topics:
        st.warning("Мавзӯъҳо вуҷуд надоранд!")
        return
    
    selected_topic = st.selectbox(
        "Интихоби мавзӯъ",
        topics,
        format_func=lambda x: f"{x[1]} (Сатҳи душворӣ: {x[2]})"
    )
    
    tests = get_tests_by_topic(selected_topic[0])
    if not tests:
        st.warning("Тестҳо вуҷуд надоранд!")
        return
    
    user_answers = []
    for i, test in enumerate(tests):
        user_answers.append(st.radio(
            f"{i + 1}. {test['question']}",
            test['options'],
            key=f"test_{selected_topic[0]}_{i}"
        ))
    
    if st.button("Иҷрои тест"):
        correct_answers = sum(1 for i, answer in enumerate(user_answers) if answer == tests[i]['answer'])
        score = int((correct_answers / len(tests)) * 100)
        
        save_test_result(st.session_state.user_id, tests[0]['id'], score)
        
        if 'recommender' in st.session_state:
            recommended_topics = st.session_state.recommender.recommend_topics(field_id, score)
            st.session_state.recommended_topics = recommended_topics
        st.success(f"Ҳоли шумо: {score}%")
        st.rerun()

def show_recommended_topics():
    if 'recommended_topics' not in st.session_state:
        return
    
    st.subheader("📚 Мавзӯъҳои тавсияшуда")
    for topic in st.session_state.recommended_topics:
        st.write(f"- {topic['name']} (Сатҳи душворӣ: {topic['level']})")

def show_scores_graph():
    scores_df = get_user_scores(st.session_state.user_id)
    if scores_df.empty:
        return
    
    st.subheader("📊 Натиҷаҳои шумо")
    
    fig, ax = plt.subplots(figsize=(10, 5))
    for field in scores_df['field_name'].unique():
        field_data = scores_df[scores_df['field_name'] == field]
        ax.plot(field_data['timestamp'], field_data['score'], label=field, marker='o')
    
    ax.set_xlabel("Сана")
    ax.set_ylabel("Ҳисоб (%)")
    ax.set_title("Натиҷаҳои тест дар мӯҳлат")
    ax.legend()
    st.pyplot(fig)

def show_community():
    st.subheader("👥 Ҷамъияти омӯзиш")
    
    tab1, tab2 = st.tabs(["Дӯстони шумо", "Иловаи дӯст"])
    
    with tab1:
        friends = get_friends(st.session_state.user_id)
        if friends:
            st.write("Дӯстони шумо:")
            for friend in friends:
                st.write(f"- {friend[1]}")
        else:
            st.warning("Дўстларингиз мавжуд эмас!")
    
    with tab2:
        with st.form("add_friend_form"):
            friend_username = st.text_input("Номи корбари дӯст")
            if st.form_submit_button("Иловаи дӯст"):
                if add_friend(st.session_state.user_id, friend_username):
                    st.success("Дӯст муваффақиятли равишда қўшилди.")
                else:
                    st.error("Дўстни қўшишда хато.")

def show_rating():
    conn = sqlite3.connect('learning_platform.db')
    df = pd.read_sql("""
        SELECT u.username, SUM(tr.score) as total_score
        FROM test_results tr
        JOIN users u ON tr.user_id = u.id
        GROUP BY u.id
        ORDER BY total_score DESC
        LIMIT 10
    """, conn)
    conn.close()
    
    st.subheader("🏆 Беҳтарин омӯзандаҳо")
    st.dataframe(df)

def show_admin_dashboard():
    st.subheader("⚙️ Панели админ")
    
    tab1, tab2, tab3 = st.tabs(["Иловаи фан", "Иловаи мавзӯъ", "Иловаи тест"])
    
    with tab1:
        with st.form("add_field_form"):
            name = st.text_input("Номи фан")
            description = st.text_area("Тавсиф")
            if st.form_submit_button("Иловаи фан"):
                add_field(name, description, st.session_state.user_id)
                st.rerun()
    
    with tab2:
        fields = get_all_fields()
        if not fields:
            st.warning("Аввал фанҳо илова кунед!")
        else:
            with st.form("add_topic_form"):
                field = st.selectbox(
                    "Интихоби фан",
                    fields,
                    format_func=lambda x: x[1]
                )
                name = st.text_input("Номи мавзӯъ")
                description = st.text_area("Тавсифи мавзӯъ")
                difficulty_level = st.select_slider("Сатҳи душворӣ", options=[1, 2, 3])
                if st.form_submit_button("Иловаи мавзӯъ"):
                    add_topic(field[0], name, description, difficulty_level, st.session_state.user_id)
                    st.rerun()
    
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
                with st.form("add_test_form"):
                    topic = st.selectbox(
                        "Интихоби мавзӯъ",
                        topics,
                        format_func=lambda x: x[1]
                    )
                    question = st.text_input("Савол")
                    
                    st.write("Вариантҳо:")
                    options = []
                    columns = st.columns(2)
                    for i in range(4):
                        with columns[i % 2]:
                            options.append(st.text_input(f"Вариант {i + 1}", key=f"variant_{i}"))
                    
                    correct_answer = st.selectbox("Ҷавоби дуруст", options)
                    
                    if st.form_submit_button("Иловаи тест"):
                        add_test(field[0], topic[0], question, options, correct_answer, st.session_state.user_id)
                        st.rerun()

def show_user_dashboard():
    st.title(f"Хуш омадед, {st.session_state.username}!")
    
    if 'recommendations' not in st.session_state:
        show_questionnaire()
        st.stop()
    
    st.subheader("Фанҳои тавсияшуда барои шумо:")
    for fan, confidence in st.session_state.recommendations:
        st.write(f"- {fan} ({confidence}% мувофиқат)")
    
    fields = get_all_fields()
    if not fields:
        return
    
    selected_field = st.selectbox(
        "Интихоби фан барои омӯзиш",
        fields,
        format_func=lambda x: x[1],
        key="fan_tanlash"
    )
    
    show_field_tests(selected_field[0])
    
    st.subheader("Дигар имкониятҳо")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Мавзӯъҳои тавсияшуда"):
            show_recommended_topics()
    
    with col2:
        if st.button("Натиҷаҳои ман"):
            show_scores_graph()
    
    with col3:
        if st.button("Ҷамъияти омӯзиш"):
            show_community()
    
    if st.button("Рейтинг"):
        show_rating()

def main():
    st.set_page_config(page_title="Платформаи омӯзиши ҳушманд", layout="wide")
    
    init_db()
    
    if 'user_id' not in st.session_state:
        show_auth_page()
    else:
        if st.session_state.is_admin:
            show_admin_dashboard()
        else:
            show_user_dashboard()
        
        if st.sidebar.button("Баромад"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
