import streamlit as st
import pandas as pd
import csv
import random
import string
from pathlib import Path
from datetime import datetime

# =========================================================
# CONFIGURATORE PRO - INTERFACCIA MODERNA UI/UX BLINDATA
# =========================================================

st.set_page_config(
    page_title="SA-TEC Configurator PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reset totale dello stile Streamlit per creare un'interfaccia Premium SaaS Real Tech
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

# LISTINO COMPONENTI INDUSTRIALI SESAMO AUTOMATIONS
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
    # Admin iniettato hardcoded nativo per bypassare qualsiasi errore del CSV
    utenti = {
        "ADMIN": {"password": "SATEC-ADMIN", "profilo": "SA-TEC", "azienda": "SA-TEC Srl", "ricarico": "0"}
    }
    if Path(UTENTI_CSV).exists():
        try:
            with open(UTENTI_CSV, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    u = r.get("utente", "").strip().upper()
                    if u and u != "ADMIN":
                        utenti[u] = {
                            "password": r.get("password", ""),
                            "profilo": r.get("profilo", "RIVENDITORE"),
                            "azienda": r.get("azienda", ""),
                            "ricarico": r.get("ricarico", "30")
                        }
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

        st.markdown("### 📐 Sezione Tecnica Automazione SESAMO PRO")
        
        allineamento_meccanico = "space-around" if ante == "2 ante" else "flex-end"
        stringa_carrello_b = '<div style="color: #a7f3d0; font-size: 12px; font-weight: bold;">⚙️ Carrello B</div>' if ante == "2 ante" else ''
        
        # Escape corretto delle parentesi graffe per evitare crash dell'interprete delle f-string
        if ante == "1 anta":
            blocco_ante_html = """
            <div style="display: flex; gap: 10px; height: 110px; margin-top: 5px;">
                <div style="flex: 1; background: rgba(56, 189, 248, 0.05); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 12px; font-weight: 500;">VANO FISSO</div>
                <div style="flex: 1; background: #ffffff; border: 2px solid #38bdf8; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                    <span style="font-size: 11px; color: #475569 !important; font-weight: bold;">ANTA MOBILE</span>
                    <span style="color: #38bdf8 !important; font-size: 24px; font-weight: bold; margin-top: 2px;">➔</span>
                </div>
            </div>
            """
        else:
            blocco_ante_html = """
            <div style="display: flex; gap: 8px; height: 110px; margin-top: 5px;">
                <div style="flex: 22; background: rgba(56, 189, 248, 0.05); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 11px;">FISSO DX</div>
                <div style="flex: 27; background: #ffffff; border: 2px solid #38bdf8; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: -2px 4px 8px rgba(0,0,0,0.3);">
                    <span style="font-size: 10px; color: #475569 !important; font-weight: bold;">ANTA 1</span>
                    <span style="color: #38bdf8 !important; font-size: 20px; font-weight: bold;">➔</span>
                </div>
                <div style="flex: 27; background: #ffffff; border: 2px solid #38bdf8; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 2px 4px 8px rgba(0,0,0,0.3);">
                    <span style="font-size: 10px; color: #475569 !important; font-weight: bold;">ANTA 2</span>
                    <span style="color: #38bdf8 !important; font-size: 20px; font-weight: bold;">⬅</span>
                </div>
                <div style="flex: 22; background: rgba(56, 189, 248, 0.05); border: 1px dashed #475569; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 11px;">FISSO SX</div>
            </div>
            """

        st.markdown(f"""
        <div style="background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; font-family: 'Inter', sans-serif;">
            <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #38bdf8; text-align: center; margin-bottom: 12px;">
                <span style="color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 600; display: block; letter-spacing: 0.5px;">Sviluppo Traversa Estruso</span>
                <strong style="color: #38bdf8; font-size: 18px;">{traversa_m:.2f} Metri Lineari</strong>
            </div>
            <div style="background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px dashed #334155;">
                    <span style="background: #ef4444; color: white; padding: 2px 6px; font-size: 9px; font-weight: bold; border-radius: 4px;">SESAMO BRAIN</span>
                    <span style="background: #f59e0b; color: #0f172a; padding: 2px 6px; font-size: 9px; font-weight: bold; border-radius: 4px;">BACKUP BATTERY</span>
                    <span style="background: #38bdf8; color: #0f172a; padding: 2px 6px; font-size: 9px; font-weight: bold; border-radius: 4px;">POWER MOTOR</span>
                </div>
                <div style="display: flex; justify-content: {allineamento_meccanico}; margin-top: 10px;">
                    <div style="color: #a7f3d0; font-size: 12px; font-weight: bold;">⚙️ Carrello A</div>
                    {stringa_carrello_b}
                </div>
            </div>
            {blocco_ante_html}
            <div style="text-align: center; font-size: 11px; color: #94a3b8; margin-top: 12px; font-weight: 500;">
                Configurazione: L {luce}mm × H {altezza}mm
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("### ⚡ Sicurezze & Selettori Sesamo")
        elettro = st.checkbox("Elettroblocco Meccanico Sesamo")
        radar = st.checkbox("Radar Volumetrico Laterale Sesamo")
        collaudo = st.checkbox("Allaccio Tecnico Certificato e Collaudo")
        
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.1); padding: 20px; border-radius: 12px; border: 1px dashed #38bdf8; margin-top: 45px;">
            <span style="color:#94a3b8; font-size:12px; text-transform:uppercase; display:block;">Taglio Profilo Traversa:</span>
            <strong style="color:#38bdf8; font-size:24px;">{traversa_m:.2f} metri lineari</strong>
        </div>
        """, unsafe_allow_html=True)

    # Motore Algoritmico di Calcolo Economico Real-time
    costo_alluminio = ((LISTINI["CASSA"] * traversa_m) + (LISTINI["COPERCHIO"] * traversa_m) + (LISTINI["CINGHIA"] * traversa_m * 2) + (LISTINI["GUIDA"] * traversa_m))
    base_meccanica = LISTINI[modello] + costo_alluminio
    elettronica_base = (LISTINI["SESAMO_RADAR_PRO"] * 2) + LISTINI["SESAMO_DIGITAL_KEY"] + LISTINI["BATTERIE_EMERGENZA"]
    kit_opzionali = (LISTINI["ELETTROBLOCCO_SESAMO"] if elettro else 0) + (LISTINI["RADAR_SICUREZZA_LATERALE"] if radar else 0) + (LISTINI["ALLACCIO_COLLAUDO_STANDARD"] if collaudo else 0)
    
    totale_listino = base_meccanica + elettronica_base + kit_opzionali
    prezzo_costo_satec = costo_satec_reale(totale_listino)
    
    imponibile_cliente = prezzo_costo_satec * (1 + (ricarico_corrente / 100))
    totale_iva = imponibile_cliente * IVA
    prezzo_finito_ivato = imponibile_cliente + totale_iva

    # Quadro Finanziario di Sintesi (KPI Cards)
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card"><div class="kpi-title">Imponibile Netto</div><div class="kpi-value">{euro(imponibile_cliente)}</div></div>
        <div class="kpi-card" style="border-top-color: #10b981;"><div class="kpi-title">Margine Applicato</div><div class="kpi-value">{ricarico_corrente} %</div></div>
        <div class="kpi-card" style="border-top-color: #6366f1;"><div class="kpi-title">Totale Ivato (22%)</div><div class="kpi-value">{euro(prezzo_finito_ivato)}</div></div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.profilo == "SA-TEC":
        with st.expander("🔍 Monitoraggio Margini Industriali (Solo Admin)"):
            st.info(f"Prezzo di Fabbrica Netto: {euro(prezzo_costo_satec)} | Utile Netto su questa vendita: {euro(imponibile_cliente - prezzo_costo_satec)}")

    st.markdown("### 📝 Intestazione e Archiviazione Preventivo")
    with st.form("salva_offerta"):
        c1, c2 = st.columns(2)
        with c1: n_client = st.text_input("Nome Referente / Cliente").strip()
        with c2: a_client = st.text_input("Società / Ragione Sociale").strip()
        t_client = st.text_input("Telefono Diretto")
        m_client = st.text_input("Email Cliente")
        
        if st.form_submit_button("Conferma ed Emetti Offerta"):
            if not n_client and not a_client: st.error("Inserire un'intestazione valida per salvare il file.")
            else:
                nuovo_cod = genera_nuovo_codice()
                payload = {
                    "codice_preventivo": nuovo_cod, "data_ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "utente": st.session_state.user, "profilo": st.session_state.profilo,
                    "cliente_nome": n_client, "cliente_azienda": a_client, "cliente_telefono": t_client, "cliente_email": m_client,
                    "configurazione": f"{modello} ({ante})", "luce_mm": str(luce), "altezza_mm": str(altezza),
                    "traversa_m": f"{traversa_m:.2f}", "imponibile": f"{imponibile_cliente:.2f}",
                    "iva": f"{totale_iva:.2f}", "totale_iva": f"{prezzo_finito_ivato:.2f}", "stato": "Bozza"
                }
                salva_preventivo_local(payload)
                st.success(f"🚀 Offerta salvata! Codice: {nuovo_cod}. Controlla il Registro per visualizzarla.")

# =========================================================
# SEZIONE 2: REGISTRO STORICO E RICEVUTE CLIENTI PREMIUM
# =========================================================
elif sezione == "📋 Registro Offerte":
    st.markdown("<h1>📋 Archivio Storico e Generazione Offerte</h1>", unsafe_allow_html=True)
    offerte = carica_preventivi()
    if st.session_state.profilo != "SA-TEC": offerte = [o for o in offerte if o.get("utente") == st.session_state.user]
    
    if not offerte: st.info("Nessun preventivo presente in archivio.")
    else:
        df = pd.DataFrame(offerte).fillna("").astype(str)
        
        cx1, cx2, cx3 = st.columns([2, 2, 1])
        with cx1: p_sel = st.selectbox("Seleziona File Preventivo", df["codice_preventivo"].unique())
        with cx2: s_sel = st.selectbox("Avanzamento Stato", STATI_PREVENTIVO)
        with cx3:
            st.write(" ")
            if st.button("Aggiorna Stato Lavori", use_container_width=True):
                if aggiorna_stato_csv(p_sel, s_sel): st.success("Stato Aggiornato!"); st.rerun()

        record = df[df["codice_preventivo"] == p_sel].iloc[0]
        
        # Estrazione e isolamento preventivo dei record
        rec_codice = record["codice_preventivo"]
        rec_data = record["data_ora"]
        rec_stato = record["stato"]
        rec_nome = record["cliente_nome"]
        rec_azienda = record["cliente_azienda"]
        rec_tel = record["cliente_telefono"]
        rec_email = record["cliente_email"]
        rec_config = record["configurazione"]
        rec_luce = record["luce_mm"]
        rec_altezza = record["altezza_mm"]
        rec_traversa = record["traversa_m"]
        rec_imponibile = euro(record["imponibile"])
        rec_iva = euro(record["iva"])
        rec_totale = euro(record["totale_iva"])
        
        st.markdown("---")
        st.markdown("### 📄 Documento Offerta Commerciale")
        
        html_stampa = f"""
        <div class="invoice-box">
            <div class="invoice-header">
                <div>
                    <div class="invoice-brand">{AZIENDA}</div>
                    <div style="font-size: 12px; color: #64748b !important;">Sistemi di Automazione Porte Professionali</div>
                    <div style="font-size: 11px; margin-top:5px;">{SEDE}<br>P.IVA: {PIVA} | {EMAIL}</div>
                </div>
                <div class="invoice-details">
                    <span style="font-size:18px; font-weight:700; color:#0f172a !important; display:block;">PREVENTIVO</span>
                    <strong>Codice:</strong> {rec_codice}<br>
                    <strong>Data:</strong> {rec_data}<br>
                    <strong>Stato Attuale:</strong> <span style="color:#38bdf8 !important; font-weight:bold;">{rec_stato}</span>
                </div>
            </div>
            
            <div style="margin: 25px 0;">
                <span style="font-size:11px; text-transform:uppercase; color:#64748b !important; font-weight:700; display:block; margin-bottom:5px;">Destinatario / Intestatario:</span>
                <strong style="font-size:16px; color:#0f172a !important;">{rec_nome} {rec_azienda}</strong><br>
                <span style="font-size:13px;">Contatti: {rec_tel} | {rec_email}</span>
            </div>
            
            <div class="invoice-grid">
                <div>
                    <small style="color:#64748b !important; display:block;">Configurazione Richiesta</small>
                    <strong style="font-size:15px;">Automazione Serie {rec_config}</strong>
                </div>
                <div>
                    <small style="color:#64748b !important; display:block;">Specifiche Geometriche</small>
                    <strong>Luce Passaggio: {rec_luce} mm | Altezza: {rec_altezza} mm</strong><br>
                    <small>Sviluppo taglio profilo della traversa: {rec_traversa} metri</small>
                </div>
            </div>
            
            <div class="invoice-totali">
                <table style="width:250px; margin-left:auto; font-size:14px; border-spacing:0 8px;">
                    <tr>
                        <td style="color:#64748b !important; text-align:left;">Totale Imponibile:</td>
                        <td style="text-align:right; font-weight:600;">{rec_imponibile}</td>
                    </tr>
                    <tr>
                        <td style="color:#64748b !important; text-align:left;">IVA Corrente (22%):</td>
                        <td style="text-align:right;">{rec_iva}</td>
                    </tr>
                    <tr style="font-size:18px; font-weight:800; border-top:2px solid #0f172a;">
                        <td style="color:#0f172a !important; text-align:left; padding-top:10px;">Totale Offerta:</td>
                        <td style="text-align:right; color:#38bdf8 !important; padding-top:10px;">{rec_totale}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        st.markdown(html_stampa, unsafe_allow_html=True)
        
        st.markdown("#### 📂 Database Storico Completo")
        st.markdown(df.to_html(index=False, classes="dataframe"), unsafe_allow_html=True)

# =========================================================
# SEZIONE 3: CRM AMMINISTRATORE (SOLO PROFILI ACCREDITATI)
# =========================================================
elif sezione == "🛠️ CRM Gestione" and st.session_state.profilo == "SA-TEC":
    st.markdown("<h1>🛠️ Controllo e Registrazione Partner</h1>", unsafe_allow_html=True)
    
    with st.form("crea_nuovo_partner"):
        st.subheader("Rilascia Nuove Credenziali di Accesso")
        r_ruolo = st.selectbox("Livello Listino Assegnato", ["RIVENDITORE", "GROSSISTA"])
        r_az = st.text_input("Ragione Sociale Azienda Partner").strip()
        r_ric = st.number_input("Ricarico Customizzato % (Lascia 0 per Default Automazione)", min_value=0.0, value=0.0)
        
        if st.form_submit_button("Genera Account Privato"):
            if not r_az: 
                st.error("Inserire la ragione sociale dell'azienda partner.")
            else:
                pref = "RIV" if r_ruolo == "RIVENDITORE" else "GROS"
                prossimo_num = random.randint(100, 999)
                nuovo_id = f"{pref}{prossimo_num}"
                nuova_pwd = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))
                ric_final = str(r_ric) if r_ric > 0 else str(ricarico_default(r_ruolo))
                
                fe = Path(UTENTI_CSV).exists()
                with open(UTENTI_CSV, "a", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=["utente", "password", "profilo", "azienda", "ricarico"])
                    if not fe: w.writeheader()
                    w.writerow({"utente": nuovo_id, "password": nuova_pwd, "profilo": r_ruolo, "azienda": r_az, "ricarico": ric_final})
                
                st.success(f"Account Creato!\n* **ID LOGIN:** `{nuovo_id}`\n* **PASSWORD TEMPORANEA:** `{nuova_pwd}`\n* **RICARICO:** {ric_final}%")
