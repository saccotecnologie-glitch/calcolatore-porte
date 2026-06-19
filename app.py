import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import csv
import pandas as pd
import random
import string
import smtplib
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime, date

# =========================================================
# CONFIGURATORE SA-TEC PRO
# Versione con:
# - Login utenti
# - Registrazione cliente automatica
# - Creazione utenti da area ADMIN
# - Salvataggio utenti su CSV
# - Salvataggio preventivi su CSV
# Formula definitiva:
# Costo SA-TEC reale = Listino × 0,50 × 0,95
# Prezzo vendita = Costo SA-TEC × (1 + ricarico utente / 100)
# Ricarico personalizzato assegnabile da ADMIN
# =========================================================

st.set_page_config(
    page_title="Configuratore Porte Automatiche SA-TEC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

AZIENDA = "SA-TEC S.R.L.s"
SEDE = "Via L. Settembrini 84, 88046 Lamezia Terme (CZ)"
PIVA = "P.IVA 04009610793"
TELEFONO = "0968-036797"
EMAIL = "sacco.tecnologie@gmail.com"
PEC = "sa-tec@pec.it"
CODICE_UNIVOCO = "M5UXCR1"
IBAN = "IT30S0825842841007000002877"
IVA = 0.22

PREVENTIVI_CSV = "preventivi_satec.csv"
UTENTI_CSV = "utenti_satec.csv"
CLIENTI_CSV = "clienti_satec.csv"
LOGHI_DIR = Path("loghi_utenti")
LOGHI_DIR.mkdir(exist_ok=True)

# =========================
# UTENTI BASE
# =========================

UTENTI_BASE = {
    "ADMIN": {
        "password": "SATEC-ADMIN",
        "profilo": "SA-TEC",
        "nome": "SA-TEC Amministratore",
        "azienda": "SA-TEC",
        "telefono": "",
        "email": "",
        "ricarico": "0"
    },
    "ROSSI01": {
        "password": "R2026#",
        "profilo": "RIVENDITORE",
        "nome": "Rivenditore Rossi",
        "azienda": "Rossi",
        "telefono": "",
        "email": "",
        "ricarico": "30"
    },
    "VERDI01": {
        "password": "V2026#",
        "profilo": "RIVENDITORE",
        "nome": "Rivenditore Verdi",
        "azienda": "Verdi",
        "telefono": "",
        "email": "",
        "ricarico": "30"
    },
    "GROS001": {
        "password": "G2026#",
        "profilo": "GROSSISTA",
        "nome": "Grossista Mario",
        "azienda": "",
        "telefono": "",
        "email": "",
        "ricarico": "20"
    },
    "GROS002": {
        "password": "G22026#",
        "profilo": "GROSSISTA",
        "nome": "Grossista Luca",
        "azienda": "",
        "telefono": "",
        "email": "",
        "ricarico": "20"
    },
}

PROFILI = {
    "CLIENTE": "Cliente finale",
    "RIVENDITORE": "Rivenditore",
    "GROSSISTA": "Grossista",
    "SA-TEC": "SA-TEC",
}

LISTINI = {
    "PW100_1": 1236.00,
    "PW100_2": 1298.00,
    "ER140_1": 2140.00,
    "ER140_2": 2200.00,

    "CASSA": 343.00 / 6.6,
    "COPERCHIO": 214.00 / 6.6,
    "GUARN_COPERCHIO": 134.00 / 35,
    "PF54_91_GUARN_ANTIVIBRAZIONE": 2.50,
    "CINGHIA": 671.00 / 60,
    "GUIDA": 49.20 / 6.6,
    "GUARN_GUIDA": 66.00 / 30,

    "HR100": 285.00,
    "ICON": 114.00,
    "BATTERIE": 118.00,
    "ELETTRO_STANDARD": 195.00,

    "SSR3_ER_BL": 375.00,
    "DIGIDOR": 180.00,
    "PULSANTE_EMERGENZA": 130.00,
    "ELETTRO_RIDONDANTE": 290.00,

    "RADAR_SICUREZZA_LATERALE": 280.00,

    "ASSEMBLAGGIO": 130.00,
    "ALLACCIO_COLLAUDO_STANDARD": 350.00,
    "ALLACCIO_COLLAUDO_RIDONDANTE": 400.00,
}

# =========================
# FUNZIONI UTILI
# =========================



def tabella_html_sicura(dati):
    """
    Mostra tabelle senza usare st.dataframe, evitando errore JSON/NaN di Streamlit.
    """
    df = pd.DataFrame(dati)
    if df.empty:
        return "<p>Nessun dato disponibile.</p>"
    df = df.fillna("").astype(str)
    return df.to_html(index=False, escape=False)

def dataframe_sicuro(dati):
    """
    Evita errore Streamlit con valori NaN nelle tabelle.
    Converte celle vuote/NaN in stringa vuota.
    """
    df = pd.DataFrame(dati)
    if df.empty:
        return df
    return df.fillna("").astype(str)

def euro(v):
    return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def costo_satec_reale(listino):
    return listino * 0.50 * 0.95

def ricarico_default(profilo):
    if profilo == "SA-TEC":
        return 0.0
    if profilo == "GROSSISTA":
        return 20.0
    if profilo == "RIVENDITORE":
        return 30.0
    return 35.0

RICARICO_ATTIVO = 35.0

def prezzo_vendita(listino):
    costo = costo_satec_reale(listino)
    return costo * (1 + (RICARICO_ATTIVO / 100))

def img_to_base64(paths):
    for p in paths:
        f = Path(p)
        if f.exists():
            return base64.b64encode(f.read_bytes()).decode()
    return ""


def salva_logo_utente(utente_codice, file_caricato):
    if not file_caricato:
        return ""
    try:
        est = Path(file_caricato.name).suffix.lower()
        if est not in [".png", ".jpg", ".jpeg"]:
            est = ".png"
        nome_file = f"{utente_codice.upper()}{est}"
        path_logo = LOGHI_DIR / nome_file
        path_logo.write_bytes(file_caricato.getbuffer())
        return str(path_logo)
    except Exception as e:
        st.sidebar.warning(f"Logo non salvato: {e}")
        return ""

def trova_logo_utente(utente_codice):
    for est in [".png", ".jpg", ".jpeg"]:
        p = LOGHI_DIR / f"{utente_codice.upper()}{est}"
        if p.exists():
            return str(p)
    return ""


def calcola_traversa(luce_mm, ante):
    if ante == "1 anta":
        return ((luce_mm * 2) + 100) / 1000
    return ((luce_mm * 2) + 200) / 1000

def genera_password(lunghezza=7):
    caratteri = string.ascii_uppercase + string.digits
    return "".join(random.choice(caratteri) for _ in range(lunghezza))

def normalizza_codice(testo):
    pulito = "".join(ch for ch in testo.upper().strip() if ch.isalnum())
    return pulito[:14] if pulito else "CLIENTE"


def dati_brand_preventivo(profilo, dati_utente):
    """
    SA-TEC e CLIENTE finale: preventivo intestato SA-TEC.
    RIVENDITORE/GROSSISTA: preventivo intestato con i dati della loro azienda, senza riferimenti SA-TEC.
    """
    if profilo in ["RIVENDITORE", "GROSSISTA"]:
        azienda_brand = dati_utente.get("azienda", "") or dati_utente.get("nome", "") or PROFILI.get(profilo, profilo)
        telefono_brand = dati_utente.get("telefono", "") or ""
        email_brand = dati_utente.get("email", "") or ""
        return {
            "azienda": azienda_brand,
            "sede": "",
            "piva": "",
            "telefono": telefono_brand,
            "email": email_brand,
            "pec": "",
            "iban": "",
            "codice_univoco": "",
            "mostra_satec": False
        }

    return {
        "azienda": AZIENDA,
        "sede": SEDE,
        "piva": PIVA,
        "telefono": TELEFONO,
        "email": EMAIL,
        "pec": PEC,
        "iban": IBAN,
        "codice_univoco": CODICE_UNIVOCO,
        "mostra_satec": True
    }

def html_intestazione_brand(brand):
    righe = [f"<b>{brand.get('azienda','')}</b>"]
    if brand.get("sede"):
        righe.append(brand["sede"])
    if brand.get("piva"):
        righe.append(brand["piva"])
    if brand.get("codice_univoco"):
        righe.append(f"Codice Univoco: {brand['codice_univoco']}")
    if brand.get("telefono"):
        righe.append(f"Tel. {brand['telefono']}")
    if brand.get("email"):
        righe.append(f"Email: {brand['email']}")
    if brand.get("pec"):
        righe.append(f"PEC: {brand['pec']}")
    return "<br>".join(righe)


# =========================
# UTENTI CSV
# =========================

def carica_utenti_csv():
    utenti = {}
    path = Path(UTENTI_CSV)
    if not path.exists():
        return utenti

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            codice = r.get("utente", "").strip().upper()
            if codice:
                utenti[codice] = {
                    "password": r.get("password", ""),
                    "profilo": r.get("profilo", "CLIENTE"),
                    "nome": r.get("nome", ""),
                    "azienda": r.get("azienda", ""),
                    "telefono": r.get("telefono", ""),
                    "email": r.get("email", ""),
                    "ricarico": r.get("ricarico", "")
                }
    return utenti

def salva_utente_csv(utente, password, profilo, nome, azienda, telefono, email, ricarico="35"):
    file_exists = Path(UTENTI_CSV).exists()
    campi = ["utente", "password", "profilo", "nome", "azienda", "telefono", "email", "ricarico", "data_creazione"]

    with open(UTENTI_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "utente": utente,
            "password": password,
            "profilo": profilo,
            "nome": nome,
            "azienda": azienda,
            "telefono": telefono,
            "email": email,
            "ricarico": ricarico,
            "data_creazione": datetime.now().strftime("%d/%m/%Y %H:%M")
        })

