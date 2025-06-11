import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt

# --- Настройка страницы (САМАЯ ПЕРВАЯ команда после импортов) ---
st.set_page_config(page_title="Мониторинг пользователей", layout="wide")
st_autorefresh(interval=10 * 1000, key="data_refresh")  # Обновление каждые 10 секунд

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
