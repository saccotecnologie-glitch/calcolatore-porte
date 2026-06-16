import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Preventivatore SA-TEC | Porte Automatiche",
    page_icon="🚪",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
st.subheader("Configuratore Online Professionale — Automazione PW100")
st.markdown("Compila i dettagli strutturali qui a sinistra per generare istantaneamente il tuo preventivo personalizzato.")
st.markdown("---")

st.sidebar.header("🔧 Configura la tua Porta")
tipo_porta = st.sidebar.selectbox("Modello Automazione:", options=["Standard", "Ridondante"], index=1)
lunghezza_t = st.sidebar.number_input("Lunghezza Complessiva T (in metri):", min_value=1.0, max_value=7.0, value=2.5, step=0.1)

st.sidebar.markdown("### ➕ Accessori Opzionali")
include_selettore = st.sidebar.checkbox("ICON – Selettore Touch (+ 3 tessere Tag)", value=False)
include_batterie = st.sidebar.checkbox("Kit batterie con scheda di controllo e ricarica", value=False)

iva_aliquota = 0.22
righe_preventivo = []

righe_preventivo.append({"Codice": "PF54.25", "Categoria": "PROFILI/CASSA", "Descrizione": "Profilo cassa grezzo 6,6 mt", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 32.09})
righe_preventivo.append({"Codice": "PF54.43", "Categoria": "PROFILI/CASSA", "Descrizione": "Profilo coperchio anodizzato naturale 6,6 mt", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 20.02})
righe_preventivo.append({"Codice": "PF54.55", "Categoria": "PROFILI/CASSA", "Descrizione": "Guarnizione per coperchio in gomma 35 m", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 2.36})
righe_preventivo.append({"Codice": "PF25.84", "Categoria": "TRASMISSIONE", "Descrizione": "Rotolo cinghia dentata 60 m", "Q.tà": round(lunghezza_t * 1.8, 2), "UM": "m", "Prezzo Unitario": 6.91})
righe_preventivo.append({"Codice": "PF54.90", "Categoria": "GUIDA", "Descrizione": "Profilo guida in alluminio anodizzato 6,6 mt", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 4.60})
righe_preventivo.append({"Codice": "PF54.91", "Categoria": "GUIDA", "Descrizione": "Guarnizione guida in gomma 30 m", "Q.tà": lunghezza_t, "UM": "m", "Prezzo Unitario": 1.36})
righe_preventivo.append({"Codice": "HOTRON", "Categoria": "ACCESSORIO", "Descrizione": "Radar apertura sicurezza EN16005", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 175.50})

if include_selettore:
    righe_preventivo.append({"Codice": "PF37.00", "Categoria": "ACCESSORIO", "Descrizione": "ICON – Selettore Touch con 3 tessere Tag", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 70.40})
if include_batterie:
    righe_preventivo.append({"Codice": "PF54.73", "Categoria": "ACCESSORIO", "Descrizione": "Kit batterie con scheda di controllo e ricarica", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 72.87})

if tipo_porta == "Ridondante":
    righe_preventivo.append({"Codice": "PF54.13", "Categoria": "RIDONDANTE", "Descrizione": "KIT RIDONDANTE 1 ANTA", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 1321.45})
    righe_preventivo.append({"Codice": "PF54.62", "Categoria": "RIDONDANTE", "Descrizione": "ELETTROBLOCCO RIDONDANTE", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 175.99})
    righe_preventivo.append({"Codice": "PEM130", "Categoria": "RIDONDANTE", "Descrizione": "PULSANTE EMERGENZA", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 80.28})
    righe_preventivo.append({"Codice": "SSR3-ER-BL", "Categoria": "RIDONDANTE", "Descrizione": "RADAR HOTRON SSR3-ER-BL", "Q.tà": 1, "UM": "pz", "Prezzo Unitario": 231.56})

righe_preventivo.append({"Codice": "ASSEMBL.", "Categoria": "MANODOPERA", "Descrizione": "Assemblaggio e collaudo automazione in officina", "Q.tà": 2, "UM": "h", "Prezzo Unitario": 65.00})

df = pd.DataFrame(righe_preventivo)
df["Totale (€)"] = (df["Q.tà"] * df["Prezzo Unitario"]).round(2)

df_visualizzazione = df.copy()
df_visualizzazione["Prezzo Unitario (€)"] = df_visualizzazione["Prezzo Unitario"].map("€ {:.2f}".format)
df_visualizzazione["Totale (€)"] = df_visualizzazione["Totale (€)"].map("€ {:.2f}".format)

col1, col2 = st.columns([5, 3])
with col1:
    st.markdown("### 📋 Computo Metrico e Righe Selezionate")
    st.dataframe(df_visualizzazione[["Codice", "Categoria", "Descrizione", "Q.tà", "UM", "Prezzo Unitario (€)", "Totale (€)"]], hide_index=True, use_container_width=True)

with col2:
    st.markdown("### 🧾 Sintesi Economica")
    totale_imponibile = df["Totale (€)"].sum()
    totale_iva = totale_imponibile * iva_aliquota
    prezzo_finito = totale_imponibile + totale_iva
    
    st.markdown(f"""
        <div class="price-box">
            <p style="margin: 0 0 8px 0; color: #555;"><strong>Modello Scelto:</strong> Automazione {tipo_porta}</p>
            <p style="margin: 0 0 8px 0; color: #555;"><strong>Larghezza Struttura (T):</strong> {lunghezza_t} metri</p>
            <hr style="border: 0; border-top: 1px solid #ddd; margin: 12px 0;">
            <p style="margin: 0 0 5px 0; font-size: 16px; color: #333;">Totale Imponibile: <strong>€ {totale_imponibile:,.2f}</strong></p>
            <p style="margin: 0; font-size: 14px; color: #666;">IVA di legge (22%): € {totale_iva:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="total-box">
            <span style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Prezzo Totale Preventivato</span>
            <h1>€ {prezzo_finito:,.2f}</h1>
            <span style="font-size: 11px; opacity: 0.75; display: block; margin-top: 5px;">* IVA inclusa nel totale</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("📝 **Note Generali:** Il presente modulo è un configuratore automatico basato sui listini ufficiali SA-TEC. Non costituisce vincolo contrattuale formale.")
