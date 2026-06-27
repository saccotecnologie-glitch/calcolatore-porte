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
st.set_page_config(page_title="Configuratore Porte Automatiche SA-TEC", layout="wide", initial_sidebar_state="expanded")

AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
PEC = "sa-tec@pec.it"
CODICE_UNIVOCO = "M5UXCR1"
IBAN = "IT30S0825842841007000002877"
PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"
LOGHI_DIR = Path("loghi_utenti")
LOGHI_DIR.mkdir(exist_ok=True)

# --- UTENTI E LISTINI ---
UTENTI_BASE = {
    "ADMIN": {"password": "SATEC-ADMIN", "profilo": "SA-TEC", "nome": "SA-TEC Amministratore", "azienda": "SA-TEC", "ricarico": "0"},
    "ROSSI01": {"password": "R2026#", "profilo": "RIVENDITORE", "nome": "Rivenditore Rossi", "azienda": "Rossi", "ricarico": "30"},
    "GROS001": {"password": "G2026#", "profilo": "GROSSISTA", "nome": "Grossista Mario", "azienda": "", "ricarico": "20"}
}
LISTINI = {"PW100_1": 1236.00, "ER140_1": 2140.00, "ASSEMBLAGGIO": 130.00}

# --- FUNZIONI CORE ---
def euro(v): return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def supabase_client():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

def html_export_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", ""))
    righe = "".join([f"<tr><th>{l}</th><td>{p.get(k, '')}</td></tr>" for l, k in [("Codice", "codice_preventivo"), ("Totale", "totale_iva"), ("Stato", "stato")]])
    return f"""
    <html>
    <head><meta charset="utf-8">
    <style>
        body {{ font-family: Arial; margin: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #eef6ff; color: #06499b; padding: 10px; text-align: left; border: 1px solid #bdd4ef; }}
        td {{ padding: 10px; border: 1px solid #bdd4ef; }}
    </style>
    </head>
    <body>
        <h1>Preventivo {codice}</h1>
        <table>{righe}</table>
    </body>
    </html>
    """

# --- LOGICA DI NAVIGAZIONE ---
def main():
    st.sidebar.title("SA-TEC Management")
    menu = st.sidebar.radio("Navigazione", ["Configuratore", "Admin Preventivi", "Gestione Utenti"])

    if menu == "Configuratore":
        st.header("Configuratore Porte")
        # Inserisci qui la tua logica di input
        
    elif menu == "Admin Preventivi":
        st.header("Gestione Preventivi")
        sb = supabase_client()
        if sb:
            res = sb.table("preventivi").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                st.dataframe(df)
            else:
                st.write("Nessun preventivo trovato.")
                
    elif menu == "Gestione Utenti":
        st.header("Gestione Utenti")
        st.write("Area gestione utenti attivata.")

if __name__ == "__main__":
    main()
