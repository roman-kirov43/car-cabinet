import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Настройка внешнего вида страницы
st.set_page_config(page_title="Личный кабинет автосалона", layout="wide")

# Ключ твоей Google Таблицы
SHARE_ID = "1On_134S1gG5Cduk3mGRNipffeNXED3CzDU3EJe-1Dfc" 

@st.cache_data(ttl=2)  # Мгновенное обновление данных
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHARE_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    # Умная очистка заголовков: убираем пробелы, подчеркивания и переводим в нижний регистр
    df.columns = df.columns.str.strip().str.lower().str.replace('_', '').str.replace(' ', '')
    return df

try:
    # Загружаем твои листы из таблицы
    df_cars = load_data("cars")
    df_activity = load_data("activity_log")
    
    # Берем первый автомобиль
    car = df_cars.iloc[0]
    
    # Ищем колонку с ID авто (теперь она называется строго 'idавто')
    car_id = car['idавто']
    
    # Фильтруем активность по этой машине
    car_activity = df_activity[df_activity['idавто'] == car_id].copy()
    
    # Находим нужные столбцы по ключевым словам, чтобы не зависеть от точного названия
    col_date = [c for c in car_activity.columns if 'дата' in c][0]
    col_calls = [c for c in car_activity.columns if 'звонк' in c][0]
    col_visits = [c for c in car_activity.columns if 'визит' in c][0]
    col_tests = [c for c in car_activity.columns if 'тест' in c][0]
    col_views = [c for c in car_activity.columns if 'просмотр' in c][0]

    car_activity[col_date] = car_activity[col_date].astype(str)
    
    days_on_sale = 23

    # --- ИНТЕРФЕЙС ---
    st.title("📊 Личный кабинет комиссионера")
    
    # Восстанавливаем оригинальные названия для вывода на экран
    model_name = car[[c for c in df_cars.columns if 'марка' in c][0]]
    vin_name = car[[c for c in df_cars.columns if 'vin' in c or 'госномер' in c][0]]
    dogovor = car[[c for c in df_cars.columns if 'договор' in c][0]]
    status = car[[c for c in df_cars.columns if 'статус' in c][0]]
    
    st.header(f"{model_name} (VIN/Госномер: {vin_name})")
    st.markdown(f"**Договор комиссии:** {dogovor} | **Текущий статус:** `{status}`")
    st.markdown("---")
    
    # БЛОК 1: Умная рекомендация по цене
    col_p_salon = [c for c in df_cars.columns if 'текущаяцена' in c or 'ценасалона' in c][0]
    col_p_market = [c for c in df_cars.columns if 'рыночнаяцена' in c][0]
    
    price_salon = int(car[col_p_salon])
    price_market = int(car[col_p_market])
    
    if price_salon > price_market:
        diff = price_salon - price_market
        pct = round((diff / price_market) * 100, 1)
        st.warning(f"⚠️ **Рекомендация по цене:** Ваша цена выше рыночной на {pct}% ({diff:,.0f} ₽). "
                   f"Рекомендуем снизить стоимость ближе к средней рыночной ({price_market:,.0f} ₽), чтобы поднять количество звонков и визитов.")
    else:
        st.success("✅ **Статус цены:** Ваша цена находится в оптимальном рыночном диапазоне. Автомобиль конкурентоспособен.")
        
    st.markdown("---")
    
    # БЛОК 2: Крупные цифры-метрики
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Текущая цена в салоне", value=f"{price_salon:,.0f} ₽")
    with col2:
        st.metric(label="Средняя цена на рынке", value=f"{price_market:,.0f} ₽")
    with col3:
        st.metric(label="Дней на комиссии", value=f"{days_on_sale} дней")
        
    st.markdown("---")
    
    # БЛОК 3: Аналитика и Воронка продаж
    col_graph, col_funnel = st.columns([2, 1])
    
    with col_graph:
        st.subheader("📈 Динамика активности по дням")
        if not car_activity.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=car_activity[col_date], y=car_activity[col_calls], name='Звонки', marker_color='#1f77b4'))
            fig.add_trace(go.Bar(x=car_activity[col_date], y=car_activity[col_visits], name='Визиты', marker_color='#2ca02c'))
            fig.add_trace(go.Bar(x=car_activity[col_date], y=car_activity[col_tests], name='Тест-драйвы', marker_color='#d62728'))
            fig.update_layout(barmode='group', margin=dict(l=20, r=20, t=20, b=20), height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Данные об активности по автомобилю пока не поступали.")
            
    with col_funnel:
        st.subheader("🎯 Сводка и Конверсии")
        total_views = car_activity[col_views].sum()
        total_calls = car_activity[col_calls].sum()
        total_visits = car_activity[col_visits].sum()
        total_tests = car_activity[col_tests].sum()
        
        # Считаем проценты конверсий
        conv_to_visit = (total_visits / total_calls * 100) if total_calls > 0 else 0
        conv_to_test = (total_tests / total_visits * 100) if total_visits > 0 else 0
        
        st.write(f"👀 Просмотров объявлений: **{total_views}**")
        st.write(f"📞 Всего звонков: **{total_calls}**")
        st.write(f"🚶 Всего визитов в салон: **{total_visits}**")
        st.write(f"🏎️ Проведено тест-драйвов: **{total_tests}**")
        
        st.markdown("---")
        st.metric(label="Конверсия: Звонки ➡️ Визиты", value=f"{conv_to_visit:.1f}%")
        st.metric(label="Конверсия: Визиты ➡️ Тест-драйв", value=f"{conv_test:.1f}%")

    st.markdown("---")
    
    # БЛОК 4: Ответственный менеджер
    col_manager = [c for c in df_cars.columns if 'фиоменеджер' in c or 'менеджер' in c][0]
    col_phone = [c for c in df_cars.columns if 'телефонменеджер' in c or 'телефон' in c][0]
    st.subheader("👤 Ваш ответственный менеджер")
    st.markdown(f"По любым вопросам вы можете связаться напрямую: **{car[col_manager]}** ({car[col_phone]})")

except Exception as e:
    st.error("Ошибка чтения данных. Пожалуйста, убедитесь, что в Google Таблице открыт доступ по ссылке, а в коде верно указан SHARE_ID.")
    st.write(e)
