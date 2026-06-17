import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="Configuratore Porte Automatiche SA-TEC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

IVA = 0.22

# =========================
# CALCOLO PREZZI
# =========================

def prezzo_cliente(listino):
    # Listino con sconto 50+5 e maggiorazione 35%
    return listino * 0.50 * 0.95 * 1.35

def euro(valore):
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# LISTINI
# =========================

LISTINI = {
    # AUTOMAZIONI
    "LH100_1": 1236.00,
    "LH100_2": 1298.00,
    "ER140_1": 2140.00,
    "ER140_2": 2200.00,

    # TRAVERSA
    "CASSA": 343.00 / 6.6,
    "COPERCHIO": 214.00 / 6.6,
    "GUARN_COPERCHIO": 134.00 / 35,
    "CINGHIA": 671.00 / 60,
    "GUIDA": 49.20 / 6.6,
    "GUARN_GUIDA": 66.00 / 30,

    # STANDARD
    "HR100": 135.00,
    "ICON": 114.00,
    "BATTERIE": 118.00,
    "ELETTRO_STANDARD": 195.00,

    # RIDONDANTE
    "SSR3_ER_BL": 375.00,
    "DIGIDOR": 180.00,
    "PULSANTE_EMERGENZA": 130.00,
    "ELETTRO_RIDONDANTE": 290.00,

    # SERVIZI
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
# CSS
# =========================

st.markdown(
    """
    <style>
    .stApp {
        background: #f2f6fb;
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
        background: linear-gradient(120deg, #ffffff 0%, #ffffff 28%, #073763 28%, #002b55 100%);
        border-radius: 0 0 20px 20px;
        padding: 25px 35px;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
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
        letter-spacing: 1px;
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
        box-shadow: 0 5px 18px rgba(0,0,0,0.08);
        border: 1px solid #dde8f4;
    }

    .card-title {
        color: #06499b;
        font-size: 23px;
        font-weight: 900;
        margin-bottom: 18px;
        border-bottom: 1px solid #dbe5f0;
        padding-bottom: 12px;
    }

    .choice-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
        margin-bottom: 15px;
    }

    .choice-card {
        border-radius: 18px;
        padding: 22px;
        border: 2px solid #d6e2f0;
        background: #f8fbff;
        text-align: center;
        min-height: 150px;
    }

    .choice-card-active {
        border: 3px solid #06499b;
        background: #eaf4ff;
        box-shadow: 0 5px 18px rgba(6,73,155,0.18);
    }

    .choice-title {
        color: #06499b;
        font-size: 22px;
        font-weight: 900;
        margin-bottom: 8px;
    }

    .choice-subtitle {
        color: #333;
        font-size: 15px;
        line-height: 1.35;
    }

    .section-standard {
        background: #eef7ff;
        border-left: 6px solid #06499b;
        padding: 20px;
        border-radius: 14px;
        margin-top: 15px;
    }

    .section-ridondante {
        background: #fff5eb;
        border-left: 6px solid #e47700;
        padding: 20px;
        border-radius: 14px;
        margin-top: 15px;
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
        background: #f8fbff;
        border: 1px solid #d9e7f7;
        border-left: 5px solid #06499b;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }

    .desc-title {
        font-weight: 900;
        color: #06499b;
        font-size: 17px;
        margin-bottom: 5px;
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
    }

    .orange-box {
        background: #fff6ed;
        border: 1px solid #ffd1a3;
        color: #a65400;
        padding: 18px;
        border-radius: 12px;
        margin-top: 18px;
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
        height: 52px;
        font-size: 18px;
        font-weight: 900;
        border: none;
        width: 100%;
    }

    .stButton>button:hover {
        background: #002b55;
        color: white;
    }

    div[role="radiogroup"] {
        gap: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

def disegno_porta(ante, tipo):
    colore = "#06499b" if tipo == "Standard" else "#e47700"
    titolo = f"PORTA AUTOMATICA {ante.upper()}"

    if ante == "1 anta":
        return f"""
        <svg width="100%" height="270" viewBox="0 0 700 270">
            <rect x="80" y="35" width="540" height="30" rx="7" fill="{colore}"/>
            <rect x="110" y="80" width="480" height="135" rx="8" fill="#eef6ff" stroke="{colore}" stroke-width="4"/>
            <rect x="130" y="98" width="220" height="98" rx="6" fill="#ffffff" stroke="{colore}" stroke-width="3"/>
            <rect x="360" y="98" width="205" height="98" rx="6" fill="#dcecff" stroke="{colore}" stroke-width="3"/>
            <line x1="355" y1="88" x2="355" y2="205" stroke="{colore}" stroke-width="4"/>
            <path d="M415 145 L510 145" stroke="{colore}" stroke-width="6" marker-end="url(#arrow1)"/>
            <circle cx="350" cy="50" r="9" fill="white"/>
            <text x="350" y="250" text-anchor="middle" font-size="24" fill="{colore}" font-weight="bold">{titolo}</text>
            <defs>
                <marker id="arrow1" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L7,3 z" fill="{colore}"/>
                </marker>
            </defs>
        </svg>
        """

    return f"""
    <svg width="100%" height="270" viewBox="0 0 700 270">
        <rect x="80" y="35" width="540" height="30" rx="7" fill="{colore}"/>
        <rect x="110" y="80" width="480" height="135" rx="8" fill="#eef6ff" stroke="{colore}" stroke-width="4"/>
        <rect x="130" y="98" width="215" height="98" rx="6" fill="#ffffff" stroke="{colore}" stroke-width="3"/>
        <rect x="355" y="98" width="215" height="98" rx="6" fill="#ffffff" stroke="{colore}" stroke-width="3"/>
        <line x1="350" y1="88" x2="350" y2="205" stroke="{colore}" stroke-width="4"/>
        <path d="M315 145 L215 145" stroke="{colore}" stroke-width="6" marker-end="url(#arrowL)"/>
        <path d="M385 145 L485 145" stroke="{colore}" stroke-width="6" marker-end="url(#arrowR)"/>
        <circle cx="350" cy="50" r="9" fill="white"/>
        <text x="350" y="250" text-anchor="middle" font-size="24" fill="{colore}" font-weight="bold">{titolo}</text>
        <defs>
            <marker id="arrowR" markerWidth="12" markerHeight="12" refX="6" refY="3" orient="auto">
                <path d="M0,0 L0,6 L7,3 z" fill="{colore}"/>
            </marker>
            <marker id="arrowL" markerWidth="12" markerHeight="12" refX="1" refY="3" orient="auto">
                <path d="M7,0 L7,6 L0,3 z" fill="{colore}"/>
            </marker>
        </defs>
    </svg>
    """

# =========================
# HEADER
# =========================

if logo64:
    logo_html = f'<img class="hero-logo" src="data:image/jpeg;base64,{logo64}">'
else:
    logo_html = "<h1 style='color:#06499b;background:white;padding:20px;'>SA-TEC</h1>"

st.markdown(
    f"""
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
    """,
    unsafe_allow_html=True
)

# =========================
# SCELTA PRINCIPALE
# =========================

st.markdown('<div class="card"><div class="card-title">1️⃣ SCEGLI LA PORTA AUTOMATICA</div>', unsafe_allow_html=True)

scelta = st.radio(
    "Seleziona configurazione",
    [
        "STANDARD 1 ANTA",
        "STANDARD 2 ANTE",
        "RIDONDANTE 1 ANTA",
        "RIDONDANTE 2 ANTE"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

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

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("STANDARD 1 ANTA", "Porta automatica normale a una anta"),
    ("STANDARD 2 ANTE", "Porta automatica normale a due ante"),
    ("RIDONDANTE 1 ANTA", "Via di fuga / emergenza a una anta"),
    ("RIDONDANTE 2 ANTE", "Via di fuga / emergenza a due ante"),
]

for col, (titolo, sottotitolo) in zip([c1, c2, c3, c4], cards):
    active = "choice-card-active" if scelta == titolo else ""
    with col:
        st.markdown(
            f"""
            <div class="choice-card {active}">
                <div class="choice-title">{titolo}</div>
                <div class="choice-subtitle">{sottotitolo}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

if tipo == "Standard":
    st.markdown(
        """
        <div class="section-standard">
            <h3 style="margin:0;color:#06499b;">CONFIGURAZIONE STANDARD</h3>
            <p style="margin-bottom:0;">
            Automazione per porta scorrevole automatica ad uso normale, completa di radar,
            selettore touch e batterie di emergenza.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div class="section-ridondante">
            <h3 style="margin:0;color:#e47700;">CONFIGURAZIONE RIDONDANTE</h3>
            <p style="margin-bottom:0;">
            Automazione ridondante dedicata a vie di fuga e uscite di emergenza,
            completa di radar evacuazione, selettore DIGIDOR, batterie e pulsante emergenza.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# LAYOUT
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

    st.markdown(disegno_porta(ante, tipo), unsafe_allow_html=True)

    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">3️⃣ COSA INCLUDE QUESTA CONFIGURAZIONE</div>', unsafe_allow_html=True)

    if tipo == "Standard":
        st.markdown(
            """
            <div class="desc-box">
                <div class="desc-title">✅ Automazione Sesamo LH100</div>
                Automazione standard per porta scorrevole automatica, completa dei componenti principali di movimento e comando.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ 2 × Hotron HR100</div>
                Radar di apertura e sicurezza EN16005, uno lato interno e uno lato esterno.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ PF37.00 ICON</div>
                Selettore Touch con 3 tessere Tag per gestione delle funzioni porta.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ PF54.73 Kit batterie</div>
                Kit batterie con scheda di controllo e ricarica.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="desc-box">
                <div class="desc-title">✅ Automazione Sesamo ER140 Ridondante</div>
                Automazione per porte su vie di fuga e uscite di emergenza.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ Hotron SSR3-ER-BL</div>
                Radar specifico per evacuazione e gestione della sicurezza su sistema ridondante.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ Hotron HR100</div>
                Radar apertura e sicurezza EN16005.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ PF37.06 DIGIDOR</div>
                Selettore dedicato per configurazioni ridondanti.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ PF54.73 Kit batterie</div>
                Kit batterie con scheda di controllo e ricarica.
            </div>
            <div class="desc-box">
                <div class="desc-title">✅ Pulsante emergenza</div>
                Pulsante per gestione emergenza e sicurezza.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card"><div class="card-title">4️⃣ ACCESSORI</div>', unsafe_allow_html=True)

    elettroblocco = st.checkbox("Aggiungi elettroblocco", value=False)

    if elettroblocco and tipo == "Standard":
        st.success("Elettroblocco PF54.59 Standard selezionato.")
    elif elettroblocco and tipo == "Ridondante":
        st.success("Elettroblocco PF54.62 Ridondante selezionato.")
    else:
        st.info("Elettroblocco non incluso.")

    allaccio = st.checkbox("Allaccio e collaudo SA-TEC", value=True)

    if allaccio:
        st.success("Allaccio e collaudo inclusi.")
    else:
        st.warning("Solo fornitura materiale. Allaccio e collaudo esclusi.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CALCOLO ARTICOLI
# =========================

articoli = []

aggiungi(
    articoli,
    "CASSA",
    "Profilo cassa traversa in alluminio",
    "Profilo principale della traversa, tagliato su misura in base alla luce passaggio.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "COPERCHIO",
    "Coperchio traversa in alluminio",
    "Coperchio frontale della traversa, removibile per manutenzione.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "GUARN_COPERCHIO",
    "Guarnizione coperchio",
    "Guarnizione tecnica di finitura per il coperchio.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "CINGHIA",
    "Cinghia dentata",
    "Cinghia dentata di trasmissione per il movimento delle ante.",
    lunghezza_traversa * 1.8
)

aggiungi(
    articoli,
    "GUIDA",
    "Profilo guida scorrimento",
    "Profilo guida per lo scorrimento corretto del sistema.",
    lunghezza_traversa
)

aggiungi(
    articoli,
    "GUARN_GUIDA",
    "Guarnizione guida",
    "Guarnizione tecnica per guida di scorrimento.",
    lunghezza_traversa
)

if tipo == "Standard":
    if ante == "1 anta":
        aggiungi(
            articoli,
            "LH100_1",
            "Automazione Sesamo LH100 1 anta",
            "Automazione standard per porta automatica scorrevole a una anta."
        )
    else:
        aggiungi(
            articoli,
            "LH100_2",
            "Automazione Sesamo LH100 2 ante",
            "Automazione standard per porta automatica scorrevole a due ante."
        )

    aggiungi(
        articoli,
        "HR100",
        "2 × Hotron HR100 Radar apertura e sicurezza EN16005",
        "Sensori radar per apertura automatica e sicurezza del passaggio.",
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
        "PF54.73 Kit batterie con scheda controllo e ricarica",
        "Kit batterie di emergenza con scheda di controllo e ricarica."
    )

    if elettroblocco:
        aggiungi(
            articoli,
            "ELETTRO_STANDARD",
            "PF54.59 Elettroblocco Standard",
            "Elettroblocco per chiusura automatica su configurazione standard."
        )

else:
    if ante == "1 anta":
        aggiungi(
            articoli,
            "ER140_1",
            "PF54.13 ER140 Ridondante 1 anta",
            "Automazione ridondante per porta scorrevole a una anta, indicata per vie di fuga."
        )
    else:
        aggiungi(
            articoli,
            "ER140_2",
            "PF54.14 ER140 Ridondante 2 ante",
            "Automazione ridondante per porta scorrevole a due ante, indicata per vie di fuga."
        )

    aggiungi(
        articoli,
        "SSR3_ER_BL",
        "Hotron SSR3-ER-BL Radar evacuazione",
        "Radar per evacuazione e sicurezza su sistemi ridondanti."
    )

    aggiungi(
        articoli,
        "HR100",
        "Hotron HR100 Radar apertura e sicurezza EN16005",
        "Radar per apertura automatica e sicurezza del passaggio."
    )

    aggiungi(
        articoli,
        "DIGIDOR",
        "PF37.06 DIGIDOR Selettore",
        "Selettore dedicato per automazioni ridondanti."
    )

    aggiungi(
        articoli,
        "BATTERIE",
        "PF54.73 Kit batterie con scheda controllo e ricarica",
        "Kit batterie di emergenza con scheda di controllo e ricarica."
    )

    aggiungi(
        articoli,
        "PULSANTE_EMERGENZA",
        "Pulsante emergenza",
        "Pulsante per gestione emergenza e sicurezza."
    )

    if elettroblocco:
        aggiungi(
            articoli,
            "ELETTRO_RIDONDANTE",
            "PF54.62 Elettroblocco Ridondante",
            "Elettroblocco specifico per configurazione ridondante."
        )

if allaccio:
    aggiungi(
        articoli,
        "ALLACCIO_COLLAUDO",
        "Allaccio e collaudo SA-TEC",
        "Collegamento elettrico, regolazione, verifica funzionamento e collaudo finale.",
        1,
        scontato=False
    )

imponibile = sum(a["totale"] for a in articoli)
iva = imponibile * IVA
totale = imponibile + iva

# =========================
# RIEPILOGO
# =========================

with col_right:
    st.markdown('<div class="card"><div class="card-title">5️⃣ RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)

    st.write("Totale imponibile")
    st.markdown(f"<h3 style='text-align:right;'>{euro(imponibile)}</h3>", unsafe_allow_html=True)

    st.write("IVA 22%")
    st.markdown(f"<h3 style='text-align:right;'>{euro(iva)}</h3>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div>
            <b style="color:#06499b;">TOTALE IVA INCLUSA</b>
            <div class="summary-price">{euro(totale)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if tipo == "Ridondante":
        st.markdown(
            """
            <div class="orange-box">
                <b>⚠️ Configurazione ridondante</b><br><br>
                Soluzione indicata per via di fuga / uscita di emergenza.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class="green-box">
            <b>✅ Preventivo cliente</b><br><br>
            I prezzi dei singoli articoli non vengono mostrati.
            Il cliente vede solo descrizione e totale finale.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.button("✈️ RICHIEDI PREVENTIVO")
    st.button("⬇️ SCARICA PDF")

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
    st.markdown(
        f"""
        <div class="desc-box">
            <div class="desc-title">✓ {art['descrizione']}</div>
            <div>{art['descrizione_lunga']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

if not allaccio:
    st.warning("Allaccio e collaudo esclusi dalla presente offerta.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# FOOTER
# =========================

st.markdown(
    """
    <div class="footer">
        <div>SA-TEC S.R.L.s</div>
        <div>📍 Lamezia Terme (CZ)</div>
        <div>☎ 0968-036797</div>
        <div>✉ sacco.tecnologie@gmail.com</div>
    </div>
    """,
    unsafe_allow_html=True
)
