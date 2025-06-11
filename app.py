import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt

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
        try:
            return pd.read_csv(CSV_FILE, encoding="utf-8-sig", on_bad_lines='skip')
        except Exception as e:
            st.error(f"❌ Ошибка загрузки данных: {e}. Создан новый файл.")
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

# --- Функция для отображения таблицы с возможностью выбора строки ---
def show_selectable_table(df, key="table"):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    gb.configure_grid_options(enableCellTextSelection=True)
    grid_options = gb.build()

    response = AgGrid(
        df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        theme="alpine",
        height=300,
        width='100%',
        key=key,
        reload_data=False,
        update_mode="MODEL_CHANGED"
    )

    if hasattr(response, "selected_rows") and response.selected_rows is not None:
        return response.selected_rows
    elif isinstance(response, dict) and "selectedRows" in response:
        return response["selectedRows"]
    else:
        return []

# --- Интерфейс Streamlit ---
st.set_page_config(page_title="Мониторинг пользователей", layout="wide")
st.title("📊 Мониторинг пользователей и водителей")

# --- Боковое меню (простые кнопки вместо selectbox) ---
st.sidebar.title("📌 Навигация")
show_add = st.sidebar.button("➕ Добавить данные")
show_history = st.sidebar.button("📜 История записей")
show_graphs = st.sidebar.button("📈 Графики")
show_search = st.sidebar.button("🔍 Поиск")

# --- Основная логика ---
df = load_data()
if not df.empty:
    dates = df["Дата"].tolist()
    data_tables = [df[col].tolist() for col in df.columns[1:]]
else:
    dates = []
    data_tables = [[] for _ in range(6)]

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
            selected_row = show_selectable_table(today_df, key="today_table")
            if len(selected_row) > 0:
                if isinstance(selected_row, list):
                    row_data = selected_row[0]  # Работаем напрямую с dict
                else:
                    row_data = selected_row.iloc[0].to_dict()  # Преобразуем Series в словарь

                copied_text = ' | '.join(f"{k}: {v}" for k, v in row_data.items())
                st.code(copied_text)
                st.info("✔️ Строка скопирована в буфер обмена!")
        else:
            st.info("❌ Сегодня записей ещё нет.")

# --- Вкладка: История записей ---
elif st.session_state.current_page == "История записей":
    st.header("📜 История ввода")
    if not df.empty:
        st.subheader("📌 Выберите строку для копирования")
        selected_row = show_selectable_table(df, key="history_table")
        if len(selected_row) > 0:
            if isinstance(selected_row, list):
                row_data = selected_row[0]
            else:
                row_data = selected_row.iloc[0].to_dict()

            copied_text = ' | '.join(f"{k}: {v}" for k, v in row_data.items())
            st.code(copied_text)
            st.info("✔️ Строка скопирована в буфер обмена!")
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
                selected_row = show_selectable_table(results, key="search_table")
                if len(selected_row) > 0:
                    if isinstance(selected_row, list):
                        row_data = selected_row[0]
                    else:
                        row_data = selected_row.iloc[0].to_dict()

                    copied_text = ' | '.join(f"{k}: {v}" for k, v in row_data.items())
                    st.code(copied_text)
                    st.info("✔️ Строка скопирована в буфер обмена!")
            else:
                st.warning("❌ Записи не найдены.")
        else:
            st.warning("❗ Введите дату для поиска.")
