import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import csv
import pandas as pd
import random
import string
from pathlib import Path
from datetime import datetime, date

# =========================================================
# CONFIGURATORE SA-TEC PRO
# Versione con:
# - Login utenti
# - Registrazione cliente automatica
# - Creazione utenti da area ADMIN
# - Salvataggio utenti su CSV
# - Salvataggio preventivi su CSV
# Formula definitiva:
# Costo SA-TEC reale = Listino × 0,50 × 0,95
# Prezzo vendita = Costo SA-TEC × (1 + ricarico utente / 100)
# Ricarico personalizzato assegnabile da ADMIN
# =========================================================

st.set_page_config(
    page_title="Configuratore Porte Automatiche SA-TEC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
PEC = "sa-tec@pec.it"
IBAN = "IT30S0825842841007000002877"
IVA = 0.22

PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"

# =========================
# UTENTI BASE
# =========================

UTENTI_BASE = {
    "ADMIN": {
        "password": "SATEC-ADMIN",
        "profilo": "SA-TEC",
        "nome": "SA-TEC Amministratore",
        "azienda": "SA-TEC",
        "telefono": "",
        "email": "",
        "ricarico": "0"
    },
    "ROSSI01": {
        "password": "R2026#",
        "profilo": "RIVENDITORE",
        "nome": "Rivenditore Rossi",
        "azienda": "Rossi",
        "telefono": "",
        "email": "",
        "ricarico": "30"
    },
    "VERDI01": {
        "password": "V2026#",
        "profilo": "RIVENDITORE",
        "nome": "Rivenditore Verdi",
        "azienda": "Verdi",
        "telefono": "",
        "email": "",
        "ricarico": "30"
    },
    "GROS001": {
        "password": "G2026#",
        "profilo": "GROSSISTA",
        "nome": "Grossista Mario",
        "azienda": "",
        "telefono": "",
        "email": "",
        "ricarico": "20"
    },
    "GROS002": {
        "password": "G22026#",
        "profilo": "GROSSISTA",
        "nome": "Grossista Luca",
        "azienda": "",
        "telefono": "",
        "email": "",
        "ricarico": "20"
    },
}

PROFILI = {
    "CLIENTE": "Cliente finale",
    "RIVENDITORE": "Rivenditore",
    "GROSSISTA": "Grossista",
    "SA-TEC": "SA-TEC",
}

LISTINI = {
    "PW100_1": 1236.00,
    "PW100_2": 1298.00,
    "ER140_1": 2140.00,
    "ER140_2": 2200.00,

    "CASSA": 343.00 / 6.6,
    "COPERCHIO": 214.00 / 6.6,
    "GUARN_COPERCHIO": 134.00 / 35,
    "PF54_91_GUARN_ANTIVIBRAZIONE": 2.50,
    "CINGHIA": 671.00 / 60,
    "GUIDA": 49.20 / 6.6,
    "GUARN_GUIDA": 66.00 / 30,

    "HR100": 285.00,
    "ICON": 114.00,
    "BATTERIE": 118.00,
    "ELETTRO_STANDARD": 195.00,

    "SSR3_ER_BL": 375.00,
    "DIGIDOR": 180.00,
    "PULSANTE_EMERGENZA": 130.00,
    "ELETTRO_RIDONDANTE": 290.00,

    "ASSEMBLAGGIO": 130.00,
    "ALLACCIO_COLLAUDO_STANDARD": 350.00,
    "ALLACCIO_COLLAUDO_RIDONDANTE": 400.00,
}

# =========================
# FUNZIONI UTILI
# =========================


def dataframe_sicuro(dati):
    """
    Evita errore Streamlit con valori NaN nelle tabelle.
    Converte celle vuote/NaN in stringa vuota.
    """
    df = pd.DataFrame(dati)
    if df.empty:
        return df
    return df.fillna("").astype(str)

def euro(v):
    return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def costo_satec_reale(listino):
    return listino * 0.50 * 0.95

def ricarico_default(profilo):
    if profilo == "SA-TEC":
        return 0.0
    if profilo == "GROSSISTA":
        return 20.0
    if profilo == "RIVENDITORE":
        return 30.0
    return 35.0

RICARICO_ATTIVO = 35.0

def prezzo_vendita(listino):
    costo = costo_satec_reale(listino)
    return costo * (1 + (RICARICO_ATTIVO / 100))

def img_to_base64(paths):
    for p in paths:
        f = Path(p)
        if f.exists():
            return base64.b64encode(f.read_bytes()).decode()
    return ""

def calcola_traversa(luce_mm, ante):
    if ante == "1 anta":
        return ((luce_mm * 2) + 100) / 1000
    return ((luce_mm * 2) + 200) / 1000

def genera_password(lunghezza=7):
    caratteri = string.ascii_uppercase + string.digits
    return "".join(random.choice(caratteri) for _ in range(lunghezza))

def normalizza_codice(testo):
    pulito = "".join(ch for ch in testo.upper().strip() if ch.isalnum())
    return pulito[:14] if pulito else "CLIENTE"

# =========================
# UTENTI CSV
# =========================

def carica_utenti_csv():
    utenti = {}
    path = Path(UTENTI_CSV)
    if not path.exists():
        return utenti

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            codice = r.get("utente", "").strip().upper()
            if codice:
                utenti[codice] = {
                    "password": r.get("password", ""),
                    "profilo": r.get("profilo", "CLIENTE"),
                    "nome": r.get("nome", ""),
                    "azienda": r.get("azienda", ""),
                    "telefono": r.get("telefono", ""),
                    "email": r.get("email", ""),
                    "ricarico": r.get("ricarico", "")
                }
    return utenti

def salva_utente_csv(utente, password, profilo, nome, azienda, telefono, email, ricarico="35"):
    file_exists = Path(UTENTI_CSV).exists()
    campi = ["utente", "password", "profilo", "nome", "azienda", "telefono", "email", "ricarico", "data_creazione"]

    with open(UTENTI_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "utente": utente,
            "password": password,
            "profilo": profilo,
            "nome": nome,
            "azienda": azienda,
            "telefono": telefono,
            "email": email,
            "ricarico": ricarico,
            "data_creazione": datetime.now().strftime("%d/%m/%Y %H:%M")
        })

