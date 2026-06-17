import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from pathlib import Path
from datetime import date

st.set_page_config(
    page_title="Configuratore Porte Automatiche SA-TEC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# DATI AZIENDALI
# =========================

AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
PEC = "sa-tec@pec.it"
IBAN = "IT30S0825842841007000002877"
IVA = 0.22

# =========================
# FUNZIONI PREZZI
# =========================

def prezzo_cliente(listino):
    return listino * 0.50 * 0.95 * 1.35

def euro(valore):
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# LISTINI
# =========================

LISTINI = {
    "PW100_1": 1236.00,
    "PW100_2": 1298.00,

    "ER140_1": 2140.00,
    "ER140_2": 2200.00,

    "CASSA": 343.00 / 6.6,
    "COPERCHIO": 214.00 / 6.6,
    "GUARN_COPERCHIO": 134.00 / 35,
    "CINGHIA": 671.00 / 60,
    "GUIDA": 49.20 / 6.6,
    "GUARN_GUIDA": 66.00 / 30,

    "HR100": 135.00,
    "ICON": 114.00,
    "BATTERIE": 118.00,
    "ELETTRO_STANDARD": 195.00,

    "SSR3_ER_BL": 375.00,
    "DIGIDOR": 180.00,
    "PULSANTE_EMERGENZA": 130.00,
    "ELETTRO_RIDONDANTE": 290.00,

    "ALLACCIO_COLLAUDO": 350.00,
}

# =========================
# LOGHI
# =========================

def img_to_base64(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

LOGO_SATEC = "logo_satec.jpg"
LOGO_SESAMO = "SESAMO LOGO.png"

logo_satec64 = img_to_base64(LOGO_SATEC)
logo_sesamo64 = img_to_base64(LOGO_SESAMO)

# =========================
# FUNZIONI CALCOLO
# =========================

def calcola_traversa(luce_mm, ante):
    if ante == "1 anta":
        return ((luce_mm * 2) + 100) / 1000
    return (luce_mm + 100) / 1000

def aggiungi(articoli, codice, descrizione, descrizione_lunga, quantita=1, scontato=True):
    prezzo = prezzo_cliente(LISTINI[codice]) if scontato else LISTINI[codice]
    articoli.append({
        "codice": codice,
        "descrizione": descrizione,
        "descrizione_lunga": descrizione_lunga,
        "quantita": quantita,
        "totale": prezzo * quantita
    })

# =========================
# DISEGNO PORTA
# =========================

def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    blu = "#06499b"
    blu_scuro = "#073763"
    vetro = "#eef7ff"
    vetro2 = "#e2f1ff"
    nero = "#111111"
    grigio = "#d8dde4"

    misura_traversa = int(lunghezza_traversa * 1000)

    if ante == "1 anta":
        return f"""
        <div style="background:white;border:2px solid #d7e6f7;border-radius:18px;padding:12px;">
        <svg width="100%" height="430" viewBox="0 0 900 430">

            <text x="450" y="35" text-anchor="middle" font-size="25" fill="{blu}" font-weight="900">
                MISURA TRAVERSA CALCOLATA
            </text>
            <text x="450" y="65" text-anchor="middle" font-size="18" fill="{blu}">
                Calcolo automatico in base alla luce passaggio.
            </text>
            <text x="450" y="108" text-anchor="middle" font-size="42" fill="{blu}" font-weight="900">
                {misura_traversa} mm
            </text>

            <line x1="90" y1="130" x2="810" y2="130" stroke="{blu}" stroke-width="4"/>
            <line x1="90" y1="116" x2="90" y2="144" stroke="{blu}" stroke-width="4"/>
            <line x1="810" y1="116" x2="810" y2="144" stroke="{blu}" stroke-width="4"/>

            <rect x="100" y="155" width="700" height="48" fill="#f1f3f5" stroke="{nero}" stroke-width="3"/>
            <rect x="110" y="164" width="680" height="10" fill="#ffffff" opacity="0.45"/>
            <rect x="430" y="170" width="44" height="20" rx="3" fill="{nero}"/>

            <rect x="145" y="205" width="610" height="205" fill="#ffffff" stroke="{nero}" stroke-width="5"/>

            <rect x="160" y="220" width="290" height="175" fill="{vetro}" stroke="{nero}" stroke-width="4"/>
            <rect x="450" y="220" width="290" height="175" fill="#ffffff" stroke="{nero}" stroke-width="4"/>

            <line x1="450" y1="220" x2="450" y2="395" stroke="{nero}" stroke-width="7"/>

            <path d="M265 307 L395 307" stroke="{blu}" stroke-width="8" marker-end="url(#arrow1)"/>

            <line x1="205" y1="420" x2="555" y2="420" stroke="{blu}" stroke-width="4"/>
            <line x1="205" y1="405" x2="205" y2="430" stroke="{blu}" stroke-width="4"/>
            <line x1="555" y1="405" x2="555" y2="430" stroke="{blu}" stroke-width="4"/>

            <text x="380" y="390" text-anchor="middle" font-size="22" fill="{blu}" font-weight="900">
                LUCE PASSAGGIO {luce_mm} mm
            </text>

            <line x1="820" y1="205" x2="820" y2="410" stroke="{blu}" stroke-width="4"/>
            <line x1="805" y1="205" x2="835" y2="205" stroke="{blu}" stroke-width="4"/>
            <line x1="805" y1="410" x2="835" y2="410" stroke="{blu}" stroke-width="4"/>
            <text x="860" y="310" text-anchor="middle" font-size="20" fill="{blu}" font-weight="900" transform="rotate(90 860,310)">
                H {altezza_mm} mm
            </text>

            <text x="450" y="382" text-anchor="middle" font-size="23" fill="{blu}" font-weight="900">
                SCORRIMENTO LINEARE 1 ANTA
            </text>

            <defs>
                <marker id="arrow1" markerWidth="14" markerHeight="14" refX="7" refY="4" orient="auto">
                    <path d="M0,0 L0,8 L9,4 z" fill="{blu}"/>
                </marker>
            </defs>

        </svg>
        </div>
        """

    return f"""
    <div style="background:white;border:2px solid #d7e6f7;border-radius:18px;padding:12px;">
    <svg width="100%" height="430" viewBox="0 0 900 430">

        <text x="450" y="35" text-anchor="middle" font-size="25" fill="{blu}" font-weight="900">
            MISURA TRAVERSA CALCOLATA
        </text>
        <text x="450" y="65" text-anchor="middle" font-size="18" fill="{blu}">
            Calcolo automatico in base alla luce passaggio.
        </text>
        <text x="450" y="108" text-anchor="middle" font-size="42" fill="{blu}" font-weight="900">
            {misura_traversa} mm
        </text>

        <line x1="90" y1="130" x2="810" y2="130" stroke="{blu}" stroke-width="4"/>
        <line x1="90" y1="116" x2="90" y2="144" stroke="{blu}" stroke-width="4"/>
        <line x1="810" y1="116" x2="810" y2="144" stroke="{blu}" stroke-width="4"/>

        <rect x="100" y="155" width="700" height="48" fill="#f1f3f5" stroke="{nero}" stroke-width="3"/>
        <rect x="110" y="164" width="680" height="10" fill="#ffffff" opacity="0.45"/>
        <rect x="430" y="170" width="44" height="20" rx="3" fill="{nero}"/>

        <rect x="145" y="205" width="610" height="205" fill="#ffffff" stroke="{nero}" stroke-width="5"/>

        <rect x="160" y="220" width="295" height="175" fill="{vetro}" stroke="{nero}" stroke-width="4"/>
        <rect x="445" y="220" width="295" height="175" fill="{vetro2}" stroke="{nero}" stroke-width="4"/>

        <rect x="435" y="220" width="12" height="175" fill="#ffffff" stroke="{nero}" stroke-width="4"/>
        <rect x="453" y="220" width="12" height="175" fill="#ffffff" stroke="{nero}" stroke-width="4"/>

        <path d="M370 307 L240 307" stroke="{blu}" stroke-width="8" marker-end="url(#arrowL)"/>
        <path d="M530 307 L660 307" stroke="{blu}" stroke-width="8" marker-end="url(#arrowR)"/>

        <line x1="205" y1="420" x2="695" y2="420" stroke="{blu}" stroke-width="4"/>
        <line x1="205" y1="405" x2="205" y2="430" stroke="{blu}" stroke-width="4"/>
        <line x1="695" y1="405" x2="695" y2="430" stroke="{blu}" stroke-width="4"/>

        <text x="450" y="390" text-anchor="middle" font-size="22" fill="{blu}" font-weight="900">
            LUCE PASSAGGIO {luce_mm} mm
        </text>

        <line x1="820" y1="205" x2="820" y2="410" stroke="{blu}" stroke-width="4"/>
        <line x1="805" y1="205" x2="835" y2="205" stroke="{blu}" stroke-width="4"/>
        <line x1="805" y1="410" x2="835" y2="410" stroke="{blu}" stroke-width="4"/>
        <text x="860" y="310" text-anchor="middle" font-size="20" fill="{blu}" font-weight="900" transform="rotate(90 860,310)">
            H {altezza_mm} mm
        </text>

        <text x="450" y="382" text-anchor="middle" font-size="23" fill="{blu}" font-weight="900">
            SCORRIMENTO LINEARE 2 ANTE
        </text>

        <defs>
            <marker id="arrowR" markerWidth="14" markerHeight="14" refX="7" refY="4" orient="auto">
                <path d="M0,0 L0,8 L9,4 z" fill="{blu}"/>
            </marker>
            <marker id="arrowL" markerWidth="14" markerHeight="14" refX="2" refY="4" orient="auto">
                <path d="M9,0 L9,8 L0,4 z" fill="{blu}"/>
            </marker>
        </defs>

    </svg>
    </div>
    """

# =========================
# CSS
# =========================

st.markdown("""
<style>
.stApp {background:#f3f7fd;font-family:Arial,sans-serif;}
.main .block-container {padding-top:0rem;max-width:1500px;}

.hero {
    display:flex;
    align-items:center;
    justify-content:space-between;
    background:linear-gradient(120deg,#ffffff 0%,#ffffff 28%,#073763 28%,#06499b 100%);
    border-radius:0 0 22px 22px;
    padding:25px 35px;
    margin-bottom:25px;
    box-shadow:0 8px 24px rgba(6,73,155,.20);
}

.hero-logo {width:310px;background:white;}
.hero-title {color:white;padding-left:35px;flex:1;}
.hero-title h1 {font-size:42px;margin:0;font-weight:900;}
.hero-title h3 {font-size:21px;margin-top:10px;font-weight:400;}
.top-icons {color:white;display:flex;gap:30px;text-align:center;font-weight:700;font-size:14px;}

.card {
    background:white;
    border-radius:18px;
    padding:26px;
    margin-bottom:20px;
    box-shadow:0 5px 18px rgba(6,73,155,.10);
    border:1px solid #d7e6f7;
}

.card-title {
    color:#06499b;
    font-size:23px;
    font-weight:900;
    margin-bottom:18px;
    border-bottom:1px solid #d7e6f7;
    padding-bottom:12px;
}

.choice-card {
    border-radius:18px;
    padding:24px;
    border:2px solid #bdd4ef;
    background:#f8fbff;
    text-align:center;
    min-height:150px;
}

.choice-card-active {
    border:4px solid #06499b;
    background:#eaf4ff;
    box-shadow:0 5px 18px rgba(6,73,155,.22);
}

.choice-title {color:#06499b;font-size:22px;font-weight:900;margin-bottom:10px;}
.choice-subtitle {color:#18324f;font-size:16px;line-height:1.45;}

.section-standard,.section-ridondante {
    background:#eef6ff;
    border-left:6px solid #06499b;
    padding:22px;
    border-radius:14px;
    margin-top:18px;
    color:#18324f;
    font-size:18px;
    line-height:1.6;
}

.info-box {
    background:linear-gradient(90deg,#eef6ff,#ffffff);
    border-radius:14px;
    padding:22px;
    margin-top:18px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    border:2px solid #bdd4ef;
    border-left:7px solid #06499b;
    color:#06499b;
}

.info-box b {
    color:#06499b;
    font-size:20px;
    font-weight:900;
}

.info-box div {
    color:#06499b;
    font-size:17px;
    font-weight:700;
}

.info-box strong {
    color:#06499b;
    font-size:34px;
    font-weight:900;
}

.desc-box {
    background:#ffffff;
    border:2px solid #d7e6f7;
    border-left:7px solid #06499b;
    border-radius:12px;
    padding:20px;
    margin-bottom:14px;
    color:#18324f;
}

.desc-title {font-weight:900;color:#06499b;font-size:20px;margin-bottom:10px;}
.desc-text {font-size:18px;line-height:1.65;color:#18324f;}

.summary-price {
    color:#06499b;
    font-size:42px;
    font-weight:900;
    text-align:right;
}

.green-box {
    background:#eefaf2;
    border:1px solid #b9e6c7;
    color:#0c7b3e;
    padding:20px;
    border-radius:12px;
    margin-top:18px;
    font-size:17px;
    line-height:1.5;
}

.blue-box {
    background:#eef6ff;
    border:1px solid #bdd4ef;
    color:#06499b;
    padding:18px;
    border-radius:12px;
    margin-top:18px;
    font-size:17px;
    line-height:1.5;
}

.accessory-box {
    border:2px solid #06499b;
    background:#f8fbff;
    border-radius:14px;
    padding:18px;
    margin-bottom:16px;
    color:#06499b;
    font-size:20px;
    font-weight:900;
}

.brand-box {
    border:2px solid #d7e6f7;
    background:#ffffff;
    border-radius:16px;
    padding:18px;
    margin-bottom:18px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
}

.brand-title {
    color:#06499b;
    font-size:24px;
    font-weight:900;
}

.brand-subtitle {
    color:#18324f;
    font-size:17px;
    font-weight:700;
}

.footer {
    background:#073763;
    color:white;
    padding:18px 30px;
    border-radius:14px 14px 0 0;
    margin-top:20px;
    display:flex;
    justify-content:space-between;
    font-weight:600;
}

.stButton>button {
    background:#06499b;
    color:white;
    border-radius:12px;
    height:56px;
    font-size:18px;
    font-weight:900;
    border:none;
    width:100%;
}

.stButton>button:hover {background:#073763;color:white;}

div[data-testid="stNumberInput"] label {
    color:#06499b!important;
    font-size:18px!important;
    font-weight:900!important;
}

div[data-testid="stNumberInput"] input {
    border:2px solid #06499b!important;
    border-radius:12px!important;
    font-size:24px!important;
    font-weight:900!important;
    color:#073763!important;
    background:#ffffff!important;
    height:52px!important;
}

div[data-testid="stCheckbox"] label {
    border:2px solid #06499b;
    background:#f8fbff;
    border-radius:14px;
    padding:14px 16px;
    width:100%;
    font-size:18px;
    font-weight:900;
    color:#06499b;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

if logo_satec64:
    logo_satec_html = f'<img class="hero-logo" src="data:image/jpeg;base64,{logo_satec64}">'
else:
    logo_satec_html = "<h1 style='color:#06499b;background:white;padding:20px;'>SA-TEC</h1>"

st.markdown(f"""
<div class="hero">
    <div>{logo_satec_html}</div>
    <div class="hero-title">
        <h1>CONFIGURATORE<br>PORTE AUTOMATICHE</h1>
        <h3>SESAMO POWERCORE PW100</h3>
    </div>
    <div class="top-icons">
        <div>🛡️<br>EN16005</div>
        <div>🚪<br>1 O 2 ANTE</div>
        <div>⚙️<br>SU MISURA</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# BRAND SESAMO
# =========================

sesamo_img_html = ""
if logo_sesamo64:
    sesamo_img_html = f'<img src="data:image/png;base64,{logo_sesamo64}" style="height:80px;">'

st.markdown(f"""
<div class="brand-box">
    <div>
        <div class="brand-title">SESAMO POWERCORE PW100</div>
        <div class="brand-subtitle">
            Automazione lineare per porte scorrevoli automatiche, configurata su misura.
        </div>
    </div>
    <div>{sesamo_img_html}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# SCELTA PORTA
# =========================

st.markdown('<div class="card"><div class="card-title">1️⃣ SCEGLI LA PORTA AUTOMATICA</div>', unsafe_allow_html=True)

if "scelta" not in st.session_state:
    st.session_state.scelta = "STANDARD 1 ANTA"

c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("STANDARD 1 ANTA"):
        st.session_state.scelta = "STANDARD 1 ANTA"

with c2:
    if st.button("STANDARD 2 ANTE"):
        st.session_state.scelta = "STANDARD 2 ANTE"

with c3:
    if st.button("RIDONDANTE 1 ANTA"):
        st.session_state.scelta = "RIDONDANTE 1 ANTA"

with c4:
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
    ("STANDARD 1 ANTA", "Porta automatica lineare standard a una anta"),
    ("STANDARD 2 ANTE", "Porta automatica lineare standard a due ante"),
    ("RIDONDANTE 1 ANTA", "Automazione lineare per via di fuga a una anta"),
    ("RIDONDANTE 2 ANTE", "Automazione lineare per via di fuga a due ante"),
]

cc = st.columns(4)

for col, (titolo, sottotitolo) in zip(cc, cards):
    active = "choice-card-active" if scelta == titolo else ""
    with col:
        st.markdown(f"""
        <div class="choice-card {active}">
            <div class="choice-title">{titolo}</div>
            <div class="choice-subtitle">{sottotitolo}</div>
        </div>
        """, unsafe_allow_html=True)

if tipo == "Standard":
    st.markdown("""
    <div class="section-standard">
        <h3 style="margin:0 0 8px 0;color:#06499b;">CONFIGURAZIONE STANDARD</h3>
        Sesamo PowerCore PW100 per porta scorrevole automatica lineare ad uso normale.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="section-ridondante">
        <h3 style="margin:0 0 8px 0;color:#06499b;">CONFIGURAZIONE RIDONDANTE</h3>
        Automazione ridondante per vie di fuga e uscite di emergenza.
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# MISURE E ACCESSORI
# =========================

col_left, col_right = st.columns([2, 1.05], gap="large")

with col_left:
    st.markdown('<div class="card"><div class="card-title">2️⃣ MISURE PORTA</div>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)

    with m1:
        luce_mm = st.number_input(
            "LUCE PASSAGGIO IN MM",
            min_value=800,
            max_value=5000,
            value=1600,
            step=50
        )

    with m2:
        altezza_mm = st.number_input(
            "ALTEZZA PASSAGGIO IN MM",
            min_value=1800,
            max_value=3000,
            value=2200,
            step=50
        )

    lunghezza_traversa = calcola_traversa(luce_mm, ante)

    components.html(
        disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa),
        height=460
    )

    st.markdown(f"""
    <div class="info-box">
        <div>
            <b>MISURA TRAVERSA CALCOLATA</b><br>
            Calcolo automatico in base alla luce passaggio.
        </div>
        <div style="text-align:right;">
            <strong>{int(lunghezza_traversa * 1000)} mm</strong><br>
            <b>{lunghezza_traversa:.2f} metri</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card"><div class="card-title">3️⃣ ACCESSORI E SERVIZI</div>', unsafe_allow_html=True)

    st.markdown('<div class="accessory-box">ELETTROBLOCCO</div>', unsafe_allow_html=True)
    elettroblocco = st.checkbox("Aggiungi elettroblocco", value=False)

    st.markdown('<div class="accessory-box">ALLACCIO E COLLAUDO</div>', unsafe_allow_html=True)
    allaccio = st.checkbox("Aggiungi allaccio e collaudo SA-TEC", value=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CALCOLO ARTICOLI
# =========================

articoli = []

aggiungi(
    articoli,
    "CASSA",
    "Profilo cassa traversa in alluminio",
    "Profilo principale della traversa tagliato su misura.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "COPERCHIO",
    "Coperchio traversa in alluminio",
    "Coperchio frontale della traversa.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "GUARN_COPERCHIO",
    "Guarnizione coperchio",
    "Guarnizione tecnica di finitura.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "CINGHIA",
    "Cinghia dentata",
    "Cinghia dentata di trasmissione.",
    lunghezza_traversa * 1.8
)

aggiungi(
    articoli,
    "GUIDA",
    "Profilo guida scorrimento",
    "Profilo guida per scorrimento.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "GUARN_GUIDA",
    "Guarnizione guida",
    "Guarnizione tecnica guida.",
    lunghezza_traversa
)

if tipo == "Standard":
    aggiungi(
        articoli,
        "PW100_1" if ante == "1 anta" else "PW100_2",
        f"Sesamo PowerCore PW100 {ante}",
        "Automazione lineare per porta scorrevole automatica standard."
    )

    aggiungi(
        articoli,
        "HR100",
        "2 × Hotron HR100 Radar apertura e sicurezza EN16005",
        "Sensori radar interno ed esterno per apertura e sicurezza del passaggio.",
        2
    )

    aggiungi(
        articoli,
        "ICON",
        "PF37.00 ICON Selettore Touch con 3 Tag",
        "Selettore funzioni touch per gestione modalità porta."
    )

    aggiungi(
        articoli,
        "BATTERIE",
        "PF54.73 Kit batterie",
        "Kit batterie con scheda controllo e ricarica."
    )

    if elettroblocco:
        aggiungi(
            articoli,
            "ELETTRO_STANDARD",
            "PF54.59 Elettroblocco Standard",
            "Elettroblocco standard per chiusura automatica."
        )

else:
    aggiungi(
        articoli,
        "ER140_1" if ante == "1 anta" else "ER140_2",
        f"Automazione Sesamo ER140 Ridondante {ante}",
        "Automazione ridondante per vie di fuga."
    )

    aggiungi(
        articoli,
        "SSR3_ER_BL",
        "Hotron SSR3-ER-BL Radar evacuazione",
        "Radar evacuazione per sistema ridondante."
    )

    aggiungi(
        articoli,
        "HR100",
        "Hotron HR100 Radar apertura e sicurezza EN16005",
        "Radar apertura e sicurezza."
    )

    aggiungi(
        articoli,
        "DIGIDOR",
        "PF37.06 DIGIDOR Selettore",
        "Selettore dedicato per automazione ridondante."
    )

    aggiungi(
        articoli,
        "BATTERIE",
        "PF54.73 Kit batterie",
        "Kit batterie con scheda controllo e ricarica."
    )

    aggiungi(
        articoli,
        "PULSANTE_EMERGENZA",
        "Pulsante emergenza",
        "Pulsante emergenza per gestione sicurezza."
    )

    if elettroblocco:
        aggiungi(
            articoli,
            "ELETTRO_RIDONDANTE",
            "PF54.62 Elettroblocco Ridondante",
            "Elettroblocco ridondante."
        )

if allaccio:
    aggiungi(
        articoli,
        "ALLACCIO_COLLAUDO",
        "Allaccio e collaudo SA-TEC",
        "Collegamento, regolazione e collaudo finale.",
        1,
        scontato=False
    )

imponibile = sum(a["totale"] for a in articoli)
iva = imponibile * IVA
totale_iva = imponibile + iva

# =========================
# RIEPILOGO
# =========================

with col_right:
    st.markdown('<div class="card"><div class="card-title">4️⃣ RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <b style="color:#06499b;font-size:20px;">TOTALE IVA ESCLUSA</b>
    <div class="summary-price">{euro(imponibile)}</div>
    <div class="blue-box">
        IVA 22%: <b>{euro(iva)}</b><br>
        Totale IVA inclusa: <b>{euro(totale_iva)}</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DESCRIZIONE CLIENTE
# =========================

st.markdown('<div class="card"><div class="card-title">📌 DESCRIZIONE FORNITURA CLIENTE</div>', unsafe_allow_html=True)

st.write(f"Configurazione: **{scelta}**")
st.write(f"Automazione: **Sesamo PowerCore PW100**" if tipo == "Standard" else "Automazione: **Sesamo Ridondante**")
st.write(f"Luce passaggio: **{luce_mm} mm**")
st.write(f"Altezza passaggio: **{altezza_mm} mm**")
st.write(f"Misura traversa: **{lunghezza_traversa:.2f} metri**")

for art in articoli:
    st.markdown(f"""
    <div class="desc-box">
        <div class="desc-title">{art['descrizione']}</div>
        <div class="desc-text">{art['descrizione_lunga']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# STAMPA HTML
# =========================

righe_descrizione = ""
for art in articoli:
    righe_descrizione += f"<tr><td>{art['descrizione']}</td><td>{art['descrizione_lunga']}</td></tr>"

logo_print = f'<img src="data:image/jpeg;base64,{logo_satec64}" style="width:240px;">' if logo_satec64 else f"<h1>{AZIENDA}</h1>"
sesamo_print = f'<img src="data:image/png;base64,{logo_sesamo64}" style="height:70px;">' if logo_sesamo64 else ""

html_stampa = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Preventivo SA-TEC</title>
<style>
body {{
    font-family: Arial, sans-serif;
    color: #18324f;
    margin: 40px;
}}
.header {{
    display: flex;
    justify-content: space-between;
    border-bottom: 4px solid #06499b;
    padding-bottom: 20px;
    margin-bottom: 25px;
}}
.company {{
    text-align: right;
    font-size: 14px;
    line-height: 1.5;
}}
h1, h2 {{
    color: #06499b;
}}
.box {{
    border: 2px solid #d7e6f7;
    border-left: 8px solid #06499b;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 20px;
}}
.brand {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    border:2px solid #d7e6f7;
    border-radius:10px;
    padding:16px;
    margin-bottom:20px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}}
th {{
    background: #06499b;
    color: white;
    padding: 12px;
    text-align: left;
}}
td {{
    border: 1px solid #d7e6f7;
    padding: 12px;
    vertical-align: top;
}}
.total {{
    text-align: right;
    font-size: 26px;
    font-weight: bold;
    color: #06499b;
    margin-top: 25px;
}}
.conditions {{
    margin-top: 30px;
    font-size: 15px;
    line-height: 1.6;
}}
.print-button {{
    background: #06499b;
    color: white;
    padding: 14px 22px;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
}}
@media print {{
    .print-button {{
        display: none;
    }}
}}
</style>
</head>
<body>
<button class="print-button" onclick="window.print()">STAMPA / SALVA PDF</button>

<div class="header">
    <div>{logo_print}</div>
    <div class="company">
        <b>{AZIENDA}</b><br>
        {SEDE}<br>
        {PIVA}<br>
        Tel. {TELEFONO}<br>
        Email: {EMAIL}<br>
        PEC: {PEC}
    </div>
</div>

<div class="brand">
    <div>
        <h2 style="margin:0;">SESAMO POWERCORE PW100</h2>
        <div>Configuratore porte automatiche lineari</div>
    </div>
    <div>{sesamo_print}</div>
</div>

<h1>Preventivo porta automatica</h1>

<div class="box">
    <b>Data:</b> {date.today().strftime("%d/%m/%Y")}<br>
    <b>Configurazione:</b> {scelta}<br>
    <b>Luce passaggio:</b> {luce_mm} mm<br>
    <b>Altezza passaggio:</b> {altezza_mm} mm<br>
    <b>Misura traversa:</b> {lunghezza_traversa:.2f} metri
</div>

<h2>Descrizione fornitura</h2>
<table>
<thead>
<tr>
<th>Voce</th>
<th>Descrizione</th>
</tr>
</thead>
<tbody>
{righe_descrizione}
</tbody>
</table>

<div class="total">
    Totale preventivo IVA esclusa: {euro(imponibile)}
</div>

<div style="text-align:right;font-size:18px;margin-top:8px;">
    IVA 22%: {euro(iva)}<br>
    Totale IVA inclusa: {euro(totale_iva)}
</div>

<div class="conditions">
<h2>Condizioni di pagamento</h2>
<p>
Pagamento tramite bonifico bancario intestato a <b>{AZIENDA}</b>.<br>
IBAN: <b>{IBAN}</b>
</p>
<p>
Condizioni proposte: 50% all’ordine e saldo 50% prima della consegna o al collaudo.
</p>
<p>
Preventivo indicativo soggetto a verifica tecnica e conferma definitiva SA-TEC S.R.L.s.
</p>
<p>
Validità offerta: 15 giorni.
</p>
</div>

</body>
</html>
"""

st.markdown('<div class="card"><div class="card-title">🖨️ STAMPA PREVENTIVO</div>', unsafe_allow_html=True)

st.download_button(
    label="SCARICA PREVENTIVO STAMPABILE HTML",
    data=html_stampa,
    file_name="Preventivo_SA_TEC.html",
    mime="text/html"
)

html_js = json.dumps(html_stampa)

components.html(f"""
<div style="border:2px solid #06499b;border-radius:14px;padding:18px;background:#f8fbff;">
<h3 style="color:#06499b;margin-top:0;">Stampa preventivo</h3>
<button onclick="openPrint()" style="
    background:#06499b;
    color:white;
    border:none;
    padding:14px 22px;
    border-radius:10px;
    font-size:18px;
    font-weight:bold;
    cursor:pointer;
">
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
""", height=150)

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# FOOTER
# =========================

st.markdown(f"""
<div class="footer">
    <div>{AZIENDA}</div>
    <div>Lamezia Terme (CZ)</div>
    <div>{TELEFONO}</div>
    <div>{EMAIL}</div>
</div>
""", unsafe_allow_html=True)
