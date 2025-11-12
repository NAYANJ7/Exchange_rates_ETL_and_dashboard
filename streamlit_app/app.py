import streamlit as st
import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import plotly.graph_objects as go

# ---------------------- Configuration ----------------------
STREAMLIT_USERNAME = os.getenv("STREAMLIT_USERNAME", "streamlit_user")
STREAMLIT_PASSWORD = os.getenv("STREAMLIT_PASSWORD", "streamlit123")
EXCHANGE_DB_URL = os.getenv("EXCHANGE_DB_URL")
AIRFLOW_DB_URL = os.getenv("AIRFLOW_DB_URL", EXCHANGE_DB_URL)
FAV_DB_PATH = os.getenv("FAV_DB_PATH", "./favorites.db")

# Minimal currency metadata (ensure USD present)
CURRENCY_INFO = {
    'USD': {'name': 'United States Dollar', 'flag_emoji': '🇺🇸', 'symbol': '$', 'country': 'United States', 'cc': 'us'},
    'EUR': {'name': 'Euro', 'flag_emoji': '🇪🇺', 'symbol': '€', 'country': 'European Union', 'cc': 'eu'},
    'GBP': {'name': 'British Pound', 'flag_emoji': '🇬🇧', 'symbol': '£', 'country': 'United Kingdom', 'cc': 'gb'},
    'JPY': {'name': 'Japanese Yen', 'flag_emoji': '🇯🇵', 'symbol': '¥', 'country': 'Japan', 'cc': 'jp'},
    'INR': {'name': 'Indian Rupee', 'flag_emoji': '🇮🇳', 'symbol': '₹', 'country': 'India', 'cc': 'in'},
}

# Helper: build flag image URL using FlagCDN SVGs for crisp scaling
def flag_svg_url(alpha2):
    if not alpha2:
        return None
    return f"https://flagcdn.com/{alpha2.lower()}.svg"

# ---------------------- Favorites persistence (SQLite) ----------------------

def init_fav_db(path=FAV_DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        currency TEXT PRIMARY KEY,
        fav INTEGER NOT NULL
    )
    """)
    conn.commit()
    return conn

def set_favorite_db(conn, currency, fav=True):
    c = conn.cursor()
    if fav:
        c.execute("INSERT OR REPLACE INTO favorites(currency, fav) VALUES (?, 1)", (currency,))
    else:
        c.execute("DELETE FROM favorites WHERE currency = ?", (currency,))
    conn.commit()

def get_favorites_db(conn):
    c = conn.cursor()
    c.execute("SELECT currency FROM favorites WHERE fav = 1")
    rows = c.fetchall()
    return {r[0]: True for r in rows}

# Initialize DB connection once
_fav_conn = None
try:
    _fav_conn = init_fav_db()
except Exception as e:
    # If DB init fails, we'll fall back to session-only favorites
    _fav_conn = None

# ---------------------- Theming & CSS (Simplified dark-only, no accents) ----------------------
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
.stApp { background: linear-gradient(180deg, #051426 0%, #061226 100%); color: #e6eef8; }
.currency-card { padding: 14px; border-radius: 10px; background-color: #06182a; box-shadow: 0 6px 18px rgba(0,0,0,0.6); margin: 10px 0; }
.currency-flag { vertical-align: middle; border-radius: 3px; margin-right: 8px; height: 20px; width: 30px; object-fit: cover; }
.currency-title { font-weight: 700; font-size:15px; color:#e6eef8; }
.currency-sub { color: #98a9c7; font-size:12px; }
.big-amount { font-size:22px; font-weight:700; color:#e6eef8 }
.muted { color: #98a9c7 }
.small { font-size:12px }
.info-box { padding: 12px; border-radius: 8px; background-color: rgba(255,255,255,0.02); border-left: 4px solid rgba(255,255,255,0.03); }
</style>
"""

# Authentication (same)
def check_password():
    def password_entered():
        if (
            st.session_state.get("username") == STREAMLIT_USERNAME
            and st.session_state.get("password") == STREAMLIT_PASSWORD
        ):
            st.session_state["password_correct"] = True
            st.session_state.pop("password", None)
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 USD Exchange Rate Dashboard")
        st.markdown("### Please login to continue")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Username", key="username", placeholder="Enter username")
            st.text_input("Password", type="password", key="password", placeholder="Enter password")
            st.button("Login", on_click=password_entered, use_container_width=True)
        st.info("💡 Default credentials: streamlit_user / streamlit123")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 USD Exchange Rate Dashboard")
        st.markdown("### Please login to continue")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Username", key="username", placeholder="Enter username")
            st.text_input("Password", type="password", key="password", placeholder="Enter password")
            st.button("Login", on_click=password_entered, use_container_width=True)
            st.error("😕 Username or password incorrect")
        return False
    else:
        return True

