import streamlit as st

st.set_page_config(page_title="Configuratore SA-TEC", layout="centered")

IVA = 0.22
SCONTO_50 = 0.50
SCONTO_EXTRA_5 = 0.95
MAGGIORAZIONE = 1.35

def prezzo_cliente(listino):
    return listino * SCONTO_50 * SCONTO_EXTRA_5 * MAGGIORAZIONE

def euro(valore):
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

LISTINI = {
    # AUTOMAZIONI STANDARD
    "PF54.05": 1236.00,   # LH100 1 anta
    "PF54.06": 1298.00,   # LH100 2 ante

    # AUTOMAZIONI RIDONDANTI
    "PF54.13": 2140.00,   # Ridondante 1 anta
    "PF54.14": 2200.00,   # Ridondante 2 ante

    # PROFILI / TRAVERSA
    "PF54.25": 343.00 / 6.6,   # Profilo cassa
    "PF54.43": 214.00 / 6.6,   # Coperchio
    "PF54.55": 134.00 / 35,    # Guarnizione coperchio
    "PF25.84": 671.00 / 60,    # Cinghia
    "PF54.90": 49.20 / 6.6,    # Guida
    "PF54.91": 66.00 / 30,     # Guarnizione guida

    # ACCESSORI STANDARD
    "HR100": 135.00,       # Hotron HR100
    "PF37.00": 114.00,     # ICON Touch con 3 tag
    "PF54.73": 118.00,     # Kit batterie
    "PF54.59": 195.00,     # Elettroblocco standard

    # ACCESSORI RIDONDANTE
    "SSR3-ER-BL": 375.00,  # Radar evacuazione
    "PF37.06": 180.00,     # DIGIDOR
    "PEM130": 130.00,      # Pulsante emergenza
    "PF54.62": 290.00,     # Elettroblocco ridondante

    # SERVIZI
    "ALLACCIO": 350.00,
}

def aggiungi(articoli, codice, descrizione, quantita=1, scontato=True):
    listino = LISTINI[codice]
    prezzo = prezzo_cliente(listino) if scontato else listino
    articoli.append({
        "codice": codice,
        "descrizione": descrizione,
        "quantita": quantita,
        "totale": prezzo * quantita
    })

def calcola_traversa(luce_mm, ante):
    if ante == "1 anta":
        lunghezza_mm = (luce_mm * 2) + 100
    else:
        lunghezza_mm = luce_mm + 100
    return lunghezza_mm / 1000

st.title("Configuratore Porta Automatica")
st.subheader("SA-TEC S.R.L.s")

tipo = st.selectbox("Tipo automazione", ["Standard", "Ridondante"])
ante = st.selectbox("Numero ante", ["1 anta", "2 ante"])
luce_mm = st.number_input("Luce passaggio in mm", min_value=800, max_value=5000, value=1600, step=50)

elettroblocco = st.checkbox("Aggiungi elettroblocco", value=False)
allaccio = st.checkbox("Allaccio e collaudo SA-TEC", value=True)

T = calcola_traversa(luce_mm, ante)

articoli = []

# TRAVERSA / PROFILI
aggiungi(articoli, "PF54.25", "Profilo cassa traversa in alluminio", T)
aggiungi(articoli, "PF54.43", "Coperchio traversa in alluminio", T)
aggiungi(articoli, "PF54.55", "Guarnizione coperchio", T)
aggiungi(articoli, "PF25.84", "Cinghia dentata", T * 1.8)
aggiungi(articoli, "PF54.90", "Profilo guida scorrimento", T)
aggiungi(articoli, "PF54.91", "Guarnizione guida", T)

# STANDARD
if tipo == "Standard":
    if ante == "1 anta":
        aggiungi(articoli, "PF54.05", "Automazione Sesamo LH100 per porta scorrevole 1 anta")
    else:
        aggiungi(articoli, "PF54.06", "Automazione Sesamo LH100 per porta scorrevole 2 ante")

    aggiungi(articoli, "HR100", "Radar Hotron HR100 apertura e sicurezza EN16005", 2)
    aggiungi(articoli, "PF37.00", "ICON – Selettore Touch con 3 tessere Tag")
    aggiungi(articoli, "PF54.73", "Kit batterie con scheda di controllo e ricarica")

    if elettroblocco:
        aggiungi(articoli, "PF54.59", "Elettroblocco standard")

# RIDONDANTE
if tipo == "Ridondante":
    if ante == "1 anta":
        aggiungi(articoli, "PF54.13", "Automazione Sesamo ER140 ridondante 1 anta")
    else:
        aggiungi(articoli, "PF54.14", "Automazione Sesamo ER140 ridondante 2 ante")

    aggiungi(articoli, "SSR3-ER-BL", "Radar Hotron SSR3-ER-BL per evacuazione")
    aggiungi(articoli, "HR100", "Radar Hotron HR100 apertura e sicurezza EN16005")
    aggiungi(articoli, "PF37.06", "DIGIDOR selettore per ridondante")
    aggiungi(articoli, "PF54.73", "Kit batterie con scheda di controllo e ricarica")
    aggiungi(articoli, "PEM130", "Pulsante emergenza")

    if elettroblocco:
        aggiungi(articoli, "PF54.62", "Elettroblocco ridondante")

# ALLACCIO E COLLAUDO
if allaccio:
    aggiungi(articoli, "ALLACCIO", "Allaccio e collaudo SA-TEC", 1, scontato=False)

imponibile = sum(a["totale"] for a in articoli)
iva = imponibile * IVA
totale = imponibile + iva

st.divider()

st.subheader("Descrizione fornitura")

st.write(f"Configurazione: **{tipo} - {ante}**")
st.write(f"Luce passaggio: **{luce_mm} mm**")
st.write(f"Lunghezza traversa calcolata: **{T:.2f} m**")

for articolo in articoli:
    st.write(f"✓ {articolo['descrizione']}")

if not allaccio:
    st.warning("Allaccio e collaudo esclusi dalla presente offerta.")

st.divider()

st.subheader("Totale preventivo")

st.success(f"Imponibile: {euro(imponibile)} + IVA")
st.success(f"Totale IVA inclusa: {euro(totale)}")

st.caption("Il preventivo è indicativo e soggetto a verifica tecnica SA-TEC.")