def carica_tutti_utenti():
    utenti = dict(UTENTI_BASE)
    utenti_csv = carica_utenti_csv()

    # Non permettere al file CSV di sovrascrivere l'ADMIN base.
    # Così ADMIN / SATEC-ADMIN funziona sempre.
    if "ADMIN" in utenti_csv:
        utenti_csv.pop("ADMIN", None)

    utenti.update(utenti_csv)
    return utenti

def genera_codice_progressivo(profilo, utenti):
    prefisso = {
        "CLIENTE": "CLI",
        "RIVENDITORE": "RIV",
        "GROSSISTA": "GROS",
        "SA-TEC": "ADM"
    }.get(profilo, "CLI")

    numeri = []
    for u in utenti.keys():
        if u.startswith(prefisso):
            try:
                numeri.append(int(u.replace(prefisso, "")))
            except:
                pass
    prossimo = max(numeri) + 1 if numeri else 1
    return f"{prefisso}{prossimo:04d}"


# =========================
# CODICE PREVENTIVO
# =========================

def genera_codice_preventivo():
    anno = datetime.now().year
    preventivi = carica_preventivi()
    numeri = []
    for p in preventivi:
        codice = str(p.get("codice_preventivo", ""))
        if codice.startswith(f"SAT-{anno}-"):
            try:
                numeri.append(int(codice.split("-")[-1]))
            except:
                pass
    prossimo = max(numeri) + 1 if numeri else 1
    return f"SAT-{anno}-{prossimo:04d}"

def testo_email_preventivo(codice_preventivo):
    return f"""Gentile Cliente,

in allegato / di seguito trasmettiamo il preventivo SA-TEC relativo alla fornitura richiesta.

Preventivo N° {codice_preventivo}
Validità offerta: 15 giorni dalla data di emissione.

Per qualsiasi chiarimento restiamo a completa disposizione.

Cordiali saluti

SA-TEC S.R.L.s

Claudio Sacco
Direzione Commerciale

Tel. 0968 036797

Email: sacco.tecnologie@gmail.com
PEC: sa-tec@pec.it

Via Luigi Settembrini 84
88046 Lamezia Terme (CZ)

P.IVA 04009610793
REA CZ-228835
Codice Univoco: M5UXCR1

IBAN: IT30S0825842841007000002877

Specialisti in ingressi automatici
"""


def invia_email_automatica(destinatario, codice_preventivo, html_preventivo):
    """
    Invia email automatica tramite Gmail SMTP.
    Richiede in Streamlit Secrets:
    EMAIL_USER
    EMAIL_PASSWORD
    EMAIL_SMTP = smtp.gmail.com
    EMAIL_PORT = 587
    """
    try:
        email_user = st.secrets["EMAIL_USER"]
        email_password = st.secrets["EMAIL_PASSWORD"]
        smtp_server = st.secrets.get("EMAIL_SMTP", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("EMAIL_PORT", "587"))

        msg = EmailMessage()
        msg["From"] = email_user
        msg["To"] = destinatario
        msg["Cc"] = EMAIL
        msg["Subject"] = f"Preventivo SA-TEC N° {codice_preventivo}"
        msg.set_content(testo_email_preventivo(codice_preventivo))

        # Allegato HTML stampabile: il cliente lo può aprire e stampare/salvare PDF.
        nome_file = f"Preventivo_SA-TEC_{codice_preventivo}.html"
        msg.add_attachment(
            html_preventivo.encode("utf-8"),
            maintype="text",
            subtype="html",
            filename=nome_file
        )

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)

        return True, ""

    except Exception as e:
        return False, str(e)

def aggiorna_stato_preventivo_csv(codice_preventivo, nuovo_stato, email_destinatario=""):
    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            righe = list(csv.DictReader(f))

        if not righe:
            return False

        fieldnames = list(righe[0].keys())
        for campo in ["stato", "email_invio", "data_invio"]:
            if campo not in fieldnames:
                fieldnames.append(campo)

        for r in righe:
            if str(r.get("codice_preventivo", "")) == str(codice_preventivo):
                r["stato"] = nuovo_stato
                r["email_invio"] = email_destinatario
                r["data_invio"] = datetime.now().strftime("%d/%m/%Y %H:%M")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(righe)

        return True
    except:
        return False


STATI_PREVENTIVO = ["Bozza", "Inviato", "Accettato", "Perso", "Ordinato"]

