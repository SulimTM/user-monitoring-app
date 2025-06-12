# utils/auth.py
import sqlite3
import hashlib
import os

# Путь к базе данных
DB_FILE = "../monitoring.db"

def init_user_db():
    """Инициализация таблицы пользователей."""
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
        # Создание тестового пользователя admin с ролью "Технический специалист"
        hashed_pw = hashlib.sha256("SecureAdmin2023!".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hashed_pw, "Технический специалист"))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Пользователь уже существует
    finally:
        conn.close()

def check_user(username, password):
    """Проверка имени пользователя и пароля."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] == hashlib.sha256(password.encode()).hexdigest():
        return result[1]
    return None

def login_form():
    """Форма входа в систему."""
    import streamlit as st
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
    """Форма регистрации нового пользователя."""
    import streamlit as st
    st.subheader("📝 Регистрация")
    
    new_username = st.text_input("Новое имя пользователя", key="register_username")
    new_password = st.text_input("Новый пароль", type="password", key="register_password")
    confirm_password = st.text_input("Подтвердите пароль", type="password", key="confirm_password")

    if st.button("Зарегистрироваться"):
        if not new_username or not new_password:
            st.error("❗ Заполните все поля")
        elif new_password != confirm_password:
            st.error("❌ Пароли не совпадают")
        elif len(new_password) < 8:
            st.error("❗ Пароль должен содержать минимум 8 символов")
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            try:
                hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                               (new_username, hashed_pw, "Пользователь"))  # По умолчанию — обычный пользователь
                conn.commit()
                st.success("✅ Регистрация прошла успешно!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Имя пользователя занято")
            finally:
                conn.close()

def add_admin_with_secret(secret, new_username, new_password):
    """
    Добавление нового администратора через секрет.
    :param secret: Секретный ключ для проверки прав.
    :param new_username: Имя нового пользователя.
    :param new_password: Пароль нового пользователя.
    :return: True если добавлено, иначе False.
    """
    if secret != os.getenv("ADMIN_SECRET"):
        return False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (new_username, hashed_pw, "Технический специалист"))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_user_role(username, new_role):
    """
    Изменение роли пользователя.
    :param username: Имя пользователя.
    :param new_role: Новая роль (например, "Пользователь" или "Технический специалист").
    :return: True если изменено, иначе False.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
