import streamlit as st
import streamlit.components.v1 as components
import base64
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
    "LH100_1": 1236.00,
    "LH100_2": 1298.00,
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
# LOGO
# =========================

def img_to_base64(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo64 = img_to_base64("logo_satec.jpg")

# =========================
# FUNZIONI
# =========================

def calcola_traversa(luce_mm, ante):
    if ante == "1 anta":
        return ((luce_mm * 2) + 100) / 1000
    return (luce_mm + 100) / 1000

def aggiungi(articoli, codice, descrizione, descrizione_lunga, quantita=1, scontato=True):
    listino = LISTINI[codice]
    prezzo = prezzo_cliente(listino) if scontato else listino
    articoli.append({
        "codice": codice,
        "descrizione": descrizione,
        "descrizione_lunga": descrizione_lunga,
        "quantita": quantita,
        "totale": prezzo * quantita
    })

def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    blu = "#06499b"
    blu_scuro = "#073763"
    azzurro = "#eaf4ff"
    vetro = "#f7fbff"

    if ante == "1 anta":
        return f"""
        <div style="background:white;border:2px solid #d7e6f7;border-radius:18px;padding:10px;">
        <svg width="100%" height="360" viewBox="0 0 760 360">
            <rect x="70" y="38" width="620" height="34" rx="4" fill="{blu_scuro}"/>
            <text x="380" y="28" text-anchor="middle" font-size="17" fill="{blu_scuro}" font-weight="bold">
                TRAVERSA {int(lunghezza_traversa * 1000)} mm
            </text>

            <rect x="120" y="98" width="520" height="170" fill="#ffffff" stroke="{blu_scuro}" stroke-width="4"/>
            <rect x="140" y="118" width="235" height="130" fill="{vetro}" stroke="{blu}" stroke-width="3"/>
            <rect x="385" y="118" width="235" height="130" fill="{azzurro}" stroke="{blu}" stroke-width="3"/>

            <line x1="380" y1="102" x2="380" y2="264" stroke="{blu_scuro}" stroke-width="4"/>
            <path d="M430 182 L560 182" stroke="{blu}" stroke-width="6" marker-end="url(#arrow1)"/>

            <line x1="120" y1="298" x2="640" y2="298" stroke="{blu_scuro}" stroke-width="3"/>
            <line x1="120" y1="286" x2="120" y2="310" stroke="{blu_scuro}" stroke-width="3"/>
            <line x1="640" y1="286" x2="640" y2="310" stroke="{blu_scuro}" stroke-width="3"/>
            <text x="380" y="326" text-anchor="middle" font-size="18" fill="{blu_scuro}" font-weight="bold">
                LUCE PASSAGGIO {luce_mm} mm
            </text>

            <line x1="678" y1="98" x2="678" y2="268" stroke="{blu_scuro}" stroke-width="3"/>
            <line x1="666" y1="98" x2="690" y2="98" stroke="{blu_scuro}" stroke-width="3"/>
            <line x1="666" y1="268" x2="690" y2="268" stroke="{blu_scuro}" stroke-width="3"/>
            <text x="720" y="190" text-anchor="middle" font-size="17" fill="{blu_scuro}" font-weight="bold" transform="rotate(90 720,190)">
                ALTEZZA {altezza_mm} mm
            </text>

            <text x="380" y="354" text-anchor="middle" font-size="20" fill="{blu_scuro}" font-weight="bold">
                PORTA AUTOMATICA 1 ANTA
            </text>

            <defs>
                <marker id="arrow1" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L7,3 z" fill="{blu}"/>
                </marker>
            </defs>
        </svg>
        </div>
        """

    return f"""
    <div style="background:white;border:2px solid #d7e6f7;border-radius:18px;padding:10px;">
    <svg width="100%" height="360" viewBox="0 0 760 360">
        <rect x="70" y="38" width="620" height="34" rx="4" fill="{blu_scuro}"/>
        <text x="380" y="28" text-anchor="middle" font-size="17" fill="{blu_scuro}" font-weight="bold">
            TRAVERSA {int(lunghezza_traversa * 1000)} mm
        </text>

        <rect x="120" y="98" width="520" height="170" fill="#ffffff" stroke="{blu_scuro}" stroke-width="4"/>
        <rect x="140" y="118" width="235" height="130" fill="{vetro}" stroke="{blu}" stroke-width="3"/>
        <rect x="385" y="118" width="235" height="130" fill="{vetro}" stroke="{blu}" stroke-width="3"/>

        <line x1="380" y1="102" x2="380" y2="264" stroke="{blu_scuro}" stroke-width="4"/>

        <path d="M340 182 L220 182" stroke="{blu}" stroke-width="6" marker-end="url(#arrowL)"/>
        <path d="M420 182 L540 182" stroke="{blu}" stroke-width="6" marker-end="url(#arrowR)"/>

        <line x1="120" y1="298" x2="640" y2="298" stroke="{blu_scuro}" stroke-width="3"/>
        <line x1="120" y1="286" x2="120" y2="310" stroke="{blu_scuro}" stroke-width="3"/>
        <line x1="640" y1="286" x2="640" y2="310" stroke="{blu_scuro}" stroke-width="3"/>
        <text x="380" y="326" text-anchor="middle" font-size="18" fill="{blu_scuro}" font-weight="bold">
            LUCE PASSAGGIO {luce_mm} mm
        </text>

        <line x1="678" y1="98" x2="678" y2="268" stroke="{blu_scuro}" stroke-width="3"/>
        <line x1="666" y1="98" x2="690" y2="98" stroke="{blu_scuro}" stroke-width="3"/>
        <line x1="666" y1="268" x2="690" y2="268" stroke="{blu_scuro}" stroke-width="3"/>
        <text x="720" y="190" text-anchor="middle" font-size="17" fill="{blu_scuro}" font-weight="bold" transform="rotate(90 720,190)">
            ALTEZZA {altezza_mm} mm
        </text>

        <text x="380" y="354" text-anchor="middle" font-size="20" fill="{blu_scuro}" font-weight="bold">
            PORTA AUTOMATICA 2 ANTE
        </text>

        <defs>
            <marker id="arrowR" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto">
                <path d="M0,0 L0,6 L7,3 z" fill="{blu}"/>
            </marker>
            <marker id="arrowL" markerWidth="12" markerHeight="12" refX="1" refY="3" orient="auto">
                <path d="M7,0 L7,6 L0,3 z" fill="{blu}"/>
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
.stApp {
    background: #f3f7fd;
    font-family: Arial, sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.main .block-container {
    padding-top: 0rem;
    max-width: 1500px;
}

.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(120deg, #ffffff 0%, #ffffff 28%, #073763 28%, #06499b 100%);
    border-radius: 0 0 22px 22px;
    padding: 25px 35px;
    margin-bottom: 25px;
    box-shadow: 0 8px 24px rgba(6,73,155,0.20);
}

.hero-logo {
    width: 320px;
    background: white;
}

.hero-title {
    color: white;
    padding-left: 35px;
    flex: 1;
}

.hero-title h1 {
    font-size: 42px;
    margin: 0;
    font-weight: 900;
}

.hero-title h3 {
    font-size: 21px;
    margin-top: 10px;
    font-weight: 400;
}

.top-icons {
    color: white;
    display: flex;
    gap: 30px;
    text-align: center;
    font-weight: 700;
    font-size: 14px;
}

.card {
    background: white;
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 20px;
    box-shadow: 0 5px 18px rgba(6,73,155,0.10);
    border: 1px solid #d7e6f7;
}

.card-title {
    color: #06499b;
    font-size: 23px;
    font-weight: 900;
    margin-bottom: 18px;
    border-bottom: 1px solid #d7e6f7;
    padding-bottom: 12px;
}

.choice-card {
    border-radius: 18px;
    padding: 24px;
    border: 2px solid #bdd4ef;
    background: #f8fbff;
    text-align: center;
    min-height: 150px;
}

.choice-card-active {
    border: 4px solid #06499b;
    background: #eaf4ff;
    box-shadow: 0 5px 18px rgba(6,73,155,0.22);
}

.choice-title {
    color: #06499b;
    font-size: 22px;
    font-weight: 900;
    margin-bottom: 10px;
}

.choice-subtitle {
    color: #18324f;
    font-size: 16px;
    line-height: 1.45;
}

.section-standard, .section-ridondante {
    background: #eef6ff;
    border-left: 6px solid #06499b;
    padding: 22px;
    border-radius: 14px;
    margin-top: 18px;
    color: #18324f;
    font-size: 18px;
    line-height: 1.6;
}

.info-box {
    background: linear-gradient(90deg, #eef6ff, #ffffff);
    border-radius: 14px;
    padding: 20px;
    margin-top: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-left: 6px solid #06499b;
}

.info-box strong {
    color: #06499b;
    font-size: 30px;
}

.desc-box {
    background: #ffffff;
    border: 2px solid #d7e6f7;
    border-left: 7px solid #06499b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 14px;
    color: #18324f;
}

.desc-title {
    font-weight: 900;
    color: #06499b;
    font-size: 20px;
    margin-bottom: 10px;
}

.desc-text {
    font-size: 18px;
    line-height: 1.65;
    color: #18324f;
}

.summary-price {
    color: #06499b;
    font-size: 42px;
    font-weight: 900;
    text-align: right;
}

.green-box {
    background: #eefaf2;
    border: 1px solid #b9e6c7;
    color: #0c7b3e;
    padding: 20px;
    border-radius: 12px;
    margin-top: 18px;
    font-size: 17px;
    line-height: 1.5;
}

.blue-box {
    background: #eef6ff;
    border: 1px solid #bdd4ef;
    color: #06499b;
    padding: 18px;
    border-radius: 12px;
    margin-top: 18px;
    font-size: 17px;
    line-height: 1.5;
}

.accessory-box {
    border: 2px solid #06499b;
    background: #f8fbff;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
    color: #073763;
    font-size: 18px;
    font-weight: 800;
}

.footer {
    background: #073763;
    color: white;
    padding: 18px 30px;
    border-radius: 14px 14px 0 0;
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
    font-weight: 600;
}

.stButton>button {
    background: #06499b;
    color: white;
    border-radius: 12px;
    height: 56px;
    font-size: 18px;
    font-weight: 900;
    border: none;
    width: 100%;
}

.stButton>button:hover {
    background: #073763;
    color: white;
}

div[data-testid="stNumberInput"] label {
    color: #06499b !important;
    font-size: 18px !important;
    font-weight: 900 !important;
}

div[data-testid="stNumberInput"] input {
    border: 2px solid #06499b !important;
    border-radius: 12px !important;
    font-size: 24px !important;
    font-weight: 900 !important;
    color: #073763 !important;
    background: #ffffff !important;
    height: 52px !important;
}

div[data-testid="stCheckbox"] label {
    border: 2px solid #06499b;
    background: #f8fbff;
    border-radius: 14px;
    padding: 14px 16px;
    width: 100%;
    font-size: 18px;
    font-weight: 900;
    color: #073763;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

if logo64:
    logo_html = f'<img class="hero-logo" src="data:image/jpeg;base64,{logo64}">'
else:
    logo_html = "<h1 style='color:#06499b;background:white;padding:20px;'>SA-TEC</h1>"

st.markdown(f"""
<div class="hero">
    <div>{logo_html}</div>
    <div class="hero-title">
        <h1>CONFIGURATORE<br>PORTE AUTOMATICHE</h1>
        <h3>STANDARD E RIDONDANTI PER VIE DI FUGA</h3>
    </div>
    <div class="top-icons">
        <div>🛡️<br>EN16005</div>
        <div>🚪<br>1 O 2 ANTE</div>
        <div>⚙️<br>SU MISURA</div>
    </div>
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
    if st.button("STANDARD 1 ANTA", key="btn_std_1"):
        st.session_state.scelta = "STANDARD 1 ANTA"
with c2:
    if st.button("STANDARD 2 ANTE", key="btn_std_2"):
        st.session_state.scelta = "STANDARD 2 ANTE"
with c3:
    if st.button("RIDONDANTE 1 ANTA", key="btn_rid_1"):
        st.session_state.scelta = "RIDONDANTE 1 ANTA"
with c4:
    if st.button("RIDONDANTE 2 ANTE", key="btn_rid_2"):
        st.session_state.scelta = "RIDONDANTE 2 ANTE"

scelta = st.session_state.scelta

if scelta == "STANDARD 1 ANTA":
    tipo = "Standard"
    ante = "1 anta"
elif scelta == "STANDARD 2 ANTE":
    tipo = "Standard"
    ante = "2 ante"
elif scelta == "RIDONDANTE 1 ANTA":
    tipo = "Ridondante"
    ante = "1 anta"
else:
    tipo = "Ridondante"
    ante = "2 ante"

cards = [
    ("STANDARD 1 ANTA", "Porta automatica standard a una anta"),
    ("STANDARD 2 ANTE", "Porta automatica standard a due ante"),
    ("RIDONDANTE 1 ANTA", "Automazione per via di fuga a una anta"),
    ("RIDONDANTE 2 ANTE", "Automazione per via di fuga a due ante"),
]

cc1, cc2, cc3, cc4 = st.columns(4)

for col, (titolo, sottotitolo) in zip([cc1, cc2, cc3, cc4], cards):
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
        Automazione per porta scorrevole automatica ad uso normale.
        Include radar di apertura e sicurezza, selettore touch e batterie di emergenza.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="section-ridondante">
        <h3 style="margin:0 0 8px 0;color:#06499b;">CONFIGURAZIONE RIDONDANTE</h3>
        Automazione dedicata a vie di fuga e uscite di emergenza.
        Include radar evacuazione, selettore DIGIDOR, batterie e pulsante emergenza.
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
        height=390
    )

    st.markdown(f"""
    <div class="info-box">
        <div>
            <b>LUNGHEZZA TRAVERSA CALCOLATA</b><br>
            Calcolo automatico in base alla luce passaggio e al numero ante.
        </div>
        <div>
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

    if elettroblocco and tipo == "Standard":
        st.success("Elettroblocco PF54.59 Standard selezionato.")
    elif elettroblocco and tipo == "Ridondante":
        st.success("Elettroblocco PF54.62 Ridondante selezionato.")
    else:
        st.info("Elettroblocco non incluso.")

    st.markdown('<div class="accessory-box">ALLACCIO E COLLAUDO</div>', unsafe_allow_html=True)
    allaccio = st.checkbox("Aggiungi allaccio e collaudo SA-TEC", value=True)

    if allaccio:
        st.success("Allaccio e collaudo inclusi nel preventivo.")
    else:
        st.warning("Solo fornitura materiale. Allaccio e collaudo esclusi.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CALCOLO ARTICOLI
# =========================

articoli = []

aggiungi(articoli, "CASSA", "Profilo cassa traversa in alluminio", "Profilo principale della traversa, tagliato su misura in base alla luce passaggio.", lunghezza_traversa)
aggiungi(articoli, "COPERCHIO", "Coperchio traversa in alluminio", "Coperchio frontale della traversa, removibile per manutenzione.", lunghezza_traversa)
aggiungi(articoli, "GUARN_COPERCHIO", "Guarnizione coperchio", "Guarnizione tecnica di finitura per il coperchio.", lunghezza_traversa)
aggiungi(articoli, "CINGHIA", "Cinghia dentata", "Cinghia dentata di trasmissione per il movimento delle ante.", lunghezza_traversa * 1.8)
aggiungi(articoli, "GUIDA", "Profilo guida scorrimento", "Profilo guida per lo scorrimento corretto del sistema.", lunghezza_traversa)
aggiungi(articoli, "GUARN_GUIDA", "Guarnizione guida", "Guarnizione tecnica per guida di scorrimento.", lunghezza_traversa)

if tipo == "Standard":
    if ante == "1 anta":
        aggiungi(articoli, "LH100_1", "Automazione Sesamo LH100 1 anta", "Automazione standard per porta automatica scorrevole a una anta.")
    else:
        aggiungi(articoli, "LH100_2", "Automazione Sesamo LH100 2 ante", "Automazione standard per porta automatica scorrevole a due ante.")

    aggiungi(articoli, "HR100", "2 × Hotron HR100 Radar apertura e sicurezza EN16005", "Sensori radar per apertura automatica e sicurezza del passaggio.", 2)
    aggiungi(articoli, "ICON", "PF37.00 ICON Selettore Touch con 3 Tag", "Selettore funzioni touch per gestione modalità porta.")
    aggiungi(articoli, "BATTERIE", "PF54.73 Kit batterie con scheda controllo e ricarica", "Kit batterie di emergenza con scheda di controllo e ricarica.")

    if elettroblocco:
        aggiungi(articoli, "ELETTRO_STANDARD", "PF54.59 Elettroblocco Standard", "Elettroblocco per chiusura automatica su configurazione standard.")

else:
    if ante == "1 anta":
        aggiungi(articoli, "ER140_1", "PF54.13 ER140 Ridondante 1 anta", "Automazione ridondante per porta scorrevole a una anta, indicata per vie di fuga.")
    else:
        aggiungi(articoli, "ER140_2", "PF54.14 ER140 Ridondante 2 ante", "Automazione ridondante per porta scorrevole a due ante, indicata per vie di fuga.")

    aggiungi(articoli, "SSR3_ER_BL", "Hotron SSR3-ER-BL Radar evacuazione", "Radar per evacuazione e sicurezza su sistemi ridondanti.")
    aggiungi(articoli, "HR100", "Hotron HR100 Radar apertura e sicurezza EN16005", "Radar per apertura automatica e sicurezza del passaggio.")
    aggiungi(articoli, "DIGIDOR", "PF37.06 DIGIDOR Selettore", "Selettore dedicato per automazioni ridondanti.")
    aggiungi(articoli, "BATTERIE", "PF54.73 Kit batterie con scheda controllo e ricarica", "Kit batterie di emergenza con scheda di controllo e ricarica.")
    aggiungi(articoli, "PULSANTE_EMERGENZA", "Pulsante emergenza", "Pulsante per gestione emergenza e sicurezza.")

    if elettroblocco:
        aggiungi(articoli, "ELETTRO_RIDONDANTE", "PF54.62 Elettroblocco Ridondante", "Elettroblocco specifico per configurazione ridondante.")

if allaccio:
    aggiungi(articoli, "ALLACCIO_COLLAUDO", "Allaccio e collaudo SA-TEC", "Collegamento elettrico, regolazione, verifica funzionamento e collaudo finale.", 1, scontato=False)

imponibile = sum(a["totale"] for a in articoli)
iva = imponibile * IVA
totale_iva = imponibile + iva

# =========================
# RIEPILOGO
# =========================

with col_right:
    st.markdown('<div class="card"><div class="card-title">4️⃣ RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div>
        <b style="color:#06499b;font-size:20px;">TOTALE PREVENTIVO IVA ESCLUSA</b>
        <div class="summary-price">{euro(imponibile)}</div>
        <div style="text-align:right;color:#18324f;font-size:17px;">IVA esclusa</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="blue-box">
        IVA 22%: <b>{euro(iva)}</b><br>
        Totale indicativo IVA inclusa: <b>{euro(totale_iva)}</b>
    </div>
    """, unsafe_allow_html=True)

    if tipo == "Ridondante":
        st.markdown("""
        <div class="blue-box">
            <b>Configurazione ridondante</b><br><br>
            Soluzione indicata per via di fuga / uscita di emergenza.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="green-box">
        <b>Preventivo cliente</b><br><br>
        Il totale principale è IVA esclusa.
        I prezzi dei singoli articoli non vengono mostrati.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DESCRIZIONE CLIENTE
# =========================

st.markdown('<div class="card"><div class="card-title">📌 DESCRIZIONE FORNITURA CLIENTE</div>', unsafe_allow_html=True)

st.write(f"Configurazione selezionata: **{scelta}**")
st.write(f"Luce passaggio: **{luce_mm} mm**")
st.write(f"Altezza passaggio: **{altezza_mm} mm**")
st.write(f"Lunghezza traversa calcolata: **{lunghezza_traversa:.2f} metri**")

for art in articoli:
    st.markdown(f"""
    <div class="desc-box">
        <div class="desc-title">{art['descrizione']}</div>
        <div class="desc-text">{art['descrizione_lunga']}</div>
    </div>
    """, unsafe_allow_html=True)

if not allaccio:
    st.warning("Allaccio e collaudo esclusi dalla presente offerta.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# HTML STAMPA
# =========================

righe_descrizione = ""
for art in articoli:
    righe_descrizione += f"""
    <tr>
        <td>{art['descrizione']}</td>
        <td>{art['descrizione_lunga']}</td>
    </tr>
    """

logo_print = ""
if logo64:
    logo_print = f'<img src="data:image/jpeg;base64,{logo64}" style="width:240px;">'
else:
    logo_print = f"<h1>{AZIENDA}</h1>"

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

<h1>Preventivo porta automatica</h1>

<div class="box">
    <b>Data:</b> {date.today().strftime("%d/%m/%Y")}<br>
    <b>Configurazione:</b> {scelta}<br>
    <b>Luce passaggio:</b> {luce_mm} mm<br>
    <b>Altezza passaggio:</b> {altezza_mm} mm<br>
    <b>Lunghezza traversa calcolata:</b> {lunghezza_traversa:.2f} metri
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
        Condizioni proposte: 50% all’ordine e saldo 50% prima della consegna o al collaudo,
        salvo diversi accordi scritti tra le parti.
    </p>
    <p>
        Il presente preventivo è indicativo e soggetto a verifica tecnica, disponibilità materiale
        e conferma definitiva da parte di SA-TEC S.R.L.s.
    </p>
    <p>
        Validità offerta: 15 giorni dalla data del presente documento.
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

components.html(
    f"""
    <div style="border:2px solid #06499b;border-radius:14px;padding:18px;background:#f8fbff;">
        <h3 style="color:#06499b;margin-top:0;">Anteprima stampa</h3>
        <p style="font-size:16px;color:#18324f;">
            Clicca sul pulsante qui sotto per aprire la stampa direttamente dal browser.
        </p>
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
        const html = `{html_stampa.replace("`", "\\`")}`;
        const win = window.open("", "_blank");
        win.document.open();
        win.document.write(html);
        win.document.close();
    }}
    </script>
    """,
    height=170
)

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
