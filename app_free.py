import streamlit as st
from models_free import init_db, get_assocs_df, get_prods_df
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import re
from bs4 import BeautifulSoup
import atexit
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Cannabis Tracker FREE", layout="wide")
init_db()  # DB auto-init

assocs_df = get_assocs_df()
prods_df = get_prods_df()

def scrape_task():
    """Scraping simples (requests, 5 sites demo - expanda para 25)"""
    sites = ['abraceesperanca.org.br', 'apepi.org']  # +23
    import sqlite3
    conn = sqlite3.connect('cannabis_free.db')
    c = conn.cursor()
    for site in sites:
        try:
            resp = requests.get(f'https://{site}', timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            precos = re.findall(r'R\$\s*([\d.,]+)', soup.text)
            if precos:
                min_p = min(float(p.replace('.', '').replace(',', '.')) for p in precos[:3])
                max_p = max(float(p.replace('.', '').replace(',', '.')) for p in precos[:3])
                c.execute("UPDATE associacoes SET preco_min=?, preco_max=?, data_coleta=? WHERE website LIKE ?",
                          (min_p, max_p, pd.Timestamp.now().isoformat(), f'%{site}%'))
        except: pass
    conn.commit()
    conn.close()
    st.cache_data.clear()  # Refresh DF

# Scheduler diário (roda em background)
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_task, trigger="interval", hours=24)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# UI igual anterior (dashboard, tabs, etc.)
st.sidebar.button("🔄 Scraping Manual", on_click=scrape_task)
# ... Cole o código das tabs de app.py anterior, usando assocs_df, prods_df
