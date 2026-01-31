import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = 'cannabis_free.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabelas simplificadas
    c.execute('''CREATE TABLE IF NOT EXISTS associacoes
                 (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, estado TEXT, website TEXT, 
                  preco_min REAL, preco_max REAL, data_coleta TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produtos
                 (id INTEGER PRIMARY KEY, nome TEXT, marca TEXT, concentracao REAL, 
                  volume REAL, preco_brl REAL, aprovado_anvisa INTEGER)''')
    
    # Seeds 25 assocs [web:67][web:63]
    assocs = [
        ('ABRACAM', 'CE', 'abracam.org', 150, 300),
        ('Abrace Esperança', 'PB', 'abraceesperanca.org.br', 79, 250),  # [web:14]
        ('APEPI', 'RJ', 'apepi.org', 160, 300),  # [web:65]
        # +22: ABRACannabis(RJ), ACP(PI), ACuCa(SP), AGAPE(GO), etc. (adicione)
    ]
    c.executemany('INSERT OR IGNORE INTO associacoes (nome, estado, website, preco_min, preco_max) VALUES (?,?,?,?,?)', assocs)
    
    # 20+ ANVISA [web:74][web:30]
    prods = [
        ('Prati 200mg/ml', 'Prati-Donaduzzi', 200, 30, 2143, 1),
        ('Verdemed Spray', 'Verdemed', 50, 30, 671, 1),
        # +18
    ]
    c.executemany('INSERT OR IGNORE INTO produtos (nome, marca, concentracao, volume, preco_brl, aprovado_anvisa) VALUES (?,?,?,?,?,?)', prods)
    conn.commit()
    conn.close()

def get_assocs_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM associacoes", conn)
    conn.close()
    return df

def get_prods_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    df['custo_mg'] = df['preco_brl'] / (df['concentracao'] * df['volume'] / 1000)
    conn.close()
    return df
