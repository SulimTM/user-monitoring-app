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
    col1, col2 = st.columns(2)
    with col1:
        users = st.number_input("Пользователи", min_value=0, step=1)
        drivers = st.number_input("Водители", min_value=0, step=1)
        done = st.number_input("Выполнено", min_value=0, step=1)
    with col2:
        canceled = st.number_input("Отмененные", min_value=0, step=1)
        not_found = st.number_input("Исполнитель не найден", min_value=0, step=1)
        in_progress = st.number_input("В работе", min_value=0, step=1)

    if st.button("✅ Добавить"):
        values = [users, drivers, done, canceled, not_found, in_progress]
        df = load_data()
        df = add_data(df, values)
        save_data(df)
        st.success("Запись успешно добавлена!")
         # Сброс значений (с помощью session_state)
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

# --- Импорт/экспорт ---
st.sidebar.markdown("### 📥 Импорт / 📤 Экспорт")
export_col, import_col = st.sidebar.columns(2)
with export_col:
    if st.button("📤 Экспортировать CSV"):
        df.to_csv("data_export.csv", index=False)
        st.sidebar.success("✅ Экспортировано как 'data_export.csv'")
        with open("data_export.csv", "rb") as f:
            st.sidebar.download_button("⬇️ Скачать CSV", f.read(), file_name="data_export.csv")

with import_col:
    uploaded_file = st.sidebar.file_uploader("📁 Импортировать", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                new_df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                new_df = pd.read_excel(uploaded_file)
            if list(new_df.columns) != COLUMNS:
                st.sidebar.error("❌ Неправильная структура файла.")
            else:
                new_df.to_csv(CSV_FILE, index=False)
                st.sidebar.success("✅ Данные импортированы!")
        except Exception as e:
            st.sidebar.error(f"Ошибка: {e}")

# --- Отображение сырых данных ---
if st.checkbox("📂 Показать сырые данные"):
    st.subheader("Raw Data")
    st.write(df)
