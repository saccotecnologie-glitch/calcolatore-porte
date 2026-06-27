import streamlit as st
import pandas as pd
import numpy as np
import csv
from pathlib import Path
from datetime import datetime
from supabase import create_client
import base64
import random
import string
import smtplib
from email.message import EmailMessage

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Configuratore SA-TEC PRO", layout="wide")

# Costanti
AZIENDA = "SA-TEC S.R.L.s"
PREVENTIVI_CSV = "preventivi_satec.csv"

# --- FUNZIONI SUPABASE E UTILS ---
def supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

def euro(v):
    return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- FUNZIONE DASHBOARD ADMIN ---
def visualizza_dashboard_admin():
    st.header("📊 Dashboard Amministrativa")
    sb = supabase_client()
    if not sb:
        st.error("Connessione DB fallita")
        return

    # Recupero dati
    res = sb.table("preventivi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    if not df.empty:
        df['totale'] = pd.to_numeric(df['totale'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Fatturato per Stato")
            fig = df.groupby('stato')['totale'].sum()
            st.bar_chart(fig)
            
        with col2:
            st.subheader("Elenco Preventivi Recenti")
            st.dataframe(df.tail(10))
    else:
        st.info("Nessun preventivo trovato.")

# --- FUNZIONE EXPORT HTML ---
def html_export_preventivo_admin(p):
    codice = p.get("codice_preventivo", "N/A")
    # Mappatura campi sicura
    html = f"""
    <html>
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #06499b; color: white; padding: 10px; text-align: left; }}
        td {{ border: 1px solid #ddd; padding: 10px; }}
    </style>
    </head>
    <body>
        <h1>Preventivo {codice}</h1>
        <table>
            <tr><th>Cliente</th><td>{p.get('cliente_id', '')}</td></tr>
            <tr><th>Totale</th><td>{euro(p.get('totale', 0))}</td></tr>
            <tr><th>Stato</th><td>{p.get('stato', '')}</td></tr>
        </table>
    </body>
    </html>
    """
    return html

# --- INTERFACCIA PRINCIPALE ---
def main():
    st.sidebar.title(f"Menu {AZIENDA}")
    menu = st.sidebar.radio("Navigazione", ["Configuratore", "Dashboard Admin", "Gestione Utenti"])

    if menu == "Configuratore":
        st.title("⚙️ Configuratore Porte")
        # Logica configurazione ...
        if st.button("Genera Preventivo"):
            st.success("Preventivo creato con successo!")

    elif menu == "Dashboard Admin":
        visualizza_dashboard_admin()

    elif menu == "Gestione Utenti":
        st.title("👥 Gestione Utenti")
        # Logica CRUD utenti ...

if __name__ == "__main__":
    main()
