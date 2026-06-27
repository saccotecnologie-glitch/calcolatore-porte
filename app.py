import streamlit as st
import pandas as pd
import csv
import random
import string
from pathlib import Path
from datetime import datetime
from supabase import create_client

# =========================================================
# CONFIGURATORE PRO - CONFIGURAZIONE E GRAFICA PREMIUM CSS
# =========================================================

st.set_page_config(
    page_title="SA-TEC Configurator PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Iniezione Stile Custom per un look moderno e pulito (Cards + Tabelle curate)
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #0f172a !important; font-family: 'Segoe UI', sans-serif; font-weight: 700 !important; }
    .metric-card {
        background: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border-left: 5px solid #0284c7; margin-bottom: 15px;
    }
    .metric-title { color: #64748b; font-size: 0.85rem; text-transform: uppercase; font-weight: bold; }
    .metric-value { color: #0f172a; font-size: 1.7rem; font-weight: 700; margin-top: 5px; }
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    section[data-testid="stSidebar"] .stButton>button { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: bold; }
    .dataframe { width: 100% !important; border-collapse: collapse; margin-top: 15px; font-size: 0.9em; }
    .dataframe th { background-color: #0f172a; color: white; padding: 10px; text-align: left; }
    .dataframe td { padding: 10px; border-bottom: 1px solid #e2e8f0; }
    .dataframe tr:nth-of-type(even) { background-color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# Costanti Aziendali
AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
IVA = 0.22

PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"

# Database Utenti Hardcoded di Base
UTENTI_BASE = {
    "ADMIN": {"password": "SATEC-ADMIN", "profilo": "SA-TEC", "azienda": "SA-TEC Srl", "ricarico": "0"},
    "ROSSI01": {"password": "R2026#", "profilo": "RIVENDITORE", "azienda": "Rossi Porte", "ricarico": "30"},
    "GROS001": {"password": "G2026#", "profilo": "GROSSISTA", "azienda": "Emme Distribuzione", "ricarico": "20"}
}

# Listino Prezzi Componenti Meccanici ed Elettronici
LISTINI = {
    "PW100_1": 1236.00, "PW100_2": 1298.00, "ER140_1": 2140.00, "ER140_2": 2200.00,
    "CASSA": 343.00 / 6.6, "COPERCHIO": 214.00 / 6.6, "CINGHIA": 671.00 / 60, "GUIDA": 49.20 / 6.6,
    "HR100": 285.00, "ICON": 114.00, "BATTERIE": 118.00, "ELETTRO_STANDARD": 195.00,
    "RADAR_SICUREZZA_LATERALE": 280.00, "ALLACCIO_COLLAUDO_STANDARD": 350.00
}

STATI_PREVENTIVO = ["Bozza", "Inviato", "Trattativa", "Accettato", "Perso", "Ordinato"]

# =========================
# FUNZIONI DI UTILITÀ E LOGICA
# =========================

def euro(v):
    try: return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(v)

def costo_satec_reale(listino):
    return listino * 0.50 * 0.95  # Sconto 50% + 5% extra distributore

def calcola_traversa(luce_mm, ante):
    if ante == "1 anta": return ((luce_mm * 2) + 100) / 1000
    return ((luce_mm * 2) + 200) / 1000

def ricarico_default(profilo):
    return {"SA-TEC": 0.0, "GROSSISTA": 20.0, "RIVENDITORE": 30.0}.get(profilo, 60.0)

# =========================
# INTEGRAZIONE DATABASE (CSV COMPATIBILE CLOUD)
# =========================

def supabase_client():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    return create_client(url, key) if url and key else None

def carica_tutti_utenti():
    utenti = dict(UTENTI_BASE)
    if Path(UTENTI_CSV).exists():
        try:
            with open(UTENTI_CSV, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    u = r.get("utente", "").strip().upper()
                    if u: utenti[u] = {"password": r.get("password", ""), "profilo": r.get("profilo", "RIVENDITORE"), "azienda": r.get("azienda", ""), "ricarico": r.get("ricarico", "30")}
        except: pass
    return utenti

def carica_preventivi():
    if not Path(PREVENTIVI_CSV).exists(): return []
    try:
        with open(PREVENTIVI_CSV, "r", encoding="utf-8") as f: return list(csv.DictReader(f))
    except: return []

def salva_preventivo_local(dati):
    fe = Path(PREVENTIVI_CSV).exists()
    campi = ["codice_preventivo", "data_ora", "utente", "profilo", "cliente_nome", "cliente_azienda", "cliente_telefono", "cliente_email", "configurazione", "luce_mm", "altezza_mm", "traversa_m", "imponibile", "iva", "totale_iva", "stato"]
    with open(PREVENTIVI_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        if not fe: w.writeheader()
        w.writerow(dati)
    
    # Sincronizzazione Silenziosa Cloud se presente
    sb = supabase_client()
    if sb:
        try:
            sb.table("preventivi").insert({
                "codice_preventivo": dati["codice_preventivo"], "configurazione": dati["configurazione"],
                "luce_mm": int(dati["luce_mm"]), "altezza_mm": int(dati["altezza_mm"]),
                "traversa_m": float(dati["traversa_m"]), "totale": float(dati["imponibile"]), "stato": dati["stato"]
            }).execute()
        except: pass

def aggiorna_stato_csv(codice, nuovo_stato):
    try:
        with open(PREVENTIVI_CSV, "r", encoding="utf-8") as f: righe = list(csv.DictReader(f))
        for r in righe:
            if r.get("codice_preventivo") == codice: r["stato"] = nuovo_stato
        with open(PREVENTIVI_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(righe[0].keys()))
            w.writeheader()
            w.writerows(righe)
        return True
    except: return False

def genera_nuovo_codice():
    anno = datetime.now().year
    nums = [int(p["codice_preventivo"].split("-")[-1]) for p in carica_preventivi() if p["codice_preventivo"].startswith(f"SAT-{anno}-")]
    return f"SAT-{anno}-{max(nums)+1 if nums else 1:04d}"

# =========================================================
# AUTENTICAZIONE E INTERFACCIA UTENTE (SIDEBAR)
# =========================================================

st.sidebar.markdown("""
<div style="text-align: center; padding: 10px; background: #1e293b; border-radius: 8px; margin-bottom: 20px;">
    <h2 style="color: #38bdf8 !important; margin: 0; font-size: 20px; letter-spacing: 1px;">SA-TEC PRO</h2>
    <span style="color: #94a3b8; font-size: 11px;">AUTOMATIC DOORS SYSTEMS</span>
</div>
""", unsafe_allow_html=True)

if "auth" not in st.session_state:
    st.session_state.auth, st.session_state.user, st.session_state.profilo, st.session_state.dati = False, "PUBBLICO", "CLIENTE", {}

utenti_totali = carica_tutti_utenti()

st.sidebar.markdown("### 🔐 ACCESSO PARTNER")
if not st.session_state.auth:
    u_in = st.sidebar.text_input("ID Partner", key="u_login").strip().upper()
    p_in = st.sidebar.text_input("Password", type="password", key="p_login")
    if st.sidebar.button("Entra nel Sistema"):
        if u_in in utenti_totali and utenti_totali[u_in]["password"] == p_in:
            st.session_state.auth, st.session_state.user, st.session_state.profilo, st.session_state.dati = True, u_in, utenti_totali[u_in]["profilo"], utenti_totali[u_in]
            st.rerun()
        else: st.sidebar.error("Credenziali errate.")
else:
    st.sidebar.markdown(f"""
    <div style="background: #1e293b; padding: 12px; border-radius: 6px; border-left: 4px solid #38bdf8; margin-bottom: 15px;">
        <p style="margin:0; font-size:11px; color:#a1a1aa;">Azienda Connessa</p>
        <strong style="color:white; font-size:14px;">{st.session_state.dati.get('azienda', st.session_state.user)}</strong>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("Esci dal Profilo"):
        st.session_state.auth, st.session_state.user, st.session_state.profilo, st.session_state.dati = False, "PUBBLICO", "CLIENTE", {}
        st.rerun()

# Definizione Ricarico Attivo
try: ricarico_corrente = float(st.session_state.dati.get("ricarico", "0")) if float(st.session_state.dati.get
