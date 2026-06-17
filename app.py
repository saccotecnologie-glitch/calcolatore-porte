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

AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
PEC = "sa-tec@pec.it"
IBAN = "IT30S0825842841007000002877"
IVA = 0.22

def prezzo_cliente(listino):
    return listino * 0.50 * 0.95 * 1.35

def euro(valore):
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

def img_to_base64(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_satec64 = img_to_base64("logo_satec.jpg")
logo_sesamo64 = img_to_base64("SESAMO LOGO.png")

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

def mini_porta(ante):
    if ante == "1 anta":
        return """
        <svg width="120" height="120" viewBox="0 0 120 120">
            <rect x="20" y="18" width="80" height="10" fill="#d9d9d9" stroke="#111"/>
            <rect x="25" y="30" width="70" height="70" fill="#f7fbff" stroke="#111" stroke-width="2"/>
            <line x1="60" y1="30" x2="60" y2="100" stroke="#111" stroke-width="2"/>
            <path d="M43 65 L67 65" stroke="#111" stroke-width="3" marker-end="url(#m1)"/>
            <defs><marker id="m1" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#111"/></marker></defs>
        </svg>
        """
    return """
    <svg width="120" height="120" viewBox="0 0 120 120">
        <rect x="20" y="18" width="80" height="10" fill="#d9d9d9" stroke="#111"/>
        <rect x="25" y="30" width="70" height="70" fill="#f7fbff" stroke="#111" stroke-width="2"/>
        <line x1="60" y1="30" x2="60" y2="100" stroke="#111" stroke-width="2"/>
        <path d="M55 65 L35 65" stroke="#111" stroke-width="3" marker-end="url(#ml)"/>
        <path d="M65 65 L85 65" stroke="#111" stroke-width="3" marker-end="url(#mr)"/>
        <defs>
            <marker id="mr" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#111"/></marker>
            <marker id="ml" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto"><path d="M6,0 L6,6 L0,3 z" fill="#111"/></marker>
        </defs>
    </svg>
    """

def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    blu = "#06499b"
    blu_scuro = "#073763"
    vetro = "#eef7ff"
    vetro2 = "#e2f1ff"
    nero = "#111111"
    misura_traversa = int(lunghezza_traversa * 1000)

    if ante == "1 anta":
        ante_svg = f"""
        <rect x="75" y="110" width="250" height="175" fill="{vetro}" stroke="{nero}" stroke-width="4"/>
        <rect x="325" y="110" width="250" height="175" fill="#ffffff" stroke="{nero}" stroke-width="4"/>
        <line x1="325" y1="110" x2="325" y2="285" stroke="{nero}" stroke-width="6"/>
        <path d="M170 205 L265 205" stroke="{blu}" stroke-width="8" marker-end="url(#arrow1)"/>
        <text x="325" y="320" text-anchor="middle" font-size="18" fill="{blu}" font-weight="900">SCORRIMENTO LINEARE 1 ANTA</text>
        <defs>
            <marker id="arrow1" markerWidth="14" markerHeight="14" refX="7" refY="4" orient="auto">
                <path d="M0,0 L0,8 L9,4 z" fill="{blu}"/>
            </marker>
        </defs>
        """
        titolo = "1 ANTA SELEZIONATA"
    else:
        ante_svg = f"""
        <rect x="75" y="110" width="250" height="175" fill="{vetro}" stroke="{nero}" stroke-width="4"/>
        <rect x="325" y="110" width="250" height="175" fill="{vetro2}" stroke="{nero}" stroke-width="4"/>
        <rect x="315" y="110" width="12" height="175" fill="#ffffff" stroke="{nero}" stroke-width="3"/>
        <rect x="329" y="110" width="12" height="175" fill="#ffffff" stroke="{nero}" stroke-width="3"/>
        <path d="M260 205 L145 205" stroke="{blu}" stroke-width="8" marker-end="url(#arrowL)"/>
        <path d="M390 205 L505 205" stroke="{blu}" stroke-width="8" marker-end="url(#arrowR)"/>
        <text x="325" y="320" text-anchor="middle" font-size="18" fill="{blu}" font-weight="900">SCORRIMENTO LINEARE 2 ANTE</text>
        <defs>
            <marker id="arrowR" markerWidth="14" markerHeight="14" refX="7" refY="4" orient="auto">
                <path d="M0,0 L0,8 L9,4 z" fill="{blu}"/>
            </marker>
            <marker id="arrowL" markerWidth="14" markerHeight="14" refX="2" refY="4" orient="auto">
                <path d="M9,0 L9,8 L0,4 z" fill="{blu}"/>
            </marker>
        </defs>
        """
        titolo = "2 ANTE SELEZIONATA"

    return f"""
    <div style="background:#ffffff;border:2px solid #b8d4f3;border-radius:12px;padding:10px;">
    <svg width="100%" height="390" viewBox="0 0 650 390">
        <text x="20" y="28" font-size="18" fill="{blu}" font-weight="900">{titolo}</text>

        <text x="325" y="58" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900">MISURA TRAVERSA CALCOLATA</text>
        <text x="325" y="84" text-anchor="middle" font-size="24" fill="{blu}" font-weight="900">{misura_traversa} mm</text>

        <line x1="75" y1="95" x2="575" y2="95" stroke="{blu}" stroke-width="3"/>
        <line x1="75" y1="82" x2="75" y2="108" stroke="{blu}" stroke-width="3"/>
        <line x1="575" y1="82" x2="575" y2="108" stroke="{blu}" stroke-width="3"/>

        <rect x="65" y="90" width="520" height="35" fill="#e9eef3" stroke="{nero}" stroke-width="2"/>
        <rect x="75" y="98" width="500" height="8" fill="#ffffff" opacity="0.45"/>
        <rect x="305" y="101" width="40" height="14" rx="3" fill="{nero}"/>

        {ante_svg}

        <line x1="145" y1="342" x2="505" y2="342" stroke="{blu}" stroke-width="3"/>
        <line x1="145" y1="330" x2="145" y2="354" stroke="{blu}" stroke-width="3"/>
        <line x1="505" y1="330" x2="505" y2="354" stroke="{blu}" stroke-width="3"/>
        <text x="325" y="370" text-anchor="middle" font-size="17" fill="{blu}" font-weight="900">LUCE PASSAGGIO {luce_mm} mm</text>

        <line x1="615" y1="110" x2="615" y2="285" stroke="{blu}" stroke-width="3"/>
        <line x1="602" y1="110" x2="628" y2="110" stroke="{blu}" stroke-width="3"/>
        <line x1="602" y1="285" x2="628" y2="285" stroke="{blu}" stroke-width="3"/>
        <text x="640" y="205" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900" transform="rotate(90 640,205)">H {altezza_mm} mm</text>
    </svg>
    </div>
    """

st.markdown("""
<style>
.stApp {background:#f3f7fd;font-family:Arial,sans-serif;}
.main .block-container {padding-top:0rem;max-width:1550px;}

.header {
    background:linear-gradient(115deg,#ffffff 0%,#ffffff 28%,#073763 28%,#06499b 100%);
    border-bottom:5px solid #063b7a;
    padding:22px 32px;
    display:grid;
    grid-template-columns: 28% 44% 28%;
    align-items:center;
    color:white;
}
.logo-satec {width:300px;}
.header-title {text-align:center;}
.header-title h1 {font-size:42px;margin:0;font-weight:900;line-height:1.05;}
.header-title div {font-size:18px;margin-top:12px;font-weight:700;}
.header-info {font-size:15px;line-height:1.45;text-align:left;font-weight:700;}

.powercore {
    background:white;
    padding:18px 34px;
    display:grid;
    grid-template-columns: 50% 50%;
    align-items:center;
    border-bottom:1px solid #bdd4ef;
}
.powercore-title {font-size:32px;font-weight:900;color:#111;}
.powercore-title span {color:#ff7900;}
.powercore-sub {font-size:17px;color:#111;margin-top:8px;}
.sesamo-logo {height:80px;}

.grid-main {
    display:grid;
    grid-template-columns: 69% 31%;
    gap:18px;
    margin-top:18px;
}

.card {
    background:white;
    border:1px solid #bdd4ef;
    border-radius:14px;
    padding:16px;
    margin-bottom:16px;
}

.title-bar {
    display:inline-block;
    background:#06499b;
    color:white;
    padding:9px 16px;
    border-radius:8px;
    font-size:18px;
    font-weight:900;
    margin-bottom:16px;
}

.choice-grid {
    display:grid;
    grid-template-columns: repeat(4,1fr);
    gap:16px;
}
.choice {
    border:2px solid #d4dce8;
    border-radius:12px;
    text-align:center;
    padding:12px;
    min-height:250px;
    background:white;
}
.choice-active {
    border:3px solid #06499b;
    background:#f0f7ff;
}
.choice-title {font-size:20px;font-weight:900;color:#111;line-height:1.1;}
.choice-desc {font-size:15px;line-height:1.25;color:#111;}

.section-row {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap:14px;
    margin-top:16px;
}
.section-box {
    background:#eef6ff;
    border-radius:12px;
    padding:16px;
    color:#06499b;
    font-weight:800;
    font-size:16px;
}
.section-box.green {
    background:#eefaf2;
    color:#0c7b3e;
}

.measure-row {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap:50px;
    margin-bottom:10px;
}
div[data-testid="stNumberInput"] label {
    color:#111!important;
    font-size:15px!important;
    font-weight:800!important;
}
div[data-testid="stNumberInput"] input {
    border:2px solid #8998b0!important;
    border-radius:0!important;
    text-align:center!important;
    font-size:28px!important;
    font-weight:800!important;
    color:#06499b!important;
    height:54px!important;
}

.diagram-row {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:14px;
}

.measure-total {
    border:2px solid #bdd4ef;
    background:#f8fbff;
    border-radius:10px;
    padding:14px;
    display:grid;
    grid-template-columns: 1fr 200px;
    align-items:center;
    color:#06499b;
    margin-top:10px;
}
.measure-total .big {font-size:30px;font-weight:900;text-align:center;}
.measure-total .small {font-size:18px;font-weight:900;text-align:center;}

.side-card {
    background:white;
    border:1px solid #bdd4ef;
    border-radius:14px;
    padding:16px;
    margin-bottom:16px;
}
.option-box {
    border:2px solid #06499b;
    border-radius:12px;
    padding:18px;
    margin-bottom:18px;
    background:white;
}
.option-title {font-size:20px;font-weight:900;color:#06499b;margin-bottom:12px;}
.check-row {
    display:flex;
    align-items:center;
    gap:14px;
    font-size:16px;
    color:#111;
    font-weight:700;
}
.custom-check {
    width:26px;
    height:26px;
    border-radius:5px;
    border:2px solid #06499b;
    background:#06499b;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:20px;
    font-weight:900;
}
div[data-testid="stCheckbox"] {display:none;}

.price {
    text-align:center;
    color:#06499b;
    font-size:42px;
    font-weight:900;
}
.price-label {
    color:#06499b;
    font-size:18px;
    font-weight:900;
    text-align:center;
}
.vat-box {
    border:1px solid #bdd4ef;
    border-radius:10px;
    padding:14px;
    color:#06499b;
    font-size:17px;
    font-weight:800;
    background:#f8fbff;
}

.power-side-title {color:#06499b;font-size:18px;font-weight:900;margin-bottom:12px;}
.power-side-text {font-size:15px;line-height:1.45;color:#111;}
.power-side-list li {margin-bottom:10px;color:#111;}

.desc-grid {
    display:grid;
    grid-template-columns: 34% 33% 33%;
    gap:16px;
    color:#111;
    font-size:15px;
}
.desc-title {color:#06499b;font-size:22px;font-weight:900;margin-bottom:10px;}
.desc-grid b {font-weight:900;}
.desc-grid li {margin-bottom:8px;}
.footer {
    background:#06499b;
    color:white;
    padding:18px 34px;
    display:grid;
    grid-template-columns: 1fr 1fr 1fr;
    font-size:16px;
    font-weight:700;
    margin-top:12px;
}
.stButton>button {
    background:#06499b;
    color:white;
    border-radius:8px;
    height:48px;
    font-size:16px;
    font-weight:900;
    border:none;
}
.stButton>button:hover {background:#073763;color:white;}
</style>
""", unsafe_allow_html=True)

logo_satec_html = f'<img class="logo-satec" src="data:image/jpeg;base64,{logo_satec64}">' if logo_satec64 else "<h1 style='color:#06499b'>SA-TEC</h1>"
sesamo_logo_html = f'<img class="sesamo-logo" src="data:image/png;base64,{logo_sesamo64}">' if logo_sesamo64 else "<h1>SESAMO</h1>"

st.markdown(f"""
<div class="header">
    <div>{logo_satec_html}</div>
    <div class="header-title">
        <h1>CONFIGURATORE<br>PORTE AUTOMATICHE</h1>
        <div>TECNOLOGIA, SICUREZZA E SOLUZIONI SU MISURA</div>
    </div>
    <div class="header-info">
        SA-TEC S.R.L.s<br>
        Via L. Settembrini 84<br>
        88046 Lamezia Terme (CZ)<br>
        P.IVA 04009610793<br>
        ☎ 0968-036797<br>
        ✉ sacco.tecnologie@gmail.com<br>
        ✉ sa-tec@pec.it
    </div>
</div>
<div class="powercore">
    <div>
        <div class="powercore-title">SESAMO <span>POWERCORE</span> PW100</div>
        <div class="powercore-sub">
            Automazione lineare per porte scorrevoli automatiche,<br>
            affidabile, sicura e compatibile con la normativa EN16005.
        </div>
    </div>
    <div style="text-align:center;">{sesamo_logo_html}</div>
</div>
""", unsafe_allow_html=True)

if "scelta" not in st.session_state:
    st.session_state.scelta = "STANDARD 1 ANTA"

st.markdown('<div class="grid-main">', unsafe_allow_html=True)

st.markdown('<div>', unsafe_allow_html=True)

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

html_cards = '<div class="choice-grid">'
for titolo, key, desc, ante_mini in cards:
    active = "choice-active" if scelta == key else ""
    html_cards += f"""
    <div class="choice {active}">
        <div class="choice-title">{titolo}</div>
        {mini_porta(ante_mini)}
        <div class="choice-desc">{desc}</div>
    </div>
    """
html_cards += "</div>"

st.markdown(html_cards, unsafe_allow_html=True)

st.markdown("""
<div class="section-row">
    <div class="section-box">
        CONFIGURAZIONE STANDARD<br>
        <span style="font-weight:500;color:#111;">Sesamo PowerCore PW100 per porta scorrevole automatica lineare ad uso normale.</span>
    </div>
    <div class="section-box green">
        CONFIGURAZIONE RIDONDANTE<br>
        <span style="font-weight:500;color:#111;">Automazione ridondante per vie di fuga e uscite di emergenza.</span>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="card"><div class="title-bar">2&nbsp;&nbsp; MISURE PORTA</div>', unsafe_allow_html=True)

m1, m2 = st.columns(2)
with m1:
    luce_mm = st.number_input("LUCE PASSAGGIO IN MM", min_value=800, max_value=5000, value=1600, step=50)
with m2:
    altezza_mm = st.number_input("ALTEZZA PASSAGGIO IN MM", min_value=1800, max_value=3000, value=2200, step=50)

lunghezza_traversa = calcola_traversa(luce_mm, ante)

d1, d2 = st.columns(2)
with d1:
    components.html(disegno_porta("1 anta", luce_mm, altezza_mm, lunghezza_traversa), height=430)
with d2:
    components.html(disegno_porta("2 ante", luce_mm, altezza_mm, lunghezza_traversa), height=430)

st.markdown(f"""
<div class="measure-total">
    <div>
        <b>MISURA TRAVERSA CALCOLATA</b><br>
        Calcolo automatico in base alla luce passaggio.
    </div>
    <div>
        <div class="big">{int(lunghezza_traversa * 1000)} mm</div>
        <div class="small">{lunghezza_traversa:.2f} metri</div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div>', unsafe_allow_html=True)

st.markdown('<div class="side-card"><div class="title-bar">3&nbsp;&nbsp; ACCESSORI E SERVIZI</div>', unsafe_allow_html=True)

elettroblocco = st.checkbox("Aggiungi elettroblocco", value=True, key="elettro")
spunta_elettro = "✓" if elettroblocco else ""

st.markdown(f"""
<div class="option-box">
    <div class="option-title">ELETTROBLOCCO</div>
    <div class="check-row">
        <div class="custom-check">{spunta_elettro}</div>
        <div>Aggiungi elettroblocco</div>
    </div>
</div>
""", unsafe_allow_html=True)

allaccio = st.checkbox("Aggiungi allaccio e collaudo SA-TEC", value=True, key="allaccio")
spunta_allaccio = "✓" if allaccio else ""

st.markdown(f"""
<div class="option-box">
    <div class="option-title">ALLACCIO E COLLAUDO</div>
    <div class="check-row">
        <div class="custom-check">{spunta_allaccio}</div>
        <div>Aggiungi allaccio e collaudo SA-TEC</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

articoli = []

aggiungi(articoli, "CASSA", "Profilo cassa traversa in alluminio", f"Profilo cassa traversa in alluminio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "COPERCHIO", "Coperchio traversa in alluminio", f"Coperchio traversa in alluminio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "GUARN_COPERCHIO", "Guarnizione coperchio", f"Guarnizione coperchio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "CINGHIA", "Cinghia dentata", f"Cinghia dentata ({lunghezza_traversa * 1.8:.2f} m)", lunghezza_traversa * 1.8)
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

if allaccio:
    aggiungi(articoli, "ALLACCIO_COLLAUDO", "Allaccio e collaudo SA-TEC", "Allaccio e collaudo SA-TEC", 1, scontato=False)

imponibile = sum(a["totale"] for a in articoli)
iva = imponibile * IVA
totale_iva = imponibile + iva

st.markdown('<div class="side-card"><div class="title-bar">4&nbsp;&nbsp; RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="price-label">TOTALE IVA ESCLUSA</div>
<div class="price">{euro(imponibile)}</div>
<div class="vat-box">
    IVA 22%: <span style="float:right;">{euro(iva)}</span><br>
    TOTALE IVA INCLUSA: <span style="float:right;">{euro(totale_iva)}</span>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="side-card">
    <div class="power-side-title">SESAMO POWERCORE PW100</div>
    <div style="margin-bottom:14px;">{sesamo_logo_html}</div>
    <div class="power-side-text">
        PowerCore PW100 è l'automazione lineare Sesamo progettata per porte scorrevoli automatiche a 1 o 2 ante.
        <br><br>
        Affidabile, silenziosa e compatta, garantisce massima sicurezza e conformità alla normativa EN16005.
    </div>
    <ul class="power-side-list">
        <li>Tecnologia lineare ad alte prestazioni</li>
        <li>Movimento fluido e silenzioso</li>
        <li>Compatibile con sensori Sesamo e dispositivi di sicurezza</li>
        <li>Ideale per ambienti pubblici e privati</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

righe1 = f"""
<b>Configurazione selezionata:</b> {scelta}<br><br>
<b>Automazione:</b> SESAMO POWERCORE PW100<br><br>
<b>Luce passaggio:</b> {luce_mm} mm<br><br>
<b>Altezza passaggio:</b> {altezza_mm} mm<br><br>
<b>Misura traversa:</b> {lunghezza_traversa:.2f} metri
"""

lista_articoli = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli])
metà = len(articoli) // 2
lista_sx = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli[:metà]])
lista_dx = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli[metà:]])

st.markdown(f"""
<div class="card">
    <div class="desc-title">DESCRIZIONE FORNITURA CLIENTE</div>
    <div class="desc-grid">
        <div>{righe1}</div>
        <div><ul>{lista_sx}</ul></div>
        <div><ul>{lista_dx}</ul></div>
    </div>
</div>
""", unsafe_allow_html=True)

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
<thead><tr><th>Voce</th><th>Descrizione</th></tr></thead>
<tbody>{righe_descrizione}</tbody>
</table>

<div class="total">Totale preventivo IVA esclusa: {euro(imponibile)}</div>
<div style="text-align:right;font-size:18px;margin-top:8px;">
IVA 22%: {euro(iva)}<br>
Totale IVA inclusa: {euro(totale_iva)}
</div>

<div class="conditions">
<h2>Condizioni di pagamento</h2>
<p>Pagamento tramite bonifico bancario intestato a <b>{AZIENDA}</b>.<br>
IBAN: <b>{IBAN}</b></p>
<p>Condizioni proposte: 50% all’ordine e saldo 50% prima della consegna o al collaudo.</p>
<p>Preventivo indicativo soggetto a verifica tecnica e conferma definitiva SA-TEC S.R.L.s.</p>
<p>Validità offerta: 15 giorni.</p>
</div>
</body>
</html>
"""

st.markdown('<div class="card"><div class="title-bar">STAMPA PREVENTIVO</div>', unsafe_allow_html=True)

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

st.markdown(f"""
<div class="footer">
    <div>📍 {AZIENDA}<br>{SEDE}</div>
    <div>☎ {TELEFONO}</div>
    <div>✉ {EMAIL}</div>
</div>
""", unsafe_allow_html=True)
