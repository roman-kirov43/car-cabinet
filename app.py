import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Настройка внешнего вида страницы
st.set_page_config(page_title="Личный кабинет автосалона", layout="wide")

# Ключ твоей Google Таблицы
SHARE_ID = "1On_134S1gG5Cduk3mGRNipffeNXED3CzDU3EJe-1Dfc" 

@st.cache_data(ttl=10)  # Быстрое обновление данных
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHARE_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

try:
    # Загружаем твои листы из таблицы
    df_cars = load_data("cars")
    df_activity = load_data("activity_log")
    
    # Берем первый автомобиль
    car = df_cars.iloc[0]
    car_id = car['ID_авто']
    
    # Фильтруем активность по этой машине
    car_activity = df_activity[df_activity['ID_авто'] == car_id].copy()
    car_activity['Дата'] = car_activity['Дата'].astype(str)
    
    # Считаем дни в продаже
    try:
        days_on_sale = int(car['Дней в продаже'])
    except:
        days_on_sale = 23

    # --- ИНТЕРФЕЙС ---
    st.title("📊 Личный кабинет комиссионера")
    
    # Шапка (Марка, модель, VIN)
    st.header(f"{car['Марка и Модель']} (VIN/Госномер: {car['Госномер / VIN']})")
    st.markdown(f"**Договор комиссии:** {car['Номер договора комиссии']} | **Текущий статус:** `{car['Текущий статус']}`")
    st.markdown("---")
    
    # БЛОК 1: Умная рекомендация по цене
    price_salon = int(car['Текущая цена салона (₽)'])
    price_market = int(car['Рыночная цена (₽)'])
    
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
            # ТУТ ИСПРАВЛЕНО: убрали (шт) из названий столбцов
            fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Звонки'], name='Звонки', marker_color='#1f77b4'))
            fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Визиты'], name='Визиты', marker_color='#2ca02c'))
            fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Тест-драйвы'], name='Тест-драйвы', marker_color='#d62728'))
            fig.update_layout(barmode='group', margin=dict(l=20, r=20, t=20, b=20), height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Данные об активности по автомобилю пока не поступали.")
            
    with col_funnel:
        st.subheader("🎯 Сводка и Конверсии")
        # ТУТ ИСПРАВЛЕНО: убрали (шт) из названий столбцов
        total_views = car_activity['Просмотры'].sum()
        total_calls = car_activity['Звонки'].sum()
        total_visits = car_activity['Визиты'].sum()
        total_tests = car_activity['Тест-драйвы'].sum()
        
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
    
    # БЛОК 4: Личный менеджер
    st.subheader("👤 Ваш ответственный менеджер")
    st.markdown(f"По любым вопросам вы можете связаться напрямую: **{car['ФИО менеджера']}** ({car['Телефон менеджера']})")

except Exception as e:
    st.error("Ошибка чтения данных. Пожалуйста, убедитесь, что в Google Таблице открыт доступ по ссылке, а в коде верно указан SHARE_ID.")
    st.write(e)
