import streamlit as st

st.set_page_config(page_title="Preventivo Porta Automatica SA-TEC")

st.title("Configuratore Porta Automatica")
st.subheader("SA-TEC S.R.L.s")

luce = st.number_input("Luce porta in mm", min_value=800, max_value=4000, value=1600)
ante = st.selectbox("Numero ante", ["1 anta", "2 ante"])
peso = st.number_input("Peso anta in kg", min_value=20, max_value=200, value=80)

montaggio = st.checkbox("Includi montaggio", value=True)
elettroblocco = st.checkbox("Elettroblocco")
batteria = st.checkbox("Kit batterie")
selettore = st.checkbox("Selettore funzioni")
radar_extra = st.checkbox("Radar aggiuntivo")

# PREZZI INTERNI NASCOSTI
prezzo_1_anta = 2140
prezzo_2_ante = 2200
ricarico = 1.40

totale = 0

if ante == "1 anta":
    totale += prezzo_1_anta * ricarico
else:
    totale += prezzo_2_ante * ricarico

# Maggiorazione per luce porta
if luce > 2500:
    totale += 350

# Maggiorazione peso
if peso > 120:
    totale += 250

if montaggio:
    totale += 500

if elettroblocco:
    totale += 285 * ricarico

if batteria:
    totale += 180 * ricarico

if selettore:
    totale += 178 * ricarico

if radar_extra:
    totale += 295 * ricarico

st.divider()

st.subheader("Totale preventivo indicativo")

st.success(f"€ {totale:,.2f} + IVA")

st.caption("Preventivo indicativo soggetto a verifica tecnica SA-TEC.")