def aggiorna_stato_preventivo_admin(codice_preventivo, nuovo_stato):
    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            righe = list(csv.DictReader(f))

        if not righe:
            return False

        fieldnames = list(righe[0].keys())
        for campo in ["stato", "data_modifica_stato"]:
            if campo not in fieldnames:
                fieldnames.append(campo)

        trovato = False
        for r in righe:
            if str(r.get("codice_preventivo", "")).strip() == str(codice_preventivo).strip():
                r["stato"] = nuovo_stato
                r["data_modifica_stato"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                trovato = True

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(righe)

        return trovato
    except Exception as e:
        st.warning(f"Stato non aggiornato: {e}")
        return False

def statistiche_stati_preventivi(preventivi):
    stats = {s: 0 for s in STATI_PREVENTIVO}
    for p in preventivi:
        stato = str(p.get("stato", "Bozza") or "Bozza")
        if stato not in stats:
            stats[stato] = 0
        stats[stato] += 1
    return stats

def box_stati_html(stats):
    colori = {
        "Bozza": "#f7c948",
        "Inviato": "#2f80ed",
        "Accettato": "#27ae60",
        "Perso": "#eb5757",
        "Ordinato": "#9b51e0",
    }
    html = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0;">'
    for stato in STATI_PREVENTIVO:
        colore = colori.get(stato, "#06499b")
        html += f"""
        <div style="background:{colore};color:white;border-radius:12px;padding:14px;text-align:center;font-weight:900;">
            <div style="font-size:15px;">{stato}</div>
            <div style="font-size:28px;">{stats.get(stato,0)}</div>
        </div>
        """
    html += "</div>"
    return html



# =========================
# CLIENTI CSV
# =========================

def carica_clienti():
    path = Path(CLIENTI_CSV)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except:
        return []

def salva_cliente_csv(nome, azienda, telefono, email, codice_preventivo, imponibile, owner_utente='CLIENTE', owner_profilo='CLIENTE'):
    nome = str(nome or "").strip()
    azienda = str(azienda or "").strip()
    telefono = str(telefono or "").strip()
    email = str(email or "").strip().lower()

    if not nome and not azienda and not telefono and not email:
        return

    clienti = carica_clienti()
    oggi = datetime.now().strftime("%d/%m/%Y %H:%M")
    trovato = False

    for c in clienti:
        stessa_email = email and str(c.get("email", "")).strip().lower() == email
        stesso_tel = telefono and str(c.get("telefono", "")).strip() == telefono

        if stessa_email or stesso_tel:
            c["nome"] = nome or c.get("nome", "")
            c["azienda"] = azienda or c.get("azienda", "")
            c["telefono"] = telefono or c.get("telefono", "")
            c["email"] = email or c.get("email", "")
            c["ultimo_preventivo"] = codice_preventivo
            c["data_ultimo_preventivo"] = oggi
            c["owner_utente"] = c.get("owner_utente", owner_utente) or owner_utente
            c["owner_profilo"] = c.get("owner_profilo", owner_profilo) or owner_profilo
            try:
                c["numero_preventivi"] = str(int(c.get("numero_preventivi", "0") or 0) + 1)
            except:
                c["numero_preventivi"] = "1"
            try:
                totale_vecchio = float(str(c.get("totale_preventivi", "0")).replace(",", ".") or 0)
            except:
                totale_vecchio = 0.0
            c["totale_preventivi"] = f"{totale_vecchio + float(imponibile or 0):.2f}"
            trovato = True
            break

    if not trovato:
        clienti.append({
            "nome": nome,
            "azienda": azienda,
            "telefono": telefono,
            "email": email,
            "primo_preventivo": codice_preventivo,
            "ultimo_preventivo": codice_preventivo,
            "data_primo_preventivo": oggi,
            "data_ultimo_preventivo": oggi,
            "numero_preventivi": "1",
            "totale_preventivi": f"{float(imponibile or 0):.2f}",
            "owner_utente": owner_utente,
            "owner_profilo": owner_profilo,
        })

    campi = [
        "nome", "azienda", "telefono", "email",
        "primo_preventivo", "ultimo_preventivo",
        "data_primo_preventivo", "data_ultimo_preventivo",
        "numero_preventivi", "totale_preventivi", "owner_utente", "owner_profilo"
    ]

    with open(CLIENTI_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        writer.writeheader()
        writer.writerows(clienti)

def righe_clienti_dashboard(clienti):
    righe = []
    for c in clienti:
        try:
            totale = euro(float(str(c.get("totale_preventivi", "0")).replace(",", ".") or 0))
        except:
            totale = ""
        righe.append({
            "Nome": c.get("nome", ""),
            "Azienda": c.get("azienda", ""),
            "Telefono": c.get("telefono", ""),
            "Email": c.get("email", ""),
            "N. preventivi": c.get("numero_preventivi", ""),
            "Totale": totale,
            "Ultimo preventivo": c.get("ultimo_preventivo", ""),
            "Data ultimo": c.get("data_ultimo_preventivo", ""),
            "Utente": c.get("owner_utente", ""),
            "Profilo": c.get("owner_profilo", ""),
        })
    return righe

def filtra_clienti_dashboard(clienti, cerca):
    cerca = str(cerca or "").strip().lower()
    if not cerca:
        return clienti
    out = []
    for c in clienti:
        testo = " ".join([
            str(c.get("nome", "")),
            str(c.get("azienda", "")),
            str(c.get("telefono", "")),
            str(c.get("email", "")),
            str(c.get("ultimo_preventivo", "")),
        ]).lower()
        if cerca in testo:
            out.append(c)
    return out

def clienti_visibili_per_profilo(clienti, profilo, utente_codice):
    if profilo == "SA-TEC":
        return clienti
    return [
        c for c in clienti
        if str(c.get("owner_utente", "")).strip().upper() == str(utente_codice).strip().upper()
    ]


# =========================
# PREVENTIVI CSV
# =========================

def salva_preventivo(dati):
    file_exists = Path(PREVENTIVI_CSV).exists()
    campi = [
        "codice_preventivo", "data_ora", "utente", "profilo", "cliente_nome", "cliente_azienda",
        "cliente_telefono", "cliente_email", "configurazione", "luce_mm",
        "altezza_mm", "traversa_m", "elettroblocco", "allaccio", "radar_sicurezza_laterale",
        "ricarico_percento", "imponibile", "iva", "totale_iva", "costo_satec", "utile_lordo", "margine_percento", "stato"
    ]
    with open(PREVENTIVI_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        if not file_exists:
            writer.writeheader()
        writer.writerow(dati)

def carica_preventivi():
    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# =========================
# LOGIN + REGISTRAZIONE
# =========================

def login_box():
    utenti = carica_tutti_utenti()

    # Sessione login stabile
    if "logged_profilo" not in st.session_state:
        st.session_state.logged_profilo = "CLIENTE"
        st.session_state.logged_nome = "Cliente finale"
        st.session_state.logged_utente = "CLIENTE"
        st.session_state.logged_dati = {
            "nome": "",
            "azienda": "",
            "telefono": "",
            "email": "",
            "ricarico": "35"
        }

    st.sidebar.markdown("## Accesso")
    st.sidebar.info("Cliente finale: può entrare libero oppure registrarsi.")

    username = st.sidebar.text_input("Utente", value="", key="login_user")
    password = st.sidebar.text_input("Password", value="", type="password", key="login_pwd")

    col_login_1, col_login_2 = st.sidebar.columns(2)

    with col_login_1:
        accedi = st.button("ACCEDI", key="btn_accedi")

    with col_login_2:
        esci = st.button("ESCI", key="btn_esci")

    if esci:
        st.session_state.logged_profilo = "CLIENTE"
        st.session_state.logged_nome = "Cliente finale"
        st.session_state.logged_utente = "CLIENTE"
        st.session_state.logged_dati = {
            "nome": "",
            "azienda": "",
            "telefono": "",
            "email": "",
            "ricarico": "35"
        }
        st.sidebar.success("Accesso cliente finale")

    if accedi:
        u = username.strip().upper()
        pwd_inserita = password.strip()

        # ADMIN SEMPRE ATTIVO, anche se CSV è sporco o mancante
        if u == "ADMIN" and pwd_inserita == "SATEC-ADMIN":
            st.session_state.logged_profilo = "SA-TEC"
            st.session_state.logged_nome = "SA-TEC Amministratore"
            st.session_state.logged_utente = "ADMIN"
            st.session_state.logged_dati = UTENTI_BASE["ADMIN"]
            st.sidebar.success("Accesso: SA-TEC Amministratore")

        elif u in utenti and str(utenti[u].get("password", "")).strip() == pwd_inserita:
            profilo_login = str(utenti[u].get("profilo", "CLIENTE")).strip().upper()
            if profilo_login not in PROFILI:
                profilo_login = "CLIENTE"

            st.session_state.logged_profilo = profilo_login
            st.session_state.logged_nome = utenti[u].get("nome", "") or u
            st.session_state.logged_utente = u
            st.session_state.logged_dati = utenti[u]
            st.sidebar.success(f"Accesso: {st.session_state.logged_nome}")

        else:
            st.sidebar.error("Utente o password non corretti.")
            st.sidebar.caption("Admin corretto: ADMIN / SATEC-ADMIN")

    profilo = st.session_state.logged_profilo
    nome_utente = st.session_state.logged_nome
    utente_codice = st.session_state.logged_utente
    dati_utente = st.session_state.logged_dati

    st.sidebar.markdown("---")
    st.sidebar.write(f"Profilo attivo: **{PROFILI.get(profilo, 'Cliente finale')}**")
    st.sidebar.caption(f"Utente attivo: {utente_codice}")

    if profilo in ["RIVENDITORE", "GROSSISTA"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Logo azienda")
        logo_presente = trova_logo_utente(utente_codice)
        if logo_presente:
            st.sidebar.success("Logo caricato")
        logo_upload = st.sidebar.file_uploader("Carica logo PDF", type=["png", "jpg", "jpeg"], key=f"logo_upload_{utente_codice}")
        if logo_upload is not None:
            if salva_logo_utente(utente_codice, logo_upload):
                st.sidebar.success("Logo salvato. Ricarica la pagina se non lo vedi nel PDF.")

    with st.sidebar.expander("Registrazione cliente"):
        st.caption("Crea automaticamente una password cliente.")
        reg_nome = st.text_input("Nome", key="reg_nome")
        reg_azienda = st.text_input("Azienda", key="reg_azienda")
        reg_tel = st.text_input("Telefono", key="reg_tel")
        reg_email = st.text_input("Email", key="reg_email")

        if st.button("GENERA ACCESSO CLIENTE"):
            utenti_now = carica_tutti_utenti()
            nuovo_user = genera_codice_progressivo("CLIENTE", utenti_now)
            nuova_pwd = genera_password()
            salva_utente_csv(
                nuovo_user,
                nuova_pwd,
                "CLIENTE",
                reg_nome,
                reg_azienda,
                reg_tel,
                reg_email,
                "35"
            )
            st.success("Accesso cliente creato.")
            st.code(f"Utente: {nuovo_user}\nPassword: {nuova_pwd}")

    try:
        ricarico_effettivo = float(str(dati_utente.get("ricarico", "")).replace(",", "."))
    except:
        ricarico_effettivo = ricarico_default(profilo)

    if profilo == "SA-TEC":
        ricarico_effettivo = 0.0

    return profilo, nome_utente, utente_codice, dati_utente, ricarico_effettivo

# =========================
# DISEGNI PORTE
# =========================

def mini_porta_html(ante):
    if ante == "1 anta":
        return """
        <svg width="120" height="120" viewBox="0 0 120 120">
        <rect x="18" y="18" width="84" height="10" fill="#d9d9d9" stroke="#111"/>
        <rect x="26" y="30" width="34" height="72" fill="#dcecff" stroke="#111" stroke-width="2"/>
        <rect x="60" y="30" width="34" height="72" fill="#fff" stroke="#111" stroke-width="2"/>
        <line x1="60" y1="30" x2="60" y2="102" stroke="#111" stroke-width="2"/>
        </svg>"""
    return """
    <svg width="120" height="120" viewBox="0 0 120 120">
    <rect x="18" y="18" width="84" height="10" fill="#d9d9d9" stroke="#111"/>
    <rect x="25" y="30" width="35" height="72" fill="#eef7ff" stroke="#111" stroke-width="2"/>
    <rect x="60" y="30" width="35" height="72" fill="#eef7ff" stroke="#111" stroke-width="2"/>
    <rect x="56" y="30" width="5" height="72" fill="#fff" stroke="#111"/>
    <rect x="61" y="30" width="5" height="72" fill="#fff" stroke="#111"/>
    </svg>"""

def render_choice_card(title, desc, ante, active):
    border = "#06499b" if active else "#d4dce8"
    bw = "4px" if active else "2px"
    bg = "#dcecff" if active else "#fff"
    components.html(f"""
    <div style="border:{bw} solid {border};background:{bg};border-radius:14px;text-align:center;padding:14px;min-height:242px;font-family:Arial;">
    <div style="font-size:19px;font-weight:900;color:#111;line-height:1.15;margin-bottom:6px;">{title}</div>
    <div>{mini_porta_html(ante)}</div>
    <div style="font-size:14px;line-height:1.28;color:#111;margin-top:4px;">{desc}</div>
    </div>""", height=260)

def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    blu = "#06499b"
    vetro_sel = "#d5eaff"
    vetro = "#fff"
    nero = "#111"
    mt = int(lunghezza_traversa * 1000)

    if ante == "1 anta":
        ante_svg = f"""
        <rect x="80" y="115" width="260" height="170" fill="{vetro_sel}" stroke="{nero}" stroke-width="4"/>
        <rect x="340" y="115" width="260" height="170" fill="{vetro}" stroke="{nero}" stroke-width="4"/>
        <line x1="340" y1="115" x2="340" y2="285" stroke="{nero}" stroke-width="6"/>"""
        titolo = "ANTE SELEZIONATA: 1 ANTA"
    else:
        ante_svg = f"""
        <rect x="80" y="115" width="260" height="170" fill="{vetro_sel}" stroke="{nero}" stroke-width="4"/>
        <rect x="340" y="115" width="260" height="170" fill="{vetro_sel}" stroke="{nero}" stroke-width="4"/>
        <rect x="328" y="115" width="10" height="170" fill="#fff" stroke="{nero}" stroke-width="3"/>
        <rect x="342" y="115" width="10" height="170" fill="#fff" stroke="{nero}" stroke-width="3"/>"""
        titolo = "ANTE SELEZIONATA: 2 ANTE"

    return f"""
    <div style="background:#fff;border:2px solid #b8d4f3;border-radius:12px;padding:10px;font-family:Arial;">
    <svg width="100%" height="390" viewBox="0 0 680 390">
    <text x="18" y="28" font-size="18" fill="{blu}" font-weight="900">{titolo}</text>
    <text x="340" y="58" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900">MISURA TRAVERSA CALCOLATA</text>
    <text x="340" y="84" text-anchor="middle" font-size="24" fill="{blu}" font-weight="900">{mt} mm</text>
    <line x1="80" y1="96" x2="600" y2="96" stroke="{blu}" stroke-width="3"/>
    <line x1="80" y1="84" x2="80" y2="108" stroke="{blu}" stroke-width="3"/>
    <line x1="600" y1="84" x2="600" y2="108" stroke="{blu}" stroke-width="3"/>
    <rect x="70" y="92" width="540" height="34" fill="#e9eef3" stroke="{nero}" stroke-width="2"/>
    <rect x="82" y="100" width="516" height="8" fill="#fff" opacity="0.45"/>
    <rect x="318" y="103" width="44" height="14" rx="3" fill="{nero}"/>
    {ante_svg}
    <line x1="145" y1="342" x2="535" y2="342" stroke="{blu}" stroke-width="3"/>
    <line x1="145" y1="330" x2="145" y2="354" stroke="{blu}" stroke-width="3"/>
    <line x1="535" y1="330" x2="535" y2="354" stroke="{blu}" stroke-width="3"/>
    <text x="340" y="370" text-anchor="middle" font-size="17" fill="{blu}" font-weight="900">LUCE PASSAGGIO {luce_mm} mm</text>
    <line x1="632" y1="115" x2="632" y2="285" stroke="{blu}" stroke-width="3"/>
    <line x1="620" y1="115" x2="644" y2="115" stroke="{blu}" stroke-width="3"/>
    <line x1="620" y1="285" x2="644" y2="285" stroke="{blu}" stroke-width="3"/>
    <text x="660" y="205" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900" transform="rotate(90 660,205)">H {altezza_mm} mm</text>
    </svg></div>"""

def aggiungi(articoli, codice, descrizione, descrizione_lunga, quantita=1, scontato=True):
    listino = LISTINI[codice]
    if scontato:
        prezzo_unitario = prezzo_vendita(listino)
        costo_unitario = costo_satec_reale(listino)
    else:
        prezzo_unitario = listino
        costo_unitario = listino

    articoli.append({
        "codice": codice,
        "descrizione": descrizione,
        "descrizione_lunga": descrizione_lunga,
        "quantita": quantita,
        "listino_unitario": listino,
        "costo_unitario_satec": costo_unitario,
        "prezzo_unitario": prezzo_unitario,
        "totale": prezzo_unitario * quantita,
        "costo_totale_satec": costo_unitario * quantita
    })

# =========================
# CSS
# =========================

st.markdown("""
<style>
.stApp {background:#f3f7fd;font-family:Arial,sans-serif;}
.main .block-container {padding-top:0rem;max-width:1550px;}
.header {background:linear-gradient(115deg,#fff 0%,#fff 28%,#073763 28%,#06499b 100%);border-bottom:5px solid #063b7a;padding:22px 32px;display:grid;grid-template-columns:28% 44% 28%;align-items:center;color:white;}
.logo-satec {width:300px;}
.header-title {text-align:center;}
.header-title h1 {font-size:42px;margin:0;font-weight:900;line-height:1.05;}
.header-title div {font-size:18px;margin-top:12px;font-weight:700;}
.header-info {font-size:15px;line-height:1.45;text-align:left;font-weight:700;}
.powercore {background:white;padding:18px 34px;display:grid;grid-template-columns:50% 50%;align-items:center;border-bottom:1px solid #bdd4ef;}
.powercore-title {font-size:34px;font-weight:900;color:#111;}
.powercore-title span {color:#ff7900;}
.powercore-sub {font-size:17px;color:#111;margin-top:8px;}
.sesamo-logo {height:115px;max-width:380px;object-fit:contain;}
.card,.side-card {background:white;border:1px solid #bdd4ef;border-radius:14px;padding:16px;margin-bottom:16px;}
.title-bar {display:inline-block;background:#06499b;color:white;padding:9px 16px;border-radius:8px;font-size:18px;font-weight:900;margin-bottom:16px;}
.section-row {display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px;}
.section-box {background:#eef6ff;border-radius:12px;padding:16px;color:#06499b;font-weight:800;font-size:16px;}
.section-box.green {background:#eefaf2;color:#0c7b3e;}
div[data-testid="stNumberInput"] label {color:#111!important;font-size:15px!important;font-weight:800!important;}
div[data-testid="stNumberInput"] input {border:2px solid #8998b0!important;border-radius:0!important;text-align:center!important;font-size:28px!important;font-weight:800!important;color:#06499b!important;height:54px!important;}
div[data-testid="stTextInput"] input {background:#ffffff!important;color:#06499b!important;border:2px solid #8998b0!important;border-radius:6px!important;font-weight:800!important;}
.measure-total {border:2px solid #bdd4ef;background:#f8fbff;border-radius:10px;padding:14px;display:grid;grid-template-columns:1fr 200px;align-items:center;color:#06499b;margin-top:10px;}
.measure-total .big {font-size:30px;font-weight:900;text-align:center;}
.measure-total .small {font-size:18px;font-weight:900;text-align:center;}
.option-box {border:2px solid #06499b;border-radius:12px;padding:18px;margin-bottom:18px;background:white;}
.option-title {font-size:20px;font-weight:900;color:#06499b;margin-bottom:12px;}
.option-note {border:2px solid #06499b;border-radius:12px;padding:13px;background:#eef6ff;color:#06499b;font-size:15px;font-weight:800;line-height:1.45;margin-top:12px;}
div[data-testid="stCheckbox"] {border:0;padding:0;margin:0;}
div[data-testid="stCheckbox"] label {color:#06499b!important;font-size:18px!important;font-weight:900!important;}
.price {text-align:center;color:#06499b;font-size:42px;font-weight:900;}
.price-label {color:#06499b;font-size:18px;font-weight:900;text-align:center;}
.vat-box {border:1px solid #bdd4ef;border-radius:10px;padding:14px;color:#06499b;font-size:17px;font-weight:800;background:#f8fbff;}
.power-side-title {color:#06499b;font-size:18px;font-weight:900;margin-bottom:12px;}
.power-side-text {font-size:15px;line-height:1.45;color:#111;}
.power-side-list li {margin-bottom:10px;color:#111;}
.desc-grid {display:grid;grid-template-columns:34% 33% 33%;gap:16px;color:#111;font-size:15px;}
.desc-title {color:#06499b;font-size:22px;font-weight:900;margin-bottom:10px;}
.footer {background:#06499b;color:white;padding:18px 34px;display:grid;grid-template-columns:1fr 1fr 1fr;font-size:16px;font-weight:700;margin-top:12px;}
.stButton>button {background:#06499b;color:white;border-radius:8px;height:48px;font-size:16px;font-weight:900;border:none;}
.stButton>button:hover {background:#073763;color:white;}
.admin-box {background:#ffffff;border:2px solid #06499b;border-radius:14px;padding:18px;margin-bottom:18px;}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    font-size: 14px;
}
th {
    background: #06499b;
    color: white;
    padding: 8px;
    text-align: left;
}
td {
    border: 1px solid #bdd4ef;
    padding: 8px;
    color: #111;
}
tr:nth-child(even) {
    background: #f3f7fd;
}


/* FIX SA-TEC: rettangoli blu e campi leggibili */
.title-bar,
.title-bar * {
    background:#06499b!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}

div[data-testid="stTextInput"] input {
    background:#ffffff!important;
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    border:2px solid #8998b0!important;
    border-radius:6px!important;
    font-weight:800!important;
}

div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stCheckbox"] label {
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    font-weight:800!important;
}

.option-note,
.option-note *,
.section-box span,
.power-side-text,
.power-side-list li,
.desc-grid,
.desc-grid *,
td {
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
}

th {
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}


/* V26 - CAMPI MISURE INTERNI GIALLI */
div[data-testid="stNumberInput"] input {
    background:#fff3a3!important;
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    border:2px solid #06499b!important;
    border-radius:8px!important;
    text-align:center!important;
    font-size:28px!important;
    font-weight:900!important;
    height:56px!important;
}

div[data-testid="stNumberInput"] label {
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    font-weight:900!important;
}


/* V29 - CHECKBOX ACCESSORI GIALLI */
div[data-testid="stCheckbox"] input[type="checkbox"] {
    accent-color:#ffd400!important;
}

div[data-testid="stCheckbox"] label {
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    font-weight:900!important;
    font-size:18px!important;
}

div[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    font-weight:900!important;
}

/* evidenzia meglio la zona dei checkbox */
div[data-testid="stCheckbox"] {
    background:#fff3a3!important;
    border:2px solid #06499b!important;
    border-radius:10px!important;
    padding:10px 12px!important;
    margin-bottom:10px!important;
}


/* V31 - Bottoni email stessa dimensione e colore */
div[data-testid="stButton"] button {
    background:#06499b!important;
    color:#ffffff!important;
    border:none!important;
    border-radius:10px!important;
    height:48px!important;
    font-size:18px!important;
    font-weight:900!important;
    width:100%!important;
}


/* V35 - CARD PORTA CLICCABILI */
.porta-card {
    border:3px solid #bdd4ef;
    background:#ffffff;
    border-radius:16px;
    padding:14px;
    min-height:235px;
    text-align:center;
    box-shadow:0 4px 12px rgba(6,73,155,0.10);
    margin-bottom:8px;
}

.porta-card-attiva {
    border:5px solid #06499b;
    background:#fff3a3;
    box-shadow:0 6px 18px rgba(6,73,155,0.25);
}

.porta-card-title {
    color:#06499b;
    font-size:19px;
    font-weight:900;
    line-height:1.15;
    margin-bottom:8px;
}

.porta-card-desc {
    color:#111111;
    font-size:14px;
    font-weight:700;
    line-height:1.35;
    margin-top:6px;
}

.porta-btn button {
    background:#06499b!important;
    color:#ffffff!important;
    border-radius:10px!important;
    height:48px!important;
    font-size:15px!important;
    font-weight:900!important;
    width:100%!important;
}

.porta-btn-attivo button {
    background:#ffd400!important;
    color:#111111!important;
    border:3px solid #06499b!important;
}


/* V36 - pulsante card integrato */
div[data-testid="stButton"] button[kind="secondary"] {
    background:#06499b!important;
    color:#ffffff!important;
    border-radius:0 0 16px 16px!important;
    min-height:54px!important;
    font-size:17px!important;
    font-weight:900!important;
    border:3px solid #06499b!important;
    margin-top:-12px!important;
}

div[data-testid="stButton"] button[kind="secondary"]:hover {
    background:#ffd400!important;
    color:#111111!important;
    border:3px solid #06499b!important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================

logo_satec64 = img_to_base64(["logo_satec.jpg", "logo_satec.png", "/mnt/data/logo_satec.jpg", "/mnt/data/logo_satec.png"])
logo_sesamo64 = img_to_base64(["SESAMO LOGO.png", "sesamo_logo.png", "logo_sesamo.png", "/mnt/data/SESAMO LOGO.png", "/mnt/data/sesamo_logo.png", "/mnt/data/logo_sesamo.png"])

logo_satec_html = f'<img class="logo-satec" src="data:image/jpeg;base64,{logo_satec64}">' if logo_satec64 else "<h1 style='color:#06499b'>SA-TEC</h1>"
sesamo_logo_html = f'<img class="sesamo-logo" src="data:image/png;base64,{logo_sesamo64}">' if logo_sesamo64 else """
<div style="display:flex;align-items:center;justify-content:center;gap:18px;">
<div style="background:#ff7900;color:white;font-size:44px;font-weight:900;padding:10px 18px;">▌</div>
<div><div style="font-size:48px;font-weight:900;color:#000;line-height:1;">SESAMO</div>
<div style="font-size:16px;font-weight:900;color:#000;letter-spacing:1px;">THE DOOR TECHNOLOGY</div></div>
</div>"""

st.markdown(f"""
<div class="header">
<div>{logo_satec_html}</div>
<div class="header-title"><h1>CONFIGURATORE<br>PORTE AUTOMATICHE</h1><div>TECNOLOGIA, SICUREZZA E SOLUZIONI SU MISURA</div></div>
<div class="header-info">SA-TEC S.R.L.s<br>Via L. Settembrini 84<br>88046 Lamezia Terme (CZ)<br>P.IVA 04009610793<br>☎ 0968-036797<br>✉ sacco.tecnologie@gmail.com<br>✉ sa-tec@pec.it</div>
</div>
<div class="powercore">
<div><div class="powercore-title">SESAMO <span>POWERCORE</span> PW100</div>
<div class="powercore-sub">Automazione lineare per porte scorrevoli automatiche,<br>affidabile, sicura e compatibile con la normativa EN16005.</div></div>
<div style="text-align:center;">{sesamo_logo_html}</div>
</div>
""", unsafe_allow_html=True)

profilo, nome_utente, utente_codice, dati_utente, ricarico_effettivo = login_box()

# Ricarico manuale solo per ADMIN SA-TEC
if profilo == "SA-TEC":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Ricarico SA-TEC")
    usa_ricarico_satec = st.sidebar.checkbox("Usa ricarico manuale SA-TEC", value=True, key="usa_ricarico_satec")
    if usa_ricarico_satec:
        ricarico_effettivo = st.sidebar.number_input(
            "Ricarico SA-TEC %",
            min_value=0.0,
            max_value=200.0,
            value=50.0,
            step=1.0,
            key="ricarico_satec_admin"
        )
    else:
        ricarico_effettivo = 0.0

RICARICO_ATTIVO = ricarico_effettivo

# =========================
# ADMIN
# =========================

if profilo == "SA-TEC":
    st.sidebar.success("AREA ADMIN ATTIVA")
    st.sidebar.markdown("---")
    mostra_dashboard = st.sidebar.checkbox("Mostra dashboard SA-TEC", value=False)

    with st.sidebar.expander("Crea utente manuale"):
        utenti_now = carica_tutti_utenti()
        profilo_new = st.selectbox("Profilo nuovo utente", ["CLIENTE", "RIVENDITORE", "GROSSISTA"], key="admin_profilo_new")
        nome_new = st.text_input("Nome", key="admin_nome_new")
        azienda_new = st.text_input("Azienda", key="admin_azienda_new")
        telefono_new = st.text_input("Telefono", key="admin_tel_new")
        email_new = st.text_input("Email", key="admin_email_new")
        ricarico_new = st.number_input("Ricarico %", min_value=0.0, max_value=100.0, value=ricarico_default(profilo_new), step=1.0, key="admin_ricarico_new")
        if st.button("CREA UTENTE"):
            codice = genera_codice_progressivo(profilo_new, utenti_now)
            pwd = genera_password()
            salva_utente_csv(codice, pwd, profilo_new, nome_new, azienda_new, telefono_new, email_new, str(ricarico_new))
            st.success("Utente creato")
            st.code(f"Utente: {codice}\nPassword: {pwd}\nProfilo: {profilo_new}\nRicarico: {ricarico_new}%")

    if mostra_dashboard:
        st.markdown('<div class="admin-box"><h2 style="color:#06499b;">Dashboard SA-TEC</h2>', unsafe_allow_html=True)

        preventivi = carica_preventivi()
        utenti_csv = carica_utenti_csv()

        tab1, tab2 = st.tabs(["Preventivi", "Utenti creati"])

        with tab1:
            if not preventivi:
                st.info("Nessun preventivo salvato ancora.")
            else:
                st.write(f"Preventivi salvati: **{len(preventivi)}**")
                stats_stati = statistiche_stati_preventivi(preventivi)
                st.markdown(box_stati_html(stats_stati), unsafe_allow_html=True)
                totale = 0.0
                for p in preventivi:
                    try:
                        totale += float(p.get("imponibile", 0))
                    except:
                        pass
                utile_totale = 0.0
                costo_totale_dashboard = 0.0
                for p in preventivi:
                    try:
                        utile_totale += float(p.get("utile_lordo", 0) or 0)
                    except:
                        pass
                    try:
                        costo_totale_dashboard += float(p.get("costo_satec", 0) or 0)
                    except:
                        pass
                margine_dash = (utile_totale / costo_totale_dashboard * 100) if costo_totale_dashboard > 0 else 0

                st.write(f"Valore totale IVA esclusa: **{euro(totale)}**")
                st.write(f"Utile lordo totale: **{euro(utile_totale)}**")
                st.write(f"Margine medio su costo: **{margine_dash:.1f}%**")
                st.markdown(tabella_html_sicura(preventivi), unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown('<h3 style="color:#06499b;">Aggiorna stato preventivo</h3>', unsafe_allow_html=True)

                codici_disponibili = [
                    p.get("codice_preventivo", "") for p in preventivi
                    if p.get("codice_preventivo", "")
                ]

                if codici_disponibili:
                    col_stato_1, col_stato_2, col_stato_3 = st.columns([2, 1, 1])
                    with col_stato_1:
                        codice_da_modificare = st.selectbox("Preventivo", codici_disponibili, key="codice_stato_admin")
                    with col_stato_2:
                        nuovo_stato_admin = st.selectbox("Nuovo stato", STATI_PREVENTIVO, key="nuovo_stato_admin")
                    with col_stato_3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("AGGIORNA STATO"):
                            if aggiorna_stato_preventivo_admin(codice_da_modificare, nuovo_stato_admin):
                                st.success(f"Stato {codice_da_modificare} aggiornato a {nuovo_stato_admin}.")
                            else:
                                st.error("Preventivo non trovato.")
                else:
                    st.info("Salva almeno un preventivo con codice SAT per aggiornare lo stato.")

                with open(PREVENTIVI_CSV, "rb") as f:
                    st.download_button("Scarica CSV preventivi", data=f, file_name="preventivi_satec.csv", mime="text/csv")

        with tab2:
            if not utenti_csv:
                st.info("Nessun utente creato da CSV.")
            else:
                righe = []
                for u, d in utenti_csv.items():
                    righe.append({
                        "Utente": u,
                        "Password": d["password"],
                        "Profilo": d["profilo"],
                        "Nome": d["nome"],
                        "Azienda": d["azienda"],
                        "Telefono": d["telefono"],
                        "Email": d["email"],
                        "Ricarico %": d.get("ricarico", ""),
                    })
                st.markdown(tabella_html_sicura(righe), unsafe_allow_html=True)
                with open(UTENTI_CSV, "rb") as f:
                    st.download_button("Scarica CSV utenti", data=f, file_name="utenti_satec.csv", mime="text/csv")


        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<h3 style="color:#06499b;">Archivio Clienti</h3>', unsafe_allow_html=True)

        clienti = carica_clienti()
        cerca_cliente_dash = st.text_input("Cerca cliente", placeholder="Nome, azienda, telefono, email o codice preventivo", key="cerca_cliente_dash")
        clienti_filtrati = filtra_clienti_dashboard(clienti, cerca_cliente_dash)

        if not clienti:
            st.info("Nessun cliente salvato ancora. Verrà creato automaticamente al salvataggio del primo preventivo.")
        elif not clienti_filtrati:
            st.warning("Nessun cliente trovato con questo filtro.")
        else:
            st.write(f"Clienti trovati: **{len(clienti_filtrati)}**")
            st.markdown(tabella_html_sicura(righe_clienti_dashboard(clienti_filtrati)), unsafe_allow_html=True)

            if Path(CLIENTI_CSV).exists():
                with open(CLIENTI_CSV, "rb") as f:
                    st.download_button("Scarica CSV clienti", data=f, file_name="clienti_satec.csv", mime="text/csv")

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CONFIGURATORE
# =========================

if "scelta" not in st.session_state:
    st.session_state.scelta = "STANDARD 1 ANTA"

col_main, col_side = st.columns([0.69, 0.31], gap="large")

with col_main:
    st.markdown('<div class="card"><div class="title-bar">1&nbsp;&nbsp; SCEGLI LA PORTA AUTOMATICA</div>', unsafe_allow_html=True)

    cards = [
        ("STANDARD<br>1 ANTA", "STANDARD 1 ANTA", "Porta automatica lineare standard a una anta", "1 anta"),
        ("STANDARD<br>2 ANTE", "STANDARD 2 ANTE", "Porta automatica lineare standard a due ante", "2 ante"),
        ("RIDONDANTE<br>1 ANTA", "RIDONDANTE 1 ANTA", "Automazione lineare per via di fuga a una anta", "1 anta"),
        ("RIDONDANTE<br>2 ANTE", "RIDONDANTE 2 ANTE", "Automazione lineare per via di fuga a due ante", "2 ante"),
    ]

    cols = st.columns(4)

    for c, (titolo, key, desc, ante_mini) in zip(cols, cards):
        with c:
            active = st.session_state.scelta == key
            classe_card = "porta-card porta-card-attiva" if active else "porta-card"

            # Card visuale
            st.markdown(f"""
            <div class="{classe_card}">
                <div class="porta-card-title">{titolo}</div>
                <div>{mini_porta_html(ante_mini)}</div>
                <div class="porta-card-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

            # Pulsante grande quanto il riquadro: è lui il riquadro cliccabile reale in Streamlit
            label_btn = "✓ SELEZIONATA" if active else "CLICCA QUI"
            if st.button(label_btn, key=f"select_{key}", use_container_width=True):
                st.session_state.scelta = key
                st.rerun()

    scelta = st.session_state.scelta

    if scelta == "STANDARD 1 ANTA":
        tipo, ante = "Standard", "1 anta"
    elif scelta == "STANDARD 2 ANTE":
        tipo, ante = "Standard", "2 ante"
    elif scelta == "RIDONDANTE 1 ANTA":
        tipo, ante = "Ridondante", "1 anta"
    else:
        tipo, ante = "Ridondante", "2 ante"

    st.markdown("""
    <div class="section-row">
    <div class="section-box">CONFIGURAZIONE STANDARD<br><span style="font-weight:500;color:#111;">Sesamo PowerCore PW100 per porta scorrevole automatica lineare ad uso normale.</span></div>
    <div class="section-box green">CONFIGURAZIONE RIDONDANTE<br><span style="font-weight:500;color:#111;">Automazione ridondante per vie di fuga e uscite di emergenza.</span></div>
    </div></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="title-bar">2&nbsp;&nbsp; MISURE PORTA</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)

    with m1:
        luce_mm = st.number_input("LUCE PASSAGGIO IN MM", min_value=800, max_value=5000, value=1600, step=50)
    with m2:
        altezza_mm = st.number_input("ALTEZZA PASSAGGIO IN MM", min_value=1800, max_value=3000, value=2200, step=50)

    lunghezza_traversa = calcola_traversa(luce_mm, ante)
    components.html(disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa), height=430)

    st.markdown(f"""
    <div class="measure-total">
    <div><b>MISURA TRAVERSA CALCOLATA</b><br>1 anta = doppio luce + 10 cm<br>2 ante = doppio luce + 20 cm</div>
    <div><div class="big">{int(lunghezza_traversa*1000)} mm</div><div class="small">{lunghezza_traversa:.2f} metri</div></div>
    </div></div>
    """, unsafe_allow_html=True)

with col_side:
    st.markdown('<div class="side-card"><div class="title-bar">3&nbsp;&nbsp; ACCESSORI E SERVIZI</div>', unsafe_allow_html=True)

    elettroblocco = st.checkbox("Aggiungi elettroblocco", value=False, key="elettro")
    stile_elettro = "background:#fff3a3;border:3px solid #06499b;" if elettroblocco else "background:white;border:2px solid #06499b;"
    st.markdown(f"""
    <div class="option-box" style="{stile_elettro}">
        <div class="option-title">ELETTROBLOCCO</div>
        <div class="option-note">
        Accessorio per blocco anta in chiusura. Se selezionato, viene inserito automaticamente nel preventivo in base alla configurazione scelta.
        </div>
    </div>
    """, unsafe_allow_html=True)

    radar_sicurezza_laterale = st.checkbox("Aggiungi radar sicurezza laterale", value=False, key="radar_sicurezza_laterale")
    stile_radar = "background:#fff3a3;border:3px solid #06499b;" if radar_sicurezza_laterale else "background:white;border:2px solid #06499b;"
    st.markdown(f"""
    <div class="option-box" style="{stile_radar}">
        <div class="option-title">RADAR SICUREZZA LATERALE</div>
        <div class="option-note">
        Il radar di sicurezza laterale serve a prevenire lo schiacciamento e l'impatto tra l'anta della porta e gli ostacoli fissi, come la parete, o le persone.<br><br>
        La soglia dei <b>20 cm</b> rappresenta lo spazio di sicurezza perimetrale critico, fondamentale per rispettare gli standard europei, inclusa la normativa <b>EN 16005</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    prezzo_allaccio = LISTINI["ALLACCIO_COLLAUDO_STANDARD"] if tipo == "Standard" else LISTINI["ALLACCIO_COLLAUDO_RIDONDANTE"]
    testo_tipo_allaccio = "Standard" if tipo == "Standard" else "Ridondante"

    allaccio = st.checkbox("Aggiungi allaccio e collaudo SA-TEC", value=False, key="allaccio")
    stile_allaccio = "background:#fff3a3;border:3px solid #06499b;" if allaccio else "background:white;border:2px solid #06499b;"
    st.markdown(f"""
    <div class="option-box" style="{stile_allaccio}">
        <div class="option-title">ALLACCIO E COLLAUDO</div>
        <div class="option-note">
        Prezzo allaccio e collaudo {testo_tipo_allaccio}: <b>{euro(prezzo_allaccio)}</b> IVA esclusa.<br><br>
        <b>Vantaggi inclusi se il servizio è eseguito da SA-TEC</b><br><br>
        Scegliendo SA-TEC per l'allaccio e il collaudo, sono inclusi nel prezzo i seguenti benefici:<br><br>
        <b>Libretto di manutenzione:</b><br>Rilascio della documentazione ufficiale dell'apparecchio/impianto.<br><br>
        <b>Certificazione:</b><br>Rilascio delle certificazioni di conformità e corretta installazione a norma di legge.<br><br>
        <b>Assistenza prioritaria:</b><br>Garanzia di un intervento risolutivo in caso di guasti o problemi entro 48 ore.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# ARTICOLI
# =========================

if 'radar_sicurezza_laterale' not in locals():
    radar_sicurezza_laterale = False

articoli = []

aggiungi(articoli, "CASSA", "Profilo cassa traversa in alluminio", f"Profilo cassa traversa in alluminio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "COPERCHIO", "Coperchio traversa in alluminio", f"Coperchio traversa in alluminio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "GUARN_COPERCHIO", "Guarnizione coperchio", f"Guarnizione coperchio ({lunghezza_traversa:.2f} m)", lunghezza_traversa)

aggiungi(
    articoli,
    "PF54_91_GUARN_ANTIVIBRAZIONE",
    "PF54.91 Guarnizione in gomma coperchio antivibrazione",
    f"PF54.91 Guarnizione in gomma coperchio antivibrazione calcolata su tutta la lunghezza della traversa ({lunghezza_traversa:.2f} m)",
    lunghezza_traversa
)

aggiungi(articoli, "CINGHIA", "Cinghia dentata", f"Cinghia dentata ({lunghezza_traversa*1.8:.2f} m)", lunghezza_traversa * 1.8)
aggiungi(articoli, "GUIDA", "Profilo guida scorrimento", f"Profilo guida scorrimento ({lunghezza_traversa:.2f} m)", lunghezza_traversa)
aggiungi(articoli, "GUARN_GUIDA", "Guarnizione guida", f"Guarnizione guida ({lunghezza_traversa:.2f} m)", lunghezza_traversa)

if tipo == "Standard":
    aggiungi(articoli, "PW100_1" if ante == "1 anta" else "PW100_2", f"Automazione Sesamo PowerCore PW100 {ante}", f"Automazione Sesamo PowerCore PW100 {ante}")
    aggiungi(articoli, "HR100", "2 × Hotron HR100 Radar apertura e sicurezza EN16005", "2 × Hotron HR100 Radar apertura e sicurezza EN16005", 2)
    aggiungi(articoli, "ICON", "PF37.00 ICON Selettore Touch con 3 Tag", "PF37.00 ICON Selettore Touch con 3 Tag")
    aggiungi(articoli, "BATTERIE", "PF54.73 Kit batterie", "PF54.73 Kit batterie")
    if elettroblocco:
        aggiungi(articoli, "ELETTRO_STANDARD", "PF54.59 Elettroblocco Standard", "PF54.59 Elettroblocco Standard")
else:
    aggiungi(articoli, "ER140_1" if ante == "1 anta" else "ER140_2", f"Automazione Sesamo ER140 Ridondante {ante}", f"Automazione Sesamo ER140 Ridondante {ante}")
    aggiungi(articoli, "SSR3_ER_BL", "Hotron SSR3-ER-BL Radar evacuazione", "Hotron SSR3-ER-BL Radar evacuazione")
    aggiungi(articoli, "HR100", "Hotron HR100 Radar apertura e sicurezza EN16005", "Hotron HR100 Radar apertura e sicurezza EN16005")
    aggiungi(articoli, "DIGIDOR", "PF37.06 DIGIDOR Selettore", "PF37.06 DIGIDOR Selettore")
    aggiungi(articoli, "BATTERIE", "PF54.73 Kit batterie", "PF54.73 Kit batterie")
    aggiungi(articoli, "PULSANTE_EMERGENZA", "Pulsante emergenza", "Pulsante emergenza")
    if elettroblocco:
        aggiungi(articoli, "ELETTRO_RIDONDANTE", "PF54.62 Elettroblocco Ridondante", "PF54.62 Elettroblocco Ridondante")

if radar_sicurezza_laterale:
    aggiungi(
        articoli,
        "RADAR_SICUREZZA_LATERALE",
        "Radar sicurezza laterale EN16005",
        "Radar di sicurezza laterale per prevenire schiacciamento e impatto tra anta, ostacoli fissi o persone. Spazio perimetrale critico 20 cm conforme ai principi della normativa EN16005.",
        1
    )

aggiungi(articoli, "ASSEMBLAGGIO", "Assemblaggio automatismo", "Assemblaggio completo automatismo presso officina SA-TEC - Franco deposito SA-TEC Lamezia Terme", 1, scontato=False)

if allaccio:
    if tipo == "Standard":
        aggiungi(articoli, "ALLACCIO_COLLAUDO_STANDARD", "Allaccio e collaudo SA-TEC Standard", "Allaccio e collaudo eseguito da SA-TEC su automazione standard. Comprende libretto di manutenzione, certificazione e assistenza prioritaria con intervento risolutivo entro 48 ore.", 1, scontato=False)
    else:
        aggiungi(articoli, "ALLACCIO_COLLAUDO_RIDONDANTE", "Allaccio e collaudo SA-TEC Ridondante", "Allaccio e collaudo eseguito da SA-TEC su automazione ridondante. Comprende libretto di manutenzione, certificazione e assistenza prioritaria con intervento risolutivo entro 48 ore.", 1, scontato=False)

imponibile = sum(a["totale"] for a in articoli)
costo_satec_totale = sum(a["costo_totale_satec"] for a in articoli)
utile_lordo = imponibile - costo_satec_totale
margine_percento = (utile_lordo / costo_satec_totale * 100) if costo_satec_totale > 0 else 0
iva = imponibile * IVA
totale_iva = imponibile + iva

with col_side:
    st.markdown('<div class="side-card"><div class="title-bar">4&nbsp;&nbsp; RIEPILOGO PREVENTIVO</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="price-label">TOTALE IVA ESCLUSA</div>
    <div class="price">{euro(imponibile)}</div>
    <div class="vat-box">
    Profilo: <b>{PROFILI[profilo]}</b><br>
    IVA 22%: <span style="float:right;">{euro(iva)}</span><br>
    TOTALE IVA INCLUSA: <span style="float:right;">{euro(totale_iva)}</span><br><br>
    <b>Prezzo franco deposito SA-TEC Lamezia Terme</b>
    </div>
    """, unsafe_allow_html=True)

    if profilo == "SA-TEC":
        st.markdown(f"""
        <div class="vat-box" style="margin-top:12px;background:#fff3a3;border:2px solid #06499b;">
        <b>Margine interno SA-TEC</b><br><br>
        Costo netto totale: <span style="float:right;">{euro(costo_satec_totale)}</span><br>
        Vendita totale: <span style="float:right;">{euro(imponibile)}</span><br>
        Utile lordo: <span style="float:right;">{euro(utile_lordo)}</span><br>
        Margine su costo: <span style="float:right;">{margine_percento:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="side-card">
    <div class="power-side-title">SESAMO POWERCORE PW100</div>
    <div style="text-align:center;margin-bottom:14px;">{sesamo_logo_html}</div>
    <div class="power-side-text">
    PowerCore PW100 è l'automazione lineare Sesamo progettata per porte scorrevoli automatiche a 1 o 2 ante.<br><br>
    Affidabile, silenziosa e compatta, garantisce massima sicurezza e conformità alla normativa EN16005.
    </div>
    <ul class="power-side-list">
    <li>Tecnologia lineare ad alte prestazioni</li>
    <li>Movimento fluido e silenzioso</li>
    <li>Compatibile con sensori Sesamo e dispositivi di sicurezza</li>
    <li>Ideale per ambienti pubblici e privati</li>
    </ul></div>
    """, unsafe_allow_html=True)

# =========================
# DATI CLIENTE
# =========================

st.markdown('<div class="card"><div class="title-bar">5&nbsp;&nbsp; DATI CLIENTE E RICHIESTA</div>', unsafe_allow_html=True)

cliente_precaricato = {}

if profilo in ["SA-TEC", "RIVENDITORE", "GROSSISTA"]:
    clienti_archivio_preventivo = clienti_visibili_per_profilo(carica_clienti(), profilo, utente_codice)
    if clienti_archivio_preventivo:
        opzioni_clienti_preventivo = ["Nuovo cliente"] + [
            f"{c.get('nome','')} | {c.get('azienda','')} | {c.get('telefono','')} | {c.get('email','')}"
            for c in clienti_archivio_preventivo
        ]

        cliente_scelto_preventivo = st.selectbox(
            "Richiama cliente esistente",
            opzioni_clienti_preventivo,
            key="richiama_cliente_preventivo"
        )

        if cliente_scelto_preventivo != "Nuovo cliente":
            idx_cliente = opzioni_clienti_preventivo.index(cliente_scelto_preventivo) - 1
            if 0 <= idx_cliente < len(clienti_archivio_preventivo):
                cliente_precaricato = clienti_archivio_preventivo[idx_cliente]
                st.success(
                    f"Cliente caricato: {cliente_precaricato.get('nome','')} - "
                    f"{cliente_precaricato.get('azienda','')}"
                )

dc1, dc2, dc3, dc4 = st.columns(4)
with dc1:
    cliente_nome = st.text_input("Nome cliente", value=cliente_precaricato.get("nome", dati_utente.get("nome", "")))
with dc2:
    cliente_azienda = st.text_input("Azienda", value=cliente_precaricato.get("azienda", dati_utente.get("azienda", "")))
with dc3:
    cliente_telefono = st.text_input("Telefono", value=cliente_precaricato.get("telefono", dati_utente.get("telefono", "")))
with dc4:
    cliente_email = st.text_input("Email", value=cliente_precaricato.get("email", dati_utente.get("email", "")))

if st.button("SALVA PREVENTIVO / RICHIESTA"):
    codice_preventivo = genera_codice_preventivo()
    dati = {
        "codice_preventivo": codice_preventivo,
        "data_ora": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "utente": utente_codice,
        "profilo": profilo,
        "cliente_nome": cliente_nome,
        "cliente_azienda": cliente_azienda,
        "cliente_telefono": cliente_telefono,
        "cliente_email": cliente_email,
        "configurazione": scelta,
        "luce_mm": luce_mm,
        "altezza_mm": altezza_mm,
        "traversa_m": f"{lunghezza_traversa:.2f}",
        "elettroblocco": "SI" if elettroblocco else "NO",
        "allaccio": "SI" if allaccio else "NO",
        "radar_sicurezza_laterale": "SI" if radar_sicurezza_laterale else "NO",
        "ricarico_percento": f"{ricarico_effettivo:.0f}",
        "imponibile": f"{imponibile:.2f}",
        "iva": f"{iva:.2f}",
        "totale_iva": f"{totale_iva:.2f}",
        "costo_satec": f"{costo_satec_totale:.2f}",
        "utile_lordo": f"{utile_lordo:.2f}",
        "margine_percento": f"{margine_percento:.1f}",
        "stato": "Bozza"
    }
    salva_preventivo(dati)
    salva_cliente_csv(cliente_nome, cliente_azienda, cliente_telefono, cliente_email, codice_preventivo, imponibile, utente_codice, profilo)
    st.session_state.ultimo_codice_preventivo = codice_preventivo
    st.success(f"Preventivo {codice_preventivo} salvato correttamente. SA-TEC lo vedrà nella dashboard.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DESCRIZIONE FORNITURA
# =========================

metà = len(articoli) // 2
lista_sx = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli[:metà]])
lista_dx = "".join([f"<li>{a['descrizione_lunga']}</li>" for a in articoli[metà:]])

st.markdown(f"""
<div class="card">
<div class="desc-title">DESCRIZIONE FORNITURA CLIENTE</div>
<div class="desc-grid">
<div>
<b>Profilo:</b> {PROFILI[profilo]}<br><br>
<b>Utente:</b> {utente_codice}<br><br>
<b>Configurazione selezionata:</b> {scelta}<br><br>
<b>Automazione:</b> SESAMO POWERCORE PW100<br><br>
<b>Luce passaggio:</b> {luce_mm} mm<br><br>
<b>Altezza passaggio:</b> {altezza_mm} mm<br><br>
<b>Misura traversa:</b> {lunghezza_traversa:.2f} metri<br><br>
<b>Resa:</b> Franco deposito SA-TEC Lamezia Terme
</div>
<div><ul>{lista_sx}</ul></div>
<div><ul>{lista_dx}</ul></div>
</div></div>
""", unsafe_allow_html=True)

if profilo != "SA-TEC":
    st.caption("Dettaglio costi e margini visibile solo a SA-TEC.")

if profilo == "SA-TEC":
    st.markdown('<div class="card"><div class="title-bar">DETTAGLIO INTERNO SA-TEC</div>', unsafe_allow_html=True)
    st.info(f"Ricarico applicato al profilo/utente: {ricarico_effettivo:.0f}%")
    tabella = []
    for a in articoli:
        utile_articolo = a["totale"] - a["costo_totale_satec"]
        margine_articolo = (utile_articolo / a["costo_totale_satec"] * 100) if a["costo_totale_satec"] > 0 else 0
        tabella.append({
            "Codice": a["codice"],
            "Descrizione": a["descrizione"],
            "Q.tà": round(a["quantita"], 2),
            "Listino unit.": euro(a["listino_unitario"]),
            "Costo SA-TEC unit.": euro(a["costo_unitario_satec"]),
            "Prezzo unit.": euro(a["prezzo_unitario"]),
            "Totale vendita": euro(a["totale"]),
            "Costo totale": euro(a["costo_totale_satec"]),
            "Utile €": euro(utile_articolo),
            "Margine %": f"{margine_articolo:.1f}%",
        })
    st.markdown(tabella_html_sicura(tabella), unsafe_allow_html=True)
    st.markdown(f"""
    <div class="vat-box" style="margin-top:16px;background:#fff3a3;border:2px solid #06499b;">
    <b>Totale interno SA-TEC</b><br><br>
    Costo netto totale: <span style="float:right;">{euro(costo_satec_totale)}</span><br>
    Vendita IVA esclusa: <span style="float:right;">{euro(imponibile)}</span><br>
    Utile lordo: <span style="float:right;">{euro(utile_lordo)}</span><br>
    Margine su costo: <span style="float:right;">{margine_percento:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# STAMPA / PDF HTML
# =========================

righe_descrizione = ""
for art in articoli:
    righe_descrizione += f"<tr><td>{art['descrizione']}</td><td>{art['descrizione_lunga']}</td></tr>"

logo_print = f'<img src="data:image/jpeg;base64,{logo_satec64}" style="width:240px;">' if logo_satec64 else f"<h1>{AZIENDA}</h1>"
sesamo_print = f'<img src="data:image/png;base64,{logo_sesamo64}" style="height:90px;">' if logo_sesamo64 else "<b>SESAMO POWERCORE PW100</b>"

codice_stampa = st.session_state.get("ultimo_codice_preventivo", "DA SALVARE")
brand_preventivo = dati_brand_preventivo(profilo, dati_utente)
intestazione_brand_html = html_intestazione_brand(brand_preventivo)

logo_utente_path = trova_logo_utente(utente_codice) if profilo in ["RIVENDITORE", "GROSSISTA"] else ""
logo_utente64 = img_to_base64([logo_utente_path]) if logo_utente_path else ""

if brand_preventivo.get("mostra_satec"):
    logo_print_finale = logo_print
elif logo_utente64:
    logo_print_finale = f'<img src="data:image/png;base64,{logo_utente64}" style="max-width:240px;max-height:105px;object-fit:contain;">'
else:
    logo_print_finale = f"<h1 style='color:#06499b;'>{brand_preventivo.get('azienda','')}</h1>"

nome_firma_azienda = brand_preventivo.get("azienda", AZIENDA)

html_stampa = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Preventivo SA-TEC</title>
<style>
body {{font-family:Arial,sans-serif;color:#18324f;margin:28px;background:#ffffff;}}
.header {{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:5px solid #06499b;padding-bottom:18px;margin-bottom:22px;}}
.company {{text-align:right;font-size:13px;line-height:1.45;color:#111;}}
h1 {{color:#06499b;font-size:30px;margin:10px 0 2px 0;}}
h2 {{color:#06499b;font-size:20px;margin:18px 0 10px 0;}}
.doc-code {{font-size:24px;font-weight:900;color:#111;margin-bottom:18px;}}
.box {{border:2px solid #d7e6f7;border-left:8px solid #06499b;border-radius:12px;padding:16px;margin-bottom:18px;background:#f8fbff;}}
.brand {{display:flex;justify-content:space-between;align-items:center;border:2px solid #d7e6f7;border-radius:12px;padding:15px;margin-bottom:18px;background:#ffffff;}}
.grid-info {{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:18px;}}
.info-card {{border:2px solid #d7e6f7;border-radius:12px;padding:14px;background:#f8fbff;min-height:88px;}}
.info-title {{font-size:13px;font-weight:900;color:#06499b;text-transform:uppercase;margin-bottom:8px;}}
.info-text {{font-size:14px;line-height:1.45;color:#111;}}
table {{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px;}}
th {{background:#06499b;color:white;padding:10px;text-align:left;}}
td {{border:1px solid #d7e6f7;padding:9px;vertical-align:top;color:#111;}}
.total-box {{margin-top:22px;border:3px solid #06499b;border-radius:14px;padding:16px;background:#f8fbff;}}
.total-line {{display:flex;justify-content:space-between;font-size:16px;margin:6px 0;}}
.total-main {{display:flex;justify-content:space-between;font-size:25px;font-weight:900;color:#06499b;margin-top:10px;border-top:2px solid #bdd4ef;padding-top:10px;}}
.conditions {{margin-top:24px;font-size:14px;line-height:1.55;color:#111;}}
.conditions ul {{margin-top:6px;}}
.signature-table td {{height:75px;text-align:center;vertical-align:bottom;}}
.print-button {{background:#06499b;color:white;padding:14px 22px;border:none;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer;margin-bottom:18px;}}
@media print {{.print-button {{display:none;}} body {{margin:18px;}}}}
</style>
</head>
<body>
<button class="print-button" onclick="window.print()">STAMPA / SALVA PDF</button>
<div class="header"><div>{logo_print_finale}</div><div class="company">{intestazione_brand_html}</div></div>
<div class="brand"><div><h2 style="margin:0;">SESAMO POWERCORE PW100</h2><div>Configuratore porte automatiche lineari</div></div><div>{sesamo_print}</div></div>
<h1>Preventivo porta automatica</h1>
<div class="doc-code">N° {codice_stampa}</div>

<div class="grid-info">
<div class="info-card">
<div class="info-title">Cliente</div>
<div class="info-text">
<b>{cliente_nome}</b><br>
{cliente_azienda}<br>
Tel. {cliente_telefono}<br>
Email: {cliente_email}
</div>
</div>

<div class="info-card">
<div class="info-title">Configurazione</div>
<div class="info-text">
<b>{scelta}</b><br>
Profilo: {PROFILI[profilo]}<br>
Utente: {utente_codice}<br>
Validità offerta: 15 giorni
</div>
</div>

<div class="info-card">
<div class="info-title">Misure</div>
<div class="info-text">
Luce passaggio: <b>{luce_mm} mm</b><br>
Altezza passaggio: <b>{altezza_mm} mm</b><br>
Traversa: <b>{lunghezza_traversa:.2f} m</b><br>
Data: {date.today().strftime("%d/%m/%Y")}
</div>
</div>
</div>

<div class="box">
<b>Resa:</b> {"Franco deposito SA-TEC Lamezia Terme" if brand_preventivo.get("mostra_satec") else "Da concordare"}<br>
<b>Codice preventivo:</b> {codice_stampa}
</div>
<h2>Descrizione fornitura</h2>
<table><thead><tr><th>Voce</th><th>Descrizione</th></tr></thead><tbody>{righe_descrizione}</tbody></table>
<div class="total-box">
<div class="total-line"><span>Totale preventivo IVA esclusa</span><b>{euro(imponibile)}</b></div>
<div class="total-line"><span>IVA 22%</span><b>{euro(iva)}</b></div>
<div class="total-main"><span>Totale IVA inclusa</span><span>{euro(totale_iva)}</span></div>
</div>
<div class="conditions">
<h2>Condizioni commerciali</h2>
<ul>
<li>Validità offerta: 15 giorni dalla data di emissione</li>
<li>Pagamento: 50% all'ordine mediante bonifico bancario</li>
<li>Saldo: 50% alla consegna</li>
<li>Tempi di consegna: da confermare all'ordine</li>
<li>IVA esclusa, salvo diversa indicazione</li>
<li>Opere murarie escluse</li>
<li>Opere elettriche escluse</li>
<li>Predisposizione alimentazione automazione a carico del committente</li>
<li>Linea dedicata 230V con interruttore magnetotermico 10A a carico del committente</li>
<li>Trasporto escluso, salvo diversa indicazione nell'offerta</li>
<li>Eventuali opere aggiuntive non indicate nel presente preventivo saranno contabilizzate separatamente</li>
<li>Misure e caratteristiche da verificare definitivamente in fase di rilievo</li>
<li>La presente offerta è subordinata alla verifica tecnica finale</li>
</ul>
{"<h2>Coordinate bancarie</h2><p><b>Intestatario:</b> " + AZIENDA + "<br><b>IBAN:</b> " + IBAN + "<br><b>Causale:</b> Acconto preventivo " + codice_stampa + "</p>" if brand_preventivo.get("mostra_satec") else ""}
<h2>Accettazione offerta</h2>
<p>Per accettazione del presente preventivo e delle condizioni commerciali sopra indicate.</p>
<table class="signature-table">
<tr><td><b>Firma Cliente</b><br><br>_____________________________</td><td><b>{nome_firma_azienda}</b><br><br>_____________________________</td></tr>
</table>
</div>
<div style="margin-top:22px;border-top:2px solid #d7e6f7;padding-top:12px;font-size:12px;color:#555;text-align:center;">
{"Documento generato con configuratore SA-TEC - Preventivo soggetto a verifica tecnica finale." if brand_preventivo.get("mostra_satec") else "Preventivo soggetto a verifica tecnica finale."}
</div>
</body>
</html>
"""

html_js = json.dumps(html_stampa)

components.html(f"""
<div style="border:2px solid #06499b;border-radius:14px;padding:18px;background:#f8fbff;">
<button onclick="openPrint()" style="background:#06499b;color:white;border:none;padding:14px 22px;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;">
STAMPA / SALVA PDF
</button>
</div>
<script>
function openPrint() {{
const html = {html_js};
const win = window.open("", "_blank");
win.document.open();
win.document.write(html);
win.document.close();
}}
</script>
""", height=100)


# =========================
# EMAIL PREVENTIVO
# =========================

codice_email = st.session_state.get("ultimo_codice_preventivo", "")
if profilo == "SA-TEC":
    st.markdown('<div class="card"><div class="title-bar">INVIO EMAIL PREVENTIVO</div>', unsafe_allow_html=True)
    email_dest = st.text_input("Email destinatario preventivo", value=cliente_email, key="email_dest_preventivo")

    if not codice_email:
        st.info("Prima salva il preventivo. Dopo il salvataggio comparirà il codice SAT e potrai inviare l'email.")
    else:
        st.write(f"Preventivo pronto per invio: **{codice_email}**")

        col_email1, col_email2 = st.columns(2)

        with col_email1:
            if st.button("INVIA PREVENTIVO VIA EMAIL"):
                if not email_dest:
                    st.error("Inserisci l'email del destinatario.")
                else:
                    ok, errore = invia_email_automatica(email_dest, codice_email, html_stampa)
                    if ok:
                        aggiorna_stato_preventivo_csv(codice_email, "Inviato", email_dest)
                        st.success(f"Email inviata correttamente a {email_dest}. Copia inviata anche a SA-TEC.")
                    else:
                        st.error(f"Email non inviata: {errore}")

        with col_email2:
            import urllib.parse
            oggetto = f"Preventivo SA-TEC N° {codice_email}"
            corpo = testo_email_preventivo(codice_email)
            mailto = "mailto:" + urllib.parse.quote(email_dest) + "?subject=" + urllib.parse.quote(oggetto) + "&body=" + urllib.parse.quote(corpo)
            st.markdown(f'<a href="{mailto}" target="_blank"><button style="background:#06499b;color:white;border:none;padding:14px 22px;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;width:100%;height:48px;">PREPARA EMAIL MANUALE</button></a>', unsafe_allow_html=True)

        st.caption("L'invio automatico allega il preventivo in formato HTML stampabile. Il cliente può aprirlo e salvarlo in PDF.")

    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Versione V36 - Riquadri porta cliccabili")

st.markdown(f"""
<div class="footer">
<div>📍 {AZIENDA}<br>{SEDE}</div>
<div>☎ {TELEFONO}</div>
<div>✉ {EMAIL}</div>
</div>
""", unsafe_allow_html=True)
