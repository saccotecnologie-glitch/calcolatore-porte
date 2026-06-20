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
from supabase import create_client
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
    return 60.0

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

# =========================
# RICERCA MANUALI ROBUSTA
# =========================

def trova_file_manuale(possibili_nomi, parole_chiave):
    for nome in possibili_nomi:
        p = Path(nome)
        if p.exists() and p.is_file() and p.stat().st_size > 1000:
            return p

    for f in Path(".").glob("*"):
        nome = f.name.lower()
        if f.is_file() and ".pdf" in nome:
            if all(k.lower() in nome for k in parole_chiave):
                if f.stat().st_size > 1000:
                    return f
    return None



# =========================
# SUPABASE
# =========================

def supabase_client():
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception as e:
        st.sidebar.warning(f"Supabase non collegato: {e}")
        return None

def supabase_attivo():
    return supabase_client() is not None

def carica_utenti_supabase():
    sb = supabase_client()
    if sb is None:
        return {}
    try:
        res = sb.table("utenti").select("*").execute()
        utenti = {}
        for r in res.data or []:
            codice = str(r.get("username", "")).strip().upper()
            if not codice:
                continue
            ruolo = str(r.get("ruolo", "CLIENTE")).strip().upper()
            utenti[codice] = {
                "password": r.get("password", ""),
                "profilo": ruolo,
                "nome": r.get("azienda", "") or codice,
                "azienda": r.get("azienda", ""),
                "telefono": r.get("telefono", ""),
                "email": r.get("email", ""),
                "ricarico": str(r.get("ricarico", "0") or "0"),
                "logo_url": r.get("logo_url", "")
            }
        return utenti
    except Exception as e:
        st.sidebar.warning(f"Utenti Supabase non caricati: {e}")
        return {}

def salva_utente_supabase(username, password, ruolo, azienda, telefono, email, ricarico=0, logo_url=""):
    sb = supabase_client()
    if sb is None:
        return False, "Supabase non collegato"

    username = str(username or "").strip().upper()
    if not username:
        return False, "Username mancante"

    try:
        payload = {
            "username": username,
            "password": str(password or "").strip(),
            "ruolo": str(ruolo or "CLIENTE").strip().upper(),
            "azienda": str(azienda or "").strip(),
            "telefono": str(telefono or "").strip(),
            "email": str(email or "").strip().lower(),
            "ricarico": float(ricarico or 0),
            "logo_url": str(logo_url or "").strip()
        }

        esistente = cerca_utente_supabase(username)
        if esistente:
            sb.table("utenti").update(payload).eq("username", username).execute()
        else:
            sb.table("utenti").insert(payload).execute()

        return True, ""

    except Exception as e:
        return False, str(e)

def aggiorna_ricarico_utente_supabase(username, nuovo_ricarico):
    sb = supabase_client()
    if sb is None:
        return False, "Supabase non collegato"

    try:
        sb.table("utenti").update({"ricarico": float(nuovo_ricarico or 0)}).eq("username", username).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

def utenti_rivenditori_grossisti():
    utenti = carica_tutti_utenti()
    righe = []
    for codice, d in utenti.items():
        prof = str(d.get("profilo", "")).upper()
        if prof in ["RIVENDITORE", "GROSSISTA"]:
            righe.append({
                "utente": codice,
                "profilo": prof,
                "azienda": d.get("azienda", ""),
                "telefono": d.get("telefono", ""),
                "email": d.get("email", ""),
                "ricarico": d.get("ricarico", "0"),
            })
    return righe


def cerca_utente_supabase(username):
    sb = supabase_client()
    if sb is None:
        return None
    try:
        res = sb.table("utenti").select("*").eq("username", username).limit(1).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None

def salva_cliente_supabase(nome, azienda, telefono, email, owner_utente, owner_profilo):
    sb = supabase_client()
    if sb is None:
        return None

    nome = str(nome or "").strip()
    azienda = str(azienda or "").strip()
    telefono = str(telefono or "").strip()
    email = str(email or "").strip().lower()

    if not nome and not azienda and not telefono and not email:
        return None

    try:
        trovato = None
        if email:
            res = sb.table("clienti").select("*").eq("email", email).limit(1).execute()
            if res.data:
                trovato = res.data[0]

        if not trovato and telefono:
            res = sb.table("clienti").select("*").eq("telefono", telefono).limit(1).execute()
            if res.data:
                trovato = res.data[0]

        utente_db = cerca_utente_supabase(owner_utente)
        utente_id = utente_db.get("id") if utente_db else None

        payload = {
            "nome": nome,
            "azienda": azienda,
            "telefono": telefono,
            "email": email,
            "utente_id": utente_id
        }

        if trovato:
            sb.table("clienti").update(payload).eq("id", trovato["id"]).execute()
            return trovato["id"]

        res = sb.table("clienti").insert(payload).execute()
        if res.data:
            return res.data[0].get("id")

    except Exception as e:
        st.sidebar.warning(f"Cliente non salvato su Supabase: {e}")

    return None

def salva_preventivo_supabase(dati, cliente_id=None, utente_codice=""):
    sb = supabase_client()
    if sb is None:
        return False

    try:
        utente_db = cerca_utente_supabase(utente_codice)
        utente_id = utente_db.get("id") if utente_db else None

        def to_int(v):
            try:
                return int(float(str(v).replace(",", ".")))
            except:
                return None

        def to_float(v):
            try:
                return float(str(v).replace(",", "."))
            except:
                return None

        payload = {
            "codice_preventivo": dati.get("codice_preventivo", ""),
            "cliente_id": cliente_id,
            "utente_id": utente_id,
            "configurazione": dati.get("configurazione", ""),
            "luce_mm": to_int(dati.get("luce_mm", "")),
            "altezza_mm": to_int(dati.get("altezza_mm", "")),
            "traversa_m": to_float(dati.get("traversa_m", "")),
            "totale": to_float(dati.get("totale_iva", dati.get("imponibile", ""))),
            "stato": dati.get("stato", "Bozza")
        }

        sb.table("preventivi").insert(payload).execute()
        return True

    except Exception as e:
        st.sidebar.warning(f"Preventivo non salvato su Supabase: {e}")
        return False

def carica_preventivi_supabase():
    sb = supabase_client()
    if sb is None:
        return []
    try:
        res = sb.table("preventivi").select("*").order("creato_il", desc=True).execute()
        righe = []
        for p in res.data or []:
            righe.append({
                "codice_preventivo": p.get("codice_preventivo", ""),
                "data_ora": p.get("creato_il", ""),
                "utente": p.get("utente_id", ""),
                "profilo": "",
                "cliente_nome": p.get("cliente_id", ""),
                "cliente_azienda": "",
                "configurazione": p.get("configurazione", ""),
                "luce_mm": p.get("luce_mm", ""),
                "altezza_mm": p.get("altezza_mm", ""),
                "traversa_m": p.get("traversa_m", ""),
                "totale_iva": p.get("totale", ""),
                "stato": p.get("stato", ""),
            })
        return righe
    except Exception as e:
        st.sidebar.warning(f"Preventivi Supabase non caricati: {e}")
        return []

def carica_clienti_supabase():
    sb = supabase_client()
    if sb is None:
        return []
    try:
        res = sb.table("clienti").select("*").order("creato_il", desc=True).execute()
        righe = []
        for c in res.data or []:
            righe.append({
                "nome": c.get("nome", ""),
                "azienda": c.get("azienda", ""),
                "telefono": c.get("telefono", ""),
                "email": c.get("email", ""),
                "primo_preventivo": "",
                "ultimo_preventivo": "",
                "data_primo_preventivo": c.get("creato_il", ""),
                "data_ultimo_preventivo": c.get("creato_il", ""),
                "numero_preventivi": "",
                "totale_preventivi": "",
                "owner_utente": c.get("utente_id", ""),
                "owner_profilo": "",
            })
        return righe
    except Exception as e:
        st.sidebar.warning(f"Clienti Supabase non caricati: {e}")
        return []



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

    utenti_supabase = carica_utenti_supabase()
    if "ADMIN" in utenti_supabase:
        utenti["ADMIN"].update(utenti_supabase["ADMIN"])

    for codice, dati in utenti_supabase.items():
        if codice != "ADMIN":
            utenti[codice] = dati

    utenti_csv = carica_utenti_csv()
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


def invia_notifica_richiesta_satec(codice_preventivo, cliente_nome, cliente_azienda, cliente_telefono, cliente_email, scelta, luce_mm, altezza_mm, totale_iva):
    """
    Invia notifica interna a SA-TEC quando un cliente finale libero invia una richiesta.
    Se SMTP non è configurato correttamente, la richiesta resta comunque salvata.
    """
    try:
        email_user = st.secrets["EMAIL_USER"]
        email_password = st.secrets["EMAIL_PASSWORD"]
        smtp_server = st.secrets.get("EMAIL_SMTP", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("EMAIL_PORT", "587"))

        corpo = f"""Nuova richiesta preventivo dal configuratore SA-TEC.

Codice: {codice_preventivo}

Cliente:
Nome: {cliente_nome}
Azienda: {cliente_azienda}
Telefono: {cliente_telefono}
Email: {cliente_email}

Configurazione:
{scelta}
Luce passaggio: {luce_mm} mm
Altezza passaggio: {altezza_mm} mm
Totale indicativo IVA inclusa: {euro(totale_iva)}

La richiesta è stata salvata nel configuratore.
"""

        msg = EmailMessage()
        msg["From"] = email_user
        msg["To"] = EMAIL
        msg["Subject"] = f"Nuova richiesta configuratore SA-TEC - {codice_preventivo}"
        msg.set_content(corpo)

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