def carica_tutti_utenti():
    utenti = dict(UTENTI_BASE)
    utenti.update(carica_utenti_csv())
    return utenti

def genera_codice_progressivo(profilo, utenti):
    prefisso = {
        "CLIENTE": "CLI",
        "RIVENDITORE": "RIV",
        "GROSSISTA": "GROS",
        "SA-TEC": "ADM"
    }.get(profilo, "CLI")

    numeri = []
    for u in utenti.keys():
        if u.startswith(prefisso):
            try:
                numeri.append(int(u.replace(prefisso, "")))
            except:
                pass
    prossimo = max(numeri) + 1 if numeri else 1
    return f"{prefisso}{prossimo:04d}"

# =========================
# PREVENTIVI CSV
# =========================

def salva_preventivo(dati):
    file_exists = Path(PREVENTIVI_CSV).exists()
    campi = [
        "data_ora", "utente", "profilo", "cliente_nome", "cliente_azienda",
        "cliente_telefono", "cliente_email", "configurazione", "luce_mm",
        "altezza_mm", "traversa_m", "elettroblocco", "allaccio",
        "ricarico_percento", "imponibile", "iva", "totale_iva", "stato"
    ]
    with open(PREVENTIVI_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        if not file_exists:
            writer.writeheader()
        writer.writerow(dati)

def carica_preventivi():
    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# =========================
# LOGIN + REGISTRAZIONE
# =========================

def login_box():
    utenti = carica_tutti_utenti()

    st.sidebar.markdown("## Accesso")
    st.sidebar.info("Cliente finale: può entrare libero oppure registrarsi.")

    username = st.sidebar.text_input("Utente", value="", key="login_user")
    password = st.sidebar.text_input("Password", value="", type="password", key="login_pwd")

    profilo = "CLIENTE"
    nome_utente = "Cliente finale"
    utente_codice = "CLIENTE"
    dati_utente = {
        "nome": "",
        "azienda": "",
        "telefono": "",
        "email": "",
        "ricarico": "35"
    }

    if username.strip() or password.strip():
        u = username.strip().upper()
        if u in utenti and utenti[u]["password"] == password:
            profilo = utenti[u]["profilo"]
            nome_utente = utenti[u]["nome"] or u
            utente_codice = u
            dati_utente = utenti[u]
            st.sidebar.success(f"Accesso: {nome_utente}")
        else:
            st.sidebar.error("Utente o password non corretti.")
    else:
        st.sidebar.success("Accesso cliente finale")

    st.sidebar.markdown("---")
    st.sidebar.write(f"Profilo attivo: **{PROFILI[profilo]}**")

    with st.sidebar.expander("Registrazione cliente"):
        st.caption("Crea automaticamente una password cliente.")
        reg_nome = st.text_input("Nome", key="reg_nome")
        reg_azienda = st.text_input("Azienda", key="reg_azienda")
        reg_tel = st.text_input("Telefono", key="reg_tel")
        reg_email = st.text_input("Email", key="reg_email")

        if st.button("GENERA ACCESSO CLIENTE"):
            utenti_now = carica_tutti_utenti()
            nuovo_user = genera_codice_progressivo("CLIENTE", utenti_now)
            nuova_pwd = genera_password()
            salva_utente_csv(
                nuovo_user,
                nuova_pwd,
                "CLIENTE",
                reg_nome,
                reg_azienda,
                reg_tel,
                reg_email,
                "35"
            )
            st.success("Accesso cliente creato.")
            st.code(f"Utente: {nuovo_user}\nPassword: {nuova_pwd}")

    try:
        ricarico_effettivo = float(str(dati_utente.get("ricarico", "")).replace(",", "."))
    except:
        ricarico_effettivo = ricarico_default(profilo)

    if profilo == "SA-TEC":
        ricarico_effettivo = 0.0

    return profilo, nome_utente, utente_codice, dati_utente, ricarico_effettivo

# =========================
# DISEGNI PORTE
# =========================

def mini_porta_html(ante):
    if ante == "1 anta":
        return """
        <svg width="120" height="120" viewBox="0 0 120 120">
        <rect x="18" y="18" width="84" height="10" fill="#d9d9d9" stroke="#111"/>
        <rect x="26" y="30" width="34" height="72" fill="#dcecff" stroke="#111" stroke-width="2"/>
        <rect x="60" y="30" width="34" height="72" fill="#fff" stroke="#111" stroke-width="2"/>
        <line x1="60" y1="30" x2="60" y2="102" stroke="#111" stroke-width="2"/>
        </svg>"""
    return """
    <svg width="120" height="120" viewBox="0 0 120 120">
    <rect x="18" y="18" width="84" height="10" fill="#d9d9d9" stroke="#111"/>
    <rect x="25" y="30" width="35" height="72" fill="#eef7ff" stroke="#111" stroke-width="2"/>
    <rect x="60" y="30" width="35" height="72" fill="#eef7ff" stroke="#111" stroke-width="2"/>
    <rect x="56" y="30" width="5" height="72" fill="#fff" stroke="#111"/>
    <rect x="61" y="30" width="5" height="72" fill="#fff" stroke="#111"/>
    </svg>"""

def render_choice_card(title, desc, ante, active):
    border = "#06499b" if active else "#d4dce8"
    bw = "4px" if active else "2px"
    bg = "#dcecff" if active else "#fff"
    components.html(f"""
    <div style="border:{bw} solid {border};background:{bg};border-radius:14px;text-align:center;padding:14px;min-height:242px;font-family:Arial;">
    <div style="font-size:19px;font-weight:900;color:#111;line-height:1.15;margin-bottom:6px;">{title}</div>
    <div>{mini_porta_html(ante)}</div>
    <div style="font-size:14px;line-height:1.28;color:#111;margin-top:4px;">{desc}</div>
    </div>""", height=260)

def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    blu = "#06499b"
    vetro_sel = "#d5eaff"
    vetro = "#fff"
    nero = "#111"
    mt = int(lunghezza_traversa * 1000)

    if ante == "1 anta":
        ante_svg = f"""
        <rect x="80" y="115" width="260" height="170" fill="{vetro_sel}" stroke="{nero}" stroke-width="4"/>
        <rect x="340" y="115" width="260" height="170" fill="{vetro}" stroke="{nero}" stroke-width="4"/>
        <line x1="340" y1="115" x2="340" y2="285" stroke="{nero}" stroke-width="6"/>"""
        titolo = "ANTE SELEZIONATA: 1 ANTA"
    else:
        ante_svg = f"""
        <rect x="80" y="115" width="260" height="170" fill="{vetro_sel}" stroke="{nero}" stroke-width="4"/>
        <rect x="340" y="115" width="260" height="170" fill="{vetro_sel}" stroke="{nero}" stroke-width="4"/>
        <rect x="328" y="115" width="10" height="170" fill="#fff" stroke="{nero}" stroke-width="3"/>
        <rect x="342" y="115" width="10" height="170" fill="#fff" stroke="{nero}" stroke-width="3"/>"""
        titolo = "ANTE SELEZIONATA: 2 ANTE"

    return f"""
    <div style="background:#fff;border:2px solid #b8d4f3;border-radius:12px;padding:10px;font-family:Arial;">
    <svg width="100%" height="390" viewBox="0 0 680 390">
    <text x="18" y="28" font-size="18" fill="{blu}" font-weight="900">{titolo}</text>
    <text x="340" y="58" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900">MISURA TRAVERSA CALCOLATA</text>
    <text x="340" y="84" text-anchor="middle" font-size="24" fill="{blu}" font-weight="900">{mt} mm</text>
    <line x1="80" y1="96" x2="600" y2="96" stroke="{blu}" stroke-width="3"/>
    <line x1="80" y1="84" x2="80" y2="108" stroke="{blu}" stroke-width="3"/>
    <line x1="600" y1="84" x2="600" y2="108" stroke="{blu}" stroke-width="3"/>
    <rect x="70" y="92" width="540" height="34" fill="#e9eef3" stroke="{nero}" stroke-width="2"/>
    <rect x="82" y="100" width="516" height="8" fill="#fff" opacity="0.45"/>
    <rect x="318" y="103" width="44" height="14" rx="3" fill="{nero}"/>
    {ante_svg}
    <line x1="145" y1="342" x2="535" y2="342" stroke="{blu}" stroke-width="3"/>
    <line x1="145" y1="330" x2="145" y2="354" stroke="{blu}" stroke-width="3"/>
    <line x1="535" y1="330" x2="535" y2="354" stroke="{blu}" stroke-width="3"/>
    <text x="340" y="370" text-anchor="middle" font-size="17" fill="{blu}" font-weight="900">LUCE PASSAGGIO {luce_mm} mm</text>
    <line x1="632" y1="115" x2="632" y2="285" stroke="{blu}" stroke-width="3"/>
    <line x1="620" y1="115" x2="644" y2="115" stroke="{blu}" stroke-width="3"/>
    <line x1="620" y1="285" x2="644" y2="285" stroke="{blu}" stroke-width="3"/>
    <text x="660" y="205" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900" transform="rotate(90 660,205)">H {altezza_mm} mm</text>
    </svg></div>"""

def aggiungi(articoli, codice, descrizione, descrizione_lunga, quantita=1, scontato=True):
    listino = LISTINI[codice]
    if scontato:
        prezzo_unitario = prezzo_vendita(listino)
        costo_unitario = costo_satec_reale(listino)
    else:
        prezzo_unitario = listino
        costo_unitario = listino

    articoli.append({
        "codice": codice,
        "descrizione": descrizione,
        "descrizione_lunga": descrizione_lunga,
        "quantita": quantita,
        "listino_unitario": listino,
        "costo_unitario_satec": costo_unitario,
        "prezzo_unitario": prezzo_unitario,
        "totale": prezzo_unitario * quantita,
        "costo_totale_satec": costo_unitario * quantita
    })

# =========================
# CSS
# =========================

st.markdown("""
<style>
.stApp {background:#f3f7fd;font-family:Arial,sans-serif;}
.main .block-container {padding-top:0rem;max-width:1550px;}
.header {background:linear-gradient(115deg,#fff 0%,#fff 28%,#073763 28%,#06499b 100%);border-bottom:5px solid #063b7a;padding:22px 32px;display:grid;grid-template-columns:28% 44% 28%;align-items:center;color:white;}
.logo-satec {width:300px;}
.header-title {text-align:center;}
.header-title h1 {font-size:42px;margin:0;font-weight:900;line-height:1.05;}
.header-title div {font-size:18px;margin-top:12px;font-weight:700;}
.header-info {font-size:15px;line-height:1.45;text-align:left;font-weight:700;}
.powercore {background:white;padding:18px 34px;display:grid;grid-template-columns:50% 50%;align-items:center;border-bottom:1px solid #bdd4ef;}
.powercore-title {font-size:34px;font-weight:900;color:#111;}
.powercore-title span {color:#ff7900;}
.powercore-sub {font-size:17px;color:#111;margin-top:8px;}
.sesamo-logo {height:115px;max-width:380px;object-fit:contain;}
.card,.side-card {background:white;border:1px solid #bdd4ef;border-radius:14px;padding:16px;margin-bottom:16px;}
.title-bar {display:inline-block;background:#06499b;color:white;padding:9px 16px;border-radius:8px;font-size:18px;font-weight:900;margin-bottom:16px;}
.section-row {display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px;}
.section-box {background:#eef6ff;border-radius:12px;padding:16px;color:#06499b;font-weight:800;font-size:16px;}
.section-box.green {background:#eefaf2;color:#0c7b3e;}
div[data-testid="stNumberInput"] label {color:#111!important;font-size:15px!important;font-weight:800!important;}
div[data-testid="stNumberInput"] input {border:2px solid #8998b0!important;border-radius:0!important;text-align:center!important;font-size:28px!important;font-weight:800!important;color:#06499b!important;height:54px!important;}
div[data-testid="stTextInput"] input {background:#ffffff!important;color:#06499b!important;border:2px solid #8998b0!important;border-radius:6px!important;font-weight:800!important;}
.measure-total {border:2px solid #bdd4ef;background:#f8fbff;border-radius:10px;padding:14px;display:grid;grid-template-columns:1fr 200px;align-items:center;color:#06499b;margin-top:10px;}
.measure-total .big {font-size:30px;font-weight:900;text-align:center;}
.measure-total .small {font-size:18px;font-weight:900;text-align:center;}
.option-box {border:2px solid #06499b;border-radius:12px;padding:18px;margin-bottom:18px;background:white;}
.option-title {font-size:20px;font-weight:900;color:#06499b;margin-bottom:12px;}
.option-note {border:2px solid #06499b;border-radius:12px;padding:13px;background:#eef6ff;color:#06499b;font-size:15px;font-weight:800;line-height:1.45;margin-top:12px;}
div[data-testid="stCheckbox"] {border:0;padding:0;margin:0;}
div[data-testid="stCheckbox"] label {color:#06499b!important;font-size:18px!important;font-weight:900!important;}
.price {text-align:center;color:#06499b;font-size:42px;font-weight:900;}
.price-label {color:#06499b;font-size:18px;font-weight:900;text-align:center;}
.vat-box {border:1px solid #bdd4ef;border-radius:10px;padding:14px;color:#06499b;font-size:17px;font-weight:800;background:#f8fbff;}
.power-side-title {color:#06499b;font-size:18px;font-weight:900;margin-bottom:12px;}
.power-side-text {font-size:15px;line-height:1.45;color:#111;}
.power-side-list li {margin-bottom:10px;color:#111;}
.desc-grid {display:grid;grid-template-columns:34% 33% 33%;gap:16px;color:#111;font-size:15px;}
.desc-title {color:#06499b;font-size:22px;font-weight:900;margin-bottom:10px;}
.footer {background:#06499b;color:white;padding:18px 34px;display:grid;grid-template-columns:1fr 1fr 1fr;font-size:16px;font-weight:700;margin-top:12px;}
.stButton>button {background:#06499b;color:white;border-radius:8px;height:48px;font-size:16px;font-weight:900;border:none;}
.stButton>button:hover {background:#073763;color:white;}
.admin-box {background:#ffffff;border:2px solid #06499b;border-radius:14px;padding:18px;margin-bottom:18px;}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

logo_satec64 = img_to_base64(["logo_satec.jpg", "logo_satec.png", "/mnt/data/logo_satec.jpg", "/mnt/data/logo_satec.png"])
logo_sesamo64 = img_to_base64(["SESAMO LOGO.png", "sesamo_logo.png", "logo_sesamo.png", "/mnt/data/SESAMO LOGO.png", "/mnt/data/sesamo_logo.png", "/mnt/data/logo_sesamo.png"])

logo_satec_html = f'<img class="logo-satec" src="data:image/jpeg;base64,{logo_satec64}">' if logo_satec64 else "<h1 style='color:#06499b'>SA-TEC</h1>"
sesamo_logo_html = f'<img class="sesamo-logo" src="data:image/png;base64,{logo_sesamo64}">' if logo_sesamo64 else """
<div style="display:flex;align-items:center;justify-content:center;gap:18px;">
<div style="background:#ff7900;color:white;font-size:44px;font-weight:900;padding:10px 18px;">▌</div>
<div><div style="font-size:48px;font-weight:900;color:#000;line-height:1;">SESAMO</div>
<div style="font-size:16px;font-weight:900;color:#000;letter-spacing:1px;">THE DOOR TECHNOLOGY</div></div>
</div>"""

st.markdown(f"""
<div class="header">
<div>{logo_satec_html}</div>
<div class="header-title"><h1>CONFIGURATORE<br>PORTE AUTOMATICHE</h1><div>TECNOLOGIA, SICUREZZA E SOLUZIONI SU MISURA</div></div>
<div class="header-info">SA-TEC S.R.L.s<br>Via L. Settembrini 84<br>88046 Lamezia Terme (CZ)<br>P.IVA 04009610793<br>☎ 0968-036797<br>✉ sacco.tecnologie@gmail.com<br>✉ sa-tec@pec.it</div>
</div>
<div class="powercore">
<div><div class="powercore-title">SESAMO <span>POWERCORE</span> PW100</div>
<div class="powercore-sub">Automazione lineare per porte scorrevoli automatiche,<br>affidabile, sicura e compatibile con la normativa EN16005.</div></div>
<div style="text-align:center;">{sesamo_logo_html}</div>
</div>
""", unsafe_allow_html=True)

profilo, nome_utente, utente_codice, dati_utente, ricarico_effettivo = login_box()
RICARICO_ATTIVO = ricarico_effettivo

# =========================
# ADMIN
# =========================

if profilo == "SA-TEC":
    st.sidebar.markdown("---")
    mostra_dashboard = st.sidebar.checkbox("Mostra dashboard SA-TEC", value=False)

    with st.sidebar.expander("Crea utente manuale"):
        utenti_now = carica_tutti_utenti()
        profilo_new = st.selectbox("Profilo nuovo utente", ["CLIENTE", "RIVENDITORE", "GROSSISTA"], key="admin_profilo_new")
        nome_new = st.text_input("Nome", key="admin_nome_new")
        azienda_new = st.text_input("Azienda", key="admin_azienda_new")
        telefono_new = st.text_input("Telefono", key="admin_tel_new")
        email_new = st.text_input("Email", key="admin_email_new")
        ricarico_new = st.number_input("Ricarico %", min_value=0.0, max_value=100.0, value=ricarico_default(profilo_new), step=1.0, key="admin_ricarico_new")
        if st.button("CREA UTENTE"):
            codice = genera_codice_progressivo(profilo_new, utenti_now)
            pwd = genera_password()
            salva_utente_csv(codice, pwd, profilo_new, nome_new, azienda_new, telefono_new, email_new, str(ricarico_new))
            st.success("Utente creato")
            st.code(f"Utente: {codice}\nPassword: {pwd}\nProfilo: {profilo_new}\nRicarico: {ricarico_new}%")

    if mostra_dashboard:
        st.markdown('<div class="admin-box"><h2 style="color:#06499b;">Dashboard SA-TEC</h2>', unsafe_allow_html=True)

        preventivi = carica_preventivi()
        utenti_csv = carica_utenti_csv()

        tab1, tab2 = st.tabs(["Preventivi", "Utenti creati"])

        with tab1:
            if not preventivi:
                st.info("Nessun preventivo salvato ancora.")
            else:
                st.write(f"Preventivi salvati: **{len(preventivi)}**")
                totale = 0.0
                for p in preventivi:
                    try:
                        totale += float(p.get("imponibile", 0))
                    except:
                        pass
                st.write(f"Valore totale IVA esclusa: **{euro(totale)}**")
                st.dataframe(dataframe_sicuro(preventivi), use_container_width=True)
                with open(PREVENTIVI_CSV, "rb") as f:
                    st.download_button("Scarica CSV preventivi", data=f, file_name="preventivi_satec.csv", mime="text/csv")

        with tab2:
            if not utenti_csv:
                st.info("Nessun utente creato da CSV.")
            else:
                righe = []
                for u, d in utenti_csv.items():
                    righe.append({
                        "Utente": u,
                        "Password": d["password"],
                        "Profilo": d["profilo"],
                        "Nome": d["nome"],
                        "Azienda": d["azienda"],
                        "Telefono": d["telefono"],
                        "Email": d["email"],
                        "Ricarico %": d.get("ricarico", ""),
                    })
                st.dataframe(dataframe_sicuro(righe), use_container_width=True)
                with open(UTENTI_CSV, "rb") as f:
                    st.download_button("Scarica CSV utenti", data=f, file_name="utenti_satec.csv", mime="text/csv")

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CONFIGURATORE
# =========================

if "scelta" not in st.session_state:
    st.session_state.scelta = "STANDARD 1 ANTA"

col_main, col_side = st.columns([0.69, 0.31], gap="large")

with col_main:
    st.markdown('<div class="card"><div class="title-bar">1&nbsp;&nbsp; SCEGLI LA PORTA AUTOMATICA</div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        if st.button("STANDARD 1 ANTA"):
            st.session_state.scelta = "STANDARD 1 ANTA"
    with b2:
        if st.button("STANDARD 2 ANTE"):
            st.session_state.scelta = "STANDARD 2 ANTE"
    with b3:
        if st.button("RIDONDANTE 1 ANTA"):
            st.session_state.scelta = "RIDONDANTE 1 ANTA"
    with b4:
        if st.button("RIDONDANTE 2 ANTE"):
            st.session_state.scelta = "RIDONDANTE 2 ANTE"

    scelta = st.session_state.scelta

    if scelta == "STANDARD 1 ANTA":
        tipo, ante = "Standard", "1 anta"
    elif scelta == "STANDARD 2 ANTE":
        tipo, ante = "Standard", "2 ante"
    elif scelta == "RIDONDANTE 1 ANTA":
        tipo, ante = "Ridondante", "1 anta"
    else:
        tipo, ante = "Ridondante", "2 ante"

    cards = [
        ("STANDARD<br>1 ANTA", "STANDARD 1 ANTA", "Porta automatica<br>lineare standard<br>a una anta", "1 anta"),
        ("STANDARD<br>2 ANTE", "STANDARD 2 ANTE", "Porta automatica<br>lineare standard<br>a due ante", "2 ante"),
        ("RIDONDANTE<br>1 ANTA", "RIDONDANTE 1 ANTA", "Automazione lineare<br>per via di fuga<br>a una anta", "1 anta"),
        ("RIDONDANTE<br>2 ANTE", "RIDONDANTE 2 ANTE", "Automazione lineare<br>per via di fuga<br>a due ante", "2 ante"),
    ]

    cols = st.columns(4)
    for c, (titolo, key, desc, ante_mini) in zip(cols, cards):
        with c:
            render_choice_card(titolo, desc, ante_mini, scelta == key)

    st.markdown("""
    <div class="section-row">
    <div class="section-box">CONFIGURAZIONE STANDARD<br><span style="font-weight:500;color:#111;">Sesamo PowerCore PW100 per porta scorrevole automatica lineare ad uso normale.</span></div>
    <div class="section-box green">CONFIGURAZIONE RIDONDANTE<br><span style="font-weight:500;color:#111;">Automazione ridondante per vie di fuga e uscite di emergenza.</span></div>
    </div></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="title-bar">2&nbsp;&nbsp; MISURE PORTA</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)

    with m1:
        luce_mm = st.number_input("LUCE PASSAGGIO IN MM", min_value=800, max_value=5000, value=1600, step=50)
    with m2:
        altezza_mm = st.number_input("ALTEZZA PASSAGGIO IN MM", min_value=1800, max_value=3000, value=2200, step=50)

    lunghezza_traversa = calcola_traversa(luce_mm, ante)
    components.html(disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa), height=430)

    st.markdown(f"""
    <div class="measure-total">
    <div><b>MISURA TRAVERSA CALCOLATA</b><br>1 anta = doppio luce + 10 cm<br>2 ante = doppio luce + 20 cm</div>
    <div><div class="big">{int(lunghezza_traversa*1000)} mm</div><div class="small">{lunghezza_traversa:.2f} metri</div></div>
    </div></div>
    """, unsafe_allow_html=True)

