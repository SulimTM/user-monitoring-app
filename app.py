import streamlit as st
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt

# --- Настройка страницы (должна быть первой!) ---
st.set_page_config(page_title="Мониторинг пользователей", layout="wide")
st.title("📊 Мониторинг пользователей и водителей")

# --- Конфигурация ---
CSV_FILE = "data_history.csv"
COLUMNS = ["Дата"] + [
    "Пользователи",
    "Водители",
    "Выполнено",
    "Отмененные",
    "Исполнитель не найден",
    "В работе",
]

# --- Загрузка данных (с кэшированием) ---
@st.cache_data(ttl=60)  # Кэш на 60 секунд
def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE, encoding="utf-8-sig", on_bad_lines='skip')
            if list(df.columns) != COLUMNS:
                st.warning("⚠️ Структура CSV повреждена. Создаём новый файл.")
                df = pd.DataFrame(columns=COLUMNS)
                df.to_csv(CSV_FILE, index=False)
            return df
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке данных: {e}. Создан новый файл.")
            df = pd.DataFrame(columns=COLUMNS)
            df.to_csv(CSV_FILE, index=False)
            return df
    else:
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_FILE, index=False)
        return df

# --- Сохранение данных ---
def save_data(df):
    df.to_csv(CSV_FILE, index=False)
    st.cache_data.clear()  # Очистка кэша после сохранения

# --- Добавить данные ---
def add_data(df, values):
    new_row = {
        "Дата": datetime.now().strftime("%d.%m.%y %H:%M"),
        "Пользователи": values[0],
        "Водители": values[1],
        "Выполнено": values[2],
        "Отмененные": values[3],
        "Исполнитель не найден": values[4],
        "В работе": values[5],
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

# --- Боковое меню (простые кнопки вместо selectbox) ---
st.sidebar.title("📌 Навигация")
show_add = st.sidebar.button("➕ Добавить данные")
show_history = st.sidebar.button("📜 История записей")
show_graphs = st.sidebar.button("📈 Графики")
show_search = st.sidebar.button("🔍 Поиск")

# --- Состояние через session_state ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Добавить данные"

# --- Обновление текущей страницы ---
if show_add:
    st.session_state.current_page = "Добавить данные"
elif show_history:
    st.session_state.current_page = "История записей"
elif show_graphs:
    st.session_state.current_page = "Графики"
elif show_search:
    st.session_state.current_page = "Поиск"

# --- Основная логика ---
df = load_data()

# --- Вкладка: Добавить данные ---
if st.session_state.current_page == "Добавить данные":
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
            values = [users, drivers, done, canceled, not_found, in_progress]
            df = load_data()
            df = add_data(df, values)
            save_data(df)
            st.success("Запись успешно добавлена!")

            # Удаляем значения из session_state, чтобы поля обновились
            del st.session_state["users_input"]
            del st.session_state["drivers_input"]
            del st.session_state["done_input"]
            del st.session_state["canceled_input"]
            del st.session_state["not_found_input"]
            del st.session_state["in_progress_input"]

    # --- Чекбокс: показать последние записи за день ---
    show_last_records = st.checkbox("📜 Показывать последние записи за день")

    if show_last_records:
        df_today = load_data()
        today = datetime.now().strftime("%d.%m.%y")
        df_today['Дата_дата'] = pd.to_datetime(df_today['Дата'], format='mixed', dayfirst=True).dt.strftime('%d.%m.%y')
        today_df = df_today[df_today['Дата_дата'] == today].drop(columns=['Дата_дата'])

        if not today_df.empty:
            st.subheader("📌 Последние записи за сегодня:")
            st.dataframe(today_df.style.highlight_max(axis=0), use_container_width=True)
        else:
            st.info("❌ Сегодня записей ещё нет.")

# --- Вкладка: История записей ---
elif st.session_state.current_page == "История записей":
    st.header("📜 История ввода")
    
    # Кнопка обновления данных
    refresh = st.button("🔄 Обновить данные")
    if refresh:
        st.cache_data.clear()  # Очистка кэша вручную
        st.rerun()

    df = load_data()
    if not df.empty:
        st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
    else:
        st.warning("❌ Нет данных для отображения.")

# --- Вкладка: Графики ---
elif st.session_state.current_page == "Графики":
    st.header("📈 Графики по категориям")
    
    refresh = st.button("🔄 Обновить график")
    if refresh:
        st.cache_data.clear()
        st.rerun()

    category = st.selectbox("Выберите категорию", COLUMNS[1:])
    df = load_data()

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
    df = load_data()

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
