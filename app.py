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
from datetime import datetime, date

# --- CONFIGURAZIONI ---
st.set_page_config(page_title="Configuratore Porte Automatiche SA-TEC", layout="wide")

AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"
LOGHI_DIR = Path("loghi_utenti")
LOGHI_DIR.mkdir(exist_ok=True)

# --- FUNZIONI DI SUPPORTO ---
def euro(v):
    try:
        return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "€ 0,00"

def supabase_client():
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if not url or not key: return None
        return create_client(url, key)
    except:
        return None

def html_export_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", ""))
    # Costruzione tabella
    righe = ""
    # Esempio di campi (aggiungi qui tutti quelli che servono)
    campi = [("Codice", "codice_preventivo"), ("Data", "data_ora"), ("Totale", "totale_iva")]
    for label, key in campi:
        righe += f"<tr><th>{label}</th><td>{p.get(key, '')}</td></tr>"

    return f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; }}
        .head {{ background:#06499b; color:white; padding:18px; border-radius:12px; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
        th {{ width:260px; background:#eef6ff; color:#06499b; padding:10px; text-align:left; border:1px solid #bdd4ef; }}
        td {{ padding:10px; border:1px solid #bdd4ef; }}
    </style>
    </head>
    <body>
        <div class="head"><h1>Preventivo {codice}</h1></div>
        <table>{righe}</table>
    </body>
    </html>
    """

# --- LOGICA DI AVVIO ---
def main():
    st.sidebar.title("SA-TEC")
    menu = st.sidebar.radio("Menu", ["Configuratore", "Admin"])

    if menu == "Configuratore":
        st.title("Configuratore")
        st.write("Benvenuto nel configuratore SA-TEC.")
    
    elif menu == "Admin":
        st.title("Area Admin")
        sb = supabase_client()
        if sb:
            st.success("Connesso a Supabase")
        else:
            st.error("Errore di connessione a Supabase. Controlla i secrets.")

if __name__ == "__main__":
    main()