with col_side:
    st.markdown('<div class="side-card"><div class="title-bar">3&nbsp;&nbsp; ACCESSORI E SERVIZI</div>', unsafe_allow_html=True)

    st.markdown('<div class="option-box"><div class="option-title">ELETTROBLOCCO</div>', unsafe_allow_html=True)
    elettroblocco = st.checkbox("Aggiungi elettroblocco", value=True, key="elettro")
    st.markdown("</div>", unsafe_allow_html=True)

    prezzo_allaccio = LISTINI["ALLACCIO_COLLAUDO_STANDARD"] if tipo == "Standard" else LISTINI["ALLACCIO_COLLAUDO_RIDONDANTE"]
    testo_tipo_allaccio = "Standard" if tipo == "Standard" else "Ridondante"

    st.markdown('<div class="option-box"><div class="option-title">ALLACCIO E COLLAUDO</div>', unsafe_allow_html=True)
    allaccio = st.checkbox("Aggiungi allaccio e collaudo SA-TEC", value=True, key="allaccio")

    st.markdown(f"""
    <div class="option-note">
    Prezzo allaccio e collaudo {testo_tipo_allaccio}: <b>{euro(prezzo_allaccio)}</b> IVA esclusa.<br><br>
    <b>Vantaggi inclusi se il servizio è eseguito da SA-TEC</b><br><br>
    Scegliendo SA-TEC per l'allaccio e il collaudo, sono inclusi nel prezzo i seguenti benefici:<br><br>
    <b>Libretto di manutenzione:</b><br>Rilascio della documentazione ufficiale dell'apparecchio/impianto.<br><br>
    <b>Certificazione:</b><br>Rilascio delle certificazioni di conformità e corretta installazione a norma di legge.<br><br>
    <b>Assistenza prioritaria:</b><br>Garanzia di un intervento risolutivo in caso di guasti o problemi entro 48 ore.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

# =========================
# ARTICOLI
# =========================

articoli = []

aggiungi(articoli, "CASSA", "Profilo cassa traversa in alluminio", f"Profilo cassa traversa in alluminio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "COPERCHIO", "Coperchio traversa in alluminio", f"Coperchio traversa in alluminio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "GUARN_COPERCHIO", "Guarnizione coperchio", f"Guarnizione coperchio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)

aggiungi(
    articoli,
    "PF54_91_GUARN_ANTIVIBRAZIONE",
    "PF54.91 Guarnizione in gomma coperchio antivibrazione",
    f"PF54.91 Guarnizione in gomma coperchio antivibrazione calcolata su tutta la lunghezza della traversa ({lunghezza_traversa:.2f} m)",
    lunghezza_traversa
)

aggiungi(articoli, "CINGHIA", "Cinghia dentata", f"Cinghia dentata ({lunghezza_traversa*1.8:.2f} m)", lunghezza_traversa * 1.8)
aggiungi(articoli, "GUIDA", "Profilo guida scorrimento", f"Profilo guida scorrimento ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "GUARN_GUIDA", "Guarnizione guida", f"Guarnizione guida ({lunghezza_traversa:.2f} m)", lunghezza_traversa)

if tipo == "Standard":
    aggiungi(articoli, "PW100_1" if ante == "1 anta" else "PW100_2", f"Automazione Sesamo PowerCore PW100 {ante}", f"Automazione Sesamo PowerCore PW100 {ante}")
    aggiungi(articoli, "HR100", "2 × Hotron HR100 Radar apertura e sicurezza EN16005", "2 × Hotron HR100 Radar apertura e sicurezza EN16005", 2)
    aggiungi(articoli, "ICON", "PF37.00 ICON Selettore Touch con 3 Tag", "PF37.00 ICON Selettore Touch con 3 Tag")
    aggiungi(articoli, "BATTERIE", "PF54.73 Kit batterie", "PF54.73 Kit batterie")
    if elettroblocco:
        aggiungi(articoli, "ELETTRO_STANDARD", "PF54.59 Elettroblocco Standard", "PF54.59 Elettroblocco Standard")
else:
    aggiungi(articoli, "ER140_1" if ante == "1 anta" else "ER140_2", f"Automazione Sesamo ER140 Ridondante {ante}", f"Automazione Sesamo ER140 Ridondante {ante}")
    aggiungi(articoli, "SSR3_ER_BL", "Hotron SSR3-ER-BL Radar evacuazione", "Hotron SSR3-ER-BL Radar evacuazione")
    aggiungi(articoli, "HR100", "Hotron HR100 Radar apertura e sicurezza EN16005", "Hotron HR100 Radar apertura e sicurezza EN16005")
    aggiungi(articoli, "DIGIDOR", "PF37.06 DIGIDOR Selettore", "PF37.06 DIGIDOR Selettore")
    aggiungi(articoli, "BATTERIE", "PF54.73 Kit batterie", "PF54.73 Kit batterie")
    aggiungi(articoli, "PULSANTE_EMERGENZA", "Pulsante emergenza", "Pulsante emergenza")
    if elettroblocco:
        aggiungi(articoli, "ELETTRO_RIDONDANTE", "PF54.62 Elettroblocco Ridondante", "PF54.62 Elettroblocco Ridondante")

aggiungi(articoli, "ASSEMBLAGGIO", "Assemblaggio automatismo", "Assemblaggio completo automatismo presso officina SA-TEC - Franco deposito SA-TEC Lamezia Terme", 1, scontato=False)

if allaccio:
    if tipo == "Standard":
        aggiungi(articoli, "ALLACCIO_COLLAUDO_STANDARD", "Allaccio e collaudo SA-TEC Standard", "Allaccio e collaudo eseguito da SA-TEC su automazione standard. Comprende libretto di manutenzione, certificazione e assistenza prioritaria con intervento risolutivo entro 48 ore.", 1, scontato=False)
    else:
        aggiungi(articoli, "ALLACCIO_COLLAUDO_RIDONDANTE", "Allaccio e collaudo SA-TEC Ridondante", "Allaccio e collaudo eseguito da SA-TEC su automazione ridondante. Comprende libretto di manutenzione, certificazione e assistenza prioritaria con intervento risolutivo entro 48 ore.", 1, scontato=False)

imponibile = sum(a["totale"] for a in articoli)
costo_satec_totale = sum(a["costo_totale_satec"] for a in articoli)
utile_lordo = imponibile - costo_satec_totale
iva = imponibile * IVA
totale_iva = imponibile + iva

with col_side:
    st.markdown('<div class="side-card"><div class="title-bar">4&nbsp;&nbsp; RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="price-label">TOTALE IVA ESCLUSA</div>
    <div class="price">{euro(imponibile)}</div>
    <div class="vat-box">
    Profilo: <b>{PROFILI[profilo]}</b><br>
    IVA 22%: <span style="float:right;">{euro(iva)}</span><br>
    TOTALE IVA INCLUSA: <span style="float:right;">{euro(totale_iva)}</span><br><br>
    <b>Prezzo franco deposito SA-TEC Lamezia Terme</b>
    </div>
    """, unsafe_allow_html=True)

    if profilo == "SA-TEC":
        st.markdown(f"""
        <div class="vat-box" style="margin-top:12px;">
        Costo reale SA-TEC: <span style="float:right;">{euro(costo_satec_totale)}</span><br>
        Utile lordo: <span style="float:right;">{euro(utile_lordo)}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="side-card">
    <div class="power-side-title">SESAMO POWERCORE PW100</div>
    <div style="text-align:center;margin-bottom:14px;">{sesamo_logo_html}</div>
    <div class="power-side-text">
    PowerCore PW100 è l'automazione lineare Sesamo progettata per porte scorrevoli automatiche a 1 o 2 ante.<br><br>
    Affidabile, silenziosa e compatta, garantisce massima sicurezza e conformità alla normativa EN16005.
    </div>
    <ul class="power-side-list">
    <li>Tecnologia lineare ad alte prestazioni</li>
    <li>Movimento fluido e silenzioso</li>
    <li>Compatibile con sensori Sesamo e dispositivi di sicurezza</li>
    <li>Ideale per ambienti pubblici e privati</li>
    </ul></div>
    """, unsafe_allow_html=True)

