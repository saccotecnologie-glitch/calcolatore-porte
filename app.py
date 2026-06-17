import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="Configuratore Porte Automatiche SA-TEC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

IVA = 0.22

def prezzo_cliente(listino):
    return listino * 0.50 * 0.95 * 1.35

def euro(valore):
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

def img_to_base64(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo64 = img_to_base64("logo_satec.jpg")

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

def disegno_porta(ante):
    if ante == "1 anta":
        return """
        <svg width="100%" height="250" viewBox="0 0 600 250">
            <rect x="60" y="45" width="480" height="25" rx="6" fill="#0b3d73"/>
            <rect x="90" y="80" width="420" height="130" rx="8" fill="#eef6ff" stroke="#0b3d73" stroke-width="4"/>
            <rect x="110" y="95" width="190" height="100" rx="6" fill="#ffffff" stroke="#0b3d73" stroke-width="3"/>
            <rect x="310" y="95" width="180" height="100" rx="6" fill="#dcecff" stroke="#0b3d73" stroke-width="3"/>
            <line x1="300" y1="85" x2="300" y2="205" stroke="#0b3d73" stroke-width="3"/>
            <path d="M360 130 L430 130" stroke="#0b3d73" stroke-width="5" marker-end="url(#arrow)"/>
            <text x="300" y="235" text-anchor="middle" font-size="24" fill="#0b3d73" font-weight="bold">PORTA AUTOMATICA 1 ANTA</text>
            <defs>
                <marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 z" fill="#0b3d73"/>
                </marker>
            </defs>
        </svg>
        """
    else:
        return """
        <svg width="100%" height="250" viewBox="0 0 600 250">
            <rect x="60" y="45" width="480" height="25" rx="6" fill="#0b3d73"/>
            <rect x="90" y="80" width="420" height="130" rx="8" fill="#eef6ff" stroke="#0b3d73" stroke-width="4"/>
            <rect x="110" y="95" width="185" height="100" rx="6" fill="#ffffff" stroke="#0b3d73" stroke-width="3"/>
            <rect x="305" y="95" width="185" height="100" rx="6" fill="#ffffff" stroke="#0b3d73" stroke-width="3"/>
            <line x1="300" y1="85" x2="300" y2="205" stroke="#0b3d73" stroke-width="3"/>
            <path d="M260 130 L190 130" stroke="#0b3d73" stroke-width="5" marker-end="url(#arrow_left)"/>
            <path d="M340 130 L410 130" stroke="#0b3d73" stroke-width="5" marker-end="url(#arrow_right)"/>
            <text x="300" y="235" text-anchor="middle" font-size="24" fill="#0b3d73" font-weight="bold">PORTA AUTOMATICA 2 ANTE</text>
            <defs>
                <marker id="arrow_right" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 z" fill="#0b3d73"/>
                </marker>
                <marker id="arrow_left" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto">
                    <path d="M6,0 L6,6 L0,3 z" fill="#0b3d73"/>
                </marker>
            </defs>
        </svg>
        """

st.markdown(
    """
    <style>
    .stApp {background:#f3f6fb;font-family:Arial,sans-serif;}
    header[data-testid="stHeader"] {background:transparent;}
    .main .block-container {padding-top:0rem;max-width:1500px;}
    .hero {
        display:flex;align-items:center;justify-content:space-between;
        background:linear-gradient(120deg,#ffffff 0%,#ffffff 28%,#073763 28%,#002b55 100%);
        border-radius:0 0 18px 18px;padding:25px 35px;margin-bottom:25px;
        box-shadow:0 8px 24px rgba(0,0,0,0.12);
    }
    .hero-logo {width:330px;background:white;}
    .hero-title {color:white;text-align:left;padding-left:30px;flex:1;}
    .hero-title h1 {font-size:44px;margin:0;font-weight:800;letter-spacing:1px;}
    .hero-title h3 {font-size:22px;margin-top:10px;font-weight:400;}
    .top-icons {color:white;display:flex;gap:35px;text-align:center;font-weight:700;}
    .step-box {
        display:flex;gap:15px;background:white;border-radius:15px;padding:20px;margin-bottom:18px;
        box-shadow:0 4px 16px rgba(0,0,0,0.08);
    }
    .step {flex:1;display:flex;align-items:center;gap:15px;border-right:1px solid #dfe6f0;}
    .step:last-child {border-right:none;}
    .circle {
        width:48px;height:48px;border-radius:50%;background:#d8dde6;color:#1b2638;
        display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;
    }
    .circle.active {background:#06499b;color:white;}
    .card {
        background:white;border-radius:15px;padding:28px;margin-bottom:18px;
        box-shadow:0 4px 16px rgba(0,0,0,0.08);border:1px solid #e3eaf3;
    }
    .card-title {
        color:#06499b;font-size:22px;font-weight:800;margin-bottom:20px;
        border-bottom:1px solid #d8e1ec;padding-bottom:12px;
    }
    .info-box {
        background:linear-gradient(90deg,#eef6ff,#ffffff);border-radius:12px;padding:20px;margin-top:18px;
        display:flex;justify-content:space-between;align-items:center;border-left:5px solid #06499b;
    }
    .info-box strong {color:#06499b;font-size:28px;}
    .summary-price {color:#06499b;font-size:42px;font-weight:900;text-align:right;}
    .green-box {
        background:#eefaf2;border:1px solid #b9e6c7;color:#0c7b3e;
        padding:20px;border-radius:12px;margin-top:20px;
    }
    .included li {margin-bottom:8px;}
    .desc-box {
        background:#f8fbff;border:1px solid #d9e7f7;border-left:5px solid #06499b;
        border-radius:10px;padding:14px;margin-bottom:10px;
    }
    .desc-title {font-weight:800;color:#06499b;}
    .footer {
        background:#073763;color:white;padding:18px 30px;border-radius:14px 14px 0 0;
        margin-top:20px;display:flex;justify-content:space-between;font-weight:600;
    }
    .stButton>button {
        background:#06499b;color:white;border-radius:10px;height:52px;
        font-size:18px;font-weight:800;border:none;width:100%;
    }
    .stButton>button:hover {background:#002b55;color:white;}
    </style>
    """,
    unsafe_allow_html=True
)

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
            <h3>PREVENTIVO IN TEMPO REALE</h3>
        </div>
        <div class="top-icons">
            <div>🛡️<br>PRODOTTI<br>CERTIFICATI</div>
            <div>🎧<br>ASSISTENZA<br>TECNICA</div>
            <div>⚙️<br>TECNOLOGIA<br>IN MOVIMENTO</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="step-box">
        <div class="step"><div class="circle active">1</div><div><b>CONFIGURAZIONE</b><br>Imposta i parametri</div></div>
        <div class="step"><div class="circle">2</div><div><b>ACCESSORI</b><br>Seleziona le opzioni</div></div>
        <div class="step"><div class="circle">3</div><div><b>RIEPILOGO</b><br>Preventivo finale</div></div>
    </div>
    """,
    unsafe_allow_html=True
)

col_left, col_right = st.columns([2, 1.05], gap="large")

with col_left:
    st.markdown('<div class="card"><div class="card-title">⚙️ CONFIGURAZIONE PORTA</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        tipo = st.radio("TIPO AUTOMAZIONE", ["Standard", "Ridondante"], horizontal=True)

    with c2:
        ante = st.radio("NUMERO ANTE", ["1 anta", "2 ante"], horizontal=True)

    c3, c4 = st.columns(2)

    with c3:
        luce_mm = st.number_input("LUCE PASSAGGIO (MM)", min_value=800, max_value=5000, value=1600, step=50)

    with c4:
        altezza_mm = st.number_input("ALTEZZA PASSAGGIO (MM)", min_value=1800, max_value=3000, value=2200, step=50)

    lunghezza_traversa = calcola_traversa(luce_mm, ante)

    st.markdown(disegno_porta(ante), unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="info-box">
            <div>
                <b>LUNGHEZZA TRAVERSA CALCOLATA</b><br>
                Calcolata automaticamente in base alla luce passaggio e al numero ante.
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

with col_right:
    st.markdown('<div class="card"><div class="card-title">🛍️ ACCESSORI OPZIONALI</div>', unsafe_allow_html=True)

    elettroblocco = st.checkbox("ELETTROBLOCCO")

    if tipo == "Standard":
        st.caption("PF54.59 - Elettroblocco Standard")
    else:
        st.caption("PF54.62 - Elettroblocco Ridondante")

    allaccio = st.checkbox("ALLACCIO E COLLAUDO", value=True)
    st.caption("Allaccio, collegamento elettrico, regolazione e collaudo finale SA-TEC.")

    st.markdown("</div>", unsafe_allow_html=True)

articoli = []

aggiungi(
    articoli, "CASSA",
    "Profilo cassa traversa in alluminio",
    "Profilo principale della traversa, tagliato su misura in base alla luce passaggio."
    , lunghezza_traversa
)

aggiungi(
    articoli, "COPERCHIO",
    "Coperchio traversa in alluminio",
    "Coperchio frontale di chiusura della traversa, removibile per manutenzione."
    , lunghezza_traversa
)

aggiungi(
    articoli, "GUARN_COPERCHIO",
    "Guarnizione coperchio",
    "Guarnizione di finitura per il coperchio della traversa."
    , lunghezza_traversa
)

aggiungi(
    articoli, "CINGHIA",
    "Cinghia dentata",
    "Cinghia dentata di trasmissione per il movimento automatico delle ante."
    , lunghezza_traversa * 1.8
)

aggiungi(
    articoli, "GUIDA",
    "Profilo guida scorrimento",
    "Guida inferiore o superiore per lo scorrimento corretto del sistema."
    , lunghezza_traversa
)

aggiungi(
    articoli, "GUARN_GUIDA",
    "Guarnizione guida",
    "Guarnizione tecnica per la guida di scorrimento."
    , lunghezza_traversa
)

if tipo == "Standard":
    if ante == "1 anta":
        aggiungi(
            articoli, "LH100_1",
            "Automazione Sesamo LH100 1 anta",
            "Automazione per porta scorrevole automatica standard a una anta, completa di gruppo motore, elettronica di comando e componenti principali."
        )
    else:
        aggiungi(
            articoli, "LH100_2",
            "Automazione Sesamo LH100 2 ante",
            "Automazione per porta scorrevole automatica standard a due ante, completa di gruppo motore, elettronica di comando e componenti principali."
        )

    aggiungi(
        articoli, "HR100",
        "2 × Hotron HR100 Radar apertura e sicurezza EN16005",
        "Sensori radar per apertura automatica e sicurezza del passaggio, installati lato interno ed esterno."
        , 2
    )

    aggiungi(
        articoli, "ICON",
        "PF37.00 ICON Selettore Touch con 3 Tag",
        "Selettore funzioni touch per gestione modalità porta, completo di tre tessere Tag."
    )

    aggiungi(
        articoli, "BATTERIE",
        "PF54.73 Kit batterie con scheda controllo e ricarica",
        "Kit batterie di emergenza con scheda di controllo e ricarica per mantenere la funzionalità in assenza di rete."
    )

    if elettroblocco:
        aggiungi(
            articoli, "ELETTRO_STANDARD",
            "PF54.59 Elettroblocco Standard",
            "Elettroblocco per chiusura automatica della porta in configurazione standard."
        )

else:
    if ante == "1 anta":
        aggiungi(
            articoli, "ER140_1",
            "PF54.13 ER140 Ridondante 1 anta",
            "Automazione ridondante per porta scorrevole a una anta, indicata per uscite di emergenza e vie di fuga."
        )
    else:
        aggiungi(
            articoli, "ER140_2",
            "PF54.14 ER140 Ridondante 2 ante",
            "Automazione ridondante per porta scorrevole a due ante, indicata per uscite di emergenza e vie di fuga."
        )

    aggiungi(
        articoli, "SSR3_ER_BL",
        "Hotron SSR3-ER-BL Radar evacuazione",
        "Radar specifico per gestione evacuazione e sicurezza su automazioni ridondanti."
    )

    aggiungi(
        articoli, "HR100",
        "Hotron HR100 Radar apertura e sicurezza EN16005",
        "Radar per apertura automatica e sicurezza del passaggio secondo configurazione scelta."
    )

    aggiungi(
        articoli, "DIGIDOR",
        "PF37.06 DIGIDOR Selettore",
        "Selettore DIGIDOR dedicato alla gestione delle automazioni ridondanti."
    )

    aggiungi(
        articoli, "BATTERIE",
        "PF54.73 Kit batterie con scheda controllo e ricarica",
        "Kit batterie di emergenza con scheda di controllo e ricarica per sistema ridondante."
    )

    aggiungi(
        articoli, "PULSANTE_EMERGENZA",
        "Pulsante emergenza",
        "Pulsante di emergenza per gestione sicurezza e apertura in condizioni di necessità."
    )

    if elettroblocco:
        aggiungi(
            articoli, "ELETTRO_RIDONDANTE",
            "PF54.62 Elettroblocco Ridondante",
            "Elettroblocco specifico per automazione ridondante."
        )

if allaccio:
    aggiungi(
        articoli, "ALLACCIO_COLLAUDO",
        "Allaccio e collaudo SA-TEC",
        "Collegamento elettrico, regolazione parametri, verifica funzionamento e collaudo finale eseguito da tecnici SA-TEC.",
        1,
        scontato=False
    )

imponibile = sum(a["totale"] for a in articoli)
iva = imponibile * IVA
totale = imponibile + iva

with col_right:
    st.markdown('<div class="card"><div class="card-title">📄 RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)

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

    st.markdown(
        """
        <div class="green-box">
            <b>✅ COSA INCLUDE IL PREVENTIVO</b><br><br>
            Fornitura di materiali e dispositivi selezionati secondo la configurazione scelta.<br><br>
            I prezzi singoli non vengono mostrati al cliente.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.button("✈️ RICHIEDI PREVENTIVO")
    st.button("⬇️ SCARICA PDF")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="card"><div class="card-title">📌 DESCRIZIONE FORNITURA CLIENTE</div>', unsafe_allow_html=True)

st.write(f"Configurazione selezionata: **{tipo} - {ante}**")
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
