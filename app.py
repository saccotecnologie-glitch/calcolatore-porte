import streamlit as st
import pandas as pd

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
    .price-box { background-color: #ffffff; padding: 22px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3d59; margin-bottom: 20px; }
    .total-box { background-color: #1e3d59; color: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 15px rgba(30,61,89,0.3); text-align: center; margin-top: 15px; }
    .total-box h1 { color: #ffc13b !important; margin: 10px 0 0 0; font-size: 38px; }
    </style>
""", unsafe_allow_html=True)

st.title("🚪 SA-TEC S.R.L.s")
st.subheader("Configuratore Online Professionale Completo — Automazione PW100")
st.markdown("Usa il pannello laterale per configurare ogni dettaglio della porta. Il prezzo e il computo metrico si aggiorneranno in tempo reale.")
st.markdown("---")

# --- PANNELLO LATERALE DI CONFIGURAZIONE ---
st.sidebar.header("🔧 Configura la tua Porta")

tipo_porta = st.sidebar.selectbox("Modello Automazione:", options=["Standard", "Ridondante"], index=0)
num_ante = st.sidebar.selectbox("Numero di Ante:", options=["1 Anta", "2 Ante"], index=1)
lunghezza_t = st.sidebar.number_input("Lunghezza Complessiva T (in metri):", min_value=1.0, max_value=7.0, value=2.5, step=0.1)
colore_profili = st.sidebar.selectbox("Finitura / Colore Profili:", options=["Argento Anodizzato", "Verniciato RAL Standard", "Verniciato RAL Speciale"])

st.sidebar.markdown("### 🪟 Configurazione Vetratura")
tipo_vetro = st.sidebar.selectbox("Tipo di Vetro:", options=["Trasparente Stratificato 10/11mm", "Camera Antisfondamento", "Nessun Vetro (Solo Telaio)"])

st.sidebar.markdown("### ➕ Accessori e Sensori Opzionali")
include_selettore = st.sidebar.checkbox("ICON – Selettore Touch (+ 3 tessere Tag)", value=True)
include_batterie = st.sidebar.checkbox("Kit batterie di emergenza (Antincendio/Continuità)", value=True)
radar_aggiuntivi = st.sidebar.slider("Radar di sicurezza EN16005 aggiuntivi:", min_value=0, max_value=4, value=0)
elettroblocco = st.sidebar.checkbox("Elettroblocco di chiusura con sblocco manuale", value=False)

# --- LOGICA DI CALCOLO LISTINO ---
iva_aliquota = 0.22
righe_preventivo = []

# Calcolo base profili e cassa in base a lunghezza T
righe_preventivo.append({"Codice": "PF54.25", "Categoria": "PROFILI", "Descrizione": f"Profilo cassa ({colore_profili})", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 35.50})
righe_preventivo.append({"Codice": "PF54.43", "Categoria": "PROFILI", "Descrizione": f"Profilo coperchio ({colore_profili})", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 22.10})
righe_preventivo.append({"Codice": "PF25.84", "Categoria": "TRASMISSIONE", "Descrizione": "Cinghia dentata rinforzata ad alta resistenza", "Q.tà": round(lunghezza_t * 2.1, 2), "UM": "m", "Prezzo Unitario": 7.20})

# Costi variabili in base al numero di ante
moltiplicatore_ante = 1 if num_ante == "1 Anta" else 2
righe_preventivo.append({"Codice": "K-ANTA", "Categoria": "CARRELLI", "Descrizione": f"Kit carrelli di sospensione e attacchi per {num_ante}", "Q.tà": moltiplicatore_ante, "UM": "kit", "Prezzo Unitario": 48.00})

# Aggiunta Vetro se selezionato
if tipo_vetro != "Nessun Vetro (Solo Telaio)":
    prezzo_mq_vetro = 85.00 if "Stratificato" in tipo_vetro else 130.00
    superficie_stimata = round(lunghezza_t * 2.2, 2)  # altezza standard stimata 2.2m
    righe_preventivo.append({"Codice": "VTR-01", "Categoria": "VETRATURA", "Descrizione": f"Vetro {tipo_vetro} (Sup. stimata)", "Q.tà": superficie_stimata, "UM": "mq", "Prezzo Unitario": prezzo_mq_vetro})

# Gestione accessori opzionali
if include_selettore:
    righe_preventivo.append({"Codice": "PF37.00", "Categoria": "ACCESSORIO", "Descrizione": "ICON – Selettore Funzioni Touch screen + 3 Tag", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 75.00})
if include_batterie:
    righe_preventivo.append({"Codice": "PF54.73", "Categoria": "ACCESSORIO", "Descrizione": "Gruppo batterie d'emergenza a scarica controllata", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 89.00})
if elettroblocco:
    righe_preventivo.append({"Codice": "LOCK-99", "Categoria": "SICUREZZA", "Descrizione": "Elettroblocco di bloccaggio meccanico motorizzato", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 145.00})
if radar_aggiuntivi > 0:
    righe_preventivo.append({"Codice": "RAD-SENS", "Categoria": "SICUREZZA", "Descrizione": "Radar volumetrico combinato apertura/sicurezza EN16005", "Q.tà": radar_aggiuntivi, "UM": "pz", "Prezzo Unitario": 168.00})

# Maggiorazione per modello Ridondante
if tipo_porta == "Ridondante":
    righe_preventivo.append({"Codice": "RND-K", "Categoria": "RIDONDANTE", "Descrizione": "Sistema a doppio motore con scheda di controllo ridondante di sicurezza", "Q.tà": 1, "UM": "sistema", "Prezzo Unitario": 1250.00})

# Manodopera e montaggio standard
righe_preventivo.append({"Codice": "LAB-01", "Categoria": "MANODOPERA", "Descrizione": "Premontaggio, cablaggio hardware e collaudo in officina SA-TEC", "Q.tà": 4, "UM": "h", "Prezzo Unitario": 55.00})

# Creazione Tabella Dati
df = pd.DataFrame(righe_preventivo)
df["Totale (€)"] = (df["Q.tà"] * df["Prezzo Unitario"]).round(2)

# Formattazione per la tabella visiva
df_visualizzazione = df.copy()
df_visualizzazione["Prezzo Unitario (€)"] = df_visualizzazione["Prezzo Unitario"].map("€ {:.2f}".format)
df_visualizzazione["Totale (€)"] = df_visualizzazione["Totale (€)"].map("€ {:.2f}".format)

# --- COSTRUZIONE INTERFACCIA GRAFICA ---
col1, col2 = st.columns([5, 3])

with col1:
    st.markdown("### 📋 Computo Metrico di Dettaglio")
    st.dataframe(df_visualizzazione[["Codice", "Categoria", "Descrizione", "Q.tà", "UM", "Prezzo Unitario (€)", "Totale (€)"]], hide_index=True, use_container_width=True)

with col2:
    st.markdown("### 🧾 Sintesi Economica")
    totale_imponibile = df["Totale (€)"].sum()
    totale_iva = totale_imponibile * iva_aliquota
    prezzo_finito = totale_imponibile + totale_iva
    
    st.markdown(f"""
        <div class="price-box">
            <p style="margin: 0 0 8px 0; color: #555;"><strong>Automazione:</strong> {tipo_porta} ({num_ante})</p>
            <p style="margin: 0 0 8px 0; color: #555;"><strong>Lunghezza Profilo T:</strong> {lunghezza_t} metri</p>
            <p style="margin: 0 0 8px 0; color: #555;"><strong>Finitura Telaio:</strong> {colore_profili}</p>
            <hr style="border: 0; border-top: 1px solid #ddd; margin: 12px 0;">
            <p style="margin: 0 0 5px 0; font-size: 16px; color: #333;">Totale Imponibile: <strong>€ {totale_imponibile:,.2f}</strong></p>
            <p style="margin: 0; font-size: 14px; color: #666;">IVA di legge (22%): € {totale_iva:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="total-box">
            <span style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Prezzo Finale Chiavi in Mano</span>
            <h1>€ {prezzo_finito:,.2f}</h1>
            <span style="font-size: 11px; opacity: 0.75; display: block; margin-top: 5px;">* Prezzo calcolato franco fabbrica</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("📝 **Note Generali:** I prezzi esposti seguono il listino SA-TEC PW100 in vigore. Per personalizzazioni fuori sagoma o vetri speciali contattare l'ufficio tecnico.")