STATI_PREVENTIVO = ["Bozza", "Inviato", "Trattativa", "Accettato", "Perso", "Ordinato"]

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


def elimina_preventivo_csv(codice_preventivo):
    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return False, "File preventivi CSV non trovato"
    try:
        with open(path, "r", encoding="utf-8") as f:
            righe = list(csv.DictReader(f))
        if not righe:
            return False, "Nessun preventivo presente"
        fieldnames = list(righe[0].keys())
        codice_preventivo = str(codice_preventivo or "").strip()
        nuove = [r for r in righe if str(r.get("codice_preventivo", "")).strip() != codice_preventivo]
        if len(nuove) == len(righe):
            return False, "Preventivo non trovato nel CSV"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(nuove)
        return True, ""
    except Exception as e:
        return False, str(e)


def elimina_preventivo_supabase(codice_preventivo):
    sb = supabase_client()
    if sb is None:
        return False, "Supabase non collegato"
    try:
        sb.table("preventivi").delete().eq("codice_preventivo", codice_preventivo).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


def elimina_preventivo_admin(codice_preventivo):
    ok_sb, err_sb = elimina_preventivo_supabase(codice_preventivo)
    if ok_sb:
        return True, "Preventivo eliminato da Supabase"
    ok_csv, err_csv = elimina_preventivo_csv(codice_preventivo)
    if ok_csv:
        return True, "Preventivo eliminato dal CSV"
    return False, f"Supabase: {err_sb} | CSV: {err_csv}"



