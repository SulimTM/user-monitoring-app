# app.py
from utils.auth import (
    init_user_db,
    check_user,
    login_form,
    register_form,
    add_admin_with_secret,
    update_user_role,
)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
# Убираем автообновление, которое может вызывать проблемы с курсором
# from streamlit_autorefresh import st_autorefresh
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# --- Настройка базы данных ---
DB_FILE = "monitoring.db"

def init_data_db():
    """Инициализация таблицы для записей."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        дата TEXT,
        пользователи INTEGER,
        водители INTEGER,
        выполнено INTEGER,
        отмененные INTEGER,
        исполнитель_не_найден INTEGER,
        в_работе INTEGER
    )
    """)
    conn.commit()
    conn.close()

def load_data():
    """Загрузка данных из базы данных."""
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(
            "SELECT дата, пользователи, водители, выполнено, отмененные, исполнитель_не_найден, в_работе FROM records ORDER BY дата DESC",
            conn
        )
        df.columns = ["Дата", "Пользователи", "Водители", "Выполнено", "Отмененные", "Исполнитель не найден", "В работе"]
    except Exception as e:
        st.warning(f"⚠️ Ошибка загрузки данных: {e}")
        df = pd.DataFrame(columns=COLUMNS)

    conn.close()
    return df

def save_data(values):
    """Сохранение новых данных в базу данных."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO records (дата, пользователи, водители, выполнено, отмененные, исполнитель_не_найден, в_работе)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, values)
    conn.commit()
    conn.close()
    st.cache_data.clear()
    # Убираем st.rerun() чтобы избежать проблем с курсором
    st.success("✅ Данные успешно сохранены!")

# --- Конфигурация ---
COLUMNS = ["Дата"] + [
    "Пользователи",
    "Водители",
    "Выполнено",
    "Отмененные",
    "Исполнитель не найден",
    "В работе",
]

# --- Streamlit конфигурация ---
st.set_page_config(
    page_title="Мониторинг пользователей", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Загружаем CSS для улучшения работы курсора
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.title("📊 Мониторинг пользователей и водителей")

# Убираем автообновление
# st_autorefresh(interval=5 * 1000, key="data_refresh")

# --- Инициализация БД ---
init_user_db()
init_data_db()

# --- Форма входа ---
if "logged_in" not in st.session_state:
    choice = st.sidebar.selectbox("Выберите действие", ["Вход", "Регистрация"])
    if choice == "Вход":
        login_form()
    elif choice == "Регистрация":
        register_form()

else:
    # Главное меню после авторизации
    st.sidebar.success(f"Добро пожаловать, {st.session_state.username}!")
    if st.sidebar.button("Выйти"):
        del st.session_state["logged_in"]
        del st.session_state["username"]
        del st.session_state["role"]
        st.rerun()

    role = st.session_state.get("role", "Пользователь")
    st.sidebar.title("📌 Навигация")

    # Состояние текущей страницы
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "История записей"

    # Переменные для кнопок
    show_add_admin = False
    show_manage_roles = False
    show_add = False

    # Кнопки для технического специалиста
    if role == "Технический специалист":
        if st.sidebar.button("Добавить администратора (секрет)"):
            show_add_admin = True
        if st.sidebar.button("Управление ролями"):
            show_manage_roles = True
        if st.sidebar.button("➕ Добавить данные"):
            show_add = True

    # Общие кнопки
    if st.sidebar.button("📜 История записей"):
        st.session_state.current_page = "История записей"
    if st.sidebar.button("📈 Графики"):
        st.session_state.current_page = "Графики"
    if st.sidebar.button("🔍 Поиск"):
        st.session_state.current_page = "Поиск"
    if st.sidebar.button("ℹ️ Инструкции"):
        st.session_state.current_page = "Инструкции"

    # Обновление состояния страницы
    if show_add_admin and role == "Технический специалист":
        st.session_state.current_page = "Добавить администратора"
    elif show_manage_roles and role == "Технический специалист":
        st.session_state.current_page = "Управление ролями"
    elif show_add:
        st.session_state.current_page = "Добавить данные"

    df = load_data()

    # --- Добавление администратора через секрет ---
    if st.session_state.current_page == "Добавить администратора":
        st.subheader("🔑 Добавить нового администратора (требуется секрет)")

        secret = st.text_input("Введите секретный ключ", type="password", key="admin_secret")
        new_username = st.text_input("Имя пользователя", key="new_admin_username")
        new_password = st.text_input("Пароль", type="password", key="new_admin_password")
        confirm_password = st.text_input("Подтвердите пароль", type="password", key="confirm_admin_password")

        if st.button("Добавить администратора"):
            if secret != os.getenv("ADMIN_SECRET"):
                st.error("❌ Неверный секретный ключ")
            elif not new_username or not new_password:
                st.error("❗ Заполните все поля")
            elif new_password != confirm_password:
                st.error("❌ Пароли не совпадают")
            elif len(new_password) < 8:
                st.error("❗ Пароль должен содержать минимум 8 символов")
            else:
                success = add_admin_with_secret(secret, new_username, new_password)
                if success:
                    st.success("✅ Администратор успешно добавлен!")
                else:
                    st.error("❌ Ошибка при добавлении администратора.")

    # --- Управление ролями пользователей ---
    elif st.session_state.current_page == "Управление ролями":
        st.subheader("👥 Управление ролями пользователей")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        conn.close()

        if not users:
            st.info("❌ Пользователи не найдены.")
        else:
            usernames = [user[0] for user in users]
            selected_user = st.selectbox("Выберите пользователя", usernames)

            current_role = next(user[1] for user in users if user[0] == selected_user)
            st.write(f"Текущая роль: **{current_role}**")

            new_role = st.selectbox("Новая роль", ["Пользователь", "Технический специалист"])

            if st.button("Изменить роль"):
                success = update_user_role(selected_user, new_role)
                if success:
                    st.success(f"✅ Роль пользователя '{selected_user}' изменена на '{new_role}'.")
                else:
                    st.error("❌ Ошибка при изменении роли.")

    # --- Добавление данных ---
    elif st.session_state.current_page == "Добавить данные" and role == "Технический специалист":
        st.header("➕ Добавить новую запись")

        with st.form("add_data_form"):
            col1, col2 = st.columns(2)
            with col1:
                users = st.number_input("Пользователи", min_value=0, step=1, key="users_input")
                drivers = st.number_input("Водители", min_value=0, step=1, key="drivers_input")
                done = st.number_input("Выполнено", min_value=0, step=1, key="done_input")
            with col2:
                canceled = st.number_input("Отмененные", min_value=0, step=1, key="canceled_input")
                not_found = st.number_input("Исполнитель не найден", min_value=0, step=1, key="not_found_input")
                in_progress = st.number_input("В работе", min_value=0, step=1, key="in_progress_input")

            submitted = st.form_submit_button("✅ Добавить")

            if submitted:
                values = (
                    datetime.now().strftime("%d.%m.%y %H:%M"),
                    users, drivers, done, canceled, not_found, in_progress
                )
                save_data(values)

                # Очистка полей без st.rerun()
                st.session_state["users_input"] = 0
                st.session_state["drivers_input"] = 0
                st.session_state["done_input"] = 0
                st.session_state["canceled_input"] = 0
                st.session_state["not_found_input"] = 0
                st.session_state["in_progress_input"] = 0

        # --- Чекбокс: показать последние записи за день ---
        show_last_records = st.checkbox("📜 Показывать последние записи за день")

        if show_last_records:
            df_today = df.copy()
            if not df_today.empty and 'Дата' in df_today.columns:
                today = datetime.now().strftime("%d.%m.%y")
                df_today['Дата_дата'] = pd.to_datetime(df_today['Дата'], format='mixed', dayfirst=True).dt.strftime('%d.%m.%y')
                today_df = df_today[df_today['Дата_дата'] == today].drop(columns=['Дата_дата'])

                if not today_df.empty:
                    st.subheader("📌 Последние записи за сегодня:")
                    st.dataframe(today_df.style.highlight_max(axis=0), use_container_width=True)
                else:
                    st.info("❌ Сегодня записей ещё нет.")
            else:
                st.warning("❌ Нет данных или структура повреждена.")

    # --- История записей ---
    elif st.session_state.current_page == "История записей":
        st.header("📜 История ввода")
        if not df.empty:
            st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
        else:
            st.warning("❌ Нет данных для отображения.")

    # --- Графики ---
    elif st.session_state.current_page == "Графики":
        st.header("📈 Графики по категориям")
        category = st.selectbox("Выберите категорию", COLUMNS[1:])
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df["Дата"], df[category], marker='o', linestyle='-')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("❌ Нет данных для построения графика.")

    # --- Поиск ---
    elif st.session_state.current_page == "Поиск":
        st.header("🔍 Поиск по дате")
        query = st.text_input("Введите дату (дд.мм.гг)")
        if st.button("Найти"):
            if query:
                results = df[df["Дата"].str.contains(query)]
                if not results.empty:
                    st.write("Результаты:")
                    st.dataframe(results)
                else:
                    st.warning("❌ Записи не найдены.")
            else:
                st.warning("❗ Введите дату для поиска.")

    # --- Инструкции ---
    elif st.session_state.current_page == "Инструкции":
        st.header("ℹ️ Инструкции по использованию")

        st.markdown("""
        ## ℹ️ Руководство по использованию
        
        ### 📍 Боковое меню:
        - **➕ Добавить данные** — доступно только техническому специалисту
        - **📜 История записей** — просмотр всех данных
        - **📈 Графики** — визуализация
        - **🔍 Поиск** — поиск по дате
        - **ℹ️ Инструкции** — текущее окно

        ### 🔐 Авторизация:
        - Только зарегистрированные пользователи могут войти
        - Технические специалисты имеют расширенные права
        """)

    else:
        st.warning("⚠️ Неизвестная страница")