# ---------------------- Data helpers ----------------------

def get_exchange_data(engine):
    try:
        with engine.connect() as conn:
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result]
            if not tables:
                return None, None
            selected_table = tables[0]
            for table in tables:
                if any(keyword in table.lower() for keyword in ['exchange', 'rate', 'currency']):
                    selected_table = table
                    break
            df = pd.read_sql(text(f"SELECT * FROM {selected_table}"), conn)
            return df, selected_table
    except Exception as e:
        # Return exception info to caller
        raise RuntimeError(f"Failed to fetch exchange data: {e}")

# ---------------------- UI Sections ----------------------

def show_currency_converter(exchange_engine):
    st.title("💰 Currency Converter")
    st.markdown("""
    <div class='info-box'>
    <b>ℹ️ How it works:</b> Enter an amount in USD and instantly see its value in other currencies.
    Use the star to favorite currencies and click "Show history" to view an inline chart.
    </div>
    """, unsafe_allow_html=True)

    try:
        df, table_name = get_exchange_data(exchange_engine)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Make sure your DAG has run successfully and created the necessary tables.")
        return

    if df is None or df.empty:
        st.warning("⚠️ No exchange rate data found. Please run your DAG first.")
        return

    # Detect columns
    currency_col = None
    rate_col = None
    date_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'currency' in col_lower or 'code' in col_lower:
            currency_col = col
        if 'rate' in col_lower or 'price' in col_lower or 'value' in col_lower:
            rate_col = col
        if 'date' in col_lower or 'time' in col_lower:
            date_col = col
    if not currency_col or not rate_col:
        st.error("❌ Could not detect currency and rate columns in the database.")
        return

    latest_rates = df.groupby(currency_col)[rate_col].last().to_dict()
    available_currencies = list(latest_rates.keys())
    if not available_currencies:
        st.warning("⚠️ No currencies available in the dataset.")
        return

    # Load favorites from DB into session_state once
    if 'favorites' not in st.session_state:
        try:
            favs = get_favorites_db(_fav_conn) if _fav_conn else {}
        except Exception:
            favs = {}
        st.session_state['favorites'] = favs

    # Search & favorites UI
    q = st.text_input("🔎 Search currencies", value="")
    visible = [c for c in available_currencies if q.upper() in c or q.lower() in (CURRENCY_INFO.get(c, {}).get('name','').lower())]
    if not visible:
        visible = available_currencies

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 💵 Convert From USD")
        amount = st.number_input("Enter amount in USD ($)", min_value=0.01, value=100.0, step=10.0, format="%.2f")
        st.markdown(f"### 🔄 Amount: **${amount:,.2f}**")
    with col2:
        st.markdown("### 🌍 Currencies")
        st.write("Click the ⭐ to favorite a currency. Favorites show at top.")

    # Order favorites first
    fav_list = [c for c, v in st.session_state['favorites'].items() if v]
    ordered = fav_list + [c for c in visible if c not in fav_list]

    # Display cards and interactive buttons
    for idx, currency in enumerate(ordered):
        rate = latest_rates.get(currency, 0)
        converted_amount = amount * rate
        info = CURRENCY_INFO.get(currency, {'name': currency, 'flag_emoji': '🏳️', 'symbol': '', 'country': 'Unknown', 'cc': None})
        flag_img = flag_svg_url(info.get('cc'))

        st.markdown(f"""
        <div class='currency-card'>
            <div style='display:flex; align-items:center; gap:12px;'>
                {f"<img src='{flag_img}' class='currency-flag' alt='{currency} flag' width='36'/>" if flag_img else info.get('flag_emoji')}
                <div>
                    <div class='currency-title'>{currency} &nbsp;<span class='small muted'>{info['name']}</span></div>
                    <div class='currency-sub'>{info['country']}</div>
                </div>
            </div>
            <div style='margin-top:12px; display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <div class='big-amount'>{info['symbol']}{converted_amount:,.2f}</div>
                    <div class='muted small'>Rate: {rate:.4f} &nbsp;•&nbsp; 1 USD = {info['symbol']}{rate:.2f}</div>
                </div>
                <div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Buttons below each card (favorites and show history)
        cols = st.columns([0.1, 0.5, 0.4])
        with cols[0]:
            fav_key = f"fav_{currency}"
            current = st.session_state['favorites'].get(currency, False)
            if st.button('⭐' if current else '☆', key=f'btn_fav_{currency}'):
                # Toggle in DB and session
                new_val = not current
                st.session_state['favorites'][currency] = new_val
                try:
                    set_favorite_db(_fav_conn, currency, fav=new_val)
                except Exception:
                    pass
                st.experimental_rerun()
        with cols[1]:
            if date_col:
                if st.button('Show history', key=f'btn_hist_{currency}'):
                    st.session_state['show_history'] = currency
                    st.experimental_rerun()
            else:
                st.write('')
        with cols[2]:
            st.write('')

    # Show inline history if requested
    if st.session_state.get('show_history'):
        show_currency = st.session_state.get('show_history')
        try:
            if show_currency in available_currencies and date_col:
                st.markdown('---')
                st.markdown(f"### 📈 Historical trend for {show_currency}")
                df[date_col] = pd.to_datetime(df[date_col])
                hist = df[df[currency_col] == show_currency].sort_values(date_col)
                if hist.empty:
                    st.info('No historical data for the selected currency.')
                else:
                    fig = go.Figure(go.Scatter(x=hist[date_col], y=hist[rate_col], mode='lines+markers', name=show_currency))
                    fig.update_layout(template='plotly_dark', height=300, margin=dict(l=20,r=20,t=40,b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    if st.button('Close history'):
                        st.session_state['show_history'] = None
                        st.experimental_rerun()
            else:
                st.info('No historical data for selected currency or date column missing.')
        except Exception as e:
            st.error(f"Could not render history: {e}")

    st.markdown('---')
    with st.expander('📊 Download visible currencies as CSV'):
        export = []
        for c in ordered:
            rate = latest_rates.get(c, 0)
            info = CURRENCY_INFO.get(c, {'name': c})
            export.append({'Currency': c, 'Name': info.get('name'), 'Rate': rate})
        df_export = pd.DataFrame(export)
        st.dataframe(df_export, use_container_width=True)
        st.download_button('📥 Download CSV', df_export.to_csv(index=False), file_name=f"currencies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")


def show_rate_comparison(exchange_engine, flag_format='svg'):
    """Show currency rate comparison with robust error handling and improved defaults"""
    st.title("📈 Exchange Rate Comparison")
    st.markdown("""
    <div class='info-box'>
    <b>ℹ️ Understanding Exchange Rates:</b> The exchange rate shows how much of a foreign currency you get for 1 USD.
    Use the controls to select currencies. Charts will render only when data is present.
    </div>
    """, unsafe_allow_html=True)

    try:
        df, table_name = get_exchange_data(exchange_engine)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Make sure your DAG has run successfully and created the necessary tables.")
        return

    if df is None or df.empty:
        st.warning("⚠️ No exchange rate data found. Please run your DAG first.")
        return

    # Detect columns
    currency_col = None
    rate_col = None
    date_col = None
    for col in df.columns:
        col_lower = col.lower()
        if 'currency' in col_lower or 'code' in col_lower:
            currency_col = col
        if 'rate' in col_lower or 'price' in col_lower or 'value' in col_lower:
            rate_col = col
        if 'date' in col_lower or 'time' in col_lower:
            date_col = col
    if not currency_col or not rate_col:
        st.error("❌ Could not detect currency and rate columns.")
        return

    latest_df = df.groupby(currency_col)[rate_col].last().reset_index()
    if latest_df.empty:
        st.warning("⚠️ No latest rate data available.")
        return

    latest_df = latest_df.sort_values(rate_col, ascending=False)
    available_currencies = latest_df[currency_col].tolist()
    if not available_currencies:
        st.warning("⚠️ No currencies found in data.")
        return

    st.markdown('---')
    default_selection = available_currencies[:6]
    selected_currencies = st.multiselect('Choose currencies to compare', options=available_currencies, default=default_selection)

    if not selected_currencies or len(selected_currencies) < 2:
        st.info('Select at least 2 currencies to compare (defaults selected).')
        return

    filtered_df = latest_df[latest_df[currency_col].isin(selected_currencies)].reset_index(drop=True)
    if filtered_df.empty:
        st.error('No data for selected currencies')
        return

    # Build chart safely
    try:
        fig = go.Figure()
        rates = filtered_df[rate_col].astype(float).tolist()
        max_rate = max(rates)
        min_rate = min(rates)
        for idx, row in filtered_df.iterrows():
            c = row[currency_col]
            r = float(row[rate_col])
            info = CURRENCY_INFO.get(c, {'flag_emoji': '🏳️'})
            color = '#ef4444' if r == max_rate else ('#10b981' if r == min_rate else '#60a5fa')
            fig.add_trace(go.Bar(x=[c], y=[r], name=c, hovertemplate=f"{info.get('flag_emoji')} {c}<br>Rate: {r:.4f}<extra></extra>", marker_color=color))
        fig.update_layout(template='plotly_dark', title='Exchange Rates per 1 USD', yaxis_title='Rate', height=480)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f'Could not render comparison chart: {e}')

    with st.expander('📋 Comparison Table'):
        comp = []
        for _,row in filtered_df.iterrows():
            c = row[currency_col]
            r = row[rate_col]
            info = CURRENCY_INFO.get(c, {'name':c,'flag_emoji':'🏳️'})
            comp.append({'Currency': f"{info.get('flag_emoji')} {c}", 'Rate': f"{r:.4f}", '$100 USD': f"{r*100:,.2f}"})
        st.dataframe(pd.DataFrame(comp), use_container_width=True)


def show_dag_logs(airflow_engine):
    st.title('📋 DAG Run Logs')
    st.markdown("""
    <div class='info-box'>
    <b>ℹ️ What are DAGs?</b> DAGs (Directed Acyclic Graphs) are workflows that fetch and process exchange rate data.
    </div>
    """, unsafe_allow_html=True)
    try:
        with airflow_engine.connect() as conn:
            df = pd.read_sql(text('''
                SELECT 
                    dag_id,
                    execution_date,
                    state,
                    run_type,
                    start_date,
                    end_date,
                    EXTRACT(EPOCH FROM (end_date - start_date)) as duration_seconds
                FROM dag_run
                ORDER BY execution_date DESC
                LIMIT 100
            '''), conn)
            if df.empty:
                st.info('📭 No DAG runs found. Trigger your DAG from Airflow UI at http://localhost:8080')
                return
            success_count = len(df[df['state']=='success'])
            failed_count = len(df[df['state']=='failed'])
            running_count = len(df[df['state']=='running'])
            col1, col2, col3, col4 = st.columns(4)
            col1.metric('Total Runs', len(df))
            col2.metric('✅ Successful', success_count)
            col3.metric('❌ Failed', failed_count)
            col4.metric('⏳ Running', running_count)
            st.markdown('---')
            st.dataframe(df.head(20), use_container_width=True)
    except Exception as e:
        st.error(f'Error loading DAG logs: {str(e)}')

# ---------------------- App Entry ----------------------

def main():
    st.set_page_config(page_title='USD Exchange Rate Dashboard', page_icon='💱', layout='wide')
    st.markdown(DARK_CSS, unsafe_allow_html=True)

    if not check_password():
        return

    # Sidebar: simplified, dark-only (no theme or color pickers)
    with st.sidebar:
        st.image('https://img.icons8.com/fluency/96/000000/us-dollar-circled.png', width=64)
        st.title('💱 Currency Dashboard')
        st.markdown(f"**👤 User:** {st.session_state.get('username','Unknown')}")
        if st.button('🚪 Logout', use_container_width=True):
            st.session_state['password_correct'] = False
            st.rerun()
        st.markdown('---')
        st.markdown('### 📊 Navigation')
        page = st.radio('Select Page', ['💰 Currency Converter','📈 Rate Comparison','📋 DAG Logs'], index=0)
        st.markdown('---')
        st.write('Tip: Use ⭐ to favorite currencies. Favorites persist across restarts.')

    try:
        exchange_engine = create_engine(EXCHANGE_DB_URL) if EXCHANGE_DB_URL else None
        airflow_engine = create_engine(AIRFLOW_DB_URL) if AIRFLOW_DB_URL else None

        if page == '💰 Currency Converter':
            if exchange_engine:
                show_currency_converter(exchange_engine)
            else:
                st.error('Exchange DB URL not configured. Set EXCHANGE_DB_URL environment variable.')
        elif page == '📈 Rate Comparison':
            if exchange_engine:
                show_rate_comparison(exchange_engine)
            else:
                st.error('Exchange DB URL not configured. Set EXCHANGE_DB_URL environment variable.')
        elif page == '📋 DAG Logs':
            if airflow_engine:
                show_dag_logs(airflow_engine)
            else:
                st.error('Airflow DB URL not configured. Set AIRFLOW_DB_URL environment variable.')

    except Exception as e:
        st.error(f'❌ Unexpected error: {str(e)}')
        st.info('💡 Make sure your DAG has run successfully and created the necessary tables.')

if __name__ == '__main__':
    main()
