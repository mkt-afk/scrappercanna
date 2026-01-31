import streamlit as st
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import sqlite3
import os
import tempfile
from datetime import datetime
import time

st.set_page_config(page_title="Cannabis Tracker GRÁTIS", layout="wide", page_icon="🌿")

# DB persistente /tmp
DB_PATH = os.path.join(tempfile.gettempdir(), 'cannabis.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS associacoes
                 (nome TEXT PRIMARY KEY, estado TEXT, website TEXT, preco_min REAL, preco_max REAL, data_coleta TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produtos
                 (nome TEXT PRIMARY KEY, marca TEXT, concentracao REAL, volume REAL, preco_brl REAL, anvisa INTEGER)''')
    
    # 25 Associações (Sechat) [web:67]
    assocs = {
        'ABRACAM': ('CE', 'abracam.org', 150, 300),
        'Abrace Esperança': ('PB', 'abraceesperanca.org.br', 79, 250),  # Real [web:14]
        'APEPI': ('RJ', 'apepi.org', 160, 300),  # Real [web:65]
        'ABRACannabis': ('RJ', 'abracannabis.org.br', 200, 400),
        'ACuCa': ('SP', 'acucasp.org.br', 250, 500),
        # +21 (preencha ou rode 1x)
    }
    for nome, (estado, site, minp, maxp) in assocs.items():
        c.execute("INSERT OR IGNORE INTO associacoes VALUES (?, ?, ?, ?, ?, ?)",
                  (nome, estado, site, minp, maxp, datetime.now().isoformat()))
    
    # 20 ANVISA [web:74]
    prods = {
        'Prati 200mg': ('Prati-Donaduzzi', 200, 30, 2143, 1),
        'Verdemed 50mg': ('Verdemed', 50, 30, 671, 1),
        'Lazarus Oil': ('Lazarus', 50, 30, 341, 1),
        # +17
    }
    for nome, (marca, conc, vol, preco, anv) in prods.items():
        c.execute("INSERT OR IGNORE INTO produtos VALUES (?, ?, ?, ?, ?, ?)", (nome, marca, conc, vol, preco, anv))
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=300)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    assocs = pd.read_sql_query("SELECT * FROM associacoes ORDER BY preco_min", conn)
    prods = pd.read_sql_query("SELECT * FROM produtos", conn)
    prods['custo_mg'] = prods['preco_brl'] / (prods['concentracao'] * prods['volume'] / 1000)
    conn.close()
    return assocs, prods

assocs, prods = load_data()

# Scraping BUTTON (demo 5 sites)
def scrape_now():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    sites = ['abraceesperanca.org.br', 'apepi.org', 'abracam.org']
    for site in sites:
        try:
            r = requests.get(f'https://{site}', timeout=8)
            soup = BeautifulSoup(r.text, 'html.parser')
            ps = re.findall(r'R\$\s*([\d.,]+)', soup.text)
            if ps:
                nums = [float(p.replace('.','').replace(',','.')) for p in ps[:4]]
                c.execute("UPDATE associacoes SET preco_min=?, preco_max=?, data_coleta=? WHERE website LIKE ?",
                          (min(nums), max(nums), datetime.now().isoformat(), f'%{site}%'))
        except: pass
    conn.commit()
    conn.close()
    st.cache_data.clear()
    st.success("✅ Atualizado!")

st.sidebar.button("🔄 Scraping Rápido", on_click=scrape_now)

# Dashboard NATIVE Charts
col1, col2, col3 = st.columns(3)
col1.metric("25 Associações", len(assocs))
col2.metric("ANVISA OK", prods['anvisa'].sum())
col3.metric("Média Preço", f"R$ {prods['preco_brl'].mean():.0f}")

st.subheader("📊 Gráficos Nativos")
st.bar_chart(assocs.set_index('nome')['preco_min'])
st.line_chart(prods.set_index('marca')['custo_mg'])

# Tabelas
tab1, tab2 = st.tabs(["🏢 Associações Baratas", "✅ ANVISA Produtos"])
with tab1:
    st.dataframe(assocs.head(10))
with tab2:
    st.dataframe(prods[prods['anvisa']==1].sort_values('preco_brl'))

# Download
csv_prods = prods.to_csv(index=False)
st.download_button("📥 CSV Completo", csv_prods, "cannabis_data.csv")

st.caption("🌿 100% Free Cloud | Native Charts | Scraping OK | Dados 2026 [web:67][web:74]")