# =========================
# DATI CLIENTE
# =========================

st.markdown('<div class="card"><div class="title-bar">5&nbsp;&nbsp; DATI CLIENTE E RICHIESTA</div>', unsafe_allow_html=True)

dc1, dc2, dc3, dc4 = st.columns(4)
with dc1:
    cliente_nome = st.text_input("Nome cliente", value=dati_utente.get("nome", ""))
with dc2:
    cliente_azienda = st.text_input("Azienda", value=dati_utente.get("azienda", ""))
with dc3:
    cliente_telefono = st.text_input("Telefono", value=dati_utente.get("telefono", ""))
with dc4:
    cliente_email = st.text_input("Email", value=dati_utente.get("email", ""))

if st.button("SALVA PREVENTIVO / RICHIESTA"):
    dati = {
        "data_ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "utente": utente_codice,
        "profilo": profilo,
        "cliente_nome": cliente_nome,
        "cliente_azienda": cliente_azienda,
        "cliente_telefono": cliente_telefono,
        "cliente_email": cliente_email,
        "configurazione": scelta,
        "luce_mm": luce_mm,
        "altezza_mm": altezza_mm,
        "traversa_m": f"{lunghezza_traversa:.2f}",
        "elettroblocco": "SI" if elettroblocco else "NO",
        "allaccio": "SI" if allaccio else "NO",
        "ricarico_percento": f"{ricarico_effettivo:.0f}",
        "imponibile": f"{imponibile:.2f}",
        "iva": f"{iva:.2f}",
        "totale_iva": f"{totale_iva:.2f}",
        "stato": "Nuovo"
    }
    salva_preventivo(dati)
    st.success("Preventivo salvato correttamente. SA-TEC lo vedrà nella dashboard.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DESCRIZIONE FORNITURA
# =========================

metà = len(articoli) // 2
lista_sx = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli[:metà]])
lista_dx = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli[metà:]])