def duplica_preventivo_admin(codice_preventivo):
    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return False, "File preventivi CSV non trovato"

    try:
        with open(path, "r", encoding="utf-8") as f:
            righe = list(csv.DictReader(f))

        originale = None
        for r in righe:
            if str(r.get("codice_preventivo", "")).strip() == str(codice_preventivo).strip():
                originale = dict(r)
                break

        if not originale:
            return False, "Preventivo originale non trovato"

        nuovo_codice = genera_codice_preventivo()
        originale["codice_preventivo"] = nuovo_codice
        originale["data_ora"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        originale["stato"] = "Bozza"

        fieldnames = list(righe[0].keys())
        for k in originale.keys():
            if k not in fieldnames:
                fieldnames.append(k)

        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(originale)

        return True, nuovo_codice
    except Exception as e:
        return False, str(e)


def html_export_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", "") or "")
    righe = ""
    campi = [
        ("Codice", "codice_preventivo"),
        ("Data", "data_ora"),
        ("Rivenditore / Utente", "utente"),
        ("Profilo", "profilo"),
        ("Cliente", "cliente_nome"),
        ("Azienda cliente", "cliente_azienda"),
        ("Telefono", "cliente_telefono"),
        ("Email", "cliente_email"),
        ("Configurazione", "configurazione"),
        ("Luce mm", "luce_mm"),
        ("Altezza mm", "altezza_mm"),
        ("Traversa m", "traversa_m"),
        ("Elettroblocco", "elettroblocco"),
        ("Radar sicurezza laterale", "radar_sicurezza_laterale"),
        ("Allaccio / Collaudo", "allaccio"),
        ("Ricarico totale %", "ricarico_percento"),
        ("Ricarico base %", "ricarico_base_percento"),
        ("Ricarico extra %", "ricarico_extra_percento"),
        ("Imponibile", "imponibile"),
        ("IVA", "iva"),
        ("Totale IVA inclusa", "totale_iva"),
        ("Costo SA-TEC", "costo_satec"),
        ("Utile lordo", "utile_lordo"),
        ("Margine %", "margine_percento"),
        ("Stato", "stato"),
    ]

    for label, key in campi:
        righe += f"<tr><th>{label}</th><td>{p.get(key, '')}</td></tr>"

    return f"""
    <html>
    <head>
    <meta charset="utf-8">
    <title>Dettaglio preventivo {codice}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; color:#111; }}
        .head {{ background:#06499b; color:white; padding:18px; border-radius:12px; }}
        h1 {{ margin:0; }}
        table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
        th {{ width:260px; background:#eef6ff; color:#06499b; text-align:left; }}
        th, td {{ border:1px solid #bdd4ef; padding:10px; }}
        .footer {{ margin-top:25px; font-size:13px; color:#555; }}
    
/* V68 - CRM DETAIL PROFESSIONALE */
.crm-detail-v68 {
    background:#ffffff;
    border:2px solid #bdd4ef;
    border-radius:18px;
    padding:16px;
    margin:18px 0;
    box-shadow:0 6px 18px rgba(6,73,155,0.10);
}
.crm-detail-head-v68 {
    background:#06499b;
    color:white;
    border-radius:12px;
    padding:14px 18px;
}
.crm-detail-code-v68 {
    font-size:24px;
    font-weight:900;
}
.crm-detail-sub-v68 {
    font-size:14px;
    font-weight:800;
    margin-top:4px;
}
.crm-detail-grid-v68 {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:12px;
    margin-top:14px;
}
.crm-mini-card-v68 {
    background:#eef6ff;
    border:1px solid #bdd4ef;
    border-radius:12px;
    padding:12px;
    color:#111;
    font-size:14px;
    font-weight:800;
}
.crm-mini-card-v68 span {
    color:#06499b;
    font-size:20px;
    font-weight:900;
}
.crm-white-box-v68 {
    background:#ffffff;
    border:2px solid #bdd4ef;
    border-radius:14px;
    padding:16px;
    color:#111;
    font-size:15px;
    font-weight:800;
    line-height:1.65;
}
.crm-price-row-v68 {
    display:flex;
    justify-content:space-between;
    gap:12px;
    padding:8px 0;
    color:#111;
    font-size:15px;
    font-weight:800;
}
.crm-price-row-v68.total {
    color:#06499b;
    font-size:20px;
    font-weight:900;
}

</style>
    </head>
    <body>
        <div class="head">
            <h1>Dettaglio preventivo {codice}</h1>
            <div>SA-TEC S.R.L.s - CRM Commerciale</div>
        </div>
        <table>{righe}</table>
        <div class="footer">Documento gestionale interno. Stampare o salvare come PDF dal browser.</div>
    </body>
    </html>
    """


def valore_admin_euro(p, campo):
    try:
        return euro(float(str(p.get(campo, "0")).replace(",", ".") or 0))
    except:
        return str(p.get(campo, "") or "")


def render_dettaglio_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", "") or "")
    configurazione = str(p.get("configurazione", "") or "")
    stato = str(p.get("stato", "Bozza") or "Bozza")
    cliente = p.get("cliente_nome", "") or p.get("cliente_azienda", "") or "Cliente non indicato"
    rivenditore = p.get("utente", "") or "Utente non indicato"

    elettro = str(p.get("elettroblocco", "") or "No")
    radar = str(p.get("radar_sicurezza_laterale", "") or "No")
    allaccio = str(p.get("allaccio", "") or "No")

    accessori = []
    if elettro and elettro.lower() not in ["no", "false", "0", ""]:
        accessori.append({"Accessorio": "Elettroblocco", "Q.tà": "1", "Valore": elettro})
    if radar and radar.lower() not in ["no", "false", "0", ""]:
        accessori.append({"Accessorio": "Radar sicurezza laterale", "Q.tà": "1", "Valore": radar})
    if allaccio and allaccio.lower() not in ["no", "false", "0", ""]:
        accessori.append({"Accessorio": "Allaccio e collaudo", "Q.tà": "1", "Valore": allaccio})
    if not accessori:
        accessori.append({"Accessorio": "Nessun accessorio extra indicato", "Q.tà": "", "Valore": ""})

    st.markdown(f"""
    <div class="crm-detail-v68">
        <div class="crm-detail-head-v68">
            <div>
                <div class="crm-detail-code-v68">DETTAGLIO PREVENTIVO {codice}</div>
                <div class="crm-detail-sub-v68">{configurazione} · Stato: {stato}</div>
            </div>
        </div>
        <div class="crm-detail-grid-v68">
            <div class="crm-mini-card-v68"><b>Cliente</b><br>{cliente}</div>
            <div class="crm-mini-card-v68"><b>Rivenditore / Utente</b><br>{rivenditore}</div>
            <div class="crm-mini-card-v68"><b>Data</b><br>{p.get('data_ora', '')}</div>
            <div class="crm-mini-card-v68"><b>Totale vendita</b><br><span>{valore_admin_euro(p, 'totale_iva')}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.25, 1])

    with c1:
        st.markdown("### Configurazione e misure")
        st.markdown(f"""
        <div class="crm-white-box-v68">
            <b>Automazione scelta:</b> {configurazione}<br>
            <b>Luce passaggio:</b> {p.get('luce_mm', '')} mm<br>
            <b>Altezza:</b> {p.get('altezza_mm', '')} mm<br>
            <b>Traversa:</b> {p.get('traversa_m', '')} m<br>
            <b>Cliente email:</b> {p.get('cliente_email', '')}<br>
            <b>Telefono:</b> {p.get('cliente_telefono', '')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Accessori / servizi")
        st.markdown(tabella_html_sicura(accessori), unsafe_allow_html=True)

    with c2:
        st.markdown("### Riepilogo economico")
        st.markdown(f"""
        <div class="crm-white-box-v68">
            <div class="crm-price-row-v68"><span>Totale netto vendita</span><b>{valore_admin_euro(p, 'imponibile')}</b></div>
            <div class="crm-price-row-v68"><span>IVA</span><b>{valore_admin_euro(p, 'iva')}</b></div>
            <div class="crm-price-row-v68 total"><span>Totale vendita</span><b>{valore_admin_euro(p, 'totale_iva')}</b></div>
            <hr>
            <div class="crm-price-row-v68"><span>Costo netto SA-TEC</span><b>{valore_admin_euro(p, 'costo_satec')}</b></div>
            <div class="crm-price-row-v68"><span>Utile lordo</span><b>{valore_admin_euro(p, 'utile_lordo')}</b></div>
            <div class="crm-price-row-v68"><span>Margine</span><b>{p.get('margine_percento', '')}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)

    with a1:
        html_admin = html_export_preventivo_admin(p)
        st.download_button(
            "ESPORTA HTML / PDF",
            data=html_admin.encode("utf-8"),
            file_name=f"Dettaglio_{codice}.html",
            mime="text/html",
            use_container_width=True,
            key=f"export_html_{codice}"
        )

    with a2:
        if st.button("DUPLICA PREVENTIVO", key=f"duplica_{codice}", use_container_width=True):
            ok_dup, msg_dup = duplica_preventivo_admin(codice)
            if ok_dup:
                st.success(f"Preventivo duplicato: {msg_dup}")
                st.rerun()
            else:
                st.error(msg_dup)

    with a3:
        st.info("Apri il file HTML e fai Stampa → Salva PDF.")


def statistiche_stati_preventivi(preventivi):
    stats = {s: 0 for s in STATI_PREVENTIVO}
    for p in preventivi:
        stato = str(p.get("stato", "Bozza") or "Bozza")
        if stato not in stats:
            stats[stato] = 0
        stats[stato] += 1
    return stats

def box_stati_html(stats):
    return ""


def valore_preventivo_float(p):
    for campo in ["imponibile", "totale_iva", "totale"]:
        try:
            return float(str(p.get(campo, "0")).replace(",", ".") or 0)
        except:
            pass
    return 0.0

def utile_preventivo_float(p):
    try:
        return float(str(p.get("utile_lordo", "0")).replace(",", ".") or 0)
    except:
        return 0.0

def dashboard_crm_html(preventivi):
    return ""

def filtra_preventivi_dashboard(preventivi, cerca="", stato="Tutti"):
    cerca = str(cerca or "").strip().lower()
    stato = str(stato or "Tutti").strip()

    out = []
    for p in preventivi:
        if stato != "Tutti" and str(p.get("stato", "")) != stato:
            continue

        if cerca:
            testo = " ".join([
                str(p.get("codice_preventivo", "")),
                str(p.get("cliente_nome", "")),
                str(p.get("cliente_azienda", "")),
                str(p.get("cliente_email", "")),
                str(p.get("utente", "")),
                str(p.get("configurazione", "")),
                str(p.get("stato", "")),
            ]).lower()
            if cerca not in testo:
                continue

        out.append(p)
    return out



# =========================
# CLIENTI CSV
# =========================

def carica_clienti():
    clienti_sb = carica_clienti_supabase()
    if clienti_sb:
        return clienti_sb

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
        "ricarico_percento", "ricarico_base_percento", "ricarico_extra_percento", "imponibile", "iva", "totale_iva", "costo_satec", "utile_lordo", "margine_percento", "stato"
    ]
    with open(PREVENTIVI_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campi)
        if not file_exists:
            writer.writeheader()
        writer.writerow(dati)

def carica_preventivi():
    preventivi_sb = carica_preventivi_supabase()
    if preventivi_sb:
        return preventivi_sb

    path = Path(PREVENTIVI_CSV)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# =========================
# CRM DASHBOARD NATIVA - FIX SICURO
# =========================

def crm_valore_float(p):
    for campo in ["imponibile", "totale_iva", "totale"]:
        try:
            return float(str(p.get(campo, "0")).replace(",", ".") or 0)
        except:
            pass
    return 0.0

def crm_utile_float(p):
    try:
        return float(str(p.get("utile_lordo", "0")).replace(",", ".") or 0)
    except:
        return 0.0

def render_dashboard_crm(preventivi):
    totale_preventivi = len(preventivi)
    valore_totale = sum(crm_valore_float(p) for p in preventivi)
    utile_totale = sum(crm_utile_float(p) for p in preventivi)

    accettati = sum(1 for p in preventivi if str(p.get("stato", "")).lower() == "accettato")
    ordinati = sum(1 for p in preventivi if str(p.get("stato", "")).lower() == "ordinato")
    persi = sum(1 for p in preventivi if str(p.get("stato", "")).lower() == "perso")
    conversione = ((accettati + ordinati) / totale_preventivi * 100) if totale_preventivi else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Preventivi", totale_preventivi)
    c2.metric("Valore totale", euro(valore_totale))
    c3.metric("Utile lordo", euro(utile_totale))
    c4.metric("Accettati/Ordinati", accettati + ordinati)
    c5.metric("Persi", persi)
    c6.metric("Conversione", f"{conversione:.1f}%")

def render_stati_preventivi(stats):
    cols = st.columns(len(STATI_PREVENTIVO))
    for col, stato in zip(cols, STATI_PREVENTIVO):
        col.metric(stato, stats.get(stato, 0))

def filtra_preventivi_dashboard(preventivi, cerca="", stato="Tutti"):
    cerca = str(cerca or "").strip().lower()
    stato = str(stato or "Tutti").strip()

    out = []
    for p in preventivi:
        if stato != "Tutti" and str(p.get("stato", "")) != stato:
            continue

        if cerca:
            testo = " ".join([
                str(p.get("codice_preventivo", "")),
                str(p.get("cliente_nome", "")),
                str(p.get("cliente_azienda", "")),
                str(p.get("cliente_email", "")),
                str(p.get("utente", "")),
                str(p.get("configurazione", "")),
                str(p.get("stato", "")),
            ]).lower()
            if cerca not in testo:
                continue

        out.append(p)
    return out



# =========================
# CRM AVANZATO V48
# =========================

def crm_nome_cliente(p):
    nome = str(p.get("cliente_nome", "") or "").strip()
    azienda = str(p.get("cliente_azienda", "") or "").strip()
    if nome and azienda:
        return f"{nome} - {azienda}"
    return nome or azienda or "Cliente non indicato"

def crm_nome_utente(p):
    return str(p.get("utente", "") or "Non indicato").strip() or "Non indicato"

def top_aggregati(preventivi, campo_nome_fn, limite=10):
    agg = {}
    for p in preventivi:
        nome = campo_nome_fn(p)
        if nome not in agg:
            agg[nome] = {"N.": 0, "Valore": 0.0, "Utile": 0.0}
        agg[nome]["N."] += 1
        agg[nome]["Valore"] += crm_valore_float(p)
        agg[nome]["Utile"] += crm_utile_float(p)

    righe = []
    for nome, d in agg.items():
        righe.append({
            "Nome": nome,
            "N. preventivi": d["N."],
            "Valore": euro(d["Valore"]),
            "Utile": euro(d["Utile"]),
        })
    righe.sort(key=lambda r: float(str(r["Valore"]).replace("€", "").replace(".", "").replace(",", ".").strip() or 0), reverse=True)
    return righe[:limite]

def render_crm_avanzato(preventivi):
    st.markdown('<h3 style="color:#06499b;">Analisi commerciale avanzata</h3>', unsafe_allow_html=True)

    stati = statistiche_stati_preventivi(preventivi)
    dati_stati = []
    for stato in STATI_PREVENTIVO:
        dati_stati.append({"Stato": stato, "Numero": stati.get(stato, 0)})

    try:
        st.bar_chart(pd.DataFrame(dati_stati).set_index("Stato"))
    except:
        pass

    ctop1, ctop2 = st.columns(2)
    with ctop1:
        st.markdown("### Top clienti")
        righe_clienti = top_aggregati(preventivi, crm_nome_cliente, 10)
        st.markdown(tabella_html_sicura(righe_clienti), unsafe_allow_html=True)

    with ctop2:
        st.markdown("### Top utenti / rivenditori")
        righe_utenti = top_aggregati(preventivi, crm_nome_utente, 10)
        st.markdown(tabella_html_sicura(righe_utenti), unsafe_allow_html=True)


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
            "ricarico": "60"
        }

    st.sidebar.markdown("## Accesso")
    st.sidebar.info("Cliente finale: può usare il configuratore senza login e inviare una richiesta a SA-TEC.")

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
            "ricarico": "60"
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

    if profilo not in ["RIVENDITORE", "GROSSISTA"]:
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
                    "60"
                )
                st.success("Accesso cliente creato.")
                st.code(f"Utente: {nuovo_user}\nPassword: {nuova_pwd}")

    if profilo not in ["RIVENDITORE", "GROSSISTA"]:
        with st.sidebar.expander("Richiesta accesso commerciale"):
            st.caption("Compila il modulo. SA-TEC valuterà la richiesta e assegnerà il livello commerciale con relativo ricarico.")
            tipo_richiesta = st.selectbox("Tipo richiesta", ["RIVENDITORE", "GROSSISTA"], key="riv_tipo_richiesta")
            riv_azienda = st.text_input("Ragione sociale", key="riv_reg_azienda")
            riv_ref = st.text_input("Referente", key="riv_reg_ref")
            riv_tel = st.text_input("Telefono", key="riv_reg_tel")
            riv_email = st.text_input("Email", key="riv_reg_email")
            riv_zona = st.text_input("Zona di competenza", key="riv_reg_zona")
            riv_password = st.text_input("Password desiderata", type="password", key="riv_reg_pwd")

            if st.button("INVIA RICHIESTA COMMERCIALE"):
                if not riv_azienda or not riv_email or not riv_password:
                    st.error("Inserisci almeno ragione sociale, email e password.")
                else:
                    utenti_now = carica_tutti_utenti()
                    nuovo_user = genera_codice_progressivo(tipo_richiesta, utenti_now)

                    azienda_con_zona = riv_azienda
                    if riv_zona:
                        azienda_con_zona = f"{riv_azienda} - Zona: {riv_zona}"

                    # Backup CSV
                    salva_utente_csv(
                        nuovo_user,
                        riv_password,
                        tipo_richiesta,
                        riv_ref,
                        azienda_con_zona,
                        riv_tel,
                        riv_email,
                        "0"
                    )

                    ok_sb, err_sb = salva_utente_supabase(
                        nuovo_user,
                        riv_password,
                        tipo_richiesta,
                        azienda_con_zona,
                        riv_tel,
                        riv_email,
                        0
                    )

                    if ok_sb:
                        st.success("Richiesta commerciale inviata e salvata su Supabase.")
                    else:
                        st.warning(f"Richiesta salvata in CSV. Supabase non disponibile: {err_sb}")

                    st.code(f"Utente: {nuovo_user}\nPassword: {riv_password}\nProfilo richiesto: {tipo_richiesta}\nStato: in attesa ricarico SA-TEC")

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
    blu_scuro = "#073763"
    nero = "#111111"
    vetro_chiaro = "#eaf6ff"
    vetro_scuro = "#8fbbe8"
    vetro_fisso = "#f8fbff"
    alluminio = "#d9e2ec"
    giallo = "#fff3a3"
    grigio = "#f7faff"

    traversa_mm = int(lunghezza_traversa * 1000)
    anta_mm = int(luce_mm) if ante == "1 anta" else int(luce_mm / 2)

    if ante == "1 anta":
        titolo = "AUTOMAZIONE SCORREVOLE 1 ANTA"
        schema_ante = f"""
        <!-- pannello fisso sinistro chiaro -->
        <rect x="165" y="180" width="205" height="175" rx="4" fill="{vetro_fisso}" stroke="{nero}" stroke-width="3"/>
        <line x1="185" y1="198" x2="350" y2="337" stroke="#c7d9ed" stroke-width="2"/>

        <!-- anta mobile scura destra -->
        <rect x="370" y="180" width="205" height="175" rx="4" fill="{vetro_scuro}" stroke="{nero}" stroke-width="5"/>
        <line x1="392" y1="198" x2="553" y2="337" stroke="#ffffff" stroke-width="2" opacity="0.7"/>

        <line x1="370" y1="180" x2="370" y2="355" stroke="{nero}" stroke-width="6"/>
        <text x="472" y="375" text-anchor="middle" font-size="13" fill="{nero}" font-weight="900">ANTA MOBILE SCURA {anta_mm} mm</text>
        <text x="268" y="375" text-anchor="middle" font-size="13" fill="{nero}" font-weight="700">FISSO / PASSAGGIO</text>
        """
        legenda = "1 ANTA MOBILE EVIDENZIATA IN BLU SCURO"
    else:
        titolo = "AUTOMAZIONE SCORREVOLE 2 ANTE"
        schema_ante = f"""
        <!-- anta mobile sx scura -->
        <rect x="165" y="180" width="205" height="175" rx="4" fill="{vetro_scuro}" stroke="{nero}" stroke-width="5"/>
        <line x1="187" y1="198" x2="348" y2="337" stroke="#ffffff" stroke-width="2" opacity="0.7"/>

        <!-- anta mobile dx scura -->
        <rect x="370" y="180" width="205" height="175" rx="4" fill="{vetro_scuro}" stroke="{nero}" stroke-width="5"/>
        <line x1="392" y1="198" x2="553" y2="337" stroke="#ffffff" stroke-width="2" opacity="0.7"/>

        <!-- incontro centrale -->
        <rect x="358" y="180" width="12" height="175" fill="#ffffff" stroke="{nero}" stroke-width="3"/>
        <rect x="370" y="180" width="12" height="175" fill="#ffffff" stroke="{nero}" stroke-width="3"/>

        <text x="267" y="375" text-anchor="middle" font-size="13" fill="{nero}" font-weight="900">ANTA 1 SCURA {anta_mm} mm</text>
        <text x="472" y="375" text-anchor="middle" font-size="13" fill="{nero}" font-weight="900">ANTA 2 SCURA {anta_mm} mm</text>
        """
        legenda = "2 ANTE MOBILI EVIDENZIATE IN BLU SCURO"

    return f"""
    <div style="background:#ffffff;border:2px solid #b8d4f3;border-radius:14px;padding:16px;font-family:Arial;">
    <svg width="100%" height="520" viewBox="0 0 760 520">

        <!-- titolo -->
        <rect x="34" y="16" width="692" height="48" rx="12" fill="{blu}"/>
        <text x="380" y="47" text-anchor="middle" font-size="22" fill="#ffffff" font-weight="900">{titolo}</text>

        <!-- corpo disegno centrato -->
        <rect x="80" y="86" width="600" height="330" rx="14" fill="#ffffff" stroke="#d7e6f7" stroke-width="2"/>

        <!-- quota traversa -->
        <text x="380" y="112" text-anchor="middle" font-size="15" fill="{blu}" font-weight="900">TRAVERSA / AUTOMAZIONE {traversa_mm} mm</text>
        <line x1="130" y1="130" x2="630" y2="130" stroke="{blu}" stroke-width="3"/>
        <line x1="130" y1="120" x2="130" y2="140" stroke="{blu}" stroke-width="3"/>
        <line x1="630" y1="120" x2="630" y2="140" stroke="{blu}" stroke-width="3"/>

        <!-- traversa centrata -->
        <rect x="120" y="145" width="520" height="40" rx="5" fill="{alluminio}" stroke="{nero}" stroke-width="3"/>
        <rect x="138" y="155" width="484" height="8" fill="#ffffff" opacity="0.55"/>
        <rect x="330" y="158" width="100" height="18" rx="4" fill="{blu_scuro}"/>
        <text x="380" y="172" text-anchor="middle" font-size="11" fill="#ffffff" font-weight="900">GRUPPO MOTORE</text>

        <!-- telaio laterale -->
        <rect x="145" y="172" width="20" height="190" fill="{alluminio}" stroke="{nero}" stroke-width="2"/>
        <rect x="575" y="172" width="20" height="190" fill="{alluminio}" stroke="{nero}" stroke-width="2"/>
        <rect x="145" y="355" width="450" height="10" fill="{alluminio}" stroke="{nero}" stroke-width="2"/>

        <!-- serramento/ante -->
        {schema_ante}

        <!-- quota luce passaggio -->
        <line x1="175" y1="402" x2="565" y2="402" stroke="{blu}" stroke-width="3"/>
        <line x1="175" y1="392" x2="175" y2="412" stroke="{blu}" stroke-width="3"/>
        <line x1="565" y1="392" x2="565" y2="412" stroke="{blu}" stroke-width="3"/>
        <text x="370" y="429" text-anchor="middle" font-size="18" fill="{blu}" font-weight="900">LUCE PASSAGGIO {luce_mm} mm</text>

        <!-- quota altezza -->
        <line x1="665" y1="180" x2="665" y2="355" stroke="{blu}" stroke-width="3"/>
        <line x1="653" y1="180" x2="677" y2="180" stroke="{blu}" stroke-width="3"/>
        <line x1="653" y1="355" x2="677" y2="355" stroke="{blu}" stroke-width="3"/>
        <text x="700" y="270" text-anchor="middle" font-size="17" fill="{blu}" font-weight="900" transform="rotate(90 700,270)">H {altezza_mm} mm</text>

        <!-- legenda tecnica -->
        <rect x="35" y="448" width="690" height="52" rx="10" fill="{grigio}" stroke="{blu}" stroke-width="2"/>
        <text x="55" y="470" font-size="14" fill="{nero}" font-weight="900">LUCE:</text>
        <text x="108" y="470" font-size="14" fill="{blu}" font-weight="900">{luce_mm} mm</text>

        <text x="200" y="470" font-size="14" fill="{nero}" font-weight="900">H:</text>
        <text x="225" y="470" font-size="14" fill="{blu}" font-weight="900">{altezza_mm} mm</text>

        <text x="315" y="470" font-size="14" fill="{nero}" font-weight="900">TRAVERSA:</text>
        <text x="410" y="470" font-size="14" fill="{blu}" font-weight="900">{traversa_mm} mm</text>

        <text x="515" y="470" font-size="14" fill="{nero}" font-weight="900">ANTA:</text>
        <text x="568" y="470" font-size="14" fill="{blu}" font-weight="900">{anta_mm} mm</text>

        <rect x="55" y="480" width="130" height="13" fill="{vetro_scuro}" stroke="{nero}" stroke-width="1"/>
        <text x="195" y="492" font-size="12" fill="{nero}" font-weight="700">{legenda}</text>

    </svg>
    </div>
    """


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


/* V37 - allineamento riquadri scelta automazione */
.porta-card {
    height:285px!important;
    min-height:285px!important;
    display:flex!important;
    flex-direction:column!important;
    justify-content:space-between!important;
    align-items:center!important;
    box-sizing:border-box!important;
}

.porta-card-title {
    min-height:46px!important;
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
    text-align:center!important;
}

.porta-card-desc {
    min-height:54px!important;
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
    text-align:center!important;
    padding:0 6px!important;
}

.porta-card svg {
    height:120px!important;
    max-height:120px!important;
}

div[data-testid="stButton"] button[kind="secondary"] {
    height:54px!important;
    min-height:54px!important;
    margin-top:-8px!important;
}


/* V51.2 - card native immagini */
.pro-card-box {
    background:#ffffff;
    border:2px solid #bdd4ef;
    border-radius:18px;
    padding:18px;
    margin-bottom:12px;
    box-shadow:0 6px 18px rgba(6,73,155,0.12);
}
.pro-card-active {
    border:4px solid #06499b!important;
    background:#fff8c7!important;
}
.pro-badge-standard {
    display:inline-block;
    background:#06499b;
    color:#ffffff;
    font-weight:900;
    border-radius:8px;
    padding:7px 12px;
    margin:8px 0;
}
.pro-badge-ridondante {
    display:inline-block;
    background:#ff7900;
    color:#ffffff;
    font-weight:900;
    border-radius:8px;
    padding:7px 12px;
    margin:8px 0;
}
.pro-title {
    color:#06499b;
    font-size:26px;
    font-weight:900;
    margin:8px 0;
}
.pro-desc {
    color:#111111;
    font-size:15px;
    font-weight:700;
    line-height:1.45;
}
.summary-pro {
    background:#ffffff;
    border:3px solid #06499b;
    border-radius:18px;
    padding:18px;
    box-shadow:0 6px 18px rgba(6,73,155,0.15);
    margin-top:12px;
}
.summary-pro-title {
    background:#06499b;
    color:#ffffff;
    font-size:20px;
    font-weight:900;
    border-radius:10px;
    padding:10px 14px;
    text-align:center;
    margin-bottom:14px;
}
.summary-line {
    display:flex;
    justify-content:space-between;
    gap:10px;
    border-bottom:1px solid #d7e6f7;
    padding:8px 0;
    font-size:15px;
    color:#111;
}
.summary-line b { color:#06499b; }
.summary-total {
    background:#fff3a3;
    border:2px solid #06499b;
    border-radius:12px;
    padding:12px;
    text-align:center;
    margin-top:14px;
}
.summary-total .label {
    color:#111;
    font-weight:900;
    font-size:15px;
}
.summary-total .value {
    color:#06499b;
    font-weight:900;
    font-size:34px;
}


/* V52 - CARD ALLINEATE E SELEZIONE ACCESA */
.pro-card-box {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:18px!important;
    padding:18px!important;
    margin-bottom:12px!important;
    box-shadow:0 6px 18px rgba(6,73,155,0.12)!important;
    min-height:520px!important;
    display:flex!important;
    flex-direction:column!important;
    justify-content:flex-start!important;
}
.pro-card-active {
    border:4px solid #06499b!important;
    background:#fff8c7!important;
}
div[data-testid="stImage"] img {
    max-height:190px!important;
    object-fit:contain!important;
}
.pro-badge-standard {
    display:inline-block;
    background:#06499b;
    color:#ffffff!important;
    font-weight:900;
    border-radius:8px;
    padding:7px 12px;
    margin:12px 0 8px 0;
}
.pro-badge-ridondante {
    display:inline-block;
    background:#ff7900;
    color:#ffffff!important;
    font-weight:900;
    border-radius:8px;
    padding:7px 12px;
    margin:12px 0 8px 0;
}
.pro-title {
    color:#06499b!important;
    font-size:26px;
    font-weight:900;
    margin:8px 0;
    min-height:64px;
}
.pro-desc {
    color:#111111!important;
    font-size:15px;
    font-weight:700;
    line-height:1.45;
    min-height:145px;
}
.pro-points {
    margin-top:8px;
    color:#111111!important;
    font-size:15px;
    font-weight:900;
    line-height:1.5;
}
.sel-box {
    border-radius:12px;
    padding:12px;
    text-align:center;
    font-weight:900;
    border:3px solid #06499b;
    margin-bottom:8px;
}
.sel-on-standard {
    background:#27ae60;
    color:white!important;
    border-color:#1e8449;
}
.sel-on-ridondante {
    background:#ff7900;
    color:white!important;
    border-color:#c75f00;
}
.sel-off {
    background:#eef6ff;
    color:#06499b!important;
}


/* V53 - SCELTA AUTOMAZIONE PULITA */
.pro-card-box {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:18px!important;
    padding:16px!important;
    margin-bottom:10px!important;
    box-shadow:0 6px 18px rgba(6,73,155,0.10)!important;
    min-height:430px!important;
}
.pro-card-active {
    border:4px solid #06499b!important;
    background:#fff8c7!important;
}
div[data-testid="stImage"] img {
    max-height:175px!important;
    object-fit:contain!important;
}
.pro-badge-standard {
    display:inline-block;
    background:#06499b;
    color:#ffffff!important;
    font-weight:900;
    border-radius:8px;
    padding:7px 12px;
    margin:10px 0 6px 0;
}
.pro-badge-ridondante {
    display:inline-block;
    background:#ff7900;
    color:#ffffff!important;
    font-weight:900;
    border-radius:8px;
    padding:7px 12px;
    margin:10px 0 6px 0;
}
.pro-title {
    color:#06499b!important;
    font-size:24px;
    font-weight:900;
    margin:6px 0;
}
.pro-desc {
    color:#111111!important;
    font-size:15px;
    font-weight:800;
    line-height:1.55;
    min-height:120px;
}
.choice-grid-title {
    color:#06499b;
    font-size:18px;
    font-weight:900;
    margin:10px 0 8px 0;
}
.sel-box {
    border-radius:12px;
    padding:14px 8px;
    text-align:center;
    font-weight:900;
    border:3px solid #06499b;
    margin-bottom:4px;
    font-size:16px;
    min-height:54px;
}
.sel-on-standard {
    background:#27ae60;
    color:white!important;
    border-color:#1e8449;
}
.sel-on-ridondante {
    background:#ff7900;
    color:white!important;
    border-color:#c75f00;
}
.sel-off {
    background:#eef6ff;
    color:#06499b!important;
}


/* V56 - ELIMINA RIQUADRI VUOTI */
div[role="radiogroup"] {
    display:none!important;
}
.choice-card-v56 {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:16px!important;
    padding:12px!important;
    margin-bottom:10px!important;
    box-shadow:0 4px 12px rgba(6,73,155,0.08)!important;
}
.choice-card-v56-active {
    background:#fff8c7!important;
    border:4px solid #06499b!important;
}
.choice-badge-standard-v56 {
    display:inline-block;
    background:#06499b;
    color:white!important;
    border-radius:8px;
    padding:7px 12px;
    font-weight:900;
    margin-top:8px;
}
.choice-badge-er-v56 {
    display:inline-block;
    background:#ff7900;
    color:white!important;
    border-radius:8px;
    padding:7px 12px;
    font-weight:900;
    margin-top:8px;
}
.choice-title-v56 {
    color:#06499b!important;
    font-size:23px!important;
    font-weight:900!important;
    margin:8px 0!important;
}
.choice-desc-v56 {
    color:#111!important;
    font-size:15px!important;
    font-weight:800!important;
    line-height:1.48!important;
}
.sel-box-v56 {
    border-radius:12px!important;
    padding:13px 8px!important;
    text-align:center!important;
    font-weight:900!important;
    border:3px solid #06499b!important;
    margin-bottom:4px!important;
    font-size:16px!important;
}
.sel-on-standard-v56 {
    background:#27ae60!important;
    color:white!important;
    border-color:#1e8449!important;
}
.sel-on-ridondante-v56 {
    background:#ff7900!important;
    color:white!important;
    border-color:#c75f00!important;
}
.sel-off-v56 {
    background:#eef6ff!important;
    color:#06499b!important;
}
div[data-testid="stImage"] img {
    max-height:145px!important;
    object-fit:contain!important;
}


/* V57 - CARD IN UN SOLO HTML, ZERO RIQUADRI VUOTI */
.choice-card-v57 {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:16px!important;
    padding:12px!important;
    margin-bottom:10px!important;
    box-shadow:0 4px 12px rgba(6,73,155,0.08)!important;
}
.choice-card-v57-active {
    background:#fff8c7!important;
    border:4px solid #06499b!important;
}
.choice-img-v57 {
    width:100%!important;
    height:145px!important;
    object-fit:contain!important;
    display:block!important;
    margin:0 auto 8px auto!important;
}
.choice-badge-standard-v57 {
    display:inline-block;
    background:#06499b;
    color:white!important;
    border-radius:8px;
    padding:7px 12px;
    font-weight:900;
    margin-top:8px;
}
.choice-badge-er-v57 {
    display:inline-block;
    background:#ff7900;
    color:white!important;
    border-radius:8px;
    padding:7px 12px;
    font-weight:900;
    margin-top:8px;
}
.choice-title-v57 {
    color:#06499b!important;
    font-size:23px!important;
    font-weight:900!important;
    margin:8px 0!important;
}
.choice-desc-v57 {
    color:#111!important;
    font-size:15px!important;
    font-weight:800!important;
    line-height:1.48!important;
}
.sel-box-v57 {
    border-radius:12px!important;
    padding:13px 8px!important;
    text-align:center!important;
    font-weight:900!important;
    border:3px solid #06499b!important;
    margin-bottom:4px!important;
    font-size:16px!important;
}
.sel-on-standard-v57 {
    background:#27ae60!important;
    color:white!important;
    border-color:#1e8449!important;
}
.sel-on-ridondante-v57 {
    background:#ff7900!important;
    color:white!important;
    border-color:#c75f00!important;
}
.sel-off-v57 {
    background:#eef6ff!important;
    color:#06499b!important;
}


/* V58 - ADMIN PREVENTIVI */
.admin-preventivo-row {
    background:#ffffff;
    border:2px solid #bdd4ef;
    border-radius:14px;
    padding:12px;
    margin-bottom:10px;
}


/* V59 - CRM ADMIN ALLINEATO */
.admin-preventivo-row {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:14px!important;
    padding:14px!important;
    margin:16px 0 8px 0!important;
    box-shadow:0 4px 12px rgba(6,73,155,0.08)!important;
}
.admin-preventivo-code {
    color:#06499b!important;
    font-size:20px!important;
    font-weight:900!important;
    margin-bottom:6px!important;
}
.admin-preventivo-line {
    color:#111!important;
    font-size:15px!important;
    font-weight:700!important;
    line-height:1.45!important;
}
.admin-action-spacer {
    height:31px!important;
}
.admin-delete-note {
    color:#eb5757!important;
    font-size:13px!important;
    font-weight:900!important;
    margin-top:4px!important;
}


/* V63 - AREA RIVENDITORI PULITA */
.extra-ricarico-box {
    background:#fff8c7;
    border:3px solid #06499b;
    border-radius:14px;
    padding:14px;
    margin:12px 0;
}
.extra-ricarico-title {
    color:#06499b;
    font-size:18px;
    font-weight:900;
    margin-bottom:6px;
}
.extra-ricarico-note {
    color:#111;
    font-size:14px;
    font-weight:800;
    line-height:1.45;
}


/* V62 - SIDEBAR ACCESSO PIU LEGGIBILE */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}
section[data-testid="stSidebar"] input {
    background:#ffffff!important;
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    border:2px solid #2f80ed!important;
    border-radius:8px!important;
    min-height:44px!important;
}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div {
    color:#111111!important;
}
section[data-testid="stSidebar"] button {
    min-height:46px!important;
    font-weight:900!important;
}


/* V64 - SELECTBOX SIDEBAR LEGGIBILE */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background:#ffffff!important;
    color:#111111!important;
    border:2px solid #2f80ed!important;
    border-radius:8px!important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    font-weight:900!important;
}


/* V67 - GRAFICA INCREMENTO PREZZO VENDITA */
.incremento-box-v67 {
    background:#ffffff;
    border:2px solid #2f80ed;
    border-radius:14px;
    padding:12px;
    margin:10px 0 8px 0;
}
.incremento-title-v67 {
    color:#06499b!important;
    font-size:17px!important;
    font-weight:900!important;
}
.incremento-note-v67 {
    color:#111111!important;
    font-size:13px!important;
    font-weight:800!important;
    margin-top:4px!important;
}
.incremento-risultato-v67 {
    background:#27ae60;
    color:#ffffff!important;
    border-radius:12px;
    padding:10px 12px;
    margin-top:8px;
    font-size:15px;
    font-weight:900;
    text-align:center;
}
section[data-testid="stSidebar"] div[role="radiogroup"] {
    display:flex!important;
    gap:7px!important;
    flex-wrap:wrap!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background:#ffffff!important;
    border:2px solid #2f80ed!important;
    border-radius:12px!important;
    padding:8px 10px!important;
    min-width:72px!important;
    text-align:center!important;
    color:#06499b!important;
    font-weight:900!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    color:#06499b!important;
    -webkit-text-fill-color:#06499b!important;
    font-weight:900!important;
    font-size:16px!important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {
    background:#27ae60!important;
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


# V63 - Incremento prezzo vendita nascosto per rivenditore/grossista
ricarico_base_assegnato = float(ricarico_effettivo or 0)
ricarico_cliente_finale = 60.0

if profilo in ["RIVENDITORE", "GROSSISTA"]:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Prezzo vendita")
    st.sidebar.caption("Seleziona l’incremento da applicare al prezzo di vendita.")

    extra_massimo = max(0.0, ricarico_cliente_finale - ricarico_base_assegnato)

    step_extra = [0.0]
    valore = 10.0
    while valore <= extra_massimo + 0.001:
        step_extra.append(float(valore))
        valore += 10.0

    labels_extra = [f"+{x:.0f}%" for x in step_extra]

    st.sidebar.markdown(
        """
        <div class="incremento-box-v67">
            <div class="incremento-title-v67">Incremento prezzo vendita</div>
            <div class="incremento-note-v67">Scegli quanto aumentare il prezzo finale.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    scelta_extra_label = st.sidebar.radio(
        "Incremento prezzo vendita",
        labels_extra,
        index=0,
        key="ricarico_extra_utente_step10",
        horizontal=True,
        label_visibility="collapsed"
    )

    ricarico_extra_utente = float(scelta_extra_label.replace("+", "").replace("%", ""))

    ricarico_effettivo = min(
        ricarico_base_assegnato + ricarico_extra_utente,
        ricarico_cliente_finale
    )

    st.sidebar.markdown(
        f"""
        <div class="incremento-risultato-v67">
            Incremento applicato: <b>{ricarico_extra_utente:.0f}%</b>
        </div>
        """,
        unsafe_allow_html=True
    )
elif profilo == "CLIENTE":
    ricarico_extra_utente = 0.0
else:
    ricarico_extra_utente = 0.0

# V68_FORCE_RICARICO_ATTIVO
RICARICO_ATTIVO = float(ricarico_effettivo or 0)

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

if supabase_attivo():
    st.sidebar.success("Supabase collegato")
else:
    st.sidebar.warning("Supabase non collegato - uso CSV")

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

                st.markdown('<h3 style="color:#06499b;">CRM Commerciale</h3>', unsafe_allow_html=True)
                render_dashboard_crm(preventivi)

                stats_stati = statistiche_stati_preventivi(preventivi)
                render_stati_preventivi(stats_stati)

                st.markdown("---")
                st.markdown("## Gestione preventivi rivenditori / clienti")

                col_filtro1, col_filtro2 = st.columns([2, 1])
                with col_filtro1:
                    cerca_preventivo_dash = st.text_input(
                        "Cerca per codice, cliente, rivenditore, email o configurazione",
                        key="cerca_preventivo_dash"
                    )
                with col_filtro2:
                    stato_filtro_dash = st.selectbox(
                        "Filtra per stato",
                        ["Tutti"] + STATI_PREVENTIVO,
                        key="stato_filtro_dash"
                    )

                preventivi_visualizzati = filtra_preventivi_dashboard(preventivi, cerca_preventivo_dash, stato_filtro_dash)

                totale = 0.0
                utile_totale = 0.0
                costo_totale_dashboard = 0.0
                for p in preventivi_visualizzati:
                    try:
                        totale += float(str(p.get("imponibile", p.get("totale_iva", 0))).replace(",", ".") or 0)
                    except:
                        pass
                    try:
                        utile_totale += float(str(p.get("utile_lordo", 0)).replace(",", ".") or 0)
                    except:
                        pass
                    try:
                        costo_totale_dashboard += float(str(p.get("costo_satec", 0)).replace(",", ".") or 0)
                    except:
                        pass

                margine_dash = (utile_totale / costo_totale_dashboard * 100) if costo_totale_dashboard > 0 else 0

                st.write(f"Preventivi visualizzati: **{len(preventivi_visualizzati)}**")
                st.write(f"Valore visualizzato: **{euro(totale)}**")
                st.write(f"Utile lordo visualizzato: **{euro(utile_totale)}**")
                st.write(f"Margine medio su costo: **{margine_dash:.1f}%**")

                if not preventivi_visualizzati:
                    st.info("Nessun preventivo trovato con questi filtri.")

                for idx, p in enumerate(preventivi_visualizzati):
                    codice = str(p.get("codice_preventivo", "") or f"RIGA-{idx}")
                    cliente = p.get("cliente_nome", "") or p.get("cliente_azienda", "") or "Cliente non indicato"
                    utente_prev = p.get("utente", "") or "Utente non indicato"
                    config_prev = p.get("configurazione", "")
                    stato_prev = p.get("stato", "Bozza") or "Bozza"

                    try:
                        totale_prev = euro(float(str(p.get("totale_iva", p.get("totale", "0"))).replace(",", ".") or 0))
                    except:
                        totale_prev = str(p.get("totale_iva", p.get("totale", "")))

                    st.markdown(f"""
                    <div class="admin-preventivo-row">
                        <div class="admin-preventivo-code">{codice}</div>
                        <div class="admin-preventivo-line"><b>Rivenditore/Utente:</b> {utente_prev}</div>
                        <div class="admin-preventivo-line"><b>Cliente:</b> {cliente}</div>
                        <div class="admin-preventivo-line"><b>Configurazione:</b> {config_prev}</div>
                        <div class="admin-preventivo-line"><b>Totale:</b> {totale_prev} &nbsp; | &nbsp; <b>Stato:</b> {stato_prev}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_apri, c_stato, c_elimina = st.columns([1, 1, 1])

                    with c_apri:
                        st.markdown('<div class="admin-action-spacer"></div>', unsafe_allow_html=True)
                        if st.button("APRI DETTAGLIO", key=f"apri_dettaglio_{codice}_{idx}", use_container_width=True):
                            st.session_state.preventivo_dettaglio_admin = codice

                    with c_stato:
                        nuovo_stato = st.selectbox(
                            "Cambia stato",
                            STATI_PREVENTIVO,
                            index=STATI_PREVENTIVO.index(stato_prev) if stato_prev in STATI_PREVENTIVO else 0,
                            key=f"stato_select_{codice}_{idx}"
                        )
                        if st.button("AGGIORNA STATO", key=f"aggiorna_stato_{codice}_{idx}", use_container_width=True):
                            if aggiorna_stato_preventivo_admin(codice, nuovo_stato):
                                st.success(f"Stato aggiornato: {codice} → {nuovo_stato}")
                                st.rerun()
                            else:
                                st.error("Stato non aggiornato.")

                    with c_elimina:
                        conferma = st.checkbox(
                            "Conferma eliminazione",
                            key=f"conferma_elimina_{codice}_{idx}"
                        )
                        if st.button("ELIMINA", key=f"elimina_prev_{codice}_{idx}", use_container_width=True):
                            if not conferma:
                                st.warning("Spunta prima 'Conferma eliminazione'.")
                            else:
                                ok_del, msg_del = elimina_preventivo_admin(codice)
                                if ok_del:
                                    st.success(msg_del)
                                    if st.session_state.get("preventivo_dettaglio_admin") == codice:
                                        st.session_state.preventivo_dettaglio_admin = ""
                                    st.rerun()
                                else:
                                    st.error(msg_del)
                        st.markdown(f'<div class="admin-delete-note">Elimina definitivamente {codice}</div>', unsafe_allow_html=True)

                    if st.session_state.get("preventivo_dettaglio_admin") == codice:
                        render_dettaglio_preventivo_admin(p)

                st.markdown("<hr>", unsafe_allow_html=True)

                if Path(PREVENTIVI_CSV).exists():
                    with open(PREVENTIVI_CSV, "rb") as f:
                        st.download_button("Scarica CSV preventivi", data=f, file_name="preventivi_satec.csv", mime="text/csv")
                else:
                    st.caption("Backup CSV preventivi non ancora creato.")

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
                if Path(UTENTI_CSV).exists():
                    with open(UTENTI_CSV, "rb") as f:
                        st.download_button("Scarica CSV utenti", data=f, file_name="utenti_satec.csv", mime="text/csv")
                else:
                    st.caption("Backup CSV utenti non ancora creato.")



        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<h3 style="color:#06499b;">Gestione Rivenditori / Grossisti</h3>', unsafe_allow_html=True)

        righe_riv = utenti_rivenditori_grossisti()
        if not righe_riv:
            st.info("Nessun rivenditore o grossista presente.")
        else:
            st.markdown(tabella_html_sicura(righe_riv), unsafe_allow_html=True)

            codici_riv = [r["utente"] for r in righe_riv]
            col_riv1, col_riv2, col_riv3 = st.columns([2, 1, 1])
            with col_riv1:
                utente_riv_mod = st.selectbox("Utente rivenditore/grossista", codici_riv, key="utente_riv_mod")
            with col_riv2:
                nuovo_ricarico_riv = st.number_input("Nuovo ricarico %", min_value=0.0, max_value=200.0, value=30.0, step=1.0, key="nuovo_ricarico_riv")
            with col_riv3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("AGGIORNA RICARICO"):
                    ok_riv, err_riv = aggiorna_ricarico_utente_supabase(utente_riv_mod, nuovo_ricarico_riv)
                    if ok_riv:
                        st.success(f"Ricarico aggiornato per {utente_riv_mod}: {nuovo_ricarico_riv:.0f}%")
                    else:
                        st.error(f"Ricarico non aggiornato: {err_riv}")


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
    st.markdown('<div class="card"><div class="title-bar">1&nbsp;&nbsp; SCEGLI L\'AUTOMAZIONE</div>', unsafe_allow_html=True)

    pw_active = st.session_state.scelta in ["STANDARD 1 ANTA", "STANDARD 2 ANTE"]
    er_active = st.session_state.scelta in ["RIDONDANTE 1 ANTA", "RIDONDANTE 2 ANTE"]

    pw100_img = img_to_base64(["pw100.png", "PW100.png", "pw100(1) (3).png"])
    er140_img = img_to_base64(["er140.png", "ER140.png", "er140(1).png"])

    pw_img_html = f'<img class="choice-img-v57" src="data:image/png;base64,{pw100_img}">' if pw100_img else ""
    er_img_html = f'<img class="choice-img-v57" src="data:image/png;base64,{er140_img}">' if er140_img else ""

    pcol1, pcol2 = st.columns(2)

    with pcol1:
        classe_pw = "choice-card-v57 choice-card-v57-active" if pw_active else "choice-card-v57"
        st.markdown(f"""
        <div class="{classe_pw}">
            {pw_img_html}
            <div class="choice-badge-standard-v57">STANDARD</div>
            <div class="choice-title-v57">Sesamo PowerCore PW100</div>
            <div class="choice-desc-v57">
                ✓ Automazione standard<br>
                ✓ Conforme EN16005<br>
                ✓ Made in Italy<br>
                ✓ Garanzia 12 mesi<br>
                ✓ Assistenza tecnica SA-TEC
            </div>
        </div>
        """, unsafe_allow_html=True)

    with pcol2:
        classe_er = "choice-card-v57 choice-card-v57-active" if er_active else "choice-card-v57"
        st.markdown(f"""
        <div class="{classe_er}">
            {er_img_html}
            <div class="choice-badge-er-v57">RIDONDANTE / VIE DI FUGA</div>
            <div class="choice-title-v57">Sesamo ER140 Ridondante</div>
            <div class="choice-desc-v57">
                ✓ Sistema ridondante<br>
                ✓ Per uscite di emergenza<br>
                ✓ Conforme EN16005<br>
                ✓ Garanzia 12 mesi<br>
                ✓ Assistenza tecnica SA-TEC
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="color:#06499b;font-size:18px;font-weight:900;margin:12px 0 8px 0;">Seleziona configurazione</div>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        classe = "sel-box-v57 sel-on-standard-v57" if st.session_state.scelta == "STANDARD 1 ANTA" else "sel-box-v57 sel-off-v57"
        testo = "✓ PW100 1 ANTA" if st.session_state.scelta == "STANDARD 1 ANTA" else "PW100 1 ANTA"
        st.markdown(f'<div class="{classe}">{testo}</div>', unsafe_allow_html=True)
        if st.button("PW100 1 ANTA", key="btn_pw100_1", use_container_width=True):
            st.session_state.scelta = "STANDARD 1 ANTA"
            st.rerun()

    with s2:
        classe = "sel-box-v57 sel-on-standard-v57" if st.session_state.scelta == "STANDARD 2 ANTE" else "sel-box-v57 sel-off-v57"
        testo = "✓ PW100 2 ANTE" if st.session_state.scelta == "STANDARD 2 ANTE" else "PW100 2 ANTE"
        st.markdown(f'<div class="{classe}">{testo}</div>', unsafe_allow_html=True)
        if st.button("PW100 2 ANTE", key="btn_pw100_2", use_container_width=True):
            st.session_state.scelta = "STANDARD 2 ANTE"
            st.rerun()

    with s3:
        classe = "sel-box-v57 sel-on-ridondante-v57" if st.session_state.scelta == "RIDONDANTE 1 ANTA" else "sel-box-v57 sel-off-v57"
        testo = "✓ ER140 1 ANTA" if st.session_state.scelta == "RIDONDANTE 1 ANTA" else "ER140 1 ANTA"
        st.markdown(f'<div class="{classe}">{testo}</div>', unsafe_allow_html=True)
        if st.button("ER140 1 ANTA", key="btn_er140_1", use_container_width=True):
            st.session_state.scelta = "RIDONDANTE 1 ANTA"
            st.rerun()

    with s4:
        classe = "sel-box-v57 sel-on-ridondante-v57" if st.session_state.scelta == "RIDONDANTE 2 ANTE" else "sel-box-v57 sel-off-v57"
        testo = "✓ ER140 2 ANTE" if st.session_state.scelta == "RIDONDANTE 2 ANTE" else "ER140 2 ANTE"
        st.markdown(f'<div class="{classe}">{testo}</div>', unsafe_allow_html=True)
        if st.button("ER140 2 ANTE", key="btn_er140_2", use_container_width=True):
            st.session_state.scelta = "RIDONDANTE 2 ANTE"
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

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="title-bar">2&nbsp;&nbsp; MISURE PORTA</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)

    with m1:
        luce_mm = st.number_input("LUCE PASSAGGIO IN MM", min_value=800, max_value=5000, value=1600, step=50)
    with m2:
        altezza_mm = st.number_input("ALTEZZA PASSAGGIO IN MM", min_value=1800, max_value=3000, value=2200, step=50)

    lunghezza_traversa = calcola_traversa(luce_mm, ante)
    components.html(disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa), height=555)

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

titolo_dati_cliente = "5&nbsp;&nbsp; DATI CLIENTE E RICHIESTA"
if profilo == "CLIENTE":
    titolo_dati_cliente = "5&nbsp;&nbsp; INVIA RICHIESTA A SA-TEC"
st.markdown(f'<div class="card"><div class="title-bar">{titolo_dati_cliente}</div>', unsafe_allow_html=True)

if profilo == "CLIENTE":
    st.info("Compila i tuoi dati e invia la richiesta. SA-TEC riceverà il preventivo e ti ricontatterà.")

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

testo_bottone_salva = "INVIA RICHIESTA A SA-TEC" if profilo == "CLIENTE" else "SALVA PREVENTIVO / RICHIESTA"
if st.button(testo_bottone_salva):
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
        "stato": "Richiesta web" if profilo == "CLIENTE" else "Bozza"
    }
    salva_preventivo(dati)
    salva_cliente_csv(cliente_nome, cliente_azienda, cliente_telefono, cliente_email, codice_preventivo, imponibile, utente_codice, profilo)

    cliente_id_supabase = salva_cliente_supabase(cliente_nome, cliente_azienda, cliente_telefono, cliente_email, utente_codice, profilo)
    salvato_cloud = salva_preventivo_supabase(dati, cliente_id_supabase, utente_codice)

    st.session_state.ultimo_codice_preventivo = codice_preventivo

    if profilo == "CLIENTE":
        ok_mail_satec, errore_mail_satec = invia_notifica_richiesta_satec(
            codice_preventivo,
            cliente_nome,
            cliente_azienda,
            cliente_telefono,
            cliente_email,
            scelta,
            luce_mm,
            altezza_mm,
            totale_iva
        )

        if salvato_cloud:
            st.success(f"Richiesta {codice_preventivo} inviata e salvata correttamente. SA-TEC ti ricontatterà.")
        else:
            st.warning(f"Richiesta {codice_preventivo} salvata in backup. SA-TEC ti ricontatterà.")

        if ok_mail_satec:
            st.info("Notifica inviata a SA-TEC.")
        else:
            st.caption("Notifica email non inviata, ma la richiesta è stata salvata.")
    else:
        if salvato_cloud:
            st.success(f"Preventivo {codice_preventivo} salvato correttamente su Supabase e backup CSV.")
        else:
            st.warning(f"Preventivo {codice_preventivo} salvato in CSV. Supabase non disponibile o bloccato da policy.")

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


# =========================
# ORDINE FORNITORE / DISTINTA MATERIALI
# =========================

def codice_ordine_da_preventivo(codice_preventivo):
    if not codice_preventivo or codice_preventivo == "DA SALVARE":
        return "ORDINE-DA-SALVARE"
    return codice_preventivo.replace("SAT-", "ORD-")

def crea_html_ordine_fornitore(codice_preventivo, articoli, scelta, luce_mm, altezza_mm, lunghezza_traversa, cliente_nome, cliente_azienda):
    codice_ordine = codice_ordine_da_preventivo(codice_preventivo)

    righe = ""
    totale_costo = 0.0

    for a in articoli:
        totale_costo += float(a.get("costo_totale_satec", 0) or 0)
        righe += f"""
        <tr>
            <td>{a.get('codice','')}</td>
            <td>{a.get('descrizione','')}</td>
            <td style="text-align:center;">{round(float(a.get('quantita',0) or 0), 2)}</td>
            <td>{a.get('descrizione_lunga','')}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Ordine Fornitore {codice_ordine}</title>
    <style>
    body {{font-family:Arial,sans-serif;margin:30px;color:#111;}}
    .header {{display:flex;justify-content:space-between;border-bottom:5px solid #06499b;padding-bottom:18px;margin-bottom:22px;}}
    h1 {{color:#06499b;margin:0;font-size:30px;}}
    h2 {{color:#06499b;margin-top:20px;}}
    .company {{text-align:right;font-size:13px;line-height:1.5;}}
    .box {{border:2px solid #d7e6f7;border-left:8px solid #06499b;border-radius:12px;padding:16px;margin-bottom:18px;background:#f8fbff;}}
    table {{width:100%;border-collapse:collapse;margin-top:14px;font-size:13px;}}
    th {{background:#06499b;color:#fff;text-align:left;padding:10px;}}
    td {{border:1px solid #d7e6f7;padding:9px;vertical-align:top;}}
    .note {{margin-top:22px;border:2px solid #06499b;border-radius:12px;padding:16px;background:#fff3a3;line-height:1.6;}}
    .print-button {{background:#06499b;color:white;padding:14px 22px;border:none;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer;margin-bottom:18px;}}
    @media print {{.print-button {{display:none;}} body {{margin:18px;}}}}
    </style>
    </head>
    <body>
    <button class="print-button" onclick="window.print()">STAMPA / SALVA PDF ORDINE</button>

    <div class="header">
        <div>
            <h1>ORDINE FORNITORE</h1>
            <h2>{codice_ordine}</h2>
        </div>
        <div class="company">
            <b>{AZIENDA}</b><br>
            {SEDE}<br>
            {PIVA}<br>
            Tel. {TELEFONO}<br>
            Email: {EMAIL}<br>
            PEC: {PEC}
        </div>
    </div>

    <div class="box">
        <b>Preventivo collegato:</b> {codice_preventivo}<br>
        <b>Data ordine:</b> {date.today().strftime("%d/%m/%Y")}<br>
        <b>Cliente finale:</b> {cliente_nome} - {cliente_azienda}<br>
        <b>Configurazione:</b> {scelta}<br>
        <b>Luce passaggio:</b> {luce_mm} mm<br>
        <b>Altezza passaggio:</b> {altezza_mm} mm<br>
        <b>Misura traversa:</b> {lunghezza_traversa:.2f} m
    </div>

    <h2>Distinta materiali da ordinare</h2>
    <table>
        <thead>
            <tr>
                <th>Codice</th>
                <th>Descrizione</th>
                <th>Q.tà</th>
                <th>Note tecniche</th>
            </tr>
        </thead>
        <tbody>{righe}</tbody>
    </table>

    <div class="note">
        <b>Note ordine</b><br>
        Verificare disponibilità materiale, tempi di consegna e conferma prezzi prima dell'evasione ordine.<br>
        Le misure di taglio profili, coperchi, guide e guarnizioni sono calcolate automaticamente dal configuratore.
    </div>

    <div style="margin-top:25px;">
        <table>
            <tr>
                <td style="height:70px;text-align:center;"><b>Preparato da SA-TEC</b><br><br>_____________________________</td>
                <td style="height:70px;text-align:center;"><b>Conferma fornitore</b><br><br>_____________________________</td>
            </tr>
        </table>
    </div>
    </body>
    </html>
    """
    return html


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



if profilo in ["SA-TEC", "RIVENDITORE", "GROSSISTA"]:
    # =========================
    # MANUALI TECNICI SESAMO
    # =========================

    st.markdown('<div class="card"><div class="title-bar">MANUALI TECNICI SESAMO</div>', unsafe_allow_html=True)

    mcol1, mcol2 = st.columns(2)

    with mcol1:
        manuale_pw100 = trova_file_manuale(
            [
                "PW100 MANUALE ISTALLAZIONE.pdf",
                "PW100 MANUALE INSTALLAZIONE.pdf",
                "manuale_sesamo_pw100.pdf",
                "Manuale_Sesamo_PowerCore_PW100.pdf",
            ],
            ["pw100"]
        )

        st.markdown("""
        <div class="option-box">
            <div class="option-title">Manuale Sesamo PowerCore PW100</div>
            <div class="option-note">
            Manuale tecnico dell'automazione lineare Sesamo PowerCore PW100.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if manuale_pw100:
            st.success(f"Manuale trovato: {manuale_pw100.name}")
            with open(manuale_pw100, "rb") as f:
                st.download_button(
                    "SCARICA MANUALE PW100",
                    data=f,
                    file_name="Manuale_Sesamo_PowerCore_PW100.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.error("Manuale PW100 non trovato. Il file deve essere PDF e contenere PW100 nel nome.")

    with mcol2:
        manuale_er140 = trova_file_manuale(
            [
                "MANUALE ER 140 ISTALLAZIONE.pdf.pdf",
                "MANUALE ER 140 ISTALLAZIONE.pdf",
                "ER140 ISTALLAZIONE.pdf",
                "ER 140 ISTALLAZIONE.pdf",
                "manuale_sesamo_er140.pdf",
                "Manuale_Sesamo_ER140_Ridondante.pdf",
            ],
            ["140"]
        )

        st.markdown("""
        <div class="option-box">
            <div class="option-title">Manuale Sesamo ER140 Ridondante</div>
            <div class="option-note">
            Manuale tecnico dell'automazione ridondante Sesamo ER140 per vie di fuga.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if manuale_er140:
            st.success(f"Manuale trovato: {manuale_er140.name}")
            with open(manuale_er140, "rb") as f:
                st.download_button(
                    "SCARICA MANUALE ER140",
                    data=f,
                    file_name="Manuale_Sesamo_ER140_Ridondante.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.error("Manuale ER140 non trovato. Il file deve essere PDF e contenere 140 nel nome.")

    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Versione V68 - CRM dettaglio preventivo completo")

st.markdown(f"""
<div class="footer">
<div>📍 {AZIENDA}<br>{SEDE}</div>
<div>☎ {TELEFONO}</div>
<div>✉ {EMAIL}</div>
</div>
""", unsafe_allow_html=True)
