import streamlit as st

st.set_page_config(
    page_title="Preventivatore SA-TEC | Porte Automatiche",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile grafico aziendale - Pulito e focalizzato sul prezzo totale
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    h1, h2, h3 { color: #1e3d59; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .price-box { background-color: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3d59; margin-bottom: 20px; }
    .total-box { background-color: #1e3d59; color: white; padding: 35px; border-radius: 8px; box-shadow: 0 4px 15px rgba(30,61,89,0.3); text-align: center; margin-top: 25px; }
    .total-box h1 { color: #ffc13b !important; margin: 15px 0 0 0; font-size: 46px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🚪 SA-TEC S.R.L.s")
st.subheader("Calcolo Preventivo Istantaneo — Automazione PW100")
st.markdown("Configura le caratteristiche della porta nel pannello laterale per visualizzare il prezzo.")
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
iva_aliquota = 0.22
totale_imponibile = 0.0

# Calcolo costi materiali
totale_imponibile += lunghezza_t_m * 35.50  # Profilo cassa
totale_imponibile += lunghezza_t_m * 22.10  # Profilo coperchio
totale_imponibile += (lunghezza_t_m * 2.1) * 7.20  # Cinghia

# Costo carrelli
moltiplicatore_ante = 1 if num_ante == "1 Anta" else 2
totale_imponibile += moltiplicatore_ante * 48.00

# Costo accessori
if include_selettore: totale_imponibile += 75.00
if include_batterie: totale_imponibile += 89.00
if elettroblocco: totale_imponibile += 145.00
totale_imponibile += radar_aggiuntivi * 168.00

# Maggiorazione ridondante e manodopera
if tipo_porta == "Ridondante": totale_imponibile += 1250.00
totale_imponibile += 4 * 55.00  # Manodopera

# Calcolo prezzo finale ivato
prezzo_finito = totale_imponibile * (1 + iva_aliquota)

# --- INTERFACCIA UTENTE (SOLO RIEPILOGO E PREZZO FINALE) ---
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 Specifiche Configurate")
    st.markdown(f"""
        <div class="price-box">
            <p style="font-size: 16px; margin: 0 0 10px 0; color: #333;"><strong>Tipologia:</strong> Automazione {tipo_porta} ({num_ante})</p>
            <p style="font-size: 16px; margin: 0 0 10px 0; color: #333;"><strong>Vano Luce:</strong> {passaggio_luce_cm} x {altezza_luce_cm} cm</p>
            <p style="font-size: 16px; margin: 0 0 10px 0; color: #333;"><strong>Finitura Profili:</strong> {colore_profili}</p>
            <p style="font-size: 16px; margin: 0; color: #333;"><strong>Ingombro Totale Macchina (T):</strong> {lunghezza_t_cm} cm</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🧾 Preventivo Economico")
    st.markdown(f"""
        <div class="total-box">
            <span style="font-size: 16px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; font-weight: bold;">Prezzo Totale Chiavi in Mano</span>
            <h1>€ {prezzo_finito:,.2f}</h1>
            <span style="font-size: 12px; opacity: 0.8; display: block; margin-top: 10px;">* IVA e manodopera di assemblaggio incluse nel prezzo</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("📝 **Note per il cliente:** Il presente modulo genera un preventivo indicativo automatizzato basato sui listini ufficiali SA-TEC. Per conferme d'ordine o varianti fuori sagoma, vi preghiamo di contattare i nostri uffici.")
