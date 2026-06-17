import streamlit as st

st.set_page_config(page_title="Configuratore SA-TEC")

st.title("Configuratore Porta Automatica SA-TEC")

luce = st.number_input("Luce porta in mm", 800, 5000, 1600)
ante = st.selectbox("Numero ante", ["1 anta", "2 ante"])

tipo = st.selectbox(
    "Tipo automazione",
    [
        "Standard",
        "Ridondante vie di fuga"
    ]
)

peso = st.number_input("Peso anta in kg", 20, 250, 80)

montaggio = st.checkbox("Montaggio incluso", value=True)
elettroblocco = st.checkbox("Elettroblocco")
batterie = st.checkbox("Kit batterie")
selettore = st.checkbox("Selettore funzioni")

# PREZZI INTERNI NON VISIBILI AL CLIENTE
PREZZI = {
    "standard_1": 2140,
    "standard_2": 2200,
    "ridondante_1": 2600,
    "ridondante_2": 2900,
    "montaggio": 500,
    "elettroblocco": 285,
    "batterie": 180,
    "selettore": 178,
    "radar_hotron": 375,
    "pulsante_emergenza": 130,
}

RICARICO = 1.40

totale = 0
descrizione = []

if tipo == "Standard":
    if ante == "1 anta":
        totale += PREZZI["standard_1"] * RICARICO
    else:
        totale += PREZZI["standard_2"] * RICARICO

    descrizione.append("Automazione per porta scorrevole automatica standard")
    descrizione.append(f"Configurazione {ante}")

if tipo == "Ridondante vie di fuga":
    if ante == "1 anta":
        totale += PREZZI["ridondante_1"] * RICARICO
    else:
        totale += PREZZI["ridondante_2"] * RICARICO

    descrizione.append("Automazione ridondante per vie di fuga")
    descrizione.append("Sistema conforme per uscite di emergenza")
    descrizione.append("Radar Hotron per sicurezza e via di fuga")
    descrizione.append("Pulsante di emergenza incluso")
    descrizione.append(f"Configurazione {ante}")

    totale += PREZZI["radar_hotron"] * RICARICO
    totale += PREZZI["pulsante_emergenza"] * RICARICO

if luce > 2500:
    totale += 350
    descrizione.append("Maggiorazione per luce porta superiore a 2500 mm")

if peso > 120:
    totale += 250
    descrizione.append("Maggiorazione per ante pesanti")

if montaggio:
    totale += PREZZI["montaggio"]
    descrizione.append("Montaggio, collegamento e collaudo inclusi")

if elettroblocco:
    totale += PREZZI["elettroblocco"] * RICARICO
    descrizione.append("Elettroblocco per chiusura automatica")

if batterie:
    totale += PREZZI["batterie"] * RICARICO
    descrizione.append("Kit batterie di emergenza")

if selettore:
    totale += PREZZI["selettore"] * RICARICO
    descrizione.append("Selettore funzioni digitale")

st.divider()

st.subheader("Descrizione fornitura")

for voce in descrizione:
    st.write("• " + voce)

st.divider()

st.subheader("Totale preventivo")

st.success(f"€ {totale:,.2f} + IVA")

st.caption("Il preventivo è indicativo e soggetto a verifica tecnica SA-TEC.")
