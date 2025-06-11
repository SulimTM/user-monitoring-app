import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import os

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

# --- Загрузка данных ---
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_FILE, index=False)
        return df

# --- Сохранение данных ---
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- Добавить данные ---
def add_data(df, values):
    new_row = {
        "Дата": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "Пользователи": values[0],
        "Водители": values[1],
        "Выполнено": values[2],
        "Отмененные": values[3],
        "Исполнитель не найден": values[4],
        "В работе": values[5],
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

# --- Интерфейс Streamlit ---
st.set_page_config(page_title="Мониторинг пользователей", layout="wide")
st.title("📊 Мониторинг пользователей и водителей")

# --- Боковое меню ---
menu = st.sidebar.selectbox("Выберите действие", ["Добавить данные", "История записей", "Графики", "Поиск"])

# --- Загрузка текущих данных ---
df = load_data()
if not df.empty:
    dates = df["Дата"].tolist()
    data_tables = [df[col].tolist() for col in df.columns[1:]]
else:
    dates = []
    data_tables = [[] for _ in range(6)]

# --- Вкладка: Добавить данные ---
if menu == "Добавить данные":
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

            # Сбрасываем значения полей
            st.session_state["users_input"] = 0
            st.session_state["drivers_input"] = 0
            st.session_state["done_input"] = 0
            st.session_state["canceled_input"] = 0
            st.session_state["not_found_input"] = 0
            st.session_state["in_progress_input"] = 0

# --- Вкладка: История записей ---
elif menu == "История записей":
    st.header("📜 История ввода")
    if not df.empty:
        st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
    else:
        st.warning("❌ Нет данных для отображения.")

# --- Вкладка: Графики ---
elif menu == "Графики":
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
elif menu == "Поиск":
    st.header("🔍 Поиск по дате")
    query = st.text_input("Введите дату (дд.мм.гггг)")
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
