import streamlit as st
import pandas as pd
import csv
import random
import string
from pathlib import Path
from datetime import datetime

# =========================================================
# CONFIGURAZIONE PROTETTA
# =========================================================
st.set_page_config(page_title="SA-TEC Configurator", layout="wide")

# CSS con escape delle parentesi graffe per evitare il crash
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .kpi-card {
        background: #1e293b; padding: 20px; border-radius: 12px;
        border: 1px solid #334155; border-top: 4px solid #38bdf8;
    }
    .kpi-value { color: #38bdf8; font-size: 1.8rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# File e Costanti
PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"

# =========================================================
# FUNZIONI CORE (BLINDATE)
# =========================================================
def carica_tutti_utenti():
    # Admin fisso per non perdere mai l'accesso
    utenti = {"ADMIN": {"password": "SATEC-ADMIN", "profilo": "SA-TEC", "azienda": "SA-TEC Srl", "ricarico": "0"}}
    if Path(UTENTI_CSV).exists():
        with open(UTENTI_CSV, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                u = r.get("utente", "").strip().upper()
                if u and u != "ADMIN":
                    utenti[u] = r
    return utenti

# --- Avvio Sistema ---
if "auth" not in st.session_state:
    st.session_state.update({"auth": False, "user": "PUBBLICO", "profilo": "CLIENTE", "dati": {}})

utenti_totali = carica_tutti_utenti()

# SIDEBAR LOGIN
with st.sidebar:
    st.title("🔐 Accesso")
    if not st.session_state.auth:
        u_in = st.text_input("ID Partner").upper()
        p_in = st.text_input("Password", type="password")
        if st.button("Entra"):
            if u_in in utenti_totali and utenti_totali[u_in]["password"] == p_in:
                st.session_state.update({"auth": True, "user": u_in, "profilo": utenti_totali[u_in]["profilo"], "dati": utenti_totali[u_in]})
                st.rerun()
            else: st.error("Credenziali errate")
    else:
        st.write(f"Connesso come: {st.session_state.user}")
        if st.button("Logout"): st.session_state.auth = False; st.rerun()

# CORPO PRINCIPALE
st.title("📐 Configuratore SA-TEC")

# ESEMPIO GRAFICA CORRETTO (SENZA CRASH)
st.markdown("""
<div style="display: flex; gap: 10px; height: 110px; margin-top: 5px;">
    <div style="flex: 1; background: rgba(56, 189, 248, 0.05); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 12px; font-weight: 500;">VANO FISSO</div>
    <div style="flex: 1; background: #ffffff; border: 2px solid #38bdf8; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
        <span style="font-size: 11px; color: #475569 !important; font-weight: bold;">ANTA MOBILE</span>
        <span style="color: #38bdf8 !important; font-size: 24px; font-weight: bold; margin-top: 2px;">➔</span>
    </div>
</div>
<div style="text-align: center; font-size: 11px; color: #94a3b8; margin-top: 12px; font-weight: 500;">
    Configurazione Standard
</div>
""", unsafe_allow_html=True)
