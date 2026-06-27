import streamlit as st
import pandas as pd
import csv
import random
import string
from pathlib import Path
from datetime import datetime

# =========================================================
# CONFIGURATORE PRO - INTERFACCIA MODERNA UI/UX COMPLETE
# =========================================================

st.set_page_config(
    page_title="SA-TEC Configurator PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reset totale dello stile Streamlit per creare un'interfaccia Premium SaaS
st.markdown("""
<style>
    /* Sfondo generale e palette tech scura */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Forzatura testi scuri nei moduli di input per massima leggibilità */
    div[data-baseweb="input"] input, div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    
    /* Stile testi e intestazioni */
    h1, h2, h3, h4 { color: #ffffff !important; font-family: 'Inter', sans-serif; font-weight: 700 !important; }
    p, span, label { color: #cbd5e1 !important; }
    
    /* Dashboard KPI Cards per i prezzi */
    .kpi-container { display: flex; gap: 20px; margin: 25px 0; }
    .kpi-card {
        flex: 1; background: #1e293b; padding: 25px; border-radius: 16px;
        border: 1px solid #334155; border-top: 4px solid #38bdf8;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .kpi-title { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }
    .kpi-value { color: #38bdf8; font-size: 2rem; font-weight: 800; margin-top: 8px; }
    
    /* La Ricevuta/Fattura Professionale per il Cliente */
    .invoice-box {
        background: #ffffff; color: #1e293b !important; padding: 40px; 
        border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        border: 1px solid #e2e8f0; font-family: 'Segoe UI', sans-serif; margin: 20px 0;
    }
    .invoice-box * { color: #1e293b !important; }
    .invoice-header { display: flex; justify-content: space-between; border-bottom: 2px solid #38bdf8; padding-bottom: 20px; margin-bottom: 20px; }
    .invoice-brand { font-size: 24px; font-weight: 800; color: #0f172a !important; }
    .invoice-details { text-align: right; font-size: 13px; color: #64748b !important; }
    .invoice-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; background: #f8fafc; padding: 20px; border-radius: 12px; }
    .invoice-totali { text-align: right; margin-top: 30px; padding-top: 20px; border-top: 1px dashed #cbd5e1; }
    
    /* Moduli dei Form nativi di Streamlit */
    div[data-testid="stForm"] { background-color: #1e293b !important; border: 1px solid #334155 !important; border-radius: 16px !important; padding: 30px !important; }
    
    /* Tabelle Storico Ordini */
    .dataframe { width: 100% !important; border-collapse: collapse; margin-top: 15px; background: #1e293b; color: white !important; border-radius: 12px; overflow: hidden; }
    .dataframe th { background-color: #38bdf8; color: #0f172a !important; padding: 12px; text-align: left; font-weight: 700; }
    .dataframe td { padding: 12px; border-bottom: 1px solid #334155; color: #cbd5e1 !important; }
    .dataframe tr:hover { background-color: #334155; }
</style>
""", unsafe_allow_html=True)

# Informazioni Istituzionali Azienda
AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
IVA = 0.22

PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"

# Credenziali Utenti Locali di Partenza
UTENTI_BASE = {
    "ADMIN": {"password": "SATEC-ADMIN", "profilo": "SA-TEC", "azienda": "SA-TEC Srl", "ricarico": "0"},
    "ROSSI01": {"password": "R2026#", "profilo": "RIVENDITORE", "azienda": "Rossi Porte", "ricarico": "30"},
    "GROS001": {"password": "G2026#", "profilo": "GROSSISTA", "azienda": "Emme Distribuzione", "ricarico": "20"}
}

# NUOVO LISTINO COMPONENTI INDUSTRIALI SESAMO AUTOMATIONS
LISTINI = {
    "SESAMO_LH100": 1340.00, 
    "SESAMO_LH140": 2280.00,
    "CASSA": 343.00 / 6.6, 
    "COPERCHIO": 214.00 / 6.6, 
    "CINGHIA": 671.00 / 60, 
    "GUIDA": 49.20 / 6.6,
    "SESAMO_RADAR_PRO": 295.00, 
    "SESAMO_DIGITAL_KEY": 135.00, 
    "BATTERIE_EMERGENZA": 120.00, 
    "ELETTROBLOCCO_SESAMO": 210.00,
    "RADAR_SICUREZZA_LATERALE": 280.00, 
    "ALLACCIO_COLLAUDO_STANDARD": 350.00
}

STATI_PREVENTIVO = ["Bozza", "Inviato", "Trattativa", "Accettato", "Perso", "Ordinato"]

# =========================
# FUNZIONI CORE ED UTILITY
# =========================

def euro(v):
    try: return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(v)

def costo_satec_reale(listino):
    return listino * 0.50 * 0.95  # Calcolo Sconto Fabbrica SA-TEC

def calcola_traversa(luce_mm, ante):
    if ante == "1 anta": return ((luce_mm * 2) + 100) / 1000
    return ((luce_mm * 2) + 200) / 1000

def ricarico_default(profilo):
    return {"SA-TEC": 0.0, "GROSSISTA": 20.0, "RIVENDITORE": 30.0}.get(profilo, 60.0)

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
# STRUTTURA LATERALE (SIDEBAR BRANDING & LOGIN)
# =========================================================

st.sidebar.markdown("""
<div style="text-align: center; padding: 15px; background: #1e293b; border-radius: 12px; margin-bottom: 25px; border: 1px solid #334155;">
    <h2 style="color: #38bdf8 !important; margin: 0; font-size: 24px; letter-spacing: 1.5px;">SA-TEC</h2>
    <span style="color: #94a3b8; font-size: 10px; text-transform: uppercase; font-weight:600;">Sesamo Dashboard</span>
</div>
""", unsafe_allow_html=True)

if "auth" not in st.session_state:
    st.session_state.auth, st.session_state.user, st.session_state.profilo, st.session_state.dati = False, "PUBBLICO", "CLIENTE", {}

utenti_totali = carica_tutti_utenti()

st.sidebar.markdown("### 🔐 AREA RISERVATA PARTNER")
if not st.session_state.auth:
    u_in = st.sidebar.text_input("ID Partner", key="u_login").strip().upper()
    p_in = st.sidebar.text_input("Password", type="password", key="p_login")
    if st.sidebar.button("Accedi al Sistema"):
        if u_in in utenti_totali and utenti_totali[u_in]["password"] == p_in:
            st.session_state.auth, st.session_state.user, st.session_state.profilo, st.session_state.dati = True, u_in, utenti_totali[u_in]["profilo"], utenti_totali[u_in]
            st.rerun()
        else: st.sidebar.error("ID o Password non validi.")
else:
    st.sidebar.markdown(f"""
    <div style="background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-bottom: 20px;">
        <span style="font-size:11px; color:#94a3b8; display:block;">Profilo Connesso:</span>
        <strong style="color:#ffffff; font-size:15px;">{st.session_state.dati.get('azienda', st.session_state.user)}</strong>
        <span style="font-size:12px; color:#38bdf8; display:block; margin-top:2px;">Listino: {st.session_state.profilo}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("Effettua Disconnessione"):
        st.session_state.auth, st.session_state.user, st.session_state.profilo, st.session_state.dati = False, "PUBBLICO", "CLIENTE", {}
        st.rerun()

try: 
    ricarico_corrente = float(st.session_state.dati.get("ricarico", "0")) if float(st.session_state.dati.get("ricarico", "0")) > 0 else ricarico_default(st.session_state.profilo)
except: 
    ricarico_corrente = ricarico_default(st.session_state.profilo)

voci = ["📐 Calcolo & Configurazione", "📋 Registro Offerte"]
if st.session_state.profilo == "SA-TEC": voci.append("🛠️ CRM Gestione")
sezione = st.sidebar.radio("Sezioni Menu", voci)

# =========================================================
# SEZIONE 1: CONFIGURATORE CORE E DISEGNO ANTE DINAMICO
# =========================================================
if sezione == "📐 Calcolo & Configurazione":
    st.markdown("<h1>📐 Sviluppo Tecnico & Configurazione</h1>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🛠️ Dimensioni e Modello Sesamo")
        modello = st.selectbox("Seleziona Automazione", ["SESAMO_LH100", "SESAMO_LH140"])
        ante = st.radio("Tipologia Ante", ["1 anta", "2 ante"], horizontal=True)
        luce = st.number_input("Luce Libera Passaggio L (mm)", 700, 3000, 1000, 50)
        altezza = st.number_input("Altezza Vano H (mm)", 1600, 3000, 2100, 50)
        traversa_m = calcola_traversa(luce, ante)

        # --- SCHEMA VISIVO SPECIFICO E REALE DELL'AUTOMAZIONE SESAMO ---
        st.markdown("### 📐 Sezione Tecnica Automazione SESAMO PRO")
        
        # Generazione dell'architettura interna dinamica (Meccanica + Elettronica superiore)
        html_schema = f"""
        <div style="background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; font-family: 'Segoe UI', sans-serif;">
            <div style="color: #38bdf8; font-weight: bold; font-size:14px; text-align: center; margin-bottom: 12px; letter-spacing:1px;">
                TRAVERSA SESAMO IN ALLUMINIO ESTRUSO: {traversa_m:.2f} m
            </div>
            
            <div style="border: 2px solid #64748b; background: #0f172a; border-radius: 6px; padding: 10px; margin-bottom: 15px; position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: bold;">
                    <span style="background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px;">CENTRALINA SESAMO DIGITAL</span>
                    <span style="background: #f59e0b; color: #0f172a; padding: 2px 6px; border-radius: 4px;">BATTERIE EMERGENZA</span>
                    <span style="background: #38bdf8; color: #0f172a; padding: 2px 6px; border-radius: 4px;">MOTORE INDUSTRIALE</span>
                </div>
                <div style="border-top: 2px dashed #475569; margin-top: 8px; padding-top: 4px; display: flex; justify-content: {"space-around" if ante == "2 ante" else "flex-end"};">
                    <span style="color: #a7f3d0; font-size: 11px;">⚙️ Carrello A</span>
                    {"<span style='color: #a7f3d0; font-size: 11px;'>⚙️ Carrello B</span>" if ante == "2 ante" else ""}
                </div>
            </div>

            {"_2_DOORS_HTML_" if ante == "2 ante" else "_1_DOOR_HTML_"}
            
            <div style="margin-top: 15px; font-size: 12px; color: #94a3b8; text-align: center;">
                Layout Operativo Sesamo (Luce Passaggio: {luce} mm | Altezza Vano: {altezza} mm)
            </div>
        </div>
        """
        
        # Sostituzione delle stringhe segnaposto con la corretta configurazione geometrica ad ante mobili
        if ante == "1 anta":
            html_schema = html_schema.replace("_1_DOOR_HTML_", f"""
            <div style="display: flex; justify-content: space-between; height: 130px; align-items: flex-end;">
                <div style="width: 49%; height: 100%; background: rgba(56, 189, 248, 0.03); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 12px;">VANO FISSO LATERALE</div>
                <div style="width: 49%; height: 100%; background: #ffffff; border: 2px solid #38bdf8; border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #0f172a; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                    <span style="font-size:11px; color:#64748b !important;">ANTA MOBILE SESAMO</span>
                    <span style="font-size: 22px; color:#38bdf8 !important; margin-top: 5px;">➔</span>
                </div>
            </div>
            """)
        else:
            html_schema = html_schema.replace("_2_DOORS_HTML_", f"""
            <div style="display: flex; justify-content: space-between; height: 130px; align-items: flex-end;">
                <div style="width: 22%; height: 100%; background: rgba(56, 189, 248, 0.03); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 11px;">FISSO DX</div>
                <div style="width: 27%; height: 100%; background: #ffffff; border: 2px solid #38bdf8; border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #0f172a; font-weight: bold; box-shadow: -3px 4px 8px rgba(0,0,0,0.25);">
                    <span style="font-size:10px; color:#64748b !important;">ANTA 1 (SESAMO)</span>
                    <span style="font-size: 20px; color:#38bdf8 !important; margin-top: 3px;">➔</span>
                </div>
                <div style="width: 27%; height: 100%; background: #ffffff; border: 2px solid #38bdf8; border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #0f172a; font-weight: bold; box-shadow: 3px 4px 8px rgba(0,0,0,0.25);">
                    <span style="font-size:10px; color:#64748b !important;">ANTA 2 (SESAMO)</span>
                    <span style="font-size: 20px; color:#38bdf8 !important; margin-top: 3px;">⬅</span>
                </div>
                <div style="width: 22%; height: 100%; background: rgba(56, 189, 248, 0.03); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 11px;">FISSO SX</div>
            </div>
            """)
            
        st.markdown(html_schema, unsafe_allow_html=True)

    with col_b:
        st.markdown("### ⚡ Sicurezze & Selettori Sesamo")
        elettro = st.checkbox("Elettroblocco Meccanico Sesamo")
        radar = st.checkbox("Radar Volumetrico Laterale Sesamo")
        collaudo = st.checkbox("Allaccio Tecnico Certificato e Collaudo")
        
        st.markdown(f"""
        <div style="background: rgba(56,
