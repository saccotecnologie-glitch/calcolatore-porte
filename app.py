import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import csv
import pandas as pd
import random
import string
import smtplib
from email.message import EmailMessage
from supabase import create_client
from pathlib import Path
from datetime import datetime

# --- CONFIGURAZIONI INIZIALI ---
st.set_page_config(page_title="Configuratore Porte Automatiche SA-TEC", layout="wide")

AZIENDA = "SA-TEC S.R.L.s"
PREVENTIVI_CSV = "preventivi_satec.csv"

# --- FUNZIONI DI SUPPORTO ---
def euro(v):
    return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def html_export_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", ""))
    campi = [("Codice", "codice_preventivo"), ("Data", "data_ora"), ("Cliente", "cliente_nome"), 
             ("Totale", "totale_iva"), ("Stato", "stato")]
    
    righe = "".join([f"<tr><th>{l}</th><td>{p.get(k, '')}</td></tr>" for l, k in campi])
    
    return f"""
    <html>
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: Arial; margin: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ width: 200px; background: #eef6ff; color: #06499b; padding: 10px; text-align: left; border: 1px solid #bdd4ef; }}
        td {{ padding: 10px; border: 1px solid #bdd4ef; }}
    </style>
    </head>
    <body>
        <h2>Dettaglio Preventivo: {codice}</h2>
        <table>{righe}</table>
    </body>
    </html>
    """

# --- LOGICA SUPABASE ---
def supabase_client():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

# --- STRUTTURA PRINCIPALE (Mantenuta) ---
def main():
    st.sidebar.title("SA-TEC Management")
    menu = st.sidebar.radio("Sezione", ["Configuratore", "Admin Preventivi", "Gestione Utenti"])

    if menu == "Configuratore":
        st.header("Configuratore Porte Automatiche")
        # Qui va la tua logica originale di selezione prodotti e calcolo
        pass

    elif menu == "Admin Preventivi":
        st.header("Gestione Preventivi")
        sb = supabase_client()
        if sb:
            res = sb.table("preventivi").select("*").execute()
            df = pd.DataFrame(res.data)
            st.dataframe(df)
            
            # Esempio di utilizzo della funzione di export
            if not df.empty and st.button("Esporta primo preventivo in HTML"):
                html = html_export_preventivo_admin(df.iloc[0].to_dict())
                st.components.v1.html(html, height=400)

    elif menu == "Gestione Utenti":
        st.header("Database Utenti")
        # Logica originale di gestione CSV/Supabase
        pass

if __name__ == "__main__":
    main()
