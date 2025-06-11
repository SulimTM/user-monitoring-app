# app.py
from utils.auth import init_user_db, check_user, login_form, register_form
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# --- Настройка базы данных ---
DB_FILE = "monitoring.db"

def init_data_db():
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO records (дата, пользователи, водители, выполнено, отмененные, исполнитель_не_найден, в_работе)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, values)
    conn.commit()
    conn.close()
    st.cache_data.clear()
    st.rerun()

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
st.set_page_config(page_title="Мониторинг пользователей", layout="wide")
st.title("📊 Мониторинг пользователей и водителей")

# --- Автообновление ---
st_autorefresh(interval=5 * 1000, key="data_refresh")

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
    st.sidebar.success(f"Добро пожаловать, {st.session_state.username}!")
    if st.sidebar.button("Выйти"):
        del st.session_state["logged_in"]
        del st.session_state["username"]
        del st.session_state["role"]
        st.rerun()

    # --- Боковое меню (разные кнопки по ролям) ---
    role = st.session_state.get("role", "Пользователь")
    st.sidebar.title("📌 Навигация")
    show_add = st.sidebar.button("➕ Добавить данные") if role == "Технический специалист" else False
    show_history = st.sidebar.button("📜 История записей")
    show_graphs = st.sidebar.button("📈 Графики")
    show_search = st.sidebar.button("🔍 Поиск")
    show_instructions = st.sidebar.button("ℹ️ Инструкции")

    # --- Состояние текущей страницы ---
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "История записей"

    if show_add:
        st.session_state.current_page = "Добавить данные"
    elif show_history:
        st.session_state.current_page = "История записей"
    elif show_graphs:
        st.session_state.current_page = "Графики"
    elif show_search:
        st.session_state.current_page = "Поиск"
    elif show_instructions:
        st.session_state.current_page = "Инструкции"

    df = load_data()

    # --- Вкладка: Добавить данные ---
    if st.session_state.current_page == "Добавить данные" and role == "Технический специалист":
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

                # Очистка полей
                del st.session_state["users_input"]
                del st.session_state["drivers_input"]
                del st.session_state["done_input"]
                del st.session_state["canceled_input"]
                del st.session_state["not_found_input"]
                del st.session_state["in_progress_input"]

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

    # --- Вкладка: История записей ---
    elif st.session_state.current_page == "История записей":
        st.header("📜 История ввода")
        if not df.empty:
            st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
        else:
            st.warning("❌ Нет данных для отображения.")

    # --- Вкладка: Графики ---
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

    # --- Вкладка: Поиск ---
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

    # --- Вкладка: Инструкции ---
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
