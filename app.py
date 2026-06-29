import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(
    page_title="Личный кабинет автосалона", 
    page_icon="🚗",
    layout="wide"
)

# --- БЛОК УЛЬТРАСОВРЕМЕННЫХ СТИЛЕЙ (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&display=swap');
    
    html, body, [data-testid="stWidgetLabel"], p, div {
        font-family: 'Ubuntu', sans-serif !important;
    }
    
    /* Делаем карточки метрик премиальными и футуристичными */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.03), rgba(120, 120, 120, 0.01));
        border: 1px solid rgba(255, 127, 14, 0.25); /* Тонкая неоновая оранжевая рамка */
        padding: 22px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    /* Эффект легкого парения при наведении на карточку цены или дней */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 127, 14, 0.6);
        box-shadow: 0 15px 35px rgba(255, 127, 14, 0.1);
    }
    
    /* Яркое выделение цифровых значений */
    div[data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #ff7f0e !important; /* Насыщенный оранжевый accent */
    }
    
    /* Современные скругления для блоков предупреждений и рекомендаций */
    .stAlert {
        border-radius: 16px !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.04);
    }
    
    /* Красивые отступы для заголовков */
    h1, h2, h3 {
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Ключ твоей Google Таблицы
SHARE_ID = "1On_134S1gG5Cduk3mGRNipffenXED3CzDU3EJe-1Dfc" 

@st.cache_data(ttl=5)  # Быстрое обновление данных
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHARE_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip() # Убираем пробелы по краям заголовков
    return df

try:
    # Загружаем листы таблицы напрямую
    df_cars = load_data("cars")
    df_activity = load_data("activity_log")
    df_analogs = load_data("market_analogs")
    
    # Пытаемся загрузить историю цен безопасно
    try:
        df_price_hist = load_data("price_history")
    except:
        df_price_hist = pd.DataFrame()
    
    # --- ЭКРАН АВТОРИЗАЦИИ ---
    st.title("🔐 Вход в личный кабинет комиссионера")
    
    # Поле для ввода последних 5 символов VIN
    user_vin_input = st.text_input("Введите последние 5 символов VIN-кода вашего автомобиля:", "", max_chars=5).strip()
    
    if user_vin_input:
        # Функция для обрезки VIN до последних 5 символов и приведения к нижнему регистру
        def get_last_5(vin_value):
            clean_vin = str(vin_value).strip().lower()
            return clean_vin[-5:] if len(clean_vin) >= 5 else clean_vin

        # Ищем машину, у которой последние 5 символов VIN совпадают с вводом пользователя
        user_cars = df_cars[df_cars['Госномер / VIN'].apply(get_last_5) == user_vin_input.lower()]
        
        if not user_cars.empty:
            st.success("Авторизация успешна!")
            st.markdown("---")
            
            # Если у одного владельца нашлось несколько машин
            if len(user_cars) > 1:
                car_options = user_cars['Марка и Модель'].tolist()
                selected_car_name = st.selectbox("Выберите нужный автомобиль для просмотра:", car_options)
                car = user_cars[user_cars['Марка и Модель'] == selected_car_name].iloc[0]
            else:
                car = user_cars.iloc[0]
                
            car_id = car['ID_авто']
            
            # Фильтруем данные по ID этого автомобиля
            car_activity = df_activity[df_activity['ID_авто'] == car_id].copy()
            car_activity['Дата'] = car_activity['Дата'].astype(str)
            
            car_analogs = df_analogs[df_analogs['ID_авто'] == car_id].copy()
            car_analogs = car_analogs.dropna(subset=['Ссылка', 'Цена'])
            
            # Супер-надежная привязка истории цен: берем только первые 3 колонки, сколько бы их ни было
            car_price_history = pd.DataFrame()
            if not df_price_hist.empty and len(df_price_hist.columns) >= 3:
                df_price_hist_clean = df_price_hist.copy()
                df_price_hist_clean = df_price_hist_clean.iloc[:, :3]
                df_price_hist_clean.columns = ['id_auto', 'date_val', 'price_val']
                
                # Фильтруем по ID авто
                car_price_history = df_price_hist_clean[df_price_hist_clean['id_auto'].astype(str) == str(car_id)].copy()
                car_price_history = car_price_history.dropna(subset=['date_val', 'price_val'])
            
            try:
                days_on_sale = int(car['Дней в продаже'])
            except:
                days_on_sale = 23

            # --- ИНТЕРФЕЙС КАБИНЕТА ---
            st.header(f"🚗 {car['Марка и Модель']}")
            st.caption(f"📍 **VIN/Госномер:** {car['Госномер / VIN']} | **Договор комиссии:** {car['Номер договора комиссии']} | **Текущий статус:** `{car['Текущий статус']}`")
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
            
            # БЛОК 2: Крупные цифры-метрики (Новые интерактивные карточки)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="💰 Текущая цена в салоне", value=f"{price_salon:,.0f} ₽")
            with col2:
                st.metric(label="📊 Средняя цена на рынке", value=f"{price_market:,.0f} ₽")
            with col3:
                st.metric(label="📅 Дней на комиссии", value=f"{days_on_sale} дней")
                
            st.markdown("---")
            
            # БЛОК 3: Аналитика и Воронка продаж
            col_graph, col_funnel = st.columns([2, 1])
            
            with col_graph:
                st.subheader("📈 Динамика активности по дням")
                if not car_activity.empty:
                    fig = go.Figure()
                    
                    # Проверяем наличие новой колонки "Сообщения"
                    if 'Сообщения' in car_activity.columns:
                        fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Сообщения'], name='💬 Сообщения', marker_color='#9467bd'))
                        
                    fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Звонки'], name='📞 Звонки', marker_color='#2ca02c'))
                    fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Визиты'], name='🚶 Визиты', marker_color='#1f77b4'))
                    fig.add_trace(go.Bar(x=car_activity['Дата'], y=car_activity['Тест-драйвы'], name='🏎️ Тест-драйвы', marker_color='#ff7f0e'))
                    
                    fig.update_layout(
                        barmode='group', 
                        margin=dict(l=10, r=10, t=10, b=10), 
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Данные об активности по автомобилю пока не поступали.")
                    
            with col_funnel:
                st.subheader("🎯 Сводка и Конверсии")
                total_views = car_activity['Просмотны' if 'Просмотны' in car_activity.columns else 'Просмотры'].sum()
                total_calls = car_activity['Звонки'].sum()
                total_visits = car_activity['Визиты'].sum()
                total_tests = car_activity['Тест-драйвы'].sum()
                
                # Подсчет общего количества сообщений
                total_chats = car_activity['Сообщения'].sum() if 'Сообщения' in car_activity.columns else 0
                
                # Считаем общую конверсию в визит от всех первичных контактов (Звонки + Сообщения)
                total_leads = total_calls + total_chats
                conv_to_visit = (total_visits / total_leads * 100) if total_leads > 0 else 0
                conv_to_test = (total_tests / total_visits * 100) if total_visits > 0 else 0
                
                st.markdown(f"👀 Просмотров объявлений: **{total_views}**")
                st.markdown(f"💬 Всего сообщений (чаты): **{total_chats}**")
                st.markdown(f"📞 Всего звонков: **{total_calls}**")
                st.markdown(f"🚶 Всего визитов в салон: **{total_visits}**")
                st.markdown(f"🏎️ Проведено тест-драйвов: **{total_tests}**")
                
                st.markdown("---")
                st.metric(label="Конверсия: Контакты ➡️ Визиты", value=f"{conv_to_visit:.1f}%")
                st.metric(label="Конверсия: Визиты ➡️ Тест-драйв", value=f"{conv_to_test:.1f}%")

            st.markdown("---")
            
            # БЛОК 4: История изменения цены и Аналоги с рынка
            col_hist_graph, col_market_table = st.columns([1, 1])
            
            with col_hist_graph:
                st.subheader("📉 История изменения цены")
                if not car_price_history.empty:
                    car_price_history['date_dt'] = pd.to_datetime(car_price_history['date_val'], dayfirst=True, errors='coerce')
                    car_price_history = car_price_history.sort_values('date_dt')
                    
                    fig_price = go.Figure()
                    fig_price.add_trace(go.Scatter(
                        x=car_price_history['date_val'], 
                        y=car_price_history['price_val'], 
                        mode='lines+markers',
                        line=dict(shape='spline', color='#ff7f0e', width=3),
                        marker=dict(size=8),
                        name='Цена автомобиля'
                    ))
                    fig_price.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10), 
                        height=300,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(tickformat=",.0f")
                    )
                    st.plotly_chart(fig_price, use_container_width=True)
                else:
                    st.info("Цена на автомобиль не корректировалась с момента постановки на комиссию.")
            
            with col_market_table:
                st.subheader("📊 Текущие аналоги на рынке")
                if not car_analogs.empty:
                    display_df = pd.DataFrame()
                    display_df['Цена аналога (₽)'] = car_analogs['Цена'].astype(int)
                    display_df['Ссылка на объявление'] = car_analogs['Ссылка'].apply(
                        lambda x: str(x).strip() if str(x).startswith('http') else 'https://' + str(x).strip()
                    )
                    
                    st.dataframe(
                        display_df,
                        column_config={
                            "Цена аналога (₽)": st.column_config.NumberColumn(format="%d ₽"),
                            "Ссылка на объявление": st.column_config.LinkColumn("Открыть объявление")
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=300
                    )
                else:
                    st.info("Данные по актуальным аналогам на рынке сейчас обновляются.")
                
            st.markdown("---")
            
            # БЛОК 5: Ответственный менеджер
            st.subheader("👤 Ваш ответственный менеджер")
            st.markdown(f"По любым вопросам вы можете связаться напрямую: **{car['ФИО менеджера']}** ({car['Телефон менеджера']})")
        else:
            st.error("Автомобиль с такими цифрами VIN не найден. Пожалуйста, проверьте правильность ввода или обратитесь к вашему менеджеру.")
    else:
        # Загружаем твой собственный баннер «Гусар» из репозитория GitHub
        try:
            st.image("banner.jpg", use_container_width=True)
        except:
            st.image("https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
            
        st.info("💡 Пожалуйста, введите последние 5 символов VIN-кода вашего автомобиля выше, чтобы войти в личный кабинет.")

except Exception as e:
    st.error("Ошибка чтения данных. Пожалуйста, убедитесь, что в Google Таблице открыт доступ по ссылке, а в коде верно указан SHARE_ID.")
    st.write(e)
