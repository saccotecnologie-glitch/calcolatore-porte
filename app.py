 import streamlit as st

st.set_page_config(
    page_title="Preventivatore SA-TEC | Porte Automatiche",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile grafico aziendale
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    h1, h2, h3 { color: #1e3d59; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .price-box { background-color: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3d59; margin-bottom: 20px; }
    .total-box { background-color: #1e3d59; color: white; padding: 35px; border-radius: 8px; box-shadow: 0 4px 15px rgba(30,61,89,0.3); text-align: center; margin-top: 25px; }
    .total-box h1 { color: #ffc13b !important; margin: 15px 0 0 0; font-size: 46px; font-weight: bold; }
    
    .print-button {
        display: block;
        width: 100%;
        text-align: center;
        background-color: #ffffff;
        color: #1e3d59;
        padding: 10px;
        border: 1px solid #1e3d59;
        border-radius: 6px;
        font-weight: bold;
        text-decoration: none;
        font-size: 14px;
        margin-top: 10px;
        cursor: pointer;
    }
    .print-button:hover { background-color: #1e3d59; color: white; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- CARICAMENTO NATIVO DEL LOGO ---
# Questo comando obbliga il sistema a cercare il file "logo satec.jpg" caricato sul tuo GitHub
try:
    st.image("logo satec.jpg", use_container_width=True)
except Exception:
    # Sistema di sicurezza: se il nome del file ha estensioni diverse (es. .jpeg o maiuscole), prova a caricarlo comunque
    try:
        st.image("logo satec.JPEG", use_container_width=True)
    except Exception:
        st.title("🚪 SA-TEC S.R.L.s")

st.subheader("Configuratore Professionale — Automazione PW100")
st.markdown("Seleziona i parametri del vano luce e gli accessori per generare il preventivo ufficiale.")
st.markdown("---")

# --- PANNELLO LATERALE DI CONFIGURAZIONE ---
st.sidebar.header("🔧 Configura la tua Porta")

tipo_porta = st.sidebar.selectbox("Modello Automazione:", options=["Standard", "Ridondante"], index=0)
num_ante = st.sidebar.selectbox("Numero di Ante:", options=["1 Anta", "2 Ante"], index=1)

# Inserimento in Centimetri (cm)
passaggio_luce_cm = st.sidebar.number_input("Larghezza Passaggio Luce L (in cm):", min_value=70, max_value=300, value=120, step=5)
altezza_luce_cm = st.sidebar.number_input("Altezza Passaggio Luce H (in cm):", min_value=150, max_value=300, value=210, step=5)

colore_profili = st.sidebar.selectbox("Finitura / Colore Profili:", options=["Argento Anodizzato", "Verniciato RAL Standard", "Verniciato RAL Speciale"])

st.sidebar.markdown("### ➕ Accessori Opzionali")
include_selettore = st.sidebar.checkbox("ICON – Selettore Touch (+ 3 tessere Tag)", value=True)
include_batterie = st.sidebar.checkbox("Kit batterie di emergenza", value=True)
elettroblocco = st.sidebar.checkbox("Elettroblocco di chiusura con sblocco manuale", value=False)
radar_aggiuntivi = st.sidebar.slider("Radar di sicurezza EN16005 aggiuntivi:", min_value=0, max_value=4, value=0)

# --- LOGICA DI CALCOLO INTERNA (INVISIBILE AL CLIENTE) ---
if num_ante == "1 Anta":
    lunghezza_t_cm = (passaggio_luce_cm * 2) + 10
else:
    lunghezza_t_cm = (passaggio_luce_cm * 2) + 20

lunghezza_t_m = lunghezza_t_cm / 100.0
totale_imponibile = 0.0

# Elenco dei materiali per la visualizzazione pulita (senza prezzi)
materiali_selezionati = []

# 1. Calcolo costi e lista profili
totale_imponibile += lunghezza_t_m * 35.50  
materiali_selezionati.append(f"Profilo cassa in finitura {colore_profili} (Sviluppo: {lunghezza_t_cm} cm)")

totale_imponibile += lunghezza_t_m * 22.10  
materiali_selezionati.append(f"Profilo coperchio in finitura {colore_profili}")

totale_imponibile += (lunghezza_t_m * 2.1) * 7.20  
materiali_selezionati.append("Cinghia dentata rinforzata ad alta resistenza")

# 2. Carrelli
moltiplicatore_ante = 1 if num_ante == "1 Anta" else 2
totale_imponibile += moltiplicatore_ante * 48.00
materiali_selez
