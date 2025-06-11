# utils/auth.py
import streamlit as st
import sqlite3
import hashlib

DB_FILE = "../monitoring.db"  # Путь к вашей БД

def init_user_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'Пользователь'
    )
    """)
    try:
        # Тестовый пользователь: admin / password → Роль: "Технический специалист"
        hashed_pw = hashlib.sha256("password".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hashed_pw, "Технический специалист"))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Уже существует
    finally:
        conn.close()

def check_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] == hashlib.sha256(password.encode()).hexdigest():
        return result[1]  # Возвращаем роль
    return None

def login_form():
    st.title("🔐 Вход в систему")

    username = st.text_input("Имя пользователя", key="login_username")
    password = st.text_input("Пароль", type="password", key="login_password")

    if st.button("Войти"):
        role = check_user(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.rerun()
        else:
            st.error("❌ Неверное имя или пароль")

def register_form():
    st.subheader("📝 Регистрация")
    
    new_username = st.text_input("Новое имя пользователя", key="register_username")
    new_password = st.text_input("Новый пароль", type="password", key="register_password")
    confirm_password = st.text_input("Подтвердите пароль", type="password", key="confirm_password")

    if st.button("Зарегистрироваться"):
        if not new_username or not new_password:
            st.error("❗ Заполните все поля")
        elif new_password != confirm_password:
            st.error("❌ Пароли не совпадают")
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            try:
                hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                               (new_username, hashed_pw, "Пользователь"))  # По умолчанию — обычный пользователь
                conn.commit()
                st.success("✅ Регистрация прошла успешно!")
            except sqlite3.IntegrityError:
                st.error("❌ Имя пользователя занято")
            finally:
                conn.close()