st.markdown(f"""
<div class="card">
<div class="desc-title">DESCRIZIONE FORNITURA CLIENTE</div>
<div class="desc-grid">
<div>
<b>Profilo:</b> {PROFILI[profilo]}<br><br>
<b>Utente:</b> {utente_codice}<br><br>
<b>Configurazione selezionata:</b> {scelta}<br><br>
<b>Automazione:</b> SESAMO POWERCORE PW100<br><br>
<b>Luce passaggio:</b> {luce_mm} mm<br><br>
<b>Altezza passaggio:</b> {altezza_mm} mm<br><br>
<b>Misura traversa:</b> {lunghezza_traversa:.2f} metri<br><br>
<b>Resa:</b> Franco deposito SA-TEC Lamezia Terme
</div>
<div><ul>{lista_sx}</ul></div>
<div><ul>{lista_dx}</ul></div>
</div></div>
""", unsafe_allow_html=True)

if profilo == "SA-TEC":
    st.markdown('<div class="card"><div class="title-bar">DETTAGLIO INTERNO SA-TEC</div>', unsafe_allow_html=True)
    st.info(f"Ricarico applicato al profilo/utente: {ricarico_effettivo:.0f}%")
    tabella = []
    for a in articoli:
        tabella.append({
            "Codice": a["codice"],
            "Descrizione": a["descrizione"],
            "Q.tà": round(a["quantita"], 2),
            "Listino unit.": euro(a["listino_unitario"]),
            "Costo SA-TEC unit.": euro(a["costo_unitario_satec"]),
            "Prezzo unit.": euro(a["prezzo_unitario"]),
            "Totale vendita": euro(a["totale"]),
            "Costo totale": euro(a["costo_totale_satec"]),
        })
    st.dataframe(dataframe_sicuro(tabella), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# STAMPA / PDF HTML
# =========================

righe_descrizione = ""
for art in articoli:
    righe_descrizione += f"<tr><td>{art['descrizione']}</td><td>{art['descrizione_lunga']}</td></tr>"

logo_print = f'<img src="data:image/jpeg;base64,{logo_satec64}" style="width:240px;">' if logo_satec64 else f"<h1>{AZIENDA}</h1>"
sesamo_print = f'<img src="data:image/png;base64,{logo_sesamo64}" style="height:90px;">' if logo_sesamo64 else "<b>SESAMO POWERCORE PW100</b>"

html_stampa = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Preventivo SA-TEC</title>
<style>
body {{font-family:Arial,sans-serif;color:#18324f;margin:40px;}}
.header {{display:flex;justify-content:space-between;border-bottom:4px solid #06499b;padding-bottom:20px;margin-bottom:25px;}}
.company {{text-align:right;font-size:14px;line-height:1.5;}}
h1,h2 {{color:#06499b;}}
.box {{border:2px solid #d7e6f7;border-left:8px solid #06499b;border-radius:10px;padding:18px;margin-bottom:20px;}}
.brand {{display:flex;justify-content:space-between;align-items:center;border:2px solid #d7e6f7;border-radius:10px;padding:16px;margin-bottom:20px;}}
table {{width:100%;border-collapse:collapse;margin-top:15px;}}
th {{background:#06499b;color:white;padding:12px;text-align:left;}}
td {{border:1px solid #d7e6f7;padding:12px;vertical-align:top;}}
.total {{text-align:right;font-size:26px;font-weight:bold;color:#06499b;margin-top:25px;}}
.conditions {{margin-top:30px;font-size:15px;line-height:1.6;}}
.print-button {{background:#06499b;color:white;padding:14px 22px;border:none;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer;}}
@media print {{.print-button {{display:none;}}}}
</style>
</head>
<body>
<button class="print-button" onclick="window.print()">STAMPA / SALVA PDF</button>
<div class="header"><div>{logo_print}</div><div class="company"><b>{AZIENDA}</b><br>{SEDE}<br>{PIVA}<br>Tel. {TELEFONO}<br>Email: {EMAIL}<br>PEC: {PEC}</div></div>
<div class="brand"><div><h2 style="margin:0;">SESAMO POWERCORE PW100</h2><div>Configuratore porte automatiche lineari</div></div><div>{sesamo_print}</div></div>
<h1>Preventivo porta automatica</h1>
<div class="box">
<b>Data:</b> {date.today().strftime("%d/%m/%Y")}<br>
<b>Profilo:</b> {PROFILI[profilo]}<br>
<b>Utente:</b> {utente_codice}<br>
<b>Cliente:</b> {cliente_nome} - {cliente_azienda}<br>
<b>Configurazione:</b> {scelta}<br>
<b>Luce passaggio:</b> {luce_mm} mm<br>
<b>Altezza passaggio:</b> {altezza_mm} mm<br>
<b>Misura traversa:</b> {lunghezza_traversa:.2f} metri<br>
<b>Resa:</b> Franco deposito SA-TEC Lamezia Terme
</div>
<h2>Descrizione fornitura</h2>
<table><thead><tr><th>Voce</th><th>Descrizione</th></tr></thead><tbody>{righe_descrizione}</tbody></table>
<div class="total">Totale preventivo IVA esclusa: {euro(imponibile)}</div>
<div style="text-align:right;font-size:18px;margin-top:8px;">IVA 22%: {euro(iva)}<br>Totale IVA inclusa: {euro(totale_iva)}</div>
<div class="conditions">
<h2>Condizioni di pagamento</h2>
<p>Pagamento tramite bonifico bancario intestato a <b>{AZIENDA}</b>.<br>IBAN: <b>{IBAN}</b></p>
<p>Condizioni proposte: 50% all’ordine e saldo 50% prima della consegna o al collaudo.</p>
<p><b>Prezzi IVA esclusa. Merce resa franco deposito SA-TEC S.R.L.s - Lamezia Terme (CZ). Trasporto escluso salvo diversa indicazione.</b></p>
<p><b>Vantaggi inclusi se il servizio è eseguito da SA-TEC:</b><br>
Scegliendo SA-TEC per l'allaccio e il collaudo, sono inclusi nel prezzo i seguenti benefici:<br><br>
<b>Libretto di manutenzione:</b> rilascio della documentazione ufficiale dell'apparecchio/impianto.<br>
<b>Certificazione:</b> rilascio delle certificazioni di conformità e corretta installazione a norma di legge.<br>
<b>Assistenza prioritaria:</b> garanzia di un intervento risolutivo in caso di guasti o problemi entro 48 ore.</p>
<p>Preventivo indicativo soggetto a verifica tecnica e conferma definitiva SA-TEC S.R.L.s.</p>
<p>Validità offerta: 15 giorni.</p>
</div>
</body>
</html>
"""

html_js = json.dumps(html_stampa)

components.html(f"""
<div style="border:2px solid #06499b;border-radius:14px;padding:18px;background:#f8fbff;">
<button onclick="openPrint()" style="background:#06499b;color:white;border:none;padding:14px 22px;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;">
STAMPA / SALVA PDF
</button>
</div>
<script>
function openPrint() {{
const html = {html_js};
const win = window.open("", "_blank");
win.document.open();
win.document.write(html);
win.document.close();
}}
</script>
""", height=100)

st.markdown(f"""
<div class="footer">
<div>📍 {AZIENDA}<br>{SEDE}</div>
<div>☎ {TELEFONO}</div>
<div>✉ {EMAIL}</div>
</div>
""", unsafe_allow_html=True)
