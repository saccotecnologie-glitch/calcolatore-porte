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
    initial_sidebar_state="expanded"
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


def elimina_utente_supabase(username):
    sb = supabase_client()
    if sb is None:
        return False, "Supabase non collegato"

    try:
        username = str(username or "").strip().upper()
        if username == "ADMIN":
            return False, "Non puoi eliminare ADMIN"

        sb.table("utenti").delete().eq("username", username).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


def elimina_utente_csv(username):
    path = Path(UTENTI_CSV)
    if not path.exists():
        return False, "CSV utenti non presente"

    try:
        username = str(username or "").strip().upper()
        if username == "ADMIN":
            return False, "Non puoi eliminare ADMIN"

        with open(path, "r", encoding="utf-8") as f:
            righe = list(csv.DictReader(f))

        if not righe:
            return False, "CSV utenti vuoto"

        fieldnames = list(righe[0].keys())
        nuove = [
            r for r in righe
            if str(r.get("utente", "")).strip().upper() != username
        ]

        if len(nuove) == len(righe):
            return False, "Utente non trovato nel CSV"

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(nuove)

        return True, ""
    except Exception as e:
        return False, str(e)


def elimina_utente_admin(username):
    username = str(username or "").strip().upper()

    if username == "ADMIN":
        return False, "Non puoi eliminare l'utente ADMIN"

    ok_sb, err_sb = elimina_utente_supabase(username)
    ok_csv, err_csv = elimina_utente_csv(username)

    if ok_sb or ok_csv:
        return True, f"Utente {username} eliminato. Lo storico preventivi resta nel CRM."

    return False, f"Supabase: {err_sb} | CSV: {err_csv}"



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

    html = """
    <html>
    <head>
    <meta charset="utf-8">
    <title>Dettaglio preventivo __CODICE__</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; color:#111; }
        .head { background:#06499b; color:white; padding:18px; border-radius:12px; }
        h1 { margin:0; }
        table { width:100%; border-collapse:collapse; margin-top:20px; }
        th { width:260px; background:#eef6ff; color:#06499b; text-align:left; }
        th, td { border:1px solid #bdd4ef; padding:10px; }
        .footer { margin-top:25px; font-size:13px; color:#555; }
    
/* V73 - CRM ADMIN PULITO */
.admin-preventivo-row {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:18px!important;
    padding:18px!important;
    margin:18px 0 10px 0!important;
    box-shadow:0 6px 18px rgba(6,73,155,0.10)!important;
}
.admin-preventivo-code {
    color:#06499b!important;
    font-size:22px!important;
    font-weight:900!important;
    margin-bottom:8px!important;
}
.admin-preventivo-line {
    color:#111!important;
    font-size:15px!important;
    font-weight:800!important;
    line-height:1.55!important;
}
.admin-actions-card-v73 {
    background:#f7fbff;
    border:2px solid #bdd4ef;
    border-radius:16px;
    padding:14px;
    margin:8px 0 18px 0;
}
.admin-delete-note {
    color:#eb5757!important;
    font-size:13px!important;
    font-weight:900!important;
    margin-top:4px!important;
}
.crm-open-detail-v73 {
    background:#06499b;
    color:white!important;
    border-radius:14px;
    padding:14px;
    margin:18px 0 10px 0;
    text-align:center;
    font-size:20px;
    font-weight:900;
}


/* V74 - CRM ADMIN DEFINITIVO */
.admin-preventivo-row {
    background:#ffffff!important;
    border:2px solid #bdd4ef!important;
    border-radius:18px!important;
    padding:18px!important;
    margin:18px 0 12px 0!important;
    box-shadow:0 6px 18px rgba(6,73,155,0.10)!important;
}
.admin-preventivo-code {
    color:#06499b!important;
    font-size:23px!important;
    font-weight:900!important;
    margin-bottom:10px!important;
}
.admin-preventivo-line {
    color:#111!important;
    font-size:15px!important;
    font-weight:800!important;
    line-height:1.55!important;
}
.crm-detail-open-title-v74 {
    background:#06499b;
    color:#ffffff!important;
    border-radius:14px;
    padding:14px 18px;
    margin:16px 0 12px 0;
    text-align:center;
    font-size:22px;
    font-weight:900;
    box-shadow:0 5px 16px rgba(6,73,155,0.18);
}
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
.admin-delete-note {
    color:#eb5757!important;
    font-size:13px!important;
    font-weight:900!important;
    margin-top:4px!important;
}


/* V85 - SEZIONI ADMIN A SCOMPARSA */
.v85-toggle-title {
    background:#06499b;
    color:#ffffff!important;
    border-radius:14px;
    padding:14px 18px;
    margin:16px 0 8px 0;
    font-size:19px;
    font-weight:900;
    box-shadow:0 5px 15px rgba(6,73,155,0.18);
}
.v85-help-box {
    background:#eef6ff;
    color:#111827!important;
    border:2px solid #bdd4ef;
    border-radius:14px;
    padding:14px;
    margin:12px 0;
    font-size:15px;
    font-weight:800;
    line-height:1.55;
}


/* =========================================================
   V87 - FIX DEFINITIVO COLORI CRM / ADMIN SA-TEC
   ========================================================= */

/* Area principale Admin */
section.main,
.stApp,
.block-container {
    color:#111827 !important;
}

/* Titoli e testi standard */
h1, h2, h3, h4, h5, h6,
p, label, span, div,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] * {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
}

/* Titoli blu SA-TEC */
h1, h2, h3 {
    color:#06499b !important;
    -webkit-text-fill-color:#06499b !important;
    font-weight:900 !important;
}

/* Tabs Streamlit: Preventivi / Utenti CRM */
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] *,
button[data-baseweb="tab"],
button[data-baseweb="tab"] * {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
    font-weight:900 !important;
}

.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] * {
    color:#06499b !important;
    -webkit-text-fill-color:#06499b !important;
    font-weight:900 !important;
}

/* Testi dentro alert/info/warning */
[data-testid="stAlert"],
[data-testid="stAlert"] *,
.stAlert,
.stAlert * {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
    font-weight:800 !important;
}

/* Input, select, textarea */
input, textarea, select,
[data-baseweb="input"] *,
[data-baseweb="select"] *,
[data-baseweb="textarea"] * {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
    background:#ffffff !important;
    font-weight:800 !important;
}

/* Labels degli input */
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stCheckbox"] label,
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label *,
[data-testid="stSelectbox"] label *,
[data-testid="stNumberInput"] label *,
[data-testid="stCheckbox"] label *,
[data-testid="stTextArea"] label * {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
    font-weight:900 !important;
}

/* Tabelle CRM */
table, thead, tbody, tr, td, th {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
}

th {
    background:#06499b !important;
    color:#ffffff !important;
    -webkit-text-fill-color:#ffffff !important;
    font-weight:900 !important;
}

td {
    background:#ffffff !important;
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
    font-weight:700 !important;
}

/* Card dashboard vecchie e nuove */
.v84-dashboard,
.v84-dashboard *,
.v85-help-box,
.v85-help-box *,
.v85-toggle-title,
.v85-toggle-title *,
.v87-crm-title,
.v87-crm-title *,
.v87-section-title,
.v87-section-title *,
.v87-card,
.v87-card * {
    -webkit-text-fill-color: unset !important;
}

.v85-help-box,
.v85-help-box * {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
}

/* Titolo sezione pulito */
.v87-section-title {
    background:#06499b !important;
    color:#ffffff !important;
    -webkit-text-fill-color:#ffffff !important;
    border-radius:14px !important;
    padding:14px 18px !important;
    margin:18px 0 12px 0 !important;
    font-size:22px !important;
    font-weight:900 !important;
    box-shadow:0 5px 15px rgba(6,73,155,0.18) !important;
}

/* Bottoni */
.stButton button,
.stDownloadButton button {
    font-weight:900 !important;
    border-radius:12px !important;
}

/* Checkbox testo */
[data-testid="stCheckbox"] span,
[data-testid="stCheckbox"] p {
    color:#111827 !important;
    -webkit-text-fill-color:#111827 !important;
}

/* Sidebar mantiene leggibilità */
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {
    color:inherit;
}


    /* V1008 - accessori/checkbox più arrotondati e bordi più spessi */
    [data-testid="stCheckbox"] label{
        border:3px solid #B7CAE8!important;
        border-radius:22px!important;
        padding:14px 16px!important;
        box-shadow:0 8px 20px rgba(0,43,103,.10)!important;
        background:#FFFFFF!important;
    }
    [data-testid="stCheckbox"] label:hover{
        border-color:#0057D9!important;
        box-shadow:0 10px 24px rgba(0,87,217,.16)!important;
    }
    [data-testid="stCheckbox"] label:has(input:checked){
        border:3px solid #0057D9!important;
        border-radius:22px!important;
        background:#EAF3FF!important;
        box-shadow:0 0 0 4px rgba(0,87,217,.14),0 12px 26px rgba(0,87,217,.18)!important;
    }

    </style>
    </head>
    <body>
        <div class="head">
            <h1>Dettaglio preventivo __CODICE__</h1>
            <div>SA-TEC S.R.L.s - CRM Commerciale</div>
        </div>
        <table>__RIGHE__</table>
        <div class="footer">Documento gestionale interno. Stampare o salvare come PDF dal browser.</div>
    </body>
    </html>
    """
    html = html.replace("__CODICE__", codice).replace("__RIGHE__", righe)
    return html


def valore_admin_euro(p, campo):
    try:
        return euro(float(str(p.get(campo, "0")).replace(",", ".") or 0))
    except:
        return str(p.get(campo, "") or "")



def cliente_label_admin(p):
    nome = str(p.get("cliente_nome", "") or "").strip()
    azienda = str(p.get("cliente_azienda", "") or "").strip()
    email = str(p.get("cliente_email", "") or "").strip()
    telefono = str(p.get("cliente_telefono", "") or "").strip()

    # Se arriva solo un ID numerico tipo "5", non usarlo come nome cliente
    if nome.isdigit() and not azienda and not email and not telefono:
        return "Cliente non indicato"

    if nome and not nome.isdigit():
        return nome
    if azienda:
        return azienda
    if email:
        return email
    if telefono:
        return telefono
    if nome:
        return nome
    return "Cliente non indicato"


def aggiorna_stato_preventivo_admin_robusto(codice_preventivo, nuovo_stato):
    ok = False

    try:
        ok = aggiorna_stato_preventivo_admin(codice_preventivo, nuovo_stato)
    except Exception:
        ok = False

    # Fallback diretto CSV se la funzione esistente non trova il preventivo
    if not ok:
        try:
            path = Path(PREVENTIVI_CSV)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    righe = list(csv.DictReader(f))
                if righe:
                    fieldnames = list(righe[0].keys())
                    if "stato" not in fieldnames:
                        fieldnames.append("stato")
                    trovato = False
                    for r in righe:
                        if str(r.get("codice_preventivo", "")).strip() == str(codice_preventivo).strip():
                            r["stato"] = nuovo_stato
                            trovato = True
                    if trovato:
                        with open(path, "w", newline="", encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(righe)
                        ok = True
        except Exception:
            pass

    # Fallback Supabase
    if not ok:
        try:
            sb = supabase_client()
            if sb is not None:
                sb.table("preventivi").update({"stato": nuovo_stato}).eq("codice_preventivo", codice_preventivo).execute()
                ok = True
        except Exception:
            pass

    return ok




def valore_admin_euro_safe(p, campo):
    try:
        return euro(float(str(p.get(campo, "0")).replace(",", ".") or 0))
    except Exception:
        return str(p.get(campo, "") or "")


def render_dettaglio_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", "") or "")
    configurazione = str(p.get("configurazione", "") or "")
    stato = str(p.get("stato", "Bozza") or "Bozza")
    cliente = cliente_label_admin(p)
    rivenditore = p.get("utente", "") or "Utente non indicato"

    elettro = str(p.get("elettroblocco", "") or "No")
    radar = str(p.get("radar_sicurezza_laterale", "") or "No")
    allaccio = str(p.get("allaccio", "") or "No")

    accessori = []
    if elettro.lower() not in ["no", "false", "0", ""]:
        accessori.append({"Accessorio": "Elettroblocco", "Q.tà": "1", "Valore": elettro})
    if radar.lower() not in ["no", "false", "0", ""]:
        accessori.append({"Accessorio": "Radar sicurezza laterale", "Q.tà": "1", "Valore": radar})
    if allaccio.lower() not in ["no", "false", "0", ""]:
        accessori.append({"Accessorio": "Allaccio e collaudo", "Q.tà": "1", "Valore": allaccio})
    if not accessori:
        accessori.append({"Accessorio": "Nessun accessorio extra indicato", "Q.tà": "", "Valore": ""})

    st.markdown(f"""
    <div class="crm-detail-v68">
        <div class="crm-detail-head-v68">
            <div class="crm-detail-code-v68">DETTAGLIO PREVENTIVO {codice}</div>
            <div class="crm-detail-sub-v68">{configurazione} · Stato: {stato}</div>
        </div>
        <div class="crm-detail-grid-v68">
            <div class="crm-mini-card-v68"><b>Cliente</b><br>{cliente}</div>
            <div class="crm-mini-card-v68"><b>Rivenditore / Utente</b><br>{rivenditore}</div>
            <div class="crm-mini-card-v68"><b>Data</b><br>{p.get('data_ora', '')}</div>
            <div class="crm-mini-card-v68"><b>Totale vendita</b><br><span>{valore_admin_euro_safe(p, 'totale_iva')}</span></div>
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
            <b>Email:</b> {p.get('cliente_email', '')}<br>
            <b>Telefono:</b> {p.get('cliente_telefono', '')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Accessori / servizi")
        st.markdown(tabella_html_sicura(accessori), unsafe_allow_html=True)

    with c2:
        st.markdown("### Riepilogo economico")
        st.markdown(f"""
        <div class="crm-white-box-v68">
            <div class="crm-price-row-v68"><span>Totale netto vendita</span><b>{valore_admin_euro_safe(p, 'imponibile')}</b></div>
            <div class="crm-price-row-v68"><span>IVA</span><b>{valore_admin_euro_safe(p, 'iva')}</b></div>
            <div class="crm-price-row-v68 total"><span>Totale vendita</span><b>{valore_admin_euro_safe(p, 'totale_iva')}</b></div>
            <hr>
            <div class="crm-price-row-v68"><span>Costo netto SA-TEC</span><b>{valore_admin_euro_safe(p, 'costo_satec')}</b></div>
            <div class="crm-price-row-v68"><span>Utile lordo</span><b>{valore_admin_euro_safe(p, 'utile_lordo')}</b></div>
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
            key=f"export_html_{codice}_{id(p)}_v74"
        )

    with a2:
        if st.button("DUPLICA PREVENTIVO", key=f"duplica_{codice}_{id(p)}_v74", use_container_width=True):
            ok_dup, msg_dup = duplica_preventivo_admin(codice)
            if ok_dup:
                st.success(f"Preventivo duplicato: {msg_dup}")
                st.rerun()
            else:
                st.error(msg_dup)

    with a3:
        st.info("Apri il file HTML e fai Stampa → Salva PDF.")




# =========================
# HEADER V400 CLEAN SA-TEC
# =========================

def v400_style():
    st.markdown("""
    <style>
    :root{
        --satec-blue:#0057D9;
        --satec-dark:#003C96;
        --satec-orange:#F5B301;
        --satec-text:#111827;
        --satec-border:#C9DCF7;
        --satec-bg:#F4F8FF;
    }

    .stApp{
        background:linear-gradient(180deg,#F4F8FF 0%,#FFFFFF 65%)!important;
    }

    .block-container{
        padding-top:0.8rem!important;
    }

    /* HEADER V400 */
    .v400-header{
        background:linear-gradient(90deg,#0057D9 0%,#003C96 100%)!important;
        border-radius:20px!important;
        padding:22px 26px!important;
        margin:8px 0 18px 0!important;
        box-shadow:0 12px 30px rgba(0,87,217,.28)!important;
        display:grid!important;
        grid-template-columns:23% 39% 23% 15%!important;
        gap:20px!important;
        align-items:center!important;
    }
    .v400-header,
    .v400-header *{
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        text-shadow:none!important;
        opacity:1!important;
    }
    .v400-brand{
        font-size:48px!important;
        font-weight:1000!important;
        letter-spacing:1px!important;
        line-height:1!important;
    }
    .v400-brand-sub{
        color:#EAF3FF!important;
        -webkit-text-fill-color:#EAF3FF!important;
        font-size:13px!important;
        font-weight:1000!important;
        letter-spacing:4px!important;
        margin-top:12px!important;
    }
    .v400-title{
        border-left:1px solid rgba(255,255,255,.42)!important;
        padding-left:22px!important;
    }
    .v400-title-main{
        font-size:31px!important;
        line-height:1.08!important;
        font-weight:1000!important;
        letter-spacing:.4px!important;
    }
    .v400-title-main span{
        color:#F5B301!important;
        -webkit-text-fill-color:#F5B301!important;
    }
    .v400-title-sub{
        color:#EAF3FF!important;
        -webkit-text-fill-color:#EAF3FF!important;
        font-size:14px!important;
        font-weight:900!important;
        margin-top:10px!important;
    }
    .v400-info{
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        font-size:13px!important;
        font-weight:900!important;
        line-height:1.55!important;
    }
    .v400-sesamo{
        border-left:1px solid rgba(255,255,255,.42)!important;
        padding-left:16px!important;
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
        gap:10px!important;
    }
    .v400-sesamo-mark{
        background:#F58220!important;
        color:#071124!important;
        -webkit-text-fill-color:#071124!important;
        font-size:34px!important;
        font-weight:1000!important;
        padding:7px 12px!important;
    }
    .v400-sesamo-name{
        font-size:28px!important;
        font-weight:1000!important;
        line-height:1!important;
        letter-spacing:1px!important;
    }
    .v400-sesamo-sub{
        color:#EAF3FF!important;
        -webkit-text-fill-color:#EAF3FF!important;
        font-size:10px!important;
        font-weight:1000!important;
        letter-spacing:.8px!important;
        margin-top:4px!important;
    }

    /* PRODUCT */
    .v400-product{
        background:#FFFFFF!important;
        border:1px solid #C9DCF7!important;
        border-radius:16px!important;
        padding:22px 26px!important;
        margin:0 0 22px 0!important;
        display:grid!important;
        grid-template-columns:65% 35%!important;
        align-items:center!important;
        box-shadow:0 8px 22px rgba(0,87,217,.08)!important;
    }
    .v400-product-title{
        color:#0B2A4A!important;
        -webkit-text-fill-color:#0B2A4A!important;
        font-size:31px!important;
        font-weight:1000!important;
    }
    .v400-product-sub{
        color:#334155!important;
        -webkit-text-fill-color:#334155!important;
        font-size:16px!important;
        font-weight:800!important;
        margin-top:9px!important;
        line-height:1.45!important;
    }
    .v400-product-logo{
        display:flex!important;
        justify-content:center!important;
        align-items:center!important;
        gap:15px!important;
    }
    .v400-product-mark{
        background:#F58220!important;
        color:#071124!important;
        -webkit-text-fill-color:#071124!important;
        font-size:39px!important;
        font-weight:1000!important;
        padding:7px 14px!important;
    }
    .v400-product-name{
        color:#111827!important;
        -webkit-text-fill-color:#111827!important;
        font-size:39px!important;
        font-weight:1000!important;
        line-height:1!important;
    }
    .v400-product-tech{
        color:#111827!important;
        -webkit-text-fill-color:#111827!important;
        font-size:13px!important;
        font-weight:1000!important;
        letter-spacing:1px!important;
        margin-top:5px!important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"]{
        background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;
        border-right:5px solid #F5B301!important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div{
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
    }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] [data-baseweb="input"],
    section[data-testid="stSidebar"] [data-baseweb="input"] *,
    section[data-testid="stSidebar"] [data-baseweb="select"],
    section[data-testid="stSidebar"] [data-baseweb="select"] *{
        background:#FFFFFF!important;
        color:#111827!important;
        -webkit-text-fill-color:#111827!important;
        font-weight:900!important;
    }

    /* BOTTONI */
    .stButton button,
    .stDownloadButton button{
        background:#FFFFFF!important;
        color:#0057D9!important;
        -webkit-text-fill-color:#0057D9!important;
        border:2px solid #0057D9!important;
        border-radius:13px!important;
        min-height:48px!important;
        font-size:15px!important;
        font-weight:1000!important;
        opacity:1!important;
        box-shadow:0 4px 12px rgba(0,87,217,.10)!important;
    }
    .stButton button *,
    .stDownloadButton button *{
        color:inherit!important;
        -webkit-text-fill-color:inherit!important;
        font-weight:1000!important;
        opacity:1!important;
    }
    .stButton button:hover,
    .stDownloadButton button:hover{
        background:#F5B301!important;
        color:#111111!important;
        -webkit-text-fill-color:#111111!important;
        border-color:#F5B301!important;
    }
    .stButton button:hover *,
    .stDownloadButton button:hover *{
        color:#111111!important;
        -webkit-text-fill-color:#111111!important;
    }

    /* PULSANTI SIDEBAR */
    section[data-testid="stSidebar"] .stButton button{
        background:#FFFFFF!important;
        color:#0057D9!important;
        -webkit-text-fill-color:#0057D9!important;
        border:2px solid #FFFFFF!important;
    }
    section[data-testid="stSidebar"] .stButton button *,
    section[data-testid="stSidebar"] .stButton button p,
    section[data-testid="stSidebar"] .stButton button span,
    section[data-testid="stSidebar"] .stButton button div{
        color:#0057D9!important;
        -webkit-text-fill-color:#0057D9!important;
        font-weight:1000!important;
    }

    /* ADMIN TOP BUTTONS */
    div[data-testid="stHorizontalBlock"] .stButton button{
        background:#0057D9!important;
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        border-color:#0057D9!important;
        min-height:56px!important;
    }
    div[data-testid="stHorizontalBlock"] .stButton button *,
    div[data-testid="stHorizontalBlock"] .stButton button p,
    div[data-testid="stHorizontalBlock"] .stButton button span,
    div[data-testid="stHorizontalBlock"] .stButton button div{
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        font-weight:1000!important;
    }
    div[data-testid="stHorizontalBlock"] .stButton button:hover,
    div[data-testid="stHorizontalBlock"] .stButton button:hover *{
        background:#F5B301!important;
        color:#111111!important;
        -webkit-text-fill-color:#111111!important;
        border-color:#F5B301!important;
    }

    /* SEZIONI ADMIN */
    .v87-section-title,
    .v85-toggle-title,
    .v100-title-bar,
    .v102-title-bar{
        background:#0057D9!important;
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        border-radius:16px!important;
        border:0!important;
    }
    .v87-section-title *,
    .v85-toggle-title *,
    .v100-title-bar *,
    .v102-title-bar *{
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
    }

    /* TABELLE */
    th{
        background:#0057D9!important;
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
    }
    td{
        background:#FFFFFF!important;
        color:#111827!important;
        -webkit-text-fill-color:#111827!important;
    }

    /* RESPONSIVE */
    @media(max-width:1100px){
        .v400-header{
            grid-template-columns:1fr!important;
            text-align:center!important;
        }
        .v400-title,
        .v400-sesamo{
            border-left:0!important;
            padding-left:0!important;
        }
        .v400-product{
            grid-template-columns:1fr!important;
            gap:18px!important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def v400_header():
    st.markdown("""
    <div class="v400-header">
        <div>
            <div class="v400-brand">SA-TEC</div>
            <div class="v400-brand-sub">PORTE AUTOMATICHE</div>
        </div>
        <div class="v400-title">
            <div class="v400-title-main">
                CONFIGURATORE<br>
                <span>PORTE AUTOMATICHE</span>
            </div>
            <div class="v400-title-sub">TECNOLOGIA, SICUREZZA E SOLUZIONI SU MISURA</div>
        </div>
        <div class="v400-info">
            📍 SA-TEC S.R.L.s<br>
            Via L. Settembrini 84<br>
            88046 Lamezia Terme (CZ)<br>
            ☎ 0968-036797<br>
            ✉ sacco.tecnologie@gmail.com
        </div>
        <div class="v400-sesamo">
            <div class="v400-sesamo-mark">▌</div>
            <div>
                <div class="v400-sesamo-name">SESAMO</div>
                <div class="v400-sesamo-sub">THE DOOR TECHNOLOGY</div>
            </div>
        </div>
    </div>

    <div class="v400-product">
        <div>
            <div class="v400-product-title">SESAMO POWERCORE PW100</div>
            <div class="v400-product-sub">
                Automazione lineare per porte scorrevoli automatiche,<br>
                affidabile, sicura e compatibile con la normativa EN16005.
            </div>
        </div>
        <div class="v400-product-logo">
            <div class="v400-product-mark">▌</div>
            <div>
                <div class="v400-product-name">SESAMO</div>
                <div class="v400-product-tech">THE DOOR TECHNOLOGY</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# V401 - LOGIN BOX RIPRISTINATA PRIMA DELLA CHIAMATA
# =========================
def login_box():
    utenti = carica_tutti_utenti()

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
    st.sidebar.info("Cliente finale: può usare il configuratore senza login.")

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
    st.sidebar.write(f"Profilo attivo: **{PROFILI.get(profilo, profilo)}**")

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
            try:
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
            except Exception as e:
                st.error(f"Errore creazione utente: {e}")

    try:
        ricarico_effettivo = float(str(dati_utente.get("ricarico", "")).replace(",", "."))
    except Exception:
        ricarico_effettivo = ricarico_default(profilo)

    if profilo == "SA-TEC":
        ricarico_effettivo = 0.0

    return profilo, nome_utente, utente_codice, dati_utente, ricarico_effettivo




# =========================
# V402 - DISEGNO PORTA RIPRISTINATO
# =========================


def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    """
    V502 - Canvas tecnico professionale SA-TEC.
    Disegno più realistico: traversa alluminio, vetri, carrelli, cinghia, motore, quote.
    """
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600

    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200

    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_label = "2 ANTE SCORREVOLI" if due_ante else "1 ANTA SCORREVOLE"

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
    html, body {{
        margin:0;
        padding:0;
        font-family:Arial, Helvetica, sans-serif;
        background:#ffffff;
    }}
    .wrap {{
        border:2px solid #C9DCF7;
        border-radius:22px;
        background:linear-gradient(180deg,#FFFFFF 0%,#F5F9FF 100%);
        box-shadow:0 12px 30px rgba(0,87,217,.10);
        overflow:hidden;
    }}
    .top {{
        background:linear-gradient(90deg,#003C96,#0057D9);
        color:white;
        padding:15px 20px;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}
    .title {{
        font-size:24px;
        font-weight:1000;
        letter-spacing:.3px;
    }}
    .sub {{
        font-size:13px;
        font-weight:800;
        color:#EAF3FF;
        margin-top:3px;
    }}
    .brand {{
        text-align:right;
        font-weight:1000;
        font-size:18px;
    }}
    .brand span {{
        display:inline-block;
        background:#F58220;
        color:#111827;
        padding:7px 10px;
        margin-right:8px;
    }}
    .canvas-area {{
        padding:12px 16px 14px 16px;
    }}
    canvas {{
        width:100%;
        height:390px;
        display:block;
        background:linear-gradient(180deg,#FFFFFF,#F7FBFF);
        border:1px solid #D7E8FF;
        border-radius:16px;
    }}
    .cards {{
        display:grid;
        grid-template-columns:repeat(4,1fr);
        gap:10px;
        margin-top:12px;
    }}
    .card {{
        background:#FFFFFF;
        border:1px solid #C9DCF7;
        border-radius:14px;
        padding:10px;
        text-align:center;
        font-weight:900;
        color:#111827;
        box-shadow:0 4px 12px rgba(0,87,217,.06);
    }}
    .card b {{
        display:block;
        color:#0057D9;
        font-size:18px;
        margin-top:4px;
    }}
</style>
</head>
<body>
<div class="wrap">
    <div class="top">
        <div>
            <div class="title">Tavola tecnica porta automatica</div>
            <div class="sub">SA-TEC · SESAMO POWERCORE PW100 · {ante_label}</div>
        </div>
        <div class="brand"><span>▌</span>SESAMO<br><small>EN 16005</small></div>
    </div>

    <div class="canvas-area">
        <canvas id="doorCanvas" width="1100" height="520"></canvas>
        <div class="cards">
            <div class="card">Configurazione<b>{ante_label}</b></div>
            <div class="card">Luce passaggio<b>{luce} mm</b></div>
            <div class="card">Altezza<b>{altezza} mm</b></div>
            <div class="card">Traversa<b>{traversa:.2f} m</b></div>
        </div>
    </div>
</div>

<script>
const canvas = document.getElementById("doorCanvas");
const ctx = canvas.getContext("2d");

const luce = {luce};
const altezza = {altezza};
const traversa = {traversa:.2f};
const dueAnte = {str(due_ante).lower()};

function roundRect(x,y,w,h,r,fill,stroke) {{
    ctx.beginPath();
    ctx.moveTo(x+r,y);
    ctx.lineTo(x+w-r,y);
    ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r);
    ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h);
    ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r);
    ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath();
    if(fill) ctx.fill();
    if(stroke) ctx.stroke();
}}

function line(x1,y1,x2,y2,color,w) {{
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.lineTo(x2,y2);
    ctx.stroke();
}}

function text(t,x,y,size,color,align="center",weight="900") {{
    ctx.font = weight + " " + size + "px Arial";
    ctx.fillStyle = color;
    ctx.textAlign = align;
    ctx.fillText(t,x,y);
}}

function arrow(x1,y1,x2,y2,color) {{
    line(x1,y1,x2,y2,color,7);
    const ang = Math.atan2(y2-y1,x2-x1);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x2,y2);
    ctx.lineTo(x2-18*Math.cos(ang-Math.PI/6), y2-18*Math.sin(ang-Math.PI/6));
    ctx.lineTo(x2-18*Math.cos(ang+Math.PI/6), y2-18*Math.sin(ang+Math.PI/6));
    ctx.closePath();
    ctx.fill();
}}

function drawGlass(x,y,w,h) {{
    const g = ctx.createLinearGradient(x,y,x+w,y+h);
    g.addColorStop(0,"rgba(255,255,255,.95)");
    g.addColorStop(.45,"rgba(185,223,255,.55)");
    g.addColorStop(1,"rgba(120,190,255,.75)");
    ctx.fillStyle = g;
    ctx.strokeStyle = "#0074E8";
    ctx.lineWidth = 4;
    roundRect(x,y,w,h,8,true,true);

    ctx.strokeStyle = "rgba(255,255,255,.70)";
    ctx.lineWidth = 3;
    line(x+24,y+18,x+w-45,y+h-35,"rgba(255,255,255,.70)",3);
    line(x+52,y+18,x+w-20,y+h-75,"rgba(255,255,255,.45)",2);
}}

function draw() {{
    ctx.clearRect(0,0,1100,520);

    // fondo griglia tecnico
    ctx.strokeStyle = "rgba(0,87,217,.05)";
    ctx.lineWidth = 1;
    for(let x=40;x<1060;x+=40) line(x,30,x,495,"rgba(0,87,217,.05)",1);
    for(let y=40;y<500;y+=40) line(35,y,1065,y,"rgba(0,87,217,.05)",1);

    // titolo tavola
    text("SA-TEC · CONFIGURAZIONE TECNICA INGRESSO AUTOMATICO",550,30,18,"#003C96");
    text("Lunghezza traversa calcolata: " + traversa.toFixed(2) + " m",550,55,14,"#111827");

    // coordinate principali
    const frameX = 250, frameY = 150, frameW = 600, frameH = 285;
    const railX = 190, railY = 95, railW = 720, railH = 58;

    // ombra traversa
    ctx.shadowColor = "rgba(0,60,150,.25)";
    ctx.shadowBlur = 18;
    ctx.shadowOffsetY = 8;

    // traversa alluminio
    let rg = ctx.createLinearGradient(railX,railY,railX,railY+railH);
    rg.addColorStop(0,"#164FAD");
    rg.addColorStop(.25,"#0057D9");
    rg.addColorStop(.55,"#003C96");
    rg.addColorStop(1,"#0B214A");
    ctx.fillStyle = rg;
    ctx.strokeStyle = "#071124";
    ctx.lineWidth = 2;
    roundRect(railX,railY,railW,railH,12,true,true);
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    text("TRAVERSA AUTOMAZIONE",550,130,19,"#FFFFFF");

    // coperchio/profilo inferiore
    line(railX+30,railY+railH+9,railX+railW-30,railY+railH+9,"#F5B301",5);

    // motore e scheda
    ctx.fillStyle = "#F58220";
    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 2;
    roundRect(815,105,62,38,7,true,true);
    text("MOT",846,130,14,"#111827");

    ctx.fillStyle = "#EAF3FF";
    ctx.strokeStyle = "#003C96";
    roundRect(735,108,58,32,6,true,true);
    text("CTRL",764,130,11,"#003C96");

    // pulegge cinghia
    ctx.fillStyle="#F5B301";
    ctx.strokeStyle="#003C96";
    ctx.lineWidth=3;
    ctx.beginPath(); ctx.arc(245,162,13,0,Math.PI*2); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.arc(855,162,13,0,Math.PI*2); ctx.fill(); ctx.stroke();
    line(245,162,855,162,"#111827",3);

    // telaio vano
    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 4;
    roundRect(frameX,frameY,frameW,frameH,10,false,true);

    // guida pavimento
    line(frameX-20,frameY+frameH+18,frameX+frameW+20,frameY+frameH+18,"#111827",3);
    line(frameX+10,frameY+frameH+28,frameX+frameW-10,frameY+frameH+28,"#9CBCE8",2);

    // carrelli
    function trolley(x) {{
        ctx.fillStyle="#111827";
        roundRect(x,150,62,17,5,true,false);
        line(x+16,167,x+16,190,"#111827",3);
        line(x+46,167,x+46,190,"#111827",3);
        ctx.fillStyle="#F5B301";
        ctx.beginPath(); ctx.arc(x+16,149,6,0,Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(x+46,149,6,0,Math.PI*2); ctx.fill();
    }}

    if(dueAnte) {{
        trolley(340); trolley(700);
        drawGlass(290,185,260,245);
        drawGlass(550,185,260,245);
        line(550,185,550,430,"#003C96",5);
        arrow(512,310,420,310,"#F5B301");
        arrow(588,310,680,310,"#F5B301");
    }} else {{
        trolley(430); trolley(620);
        drawGlass(385,185,330,245);
        arrow(535,310,675,310,"#F5B301");
    }}

    // quote luce orizzontale
    line(frameX,470,frameX+frameW,470,"#111827",2);
    line(frameX,460,frameX,480,"#111827",2);
    line(frameX+frameW,460,frameX+frameW,480,"#111827",2);
    text("LUCE PASSAGGIO " + luce + " mm",550,505,15,"#111827");

    // quota altezza
    line(920,frameY,920,frameY+frameH,"#111827",2);
    line(905,frameY,935,frameY,"#111827",2);
    line(905,frameY+frameH,935,frameY+frameH,"#111827",2);
    ctx.save();
    ctx.translate(955,frameY+frameH/2+70);
    ctx.rotate(-Math.PI/2);
    text("ALTEZZA " + altezza + " mm",0,0,15,"#111827");
    ctx.restore();

    // dettaglio profili laterali
    ctx.fillStyle="#DDE7F4";
    ctx.fillRect(frameX-16,frameY,10,frameH);
    ctx.fillRect(frameX+frameW+6,frameY,10,frameH);
    ctx.fillStyle="#003C96";
    ctx.fillRect(frameX-16,frameY,4,frameH);
    ctx.fillRect(frameX+frameW+12,frameY,4,frameH);

    // legenda tecnica
    ctx.fillStyle="rgba(255,255,255,.92)";
    ctx.strokeStyle="#C9DCF7";
    ctx.lineWidth=2;
    roundRect(45,115,120,168,12,true,true);
    text("DETTAGLI",105,143,14,"#003C96");
    text("• Cinghia",60,172,13,"#111827","left","800");
    text("• Carrelli",60,198,13,"#111827","left","800");
    text("• Motore",60,224,13,"#111827","left","800");
    text("• Vetro",60,250,13,"#111827","left","800");

    // badge normativa
    ctx.fillStyle="#F5B301";
    roundRect(940,95,120,40,20,true,false);
    text("EN 16005",1000,121,15,"#111827");

    // mini logo
    ctx.fillStyle="#F58220";
    roundRect(945,375,45,55,3,true,false);
    text("▌",967,414,36,"#111827");
    text("SESAMO",1018,402,22,"#111827","center","1000");
    text("THE DOOR TECHNOLOGY",1018,424,10,"#111827","center","900");
}}

draw();
</script>
</body>
</html>
"""


# =========================
# V500 UFFICIALE - FUNZIONI STABILI RIPRISTINATE
# =========================
# Questo blocco ripristina le funzioni mancanti senza toccare Supabase,
# preventivi, CRM e configuratore esistenti.

logo_satec64 = img_to_base64([
    "logo_satec.jpg", "logo_satec.png", "LOGO_SATEC.png",
    "/mnt/data/logo_satec.jpg", "/mnt/data/logo_satec.png", "/mnt/data/LOGO_SATEC.png"
])

logo_sesamo64 = img_to_base64([
    "SESAMO LOGO.png", "sesamo_logo.png", "logo_sesamo.png", "sesamo.png",
    "/mnt/data/SESAMO LOGO.png", "/mnt/data/sesamo_logo.png", "/mnt/data/logo_sesamo.png", "/mnt/data/sesamo.png"
])

sesamo_logo_html = (
    f'<img src="data:image/png;base64,{logo_sesamo64}" style="max-height:82px;max-width:280px;object-fit:contain;">'
    if logo_sesamo64 else
    '<div style="font-size:32px;font-weight:1000;color:#111827;-webkit-text-fill-color:#111827;">SESAMO</div><div style="font-size:12px;font-weight:900;color:#111827;-webkit-text-fill-color:#111827;">THE DOOR TECHNOLOGY</div>'
)


def carica_preventivi():
    righe = []
    path = Path(PREVENTIVI_CSV)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                righe.extend(list(csv.DictReader(f)))
        except Exception as e:
            st.sidebar.warning(f"Preventivi CSV non caricati: {e}")
    if not righe:
        try:
            righe.extend(carica_preventivi_supabase() or [])
        except Exception:
            pass
    return righe


def salva_preventivo(dati):
    path = Path(PREVENTIVI_CSV)
    campi_base = [
        "codice_preventivo", "data_ora", "utente", "profilo", "cliente_nome", "cliente_azienda",
        "cliente_telefono", "cliente_email", "configurazione", "luce_mm", "altezza_mm", "traversa_m",
        "elettroblocco", "allaccio", "radar_sicurezza_laterale", "ricarico_percento",
        "ricarico_base_percento", "ricarico_extra_percento", "imponibile", "iva", "totale_iva",
        "costo_satec", "utile_lordo", "margine_percento", "stato"
    ]
    campi = list(campi_base)
    for k in dati.keys():
        if k not in campi:
            campi.append(k)
    file_exists = path.exists()
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campi)
            if not file_exists:
                writer.writeheader()
            writer.writerow({k: dati.get(k, "") for k in campi})
        return True
    except Exception as e:
        st.error(f"Errore salvataggio preventivo CSV: {e}")
        return False


def salva_cliente_csv(nome, azienda, telefono, email, codice_preventivo="", imponibile=0, owner_utente="", owner_profilo=""):
    path = Path(CLIENTI_CSV)
    campi = ["nome", "azienda", "telefono", "email", "primo_preventivo", "ultimo_preventivo", "data_primo_preventivo", "data_ultimo_preventivo", "numero_preventivi", "totale_preventivi", "owner_utente", "owner_profilo"]
    nome = str(nome or "").strip(); azienda = str(azienda or "").strip(); telefono = str(telefono or "").strip(); email = str(email or "").strip().lower()
    if not any([nome, azienda, telefono, email]):
        return False
    oggi = datetime.now().strftime("%d/%m/%Y %H:%M")
    try:
        clienti = []
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                clienti = list(csv.DictReader(f))
        trovato = None
        for c in clienti:
            if email and str(c.get("email", "")).strip().lower() == email:
                trovato = c; break
            if telefono and str(c.get("telefono", "")).strip() == telefono:
                trovato = c; break
        try:
            imp = float(str(imponibile or 0).replace(",", "."))
        except Exception:
            imp = 0.0
        if trovato:
            try:
                prec = int(float(trovato.get("numero_preventivi", "0") or 0))
            except Exception:
                prec = 0
            try:
                oldtot = float(str(trovato.get("totale_preventivi", "0") or 0).replace(",", "."))
            except Exception:
                oldtot = 0.0
            trovato.update({"nome": nome or trovato.get("nome", ""), "azienda": azienda or trovato.get("azienda", ""), "telefono": telefono or trovato.get("telefono", ""), "email": email or trovato.get("email", ""), "ultimo_preventivo": codice_preventivo, "data_ultimo_preventivo": oggi, "numero_preventivi": str(prec + 1), "totale_preventivi": f"{oldtot + imp:.2f}", "owner_utente": owner_utente or trovato.get("owner_utente", ""), "owner_profilo": owner_profilo or trovato.get("owner_profilo", "")})
        else:
            clienti.append({"nome": nome, "azienda": azienda, "telefono": telefono, "email": email, "primo_preventivo": codice_preventivo, "ultimo_preventivo": codice_preventivo, "data_primo_preventivo": oggi, "data_ultimo_preventivo": oggi, "numero_preventivi": "1", "totale_preventivi": f"{imp:.2f}", "owner_utente": owner_utente, "owner_profilo": owner_profilo})
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campi); writer.writeheader()
            for c in clienti:
                writer.writerow({k: c.get(k, "") for k in campi})
        return True
    except Exception as e:
        st.sidebar.warning(f"Cliente non salvato in CSV: {e}")
        return False


def carica_clienti():
    righe = []
    path = Path(CLIENTI_CSV)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                righe.extend(list(csv.DictReader(f)))
        except Exception as e:
            st.sidebar.warning(f"Clienti CSV non caricati: {e}")
    if not righe:
        try:
            righe.extend(carica_clienti_supabase() or [])
        except Exception:
            pass
    return righe


def clienti_visibili_per_profilo(clienti, profilo, utente_codice):
    if profilo == "SA-TEC":
        return clienti
    out = []
    for c in clienti:
        owner = str(c.get("owner_utente", "")).strip().upper()
        if not owner or owner == str(utente_codice or "").strip().upper():
            out.append(c)
    return out


def _cliente_search_text(c):
    return " ".join(str(c.get(k, "")) for k in ["nome", "azienda", "telefono", "email", "primo_preventivo", "ultimo_preventivo", "owner_utente"]).lower()


def filtra_clienti_dashboard(clienti, query):
    q = str(query or "").strip().lower()
    if not q:
        return clienti
    return [c for c in clienti if q in _cliente_search_text(c)]


def righe_clienti_dashboard(clienti):
    out = []
    for c in clienti:
        tot = ""
        if str(c.get("totale_preventivi", "")).strip():
            tot = euro(_num(c.get("totale_preventivi", 0)))
        out.append({"Nome": c.get("nome", ""), "Azienda": c.get("azienda", ""), "Telefono": c.get("telefono", ""), "Email": c.get("email", ""), "Ultimo preventivo": c.get("ultimo_preventivo", c.get("primo_preventivo", "")), "N. preventivi": c.get("numero_preventivi", ""), "Totale": tot, "Owner": c.get("owner_utente", "")})
    return out


def label_cliente_elimina(c):
    return f"{c.get('nome','')} | {c.get('azienda','')} | {c.get('telefono','')} | {c.get('email','')}".strip(" |")


def identificativo_cliente_elimina(c):
    return c.get("email") or c.get("telefono") or c.get("nome") or c.get("azienda") or ""


def elimina_cliente_admin(ident):
    ident = str(ident or "").strip().lower()
    if not ident:
        return False, "Identificativo cliente mancante"
    path = Path(CLIENTI_CSV)
    if not path.exists():
        return False, "Archivio clienti CSV non trovato"
    try:
        with open(path, "r", encoding="utf-8") as f:
            righe = list(csv.DictReader(f))
        if not righe:
            return False, "Archivio clienti vuoto"
        fieldnames = list(righe[0].keys())
        nuove = []
        eliminato = False
        for c in righe:
            valori = [str(c.get(k, "")).strip().lower() for k in ["email", "telefono", "nome", "azienda"]]
            if ident in valori:
                eliminato = True
            else:
                nuove.append(c)
        if not eliminato:
            return False, "Cliente non trovato"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames); writer.writeheader(); writer.writerows(nuove)
        return True, "Cliente eliminato"
    except Exception as e:
        return False, str(e)


def _num(v, default=0.0):
    try:
        s = str(v if v is not None else "").replace("€", "").replace(" ", "").strip()
        if not s: return default
        if "," in s and "." in s and s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return default


def statistiche_stati_preventivi(preventivi):
    d = {s: 0 for s in STATI_PREVENTIVO}
    for p in preventivi:
        stato = str(p.get("stato", "Bozza") or "Bozza")
        d[stato] = d.get(stato, 0) + 1
    return d


def crm_valore_float(p):
    return _num(p.get("imponibile", p.get("totale_iva", 0)))


def crm_utile_float(p):
    utile = _num(p.get("utile_lordo", 0))
    if utile: return utile
    return max(_num(p.get("imponibile", 0)) - _num(p.get("costo_satec", 0)), 0)


def v100_render_admin(preventivi):
    st.markdown('<div class="v100-title-bar">📋 GESTIONE PREVENTIVI</div>', unsafe_allow_html=True)
    if not preventivi:
        st.info("Nessun preventivo salvato ancora."); return
    cerca = st.text_input("Cerca preventivo", key="cerca_prev_v500", placeholder="Codice, cliente, azienda, configurazione")
    q = str(cerca or "").lower().strip(); righe = []
    for p in preventivi:
        testo = " ".join(str(p.get(k, "")) for k in p.keys()).lower()
        if q and q not in testo: continue
        righe.append(p)
    st.write(f"Preventivi trovati: **{len(righe)}**")
    vista = []
    for p in righe[:200]:
        vista.append({"Codice": p.get("codice_preventivo", ""), "Data": p.get("data_ora", ""), "Utente": p.get("utente", ""), "Cliente": p.get("cliente_nome", "") or p.get("cliente_azienda", ""), "Configurazione": p.get("configurazione", ""), "Totale IVA incl.": euro(_num(p.get("totale_iva", 0))), "Stato": p.get("stato", "")})
    st.markdown(tabella_html_sicura(vista), unsafe_allow_html=True)
    codici = [str(p.get("codice_preventivo", "")) for p in righe if p.get("codice_preventivo")]
    if codici:
        st.markdown("### Azioni preventivo")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: codice_sel = st.selectbox("Preventivo", codici, key="prev_sel_v500")
        with c2: nuovo_stato = st.selectbox("Stato", STATI_PREVENTIVO, key="prev_stato_v500")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("AGGIORNA STATO", key="prev_agg_v500", use_container_width=True):
                if aggiorna_stato_preventivo_admin_robusto(codice_sel, nuovo_stato):
                    st.success("Stato aggiornato"); st.rerun()
                else:
                    st.error("Stato non aggiornato")
        dettaglio = next((p for p in righe if str(p.get("codice_preventivo", "")) == str(codice_sel)), None)
        if dettaglio:
            with st.expander("Dettaglio preventivo", expanded=False): render_dettaglio_preventivo_admin(dettaglio)


def aggiungi(articoli, codice, descrizione, descrizione_lunga, quantita=1, scontato=True):
    listino = float(LISTINI.get(codice, 0) or 0)
    try: qta = float(quantita or 0)
    except Exception: qta = 0.0
    if scontato:
        costo_unitario = costo_satec_reale(listino)
        prezzo_unitario = costo_unitario * (1 + (float(RICARICO_ATTIVO or 0) / 100))
    else:
        costo_unitario = listino; prezzo_unitario = listino
    articoli.append({"codice": codice, "descrizione": descrizione, "descrizione_lunga": descrizione_lunga, "quantita": qta, "listino_unitario": listino, "costo_unitario_satec": costo_unitario, "prezzo_unitario": prezzo_unitario, "totale": prezzo_unitario * qta, "costo_totale_satec": costo_unitario * qta})


def disegno_porta(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try: luce = int(float(luce_mm))
    except Exception: luce = 1600
    try: altezza = int(float(altezza_mm))
    except Exception: altezza = 2200
    try: traversa = float(lunghezza_traversa)
    except Exception: traversa = 0.0
    due = "2" in str(ante)
    if due:
        ante_svg = """
        <rect x="116" y="120" width="184" height="250" rx="8" fill="#F8FBFF" stroke="#0057D9" stroke-width="5"/>
        <rect x="300" y="120" width="184" height="250" rx="8" fill="#F8FBFF" stroke="#0057D9" stroke-width="5"/>
        <line x1="300" y1="120" x2="300" y2="370" stroke="#003C96" stroke-width="5"/>
        <path d="M270 245 L230 245" stroke="#F5B301" stroke-width="9" stroke-linecap="round"/>
        <path d="M330 245 L370 245" stroke="#F5B301" stroke-width="9" stroke-linecap="round"/>
        """
        titolo = "Schema porta scorrevole a 2 ante"
    else:
        ante_svg = """
        <rect x="155" y="120" width="290" height="250" rx="8" fill="#F8FBFF" stroke="#0057D9" stroke-width="5"/>
        <path d="M295 245 L370 245" stroke="#F5B301" stroke-width="9" stroke-linecap="round"/>
        """
        titolo = "Schema porta scorrevole a 1 anta"
    return f"""
    <!doctype html><html><head><meta charset="utf-8"><style>
    body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:transparent;}}
    .wrap{{background:#fff;border:1px solid #C9DCF7;border-radius:18px;padding:18px;box-shadow:0 8px 22px rgba(0,87,217,.08);}}
    .head{{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(90deg,#0057D9,#003C96);color:white;border-radius:14px;padding:14px 18px;margin-bottom:14px;}}
    .title{{font-size:21px;font-weight:900;color:white;}}
    .badge{{background:#F5B301;color:#111827;border-radius:999px;padding:8px 13px;font-size:13px;font-weight:900;}}
    .measures{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;}}
    .m{{border:1px solid #C9DCF7;border-radius:12px;text-align:center;padding:10px;font-weight:800;color:#111827;background:#F4F8FF;}}
    .m b{{display:block;color:#0057D9;font-size:18px;margin-top:4px;}}
    </style></head><body><div class="wrap"><div class="head"><div class="title">{titolo}</div><div class="badge">EN16005</div></div>
      <svg width="100%" height="335" viewBox="0 0 600 405"><rect x="72" y="72" width="456" height="40" rx="9" fill="#003C96"/><text x="300" y="98" text-anchor="middle" font-size="17" font-weight="900" fill="#FFFFFF">TRAVERSA AUTOMAZIONE</text><rect x="92" y="112" width="416" height="270" rx="10" fill="none" stroke="#111827" stroke-width="3"/>{ante_svg}<line x1="92" y1="392" x2="508" y2="392" stroke="#111827" stroke-width="3"/></svg>
      <div class="measures"><div class="m">Luce<b>{luce} mm</b></div><div class="m">Altezza<b>{altezza} mm</b></div><div class="m">Traversa<b>{traversa:.2f} m</b></div></div></div></body></html>
    """



# =========================
# V503 - GRAFICA TECNICA DEFINITIVA SA-TEC
# =========================
def disegno_porta_v503(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo_schema = "502 - SCHEMA TECNICO PORTA SCORREVOLE A 2 ANTE" if due_ante else "501 - SCHEMA TECNICO PORTA SCORREVOLE A 1 ANTA"
    totale_demo = "€ 2.356,80" if due_ante else "€ 1.981,11"
    due_ante_js = "true" if due_ante else "false"
    traversa_mm = int(traversa * 1000)

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:#f4f8ff;color:#061b44}}
.app{{width:100%;background:#f4f8ff;border-radius:22px;border:1px solid #d8e7fb;overflow:hidden;box-shadow:0 14px 36px rgba(0,42,110,.14)}}
.top{{height:72px;background:#fff;border-bottom:1px solid #d8e7fb;display:flex;align-items:center;justify-content:space-between;padding:0 20px}}
.t1{{font-size:24px;font-weight:1000;color:#061b44;line-height:1}} .t2{{font-size:15px;font-weight:800;color:#4d82d9;margin-top:5px}}
.brand{{display:flex;gap:22px;align-items:center;font-weight:1000;color:#061b44}} .badge{{background:#0057d9;color:white;border-radius:8px;padding:8px 13px;font-size:13px}} .ses{{font-size:28px;letter-spacing:.4px}}
.steps{{margin:14px 16px 0 16px;background:#fff;border:1px solid #e4ecf8;border-radius:15px;padding:13px;display:grid;grid-template-columns:repeat(5,1fr);gap:6px}}
.step{{display:flex;justify-content:center;align-items:center;gap:8px;font-size:13px;font-weight:1000;color:#061b44;border-right:1px solid #d8e7fb}}.step:last-child{{border:0}}.dot{{width:28px;height:28px;border-radius:50%;background:#eaf3ff;display:flex;align-items:center;justify-content:center}}.active .dot{{background:#0057d9;color:#fff}}.active{{color:#0057d9}}
.grid{{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:18px;padding:14px 16px 18px}}
.card{{background:#fff;border:1px solid #d8e7fb;border-radius:16px;box-shadow:0 10px 26px rgba(0,42,110,.08);overflow:hidden}}
.head{{padding:17px 18px 8px;color:#0047b8;font-size:18px;font-weight:1000}}
.drow{{display:grid;grid-template-columns:minmax(0,1fr) 210px;gap:14px;padding:0 14px 12px}}
.dbox{{background:#fff;border:1px solid #edf3fc;border-radius:14px;padding:8px;min-height:360px}} canvas{{width:100%;display:block}}
#frontCanvas{{height:350px}} #sectionCanvas{{height:310px}}
.sez{{border-left:1px solid #d8e7fb;padding:8px;display:flex;flex-direction:column;align-items:center;justify-content:center}}.lab{{align-self:flex-start;background:#0057d9;color:#fff;border-radius:6px;padding:8px 11px;font-size:12px;font-weight:1000;margin-bottom:8px}}
.metrics{{border-top:1px solid #d8e7fb;background:#fbfdff;display:grid;grid-template-columns:repeat(6,1fr)}}.met{{min-height:78px;padding:12px 7px;border-right:1px solid #d8e7fb;display:flex;align-items:center;justify-content:center;gap:8px;text-align:center}}.met:last-child{{border:0}}.mi{{font-size:25px;color:#0057d9;font-weight:1000}}.mt{{font-size:11px;font-weight:900;color:#061b44;text-transform:uppercase}}.mv{{font-size:16px;font-weight:1000;color:#0057d9;margin-top:2px}}.mn{{font-size:10px;font-weight:800;color:#465b78}}
.bens{{border-top:1px solid #d8e7fb;padding:13px 15px;display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}.ben{{font-size:11px;font-weight:800;color:#061b44;display:flex;gap:7px}}.ben b{{color:#0047b8;font-size:12px}}.bi{{font-size:18px;color:#0057d9;font-weight:1000}}
.side{{display:flex;flex-direction:column;gap:13px}}.sh{{background:#0057d9;color:white;padding:13px 15px;font-size:15px;font-weight:1000}}.row{{display:grid;grid-template-columns:28px 1fr auto;gap:7px;align-items:center;padding:9px 12px;border-bottom:1px solid #e7eef8;font-size:12px;font-weight:800;color:#061b44}}.rv{{font-weight:1000;color:#071124;text-align:right;white-space:nowrap}}.ri{{color:#0057d9;text-align:center}}
.price{{background:#fff;border:1px solid #d8e7fb;border-radius:14px;padding:24px 16px;text-align:center;box-shadow:0 10px 26px rgba(0,42,110,.08)}}.pt{{font-weight:1000;font-size:16px}}.pv{{font-weight:1000;font-size:34px;margin:10px 0 4px}}.pn{{font-size:12px;font-weight:800;color:#465b78}}
.btn{{border-radius:10px;padding:14px;text-align:center;font-weight:1000;font-size:15px;color:white;box-shadow:0 8px 18px rgba(0,42,110,.12)}}.blue{{background:#003c96}}.orange{{background:#f58220}}
</style>
</head>
<body>
<div class="app">
 <div class="top">
  <div><div class="t1">CONFIGURATORE PORTE AUTOMATICHE SCORREVOLI</div><div class="t2">Progetta la tua porta automatica in pochi passaggi</div></div>
  <div class="brand"><div><span class="badge">EN16005</span> <span style="font-size:12px">Conforme alla norma europea</span></div><div class="ses">sesamo</div></div>
 </div>
 <div class="steps"><div class="step"><div class="dot">✓</div>TIPOLOGIA</div><div class="step active"><div class="dot">2</div>DIMENSIONI</div><div class="step"><div class="dot">3</div>ACCESSORI</div><div class="step"><div class="dot">4</div>FINITURE</div><div class="step"><div class="dot">5</div>RIEPILOGO</div></div>
 <div class="grid">
  <div class="card">
   <div class="head">{titolo_schema}</div>
   <div class="drow"><div class="dbox"><canvas id="frontCanvas" width="920" height="440"></canvas></div><div class="sez"><div class="lab">SEZIONE TRAVERSA</div><canvas id="sectionCanvas" width="210" height="310"></canvas></div></div>
   <div class="metrics">
    <div class="met"><div class="mi">↔</div><div><div class="mt">Tipologia</div><div class="mv">{ante_numero}</div><div class="mn">Scorrevole</div></div></div>
    <div class="met"><div class="mi">↕</div><div><div class="mt">Luce netta</div><div class="mv">{luce} mm</div><div class="mn">Passaggio utile</div></div></div>
    <div class="met"><div class="mi">⤢</div><div><div class="mt">Altezza luce</div><div class="mv">{altezza} mm</div><div class="mn">Personalizzata</div></div></div>
    <div class="met"><div class="mi">⟷</div><div><div class="mt">Traversa</div><div class="mv">{traversa_mm} mm</div><div class="mn">Lunghezza totale</div></div></div>
    <div class="met"><div class="mi">▣</div><div><div class="mt">Portata</div><div class="mv">120 kg</div><div class="mn">Per anta</div></div></div>
    <div class="met"><div class="mi">◴</div><div><div class="mt">Velocità</div><div class="mv">0,6 m/s</div><div class="mn">Regolabile</div></div></div>
   </div>
   <div class="bens"><div class="ben"><div class="bi">▣</div><div><b>Conformità EN16005</b><br>Sicurezza garantita</div></div><div class="ben"><div class="bi">◇</div><div><b>Qualità Sesamo</b><br>Componenti originali</div></div><div class="ben"><div class="bi">♙</div><div><b>Assistenza prioritaria</b><br>Intervento entro 48 ore</div></div><div class="ben"><div class="bi">⬟</div><div><b>Garanzia 24 mesi</b><br>Su tutti i componenti</div></div><div class="ben"><div class="bi">⚙</div><div><b>SA-TEC</b><br>Progettazione e posa</div></div></div>
  </div>
  <div class="side">
   <div class="card"><div class="sh">RIEPILOGO CONFIGURAZIONE</div>
    <div class="row"><div class="ri">↔</div><div>Tipologia</div><div class="rv">{ante_numero}</div></div><div class="row"><div class="ri">↕</div><div>Luce netta passaggio</div><div class="rv">{luce} mm</div></div><div class="row"><div class="ri">⤢</div><div>Altezza luce</div><div class="rv">{altezza} mm</div></div><div class="row"><div class="ri">⟷</div><div>Lunghezza traversa</div><div class="rv">{traversa_mm} mm</div></div><div class="row"><div class="ri">▣</div><div>Portata</div><div class="rv">120 kg</div></div><div class="row"><div class="ri">◴</div><div>Velocità</div><div class="rv">0,6 m/s</div></div><div class="row"><div class="ri">🔒</div><div>Sblocco</div><div class="rv">Interno a chiave</div></div><div class="row"><div class="ri">☷</div><div>Radar</div><div class="rv">2 sensori</div></div><div class="row"><div class="ri">✓</div><div>Normativa</div><div class="rv">EN16005</div></div>
   </div>
   <div class="price"><div class="pt">TOTALE PREVENTIVO</div><div class="pv">{totale_demo}</div><div class="pn">IVA ESCLUSA</div></div>
   <div class="btn blue">▣ SALVA PREVENTIVO</div><div class="btn orange">▤ ESPORTA PDF</div>
  </div>
 </div>
</div>
<script>
const dueAnte={due_ante_js}, luce={luce}, altezza={altezza}, traversaMm={traversa_mm};
function rr(c,x,y,w,h,r,f,s){{c.beginPath();c.moveTo(x+r,y);c.lineTo(x+w-r,y);c.quadraticCurveTo(x+w,y,x+w,y+r);c.lineTo(x+w,y+h-r);c.quadraticCurveTo(x+w,y+h,x+w-r,y+h);c.lineTo(x+r,y+h);c.quadraticCurveTo(x,y+h,x,y+h-r);c.lineTo(x,y+r);c.quadraticCurveTo(x,y,x+r,y);c.closePath();if(f)c.fill();if(s)c.stroke();}}
function line(c,x1,y1,x2,y2,col,w){{c.strokeStyle=col;c.lineWidth=w;c.beginPath();c.moveTo(x1,y1);c.lineTo(x2,y2);c.stroke();}}
function txt(c,t,x,y,s,col,a="center",w="900"){{c.font=w+" "+s+"px Arial";c.fillStyle=col;c.textAlign=a;c.fillText(t,x,y);}}
function arrow(c,x1,y1,x2,y2,col){{line(c,x1,y1,x2,y2,col,7);let a=Math.atan2(y2-y1,x2-x1);c.fillStyle=col;c.beginPath();c.moveTo(x2,y2);c.lineTo(x2-16*Math.cos(a-Math.PI/6),y2-16*Math.sin(a-Math.PI/6));c.lineTo(x2-16*Math.cos(a+Math.PI/6),y2-16*Math.sin(a+Math.PI/6));c.closePath();c.fill();}}
function glass(c,x,y,w,h){{let g=c.createLinearGradient(x,y,x+w,y+h);g.addColorStop(0,"rgba(255,255,255,.96)");g.addColorStop(.45,"rgba(205,238,255,.66)");g.addColorStop(1,"rgba(150,215,255,.75)");c.fillStyle=g;c.strokeStyle="#1d8bff";c.lineWidth=3;rr(c,x,y,w,h,4,1,1);line(c,x+25,y+12,x+w-35,y+h-38,"rgba(255,255,255,.8)",2);line(c,x+60,y+12,x+w-10,y+h-85,"rgba(255,255,255,.55)",2);}}
function front(){{let c=document.getElementById("frontCanvas").getContext("2d");c.clearRect(0,0,920,440);for(let x=20;x<900;x+=35)line(c,x,20,x,420,"rgba(0,87,217,.035)",1);for(let y=20;y<420;y+=35)line(c,20,y,900,y,"rgba(0,87,217,.035)",1);let fx=135,fy=112,fw=610,fh=235,rx=92,ry=54,rw=700,rh=50;c.strokeStyle="#222";c.lineWidth=3;rr(c,fx,fy,fw,fh,5,0,1);let rg=c.createLinearGradient(rx,ry,rx,ry+rh);rg.addColorStop(0,"#eee");rg.addColorStop(.25,"#aaa");rg.addColorStop(.55,"#f6f6f6");rg.addColorStop(1,"#777");c.fillStyle=rg;c.strokeStyle="#222";c.lineWidth=2;rr(c,rx,ry,rw,rh,3,1,1);line(c,rx+20,ry+17,rx+rw-20,ry+17,"#252525",3);line(c,rx+20,ry+32,rx+rw-20,ry+32,"#555",2);txt(c,"sesamo",rx+55,ry+20,12,"#0057d9");txt(c,"SA-TEC",rx+55,ry+38,12,"#0057d9");function pul(x){{c.fillStyle="#111";c.beginPath();c.arc(x,ry+25,10,0,Math.PI*2);c.fill();c.fillStyle="#666";c.beginPath();c.arc(x,ry+25,4,0,Math.PI*2);c.fill();}}pul(250);pul(290);pul(515);pul(555);c.fillStyle="#111";rr(c,646,ry+8,62,34,4,1,0);c.fillStyle="#333";rr(c,710,ry+13,40,24,4,1,0);txt(c,"MOT",731,ry+30,10,"#fff");function tro(x){{c.fillStyle="#1a1a1a";rr(c,x,ry+40,44,11,3,1,0);line(c,x+10,ry+51,x+10,fy+13,"#222",2);line(c,x+34,ry+51,x+34,fy+13,"#222",2);}}if(dueAnte){{tro(285);tro(535);glass(c,195,125,245,210);glass(c,440,125,245,210);line(c,440,125,440,335,"#003c96",4);arrow(c,420,235,355,235,"#148c2e");arrow(c,460,235,525,235,"#148c2e");}}else{{tro(365);tro(565);glass(c,315,125,300,210);arrow(c,450,235,560,235,"#148c2e");}}txt(c,"APERTURA",465,265,13,"#148c2e");txt(c,"AUTOMATICA",465,282,13,"#148c2e");c.fillStyle="#d8d8d8";c.fillRect(fx-12,fy,12,fh);c.fillRect(fx+fw,fy,12,fh);c.fillRect(fx-35,fy+fh,fw+70,10);line(c,fx-45,fy+fh+14,fx+fw+45,fy+fh+14,"#9a9a9a",3);line(c,70,fy,70,fy+fh,"#003c96",2);line(c,60,fy,80,fy,"#003c96",2);line(c,60,fy+fh,80,fy+fh,"#003c96",2);txt(c,"ALTEZZA LUCE",62,230,11,"#003c96","right");txt(c,altezza+" mm",62,250,12,"#003c96","right","1000");line(c,835,fy-48,835,fy+fh,"#003c96",2);line(c,824,fy-48,846,fy-48,"#003c96",2);line(c,824,fy+fh,846,fy+fh,"#003c96",2);txt(c,"ALTEZZA TOTALE",850,230,11,"#003c96","left");txt(c,(altezza+100)+" mm",850,250,12,"#003c96","left","1000");line(c,fx+120,375,fx+fw-120,375,"#003c96",2);line(c,fx+120,366,fx+120,384,"#003c96",2);line(c,fx+fw-120,366,fx+fw-120,384,"#003c96",2);txt(c,"LUCE NETTA DI PASSAGGIO",440,370,11,"#003c96");txt(c,luce+" mm",440,393,13,"#003c96","center","1000");line(c,fx,415,fx+fw,415,"#003c96",2);line(c,fx,406,fx,424,"#003c96",2);line(c,fx+fw,406,fx+fw,424,"#003c96",2);txt(c,"LUNGHEZZA TRAVERSA",440,410,11,"#003c96");txt(c,traversaMm+" mm",440,433,13,"#003c96","center","1000");}}
function section(){{let c=document.getElementById("sectionCanvas").getContext("2d");c.clearRect(0,0,210,310);txt(c,"140 mm",105,25,13,"#003c96");line(c,55,34,155,34,"#003c96",2);line(c,55,26,55,42,"#003c96",2);line(c,155,26,155,42,"#003c96",2);c.strokeStyle="#777";c.lineWidth=2;c.fillStyle="#f4f4f4";rr(c,65,58,80,95,8,1,1);c.fillStyle="#dadada";rr(c,75,68,60,75,5,1,1);c.fillStyle="#111";rr(c,86,78,38,55,6,1,0);c.fillStyle="#333";c.beginPath();c.arc(105,105,16,0,Math.PI*2);c.fill();c.fillStyle="#777";c.beginPath();c.arc(105,105,7,0,Math.PI*2);c.fill();let g=c.createLinearGradient(98,153,118,270);g.addColorStop(0,"rgba(205,238,255,.8)");g.addColorStop(1,"rgba(130,205,255,.65)");c.fillStyle=g;c.strokeStyle="#1d8bff";c.lineWidth=2;c.fillRect(99,153,12,105);c.strokeRect(99,153,12,105);txt(c,"160 mm",32,112,12,"#003c96");line(c,42,58,42,153,"#003c96",2);line(c,33,58,51,58,"#003c96",2);line(c,33,153,51,153,"#003c96",2);txt(c,"185 mm",174,120,12,"#003c96");line(c,165,58,165,173,"#003c96",2);line(c,156,58,174,58,"#003c96",2);line(c,156,173,174,173,"#003c96",2);txt(c,"10 mm",155,216,12,"#003c96","left");txt(c,"40 mm",105,282,12,"#003c96");line(c,85,268,125,268,"#003c96",2);line(c,85,260,85,276,"#003c96",2);line(c,125,260,125,276,"#003c96",2);}}
front(); section();
</script>
</body>
</html>
"""



# =========================
# V504 - RENDER TECNICO DEFINITIVO SA-TEC
# Anta più larga + sezione traversa rettangolare 115 x 155 mm, fissaggio 80 mm
# =========================
def disegno_porta_v504(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600

    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200

    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo_schema = "SCHEMA TECNICO PORTA SCORREVOLE A 2 ANTE" if due_ante else "SCHEMA TECNICO PORTA SCORREVOLE A 1 ANTA"
    due_ante_js = "true" if due_ante else "false"

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
html,body{{
    margin:0;
    padding:0;
    font-family:Arial, Helvetica, sans-serif;
    background:#fff;
    color:#071124;
}}
.v504-box{{
    width:100%;
    background:#fff;
    border:1px solid #D8E7FB;
    border-radius:18px;
    overflow:hidden;
    box-shadow:0 10px 26px rgba(0,42,110,.08);
}}
.v504-head{{
    padding:14px 18px;
    display:flex;
    justify-content:space-between;
    align-items:center;
}}
.v504-title{{
    color:#0047B8;
    font-size:22px;
    font-weight:1000;
}}
.v504-badge{{
    background:#0057D9;
    color:#fff;
    padding:8px 14px;
    border-radius:8px;
    font-size:13px;
    font-weight:1000;
}}
.v504-main{{
    display:grid;
    grid-template-columns:minmax(0,1fr) 280px;
    gap:18px;
    padding:0 18px 14px 18px;
}}
.v504-panel{{
    background:#fff;
    border:1px solid #EDF3FC;
    border-radius:14px;
    min-height:430px;
    padding:6px;
}}
.v504-section{{
    background:#fff;
    border-left:1px solid #D8E7FB;
    min-height:430px;
    padding:6px;
}}
.v504-label{{
    display:inline-block;
    background:#0057D9;
    color:#fff;
    font-size:13px;
    font-weight:1000;
    padding:8px 12px;
    border-radius:6px;
    margin:0 0 8px 0;
}}
canvas{{
    width:100%;
    display:block;
}}
#frontCanvasV504{{
    height:410px;
}}
#sectionCanvasV504{{
    height:380px;
}}
.v504-metrics{{
    border-top:1px solid #D8E7FB;
    background:#FBFDFF;
    display:grid;
    grid-template-columns:repeat(6,1fr);
}}
.v504-metric{{
    padding:12px 8px;
    border-right:1px solid #D8E7FB;
    min-height:72px;
    text-align:center;
    color:#06245C;
    font-weight:900;
}}
.v504-metric:last-child{{border-right:0}}
.v504-metric b{{
    display:block;
    color:#0057D9;
    font-size:17px;
    margin-top:4px;
}}
.v504-metric small{{
    display:block;
    color:#465B78;
    font-size:10px;
    margin-top:3px;
}}
</style>
</head>
<body>
<div class="v504-box">
    <div class="v504-head">
        <div class="v504-title">{titolo_schema}</div>
        <div class="v504-badge">EN16005</div>
    </div>

    <div class="v504-main">
        <div class="v504-panel">
            <div class="v504-label">VISTA FRONTALE</div>
            <canvas id="frontCanvasV504" width="980" height="430"></canvas>
        </div>
        <div class="v504-section">
            <div class="v504-label">SEZIONE TRAVERSA</div>
            <canvas id="sectionCanvasV504" width="300" height="390"></canvas>
        </div>
    </div>

    <div class="v504-metrics">
        <div class="v504-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
        <div class="v504-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
        <div class="v504-metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div>
        <div class="v504-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        <div class="v504-metric">Sezione<b>115 × 155</b><small>mm</small></div>
        <div class="v504-metric">Fissaggio<b>80 mm</b><small>Interasse</small></div>
    </div>
</div>

<script>
const dueAnte = {due_ante_js};
const luce = {luce};
const altezza = {altezza};
const traversaMm = {int(traversa*1000)};

function rr(ctx,x,y,w,h,r,fill,stroke){{
    ctx.beginPath();
    ctx.moveTo(x+r,y);
    ctx.lineTo(x+w-r,y);
    ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r);
    ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h);
    ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r);
    ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath();
    if(fill) ctx.fill();
    if(stroke) ctx.stroke();
}}
function line(ctx,x1,y1,x2,y2,c,w){{
    ctx.strokeStyle=c; ctx.lineWidth=w; ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
}}
function txt(ctx,t,x,y,s,c,a="center",w="900"){{
    ctx.font=w+" "+s+"px Arial"; ctx.fillStyle=c; ctx.textAlign=a; ctx.fillText(t,x,y);
}}
function arrow(ctx,x1,y1,x2,y2,c){{
    line(ctx,x1,y1,x2,y2,c,7);
    const a=Math.atan2(y2-y1,x2-x1);
    ctx.fillStyle=c;
    ctx.beginPath();
    ctx.moveTo(x2,y2);
    ctx.lineTo(x2-16*Math.cos(a-Math.PI/6),y2-16*Math.sin(a-Math.PI/6));
    ctx.lineTo(x2-16*Math.cos(a+Math.PI/6),y2-16*Math.sin(a+Math.PI/6));
    ctx.closePath(); ctx.fill();
}}
function glass(ctx,x,y,w,h){{
    const g=ctx.createLinearGradient(x,y,x+w,y+h);
    g.addColorStop(0,"rgba(255,255,255,.96)");
    g.addColorStop(.45,"rgba(205,238,255,.62)");
    g.addColorStop(1,"rgba(145,215,255,.74)");
    ctx.fillStyle=g; ctx.strokeStyle="#1D8BFF"; ctx.lineWidth=3;
    rr(ctx,x,y,w,h,4,true,true);
    line(ctx,x+30,y+12,x+w-38,y+h-36,"rgba(255,255,255,.82)",2);
    line(ctx,x+75,y+12,x+w-12,y+h-90,"rgba(255,255,255,.55)",2);
}}
function drawFront(){{
    const c=document.getElementById("frontCanvasV504");
    const ctx=c.getContext("2d");
    ctx.clearRect(0,0,c.width,c.height);

    const fx=110, fy=112, fw=735, fh=235;
    const railX=70, railY=55, railW=810, railH=50;

    // traversa lunga e rettangolare
    const rg=ctx.createLinearGradient(railX,railY,railX,railY+railH);
    rg.addColorStop(0,"#eeeeee");
    rg.addColorStop(.28,"#b9b9b9");
    rg.addColorStop(.58,"#f7f7f7");
    rg.addColorStop(1,"#8c8c8c");
    ctx.fillStyle=rg; ctx.strokeStyle="#222"; ctx.lineWidth=2;
    rr(ctx,railX,railY,railW,railH,3,true,true);

    line(ctx,railX+22,railY+17,railX+railW-22,railY+17,"#222",3);
    line(ctx,railX+22,railY+33,railX+railW-22,railY+33,"#555",2);
    txt(ctx,"sesamo",railX+70,railY+20,12,"#0057D9","center","900");
    txt(ctx,"SA-TEC",railX+70,railY+39,13,"#0057D9","center","1000");

    // motore
    ctx.fillStyle="#111"; rr(ctx,railX+railW-135,railY+8,70,34,4,true,false);
    ctx.fillStyle="#333"; rr(ctx,railX+railW-66,railY+13,36,24,4,true,false);
    txt(ctx,"MOT",railX+railW-48,railY+30,10,"#FFF");

    // pulegge / carrelli
    function pulley(x){{
        ctx.fillStyle="#111"; ctx.beginPath(); ctx.arc(x,railY+25,10,0,Math.PI*2); ctx.fill();
        ctx.fillStyle="#777"; ctx.beginPath(); ctx.arc(x,railY+25,4,0,Math.PI*2); ctx.fill();
    }}
    [250,290,500,540,680].forEach(pulley);

    function trolley(x){{
        ctx.fillStyle="#222"; rr(ctx,x,railY+42,48,11,3,true,false);
        line(ctx,x+10,railY+53,x+10,fy+14,"#222",2);
        line(ctx,x+38,railY+53,x+38,fy+14,"#222",2);
    }}

    // telaio e ante più larghe
    ctx.strokeStyle="#222"; ctx.lineWidth=3; rr(ctx,fx,fy,fw,fh,5,false,true);

    if(dueAnte){{
        trolley(300); trolley(610);
        glass(ctx,170,125,335,210);
        glass(ctx,505,125,335,210);
        line(ctx,505,125,505,335,"#003C96",4);
        arrow(ctx,485,235,410,235,"#148C2E");
        arrow(ctx,525,235,600,235,"#148C2E");
        txt(ctx,"APERTURA",505,266,13,"#148C2E");
        txt(ctx,"AUTOMATICA",505,283,13,"#148C2E");
    }} else {{
        trolley(390); trolley(650);
        glass(ctx,285,125,410,210);
        arrow(ctx,470,235,625,235,"#148C2E");
        txt(ctx,"APERTURA",505,266,13,"#148C2E");
        txt(ctx,"AUTOMATICA",505,283,13,"#148C2E");
    }}

    // montanti e pavimento
    ctx.fillStyle="#D8D8D8";
    ctx.fillRect(fx-12,fy,12,fh);
    ctx.fillRect(fx+fw,fy,12,fh);
    ctx.fillRect(fx-40,fy+fh,fw+80,10);
    line(ctx,fx-50,fy+fh+14,fx+fw+50,fy+fh+14,"#9A9A9A",3);

    // quote verticali
    line(ctx,55,fy,55,fy+fh,"#003C96",2);
    line(ctx,45,fy,65,fy,"#003C96",2);
    line(ctx,45,fy+fh,65,fy+fh,"#003C96",2);
    txt(ctx,"ALTEZZA LUCE",47,225,11,"#003C96","right");
    txt(ctx,altezza+" mm",47,245,12,"#003C96","right","1000");

    line(ctx,920,fy-48,920,fy+fh,"#003C96",2);
    line(ctx,909,fy-48,931,fy-48,"#003C96",2);
    line(ctx,909,fy+fh,931,fy+fh,"#003C96",2);
    txt(ctx,"ALTEZZA TOTALE",935,225,11,"#003C96","left");
    txt(ctx,(altezza+100)+" mm",935,245,12,"#003C96","left","1000");

    // quote orizzontali
    line(ctx,fx+160,378,fx+fw-160,378,"#003C96",2);
    line(ctx,fx+160,368,fx+160,388,"#003C96",2);
    line(ctx,fx+fw-160,368,fx+fw-160,388,"#003C96",2);
    txt(ctx,"LUCE NETTA DI PASSAGGIO",505,372,11,"#003C96");
    txt(ctx,luce+" mm",505,398,13,"#003C96","center","1000");

    line(ctx,fx,416,fx+fw,416,"#003C96",2);
    line(ctx,fx,406,fx,426,"#003C96",2);
    line(ctx,fx+fw,406,fx+fw,426,"#003C96",2);
    txt(ctx,"LUNGHEZZA TRAVERSA",505,410,11,"#003C96");
    txt(ctx,traversaMm+" mm",505,432,13,"#003C96","center","1000");
}}
function drawSection(){{
    const c=document.getElementById("sectionCanvasV504");
    const ctx=c.getContext("2d");
    ctx.clearRect(0,0,c.width,c.height);

    // quote 115 x 155 + fissaggio 80
    txt(ctx,"115 mm",150,33,16,"#003C96","center","1000");
    line(ctx,88,45,212,45,"#003C96",2);
    line(ctx,88,34,88,56,"#003C96",2);
    line(ctx,212,34,212,56,"#003C96",2);

    // corpo traversa rettangolare
    const x=92, y=70, w=116, h=155;
    ctx.fillStyle="#F7F7F7";
    ctx.strokeStyle="#111";
    ctx.lineWidth=2.5;
    rr(ctx,x,y,w,h,8,true,true);

    // profilo interno tipo estruso
    ctx.strokeStyle="#444";
    ctx.lineWidth=2;
    rr(ctx,x+10,y+10,w-20,h-20,5,false,true);
    line(ctx,x+10,y+45,x+w-10,y+45,"#666",2);
    line(ctx,x+10,y+108,x+w-10,y+108,"#666",2);
    line(ctx,x+26,y+10,x+26,y+h-10,"#666",1.6);
    line(ctx,x+w-26,y+10,x+w-26,y+h-10,"#666",1.6);

    // fissaggio 80 mm
    ctx.fillStyle="#DADADA";
    ctx.strokeStyle="#111";
    rr(ctx,x+18,y+18,80,18,3,true,true);
    txt(ctx,"fiss. 80",x+58,y+31,9,"#111","center","900");

    // carrello / ruota
    ctx.fillStyle="#111";
    rr(ctx,x+36,y+58,48,42,6,true,false);
    ctx.fillStyle="#333";
    ctx.beginPath(); ctx.arc(x+60,y+79,18,0,Math.PI*2); ctx.fill();
    ctx.fillStyle="#8A8A8A";
    ctx.beginPath(); ctx.arc(x+60,y+79,7,0,Math.PI*2); ctx.fill();

    // supporto anta
    ctx.fillStyle="#111";
    rr(ctx,x+48,y+105,24,42,4,true,false);
    ctx.fillStyle="#1D8BFF";
    ctx.globalAlpha=.22;
    ctx.fillRect(x+50,y+150,20,110);
    ctx.globalAlpha=1;
    ctx.strokeStyle="#1D8BFF";
    ctx.strokeRect(x+50,y+150,20,110);

    // quota altezza 155
    line(ctx,235,y,235,y+h,"#003C96",2);
    line(ctx,224,y,246,y,"#003C96",2);
    line(ctx,224,y+h,246,y+h,"#003C96",2);
    txt(ctx,"155 mm",254,y+83,16,"#003C96","left","1000");

    // quota lato sinistra 155
    line(ctx,65,y,65,y+h,"#003C96",2);
    line(ctx,54,y,76,y,"#003C96",2);
    line(ctx,54,y+h,76,y+h,"#003C96",2);
    ctx.save();
    ctx.translate(36,y+88);
    ctx.rotate(-Math.PI/2);
    txt(ctx,"155 mm",0,0,15,"#003C96","center","1000");
    ctx.restore();

    // quota vetro 40
    txt(ctx,"40 mm",150,352,16,"#003C96","center","1000");
    line(ctx,130,332,170,332,"#003C96",2);
    line(ctx,130,322,130,342,"#003C96",2);
    line(ctx,170,322,170,342,"#003C96",2);
}}
drawFront();
drawSection();
</script>
</body>
</html>
"""




# =========================
# V505 - RENDER DEFINITIVO SOLO AUTOMAZIONE
# Tolta sezione traversa. Disegno automazione/porta più largo e pulito.
# =========================
def disegno_porta_v505(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600

    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200

    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo_schema = "SCHEMA TECNICO AUTOMAZIONE SCORREVOLE A 2 ANTE" if due_ante else "SCHEMA TECNICO AUTOMAZIONE SCORREVOLE A 1 ANTA"
    due_ante_js = "true" if due_ante else "false"

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
html,body{{
    margin:0;
    padding:0;
    font-family:Arial, Helvetica, sans-serif;
    background:#fff;
    color:#071124;
}}
.v505-box{{
    width:100%;
    background:#fff;
    border:1px solid #D8E7FB;
    border-radius:18px;
    overflow:hidden;
    box-shadow:0 10px 26px rgba(0,42,110,.08);
}}
.v505-head{{
    padding:14px 18px;
    display:flex;
    justify-content:space-between;
    align-items:center;
}}
.v505-title{{
    color:#0047B8;
    font-size:22px;
    font-weight:1000;
}}
.v505-badge{{
    background:#0057D9;
    color:#fff;
    padding:8px 14px;
    border-radius:8px;
    font-size:13px;
    font-weight:1000;
}}
.v505-panel{{
    background:#fff;
    border-top:1px solid #EDF3FC;
    padding:10px 18px 14px 18px;
}}
.v505-label{{
    display:inline-block;
    background:#0057D9;
    color:#fff;
    font-size:13px;
    font-weight:1000;
    padding:8px 12px;
    border-radius:6px;
    margin:0 0 8px 0;
}}
canvas{{
    width:100%;
    display:block;
}}
#frontCanvasV505{{
    height:455px;
    border:1px solid #EDF3FC;
    border-radius:14px;
    background:#fff;
}}
.v505-metrics{{
    border-top:1px solid #D8E7FB;
    background:#FBFDFF;
    display:grid;
    grid-template-columns:repeat(6,1fr);
}}
.v505-metric{{
    padding:12px 8px;
    border-right:1px solid #D8E7FB;
    min-height:72px;
    text-align:center;
    color:#06245C;
    font-weight:900;
}}
.v505-metric:last-child{{border-right:0}}
.v505-metric b{{
    display:block;
    color:#0057D9;
    font-size:17px;
    margin-top:4px;
}}
.v505-metric small{{
    display:block;
    color:#465B78;
    font-size:10px;
    margin-top:3px;
}}
</style>
</head>
<body>
<div class="v505-box">
    <div class="v505-head">
        <div class="v505-title">{titolo_schema}</div>
        <div class="v505-badge">EN16005</div>
    </div>

    <div class="v505-panel">
        <div class="v505-label">VISTA FRONTALE AUTOMAZIONE</div>
        <canvas id="frontCanvasV505" width="1180" height="455"></canvas>
    </div>

    <div class="v505-metrics">
        <div class="v505-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
        <div class="v505-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
        <div class="v505-metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div>
        <div class="v505-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        <div class="v505-metric">Normativa<b>EN16005</b><small>Sicurezza</small></div>
        <div class="v505-metric">Sistema<b>PW100</b><small>Sesamo</small></div>
    </div>
</div>

<script>
const dueAnte = {due_ante_js};
const luce = {luce};
const altezza = {altezza};
const traversaMm = {int(traversa*1000)};

function rr(ctx,x,y,w,h,r,fill,stroke){{
    ctx.beginPath();
    ctx.moveTo(x+r,y);
    ctx.lineTo(x+w-r,y);
    ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r);
    ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h);
    ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r);
    ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath();
    if(fill) ctx.fill();
    if(stroke) ctx.stroke();
}}
function line(ctx,x1,y1,x2,y2,c,w){{
    ctx.strokeStyle=c; ctx.lineWidth=w; ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
}}
function txt(ctx,t,x,y,s,c,a="center",w="900"){{
    ctx.font=w+" "+s+"px Arial"; ctx.fillStyle=c; ctx.textAlign=a; ctx.fillText(t,x,y);
}}
function arrow(ctx,x1,y1,x2,y2,c){{
    line(ctx,x1,y1,x2,y2,c,7);
    const a=Math.atan2(y2-y1,x2-x1);
    ctx.fillStyle=c;
    ctx.beginPath();
    ctx.moveTo(x2,y2);
    ctx.lineTo(x2-16*Math.cos(a-Math.PI/6),y2-16*Math.sin(a-Math.PI/6));
    ctx.lineTo(x2-16*Math.cos(a+Math.PI/6),y2-16*Math.sin(a+Math.PI/6));
    ctx.closePath(); ctx.fill();
}}
function glass(ctx,x,y,w,h){{
    const g=ctx.createLinearGradient(x,y,x+w,y+h);
    g.addColorStop(0,"rgba(255,255,255,.96)");
    g.addColorStop(.45,"rgba(205,238,255,.62)");
    g.addColorStop(1,"rgba(145,215,255,.74)");
    ctx.fillStyle=g; ctx.strokeStyle="#1D8BFF"; ctx.lineWidth=3;
    rr(ctx,x,y,w,h,4,true,true);
    line(ctx,x+30,y+12,x+w-38,y+h-36,"rgba(255,255,255,.82)",2);
    line(ctx,x+75,y+12,x+w-12,y+h-90,"rgba(255,255,255,.55)",2);
}}
function drawFront(){{
    const c=document.getElementById("frontCanvasV505");
    const ctx=c.getContext("2d");
    ctx.clearRect(0,0,c.width,c.height);

    const fx=120, fy=118, fw=905, fh=235;
    const railX=80, railY=56, railW=985, railH=52;

    // traversa lunga e rettangolare automazione
    const rg=ctx.createLinearGradient(railX,railY,railX,railY+railH);
    rg.addColorStop(0,"#eeeeee");
    rg.addColorStop(.28,"#b9b9b9");
    rg.addColorStop(.58,"#f7f7f7");
    rg.addColorStop(1,"#8c8c8c");
    ctx.fillStyle=rg; ctx.strokeStyle="#222"; ctx.lineWidth=2;
    rr(ctx,railX,railY,railW,railH,3,true,true);

    // dettagli interni
    line(ctx,railX+22,railY+17,railX+railW-22,railY+17,"#222",3);
    line(ctx,railX+22,railY+34,railX+railW-22,railY+34,"#555",2);
    txt(ctx,"sesamo",railX+72,railY+21,12,"#0057D9","center","900");
    txt(ctx,"SA-TEC",railX+72,railY+40,13,"#0057D9","center","1000");

    // motore
    ctx.fillStyle="#111"; rr(ctx,railX+railW-160,railY+8,84,36,4,true,false);
    ctx.fillStyle="#333"; rr(ctx,railX+railW-76,railY+13,42,26,4,true,false);
    txt(ctx,"MOT",railX+railW-55,railY+31,10,"#FFF");

    // pulegge e carrelli
    function pulley(x){{
        ctx.fillStyle="#111"; ctx.beginPath(); ctx.arc(x,railY+26,10,0,Math.PI*2); ctx.fill();
        ctx.fillStyle="#777"; ctx.beginPath(); ctx.arc(x,railY+26,4,0,Math.PI*2); ctx.fill();
    }}
    [275,320,545,590,760,805].forEach(pulley);

    function trolley(x){{
        ctx.fillStyle="#222"; rr(ctx,x,railY+44,52,11,3,true,false);
        line(ctx,x+11,railY+55,x+11,fy+14,"#222",2);
        line(ctx,x+41,railY+55,x+41,fy+14,"#222",2);
    }}

    // telaio largo e ante larghe
    ctx.strokeStyle="#222"; ctx.lineWidth=3; rr(ctx,fx,fy,fw,fh,5,false,true);

    if(dueAnte){{
        trolley(355); trolley(700);
        glass(ctx,190,132,415,205);
        glass(ctx,605,132,415,205);
        line(ctx,605,132,605,337,"#003C96",4);
        arrow(ctx,585,238,500,238,"#148C2E");
        arrow(ctx,625,238,710,238,"#148C2E");
        txt(ctx,"APERTURA",605,270,13,"#148C2E");
        txt(ctx,"AUTOMATICA",605,287,13,"#148C2E");
    }} else {{
        trolley(450); trolley(735);
        glass(ctx,330,132,520,205);
        arrow(ctx,565,238,735,238,"#148C2E");
        txt(ctx,"APERTURA",610,270,13,"#148C2E");
        txt(ctx,"AUTOMATICA",610,287,13,"#148C2E");
    }}

    // montanti e pavimento
    ctx.fillStyle="#D8D8D8";
    ctx.fillRect(fx-12,fy,12,fh);
    ctx.fillRect(fx+fw,fy,12,fh);
    ctx.fillRect(fx-45,fy+fh,fw+90,10);
    line(ctx,fx-55,fy+fh+14,fx+fw+55,fy+fh+14,"#9A9A9A",3);

    // quote verticali
    line(ctx,58,fy,58,fy+fh,"#003C96",2);
    line(ctx,48,fy,68,fy,"#003C96",2);
    line(ctx,48,fy+fh,68,fy+fh,"#003C96",2);
    txt(ctx,"ALTEZZA LUCE",50,225,11,"#003C96","right");
    txt(ctx,altezza+" mm",50,245,12,"#003C96","right","1000");

    line(ctx,1110,fy-50,1110,fy+fh,"#003C96",2);
    line(ctx,1099,fy-50,1121,fy-50,"#003C96",2);
    line(ctx,1099,fy+fh,1121,fy+fh,"#003C96",2);
    txt(ctx,"ALTEZZA TOTALE",1126,225,11,"#003C96","left");
    txt(ctx,(altezza+100)+" mm",1126,245,12,"#003C96","left","1000");

    // quote orizzontali
    line(ctx,fx+220,385,fx+fw-220,385,"#003C96",2);
    line(ctx,fx+220,375,fx+220,395,"#003C96",2);
    line(ctx,fx+fw-220,375,fx+fw-220,395,"#003C96",2);
    txt(ctx,"LUCE NETTA DI PASSAGGIO",590,379,11,"#003C96");
    txt(ctx,luce+" mm",590,406,13,"#003C96","center","1000");

    line(ctx,fx,428,fx+fw,428,"#003C96",2);
    line(ctx,fx,418,fx,438,"#003C96",2);
    line(ctx,fx+fw,418,fx+fw,438,"#003C96",2);
    txt(ctx,"LUNGHEZZA TRAVERSA",590,422,11,"#003C96");
    txt(ctx,traversaMm+" mm",590,448,13,"#003C96","center","1000");
}}
drawFront();
</script>
</body>
</html>
"""




# =========================
# V600 - HEADER DEFINITIVO SA-TEC
# =========================
def v600_style():
    st.markdown("""
    <style>
    .stApp {
        background:linear-gradient(180deg,#F3F8FF 0%,#FFFFFF 70%)!important;
    }
    .block-container {
        padding-top:0.8rem!important;
    }
    .v600-main-header {
        background:linear-gradient(90deg,#002B67 0%,#0057D9 65%,#003C96 100%);
        border-radius:24px;
        padding:22px 26px;
        margin:8px 0 20px 0;
        box-shadow:0 14px 34px rgba(0,43,103,.25);
        display:grid;
        grid-template-columns:230px minmax(0,1fr) 330px;
        gap:26px;
        align-items:center;
        border:1px solid rgba(255,255,255,.28);
    }
    .v600-logo-card {
        background:#FFFFFF;
        border:4px solid rgba(255,255,255,.92);
        border-radius:22px;
        min-height:132px;
        display:flex;
        align-items:center;
        justify-content:center;
        padding:14px;
        box-shadow:0 10px 26px rgba(0,0,0,.16);
        overflow:hidden;
    }
    .v600-logo-img {
        max-width:190px;
        max-height:105px;
        object-fit:contain;
        display:block;
    }
    .v600-logo-fallback {
        color:#0057D9;
        font-size:42px;
        font-weight:1000;
    }
    .v600-title-area {
        border-left:1px solid rgba(255,255,255,.45);
        padding-left:26px;
    }
    .v600-title-main {
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        font-size:42px;
        line-height:1.02;
        font-weight:1000;
        letter-spacing:.4px;
    }
    .v600-title-main span {
        color:#F5B301!important;
        -webkit-text-fill-color:#F5B301!important;
    }
    .v600-title-sub {
        color:#EAF3FF!important;
        -webkit-text-fill-color:#EAF3FF!important;
        font-size:17px;
        font-weight:900;
        margin-top:12px;
    }
    .v600-info-card {
        background:rgba(255,255,255,.10);
        border:1px solid rgba(255,255,255,.35);
        border-radius:18px;
        padding:16px 18px;
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
        font-size:14px;
        line-height:1.55;
        font-weight:900;
    }
    .v600-info-card * {
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
    }
    section[data-testid="stSidebar"] {
        background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;
        border-right:5px solid #F5B301!important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div {
        color:#FFFFFF!important;
        -webkit-text-fill-color:#FFFFFF!important;
    }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] [data-baseweb="input"],
    section[data-testid="stSidebar"] [data-baseweb="input"] *,
    section[data-testid="stSidebar"] [data-baseweb="select"],
    section[data-testid="stSidebar"] [data-baseweb="select"] * {
        background:#FFFFFF!important;
        color:#071124!important;
        -webkit-text-fill-color:#071124!important;
        font-weight:900!important;
    }
    .stButton button,
    .stDownloadButton button {
        background:#FFFFFF!important;
        color:#0057D9!important;
        -webkit-text-fill-color:#0057D9!important;
        border:2px solid #0057D9!important;
        border-radius:14px!important;
        min-height:48px!important;
        font-size:15px!important;
        font-weight:1000!important;
        box-shadow:0 6px 15px rgba(0,87,217,.12)!important;
    }
    .stButton button:hover,
    .stDownloadButton button:hover {
        background:#F5B301!important;
        color:#111111!important;
        -webkit-text-fill-color:#111111!important;
        border-color:#F5B301!important;
    }
    [data-testid="stCheckbox"] label {
        background:#FFFFFF!important;
        border:2px solid #C9DCF7!important;
        border-radius:14px!important;
        padding:10px 12px!important;
        box-shadow:0 4px 12px rgba(0,87,217,.06)!important;
        transition:all .18s ease!important;
        color:#071124!important;
        -webkit-text-fill-color:#071124!important;
        font-weight:900!important;
    }
    [data-testid="stCheckbox"] label:hover {
        border-color:#0057D9!important;
        background:#F4F8FF!important;
    }
    [data-testid="stCheckbox"] label:has(input:checked) {
        background:#EAF3FF!important;
        border-color:#0057D9!important;
        box-shadow:0 0 0 3px rgba(0,87,217,.16),0 8px 18px rgba(0,87,217,.12)!important;
    }
    @media(max-width:1100px) {
        .v600-main-header {
            grid-template-columns:1fr;
            text-align:center;
        }
        .v600-title-area {
            border-left:0;
            padding-left:0;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def v600_header():
    st.markdown("""
    <div class="v600-main-header">
        <div class="v600-logo-card">
            <img src="data:image/png;base64,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" class="v600-logo-img">
        </div>
        <div class="v600-title-area">
            <div class="v600-title-main">
                CONFIGURATORE<br>
                <span>PORTE AUTOMATICHE</span>
            </div>
            <div class="v600-title-sub">
                Tecnologia, sicurezza e soluzioni su misura per ingressi automatici
            </div>
        </div>
        <div class="v600-info-card">
            <b>SA-TEC S.R.L.s</b><br>
            Via L. Settembrini 84<br>
            88046 Lamezia Terme (CZ)<br>
            ☎ 0968-036797<br>
            ✉ sacco.tecnologie@gmail.com<br>
            PEC sa-tec@pec.it
        </div>
    </div>
    """, unsafe_allow_html=True)




# =========================
# V700 - HEADER E RENDER DEFINITIVO SA-TEC
# =========================
def v700_style():
    st.markdown("""
    <style>
    .stApp{background:linear-gradient(180deg,#F3F8FF 0%,#FFFFFF 72%)!important;}
    .block-container{padding-top:.6rem!important;max-width:1550px!important;}
    .v700-header{background:#FFFFFF;border:1px solid #C9DCF7;border-radius:20px;overflow:hidden;box-shadow:0 10px 26px rgba(0,43,103,.10);margin:6px 0 12px 0;}
    .v700-header-top{display:grid;grid-template-columns:190px minmax(0,1fr) 330px;align-items:center;min-height:128px;background:#FFFFFF;}
    .v700-logo-box{height:128px;border-right:1px solid #D8E7FB;display:flex;align-items:center;justify-content:center;background:#FFFFFF;padding:10px;}
    .v700-logo-img{max-width:145px;max-height:105px;object-fit:contain;}
    .v700-logo-fallback{color:#0057D9;font-size:34px;font-weight:1000;}
    .v700-title-box{padding:18px 26px;}
    .v700-title{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:42px;line-height:1;font-weight:1000;letter-spacing:.3px;}
    .v700-subtitle{color:#475569!important;-webkit-text-fill-color:#475569!important;font-size:17px;font-weight:900;margin-top:10px;letter-spacing:.4px;text-transform:uppercase;}
    .v700-company{border-left:1px solid #D8E7FB;padding:16px 22px;color:#061A40!important;-webkit-text-fill-color:#061A40!important;font-size:14px;line-height:1.55;font-weight:900;}
    .v700-company b{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:15px;}
    .v700-nav{background:linear-gradient(90deg,#003C96,#0057D9);min-height:48px;display:grid;grid-template-columns:repeat(6,1fr);align-items:center;color:#FFFFFF!important;}
    .v700-nav div{text-align:center;font-size:14px;font-weight:1000;color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;border-right:1px solid rgba(255,255,255,.22);}
    .v700-nav div:last-child{border-right:0;}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;border-right:5px solid #F5B301!important;}
    section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] div{color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;}
    section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea,section[data-testid="stSidebar"] [data-baseweb="input"],section[data-testid="stSidebar"] [data-baseweb="input"] *,section[data-testid="stSidebar"] [data-baseweb="select"],section[data-testid="stSidebar"] [data-baseweb="select"] *{background:#FFFFFF!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    .stButton button,.stDownloadButton button{background:#FFFFFF!important;color:#0057D9!important;-webkit-text-fill-color:#0057D9!important;border:2px solid #0057D9!important;border-radius:14px!important;min-height:48px!important;font-size:15px!important;font-weight:1000!important;box-shadow:0 6px 15px rgba(0,87,217,.12)!important;}
    .stButton button:hover,.stDownloadButton button:hover{background:#F5B301!important;color:#111111!important;-webkit-text-fill-color:#111111!important;border-color:#F5B301!important;}
    [data-testid="stCheckbox"] label{background:#FFFFFF!important;border:2px solid #C9DCF7!important;border-radius:14px!important;padding:10px 12px!important;box-shadow:0 4px 12px rgba(0,87,217,.06)!important;transition:all .18s ease!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    [data-testid="stCheckbox"] label:hover{border-color:#0057D9!important;background:#F4F8FF!important;}
    [data-testid="stCheckbox"] label:has(input:checked){background:#EAF3FF!important;border-color:#0057D9!important;box-shadow:0 0 0 3px rgba(0,87,217,.16),0 8px 18px rgba(0,87,217,.12)!important;}
    @media(max-width:1100px){.v700-header-top{grid-template-columns:1fr;text-align:center;}.v700-company,.v700-logo-box{border-left:0;border-right:0;border-top:1px solid #D8E7FB;}.v700-nav{grid-template-columns:repeat(2,1fr);}}
    </style>
    """, unsafe_allow_html=True)

def v700_header():
    st.markdown("""
    <div class="v700-header">
        <div class="v700-header-top">
            <div class="v700-logo-box"><img src="data:image/png;base64,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" class="v700-logo-img"></div>
            <div class="v700-title-box">
                <div class="v700-title">SA-TEC - CONFIGURATORE PORTE AUTOMATICHE</div>
                <div class="v700-subtitle">Tecnologia, sicurezza e soluzioni su misura</div>
            </div>
            <div class="v700-company">
                <b>SA-TEC S.R.L.s</b><br>
                📍 Via L. Settembrini 84<br>
                88046 Lamezia Terme (CZ)<br>
                ☎ 0968-036797<br>
                ✉ sacco.tecnologie@gmail.com
            </div>
        </div>
        <div class="v700-nav">
            <div>⌂ HOME</div><div>⚙ CONFIGURATORE</div><div>▤ CATALOGO</div><div>▥ CODICI</div><div>☏ ASSISTENZA</div><div>⚙ IMPOSTAZIONI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def disegno_porta_v700(ante, luce_mm, altezza_mm, lunghezza_traversa, elettro=False, radar=False, allaccio=False):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo_schema = "SCHEMA TECNICO PORTA SCORREVOLE A 2 ANTE" if due_ante else "SCHEMA TECNICO PORTA SCORREVOLE A 1 ANTA"
    due_ante_js = "true" if due_ante else "false"

    return f"""
<!doctype html>
<html>
<head><meta charset="utf-8">
<style>
*{{box-sizing:border-box}}html,body{{margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#fff;color:#061A40}}
.v700-wrap{{width:100%;background:#fff;border:1px solid #D8E7FB;border-radius:18px;overflow:hidden;box-shadow:0 10px 26px rgba(0,42,110,.08)}}
.v700-body{{display:grid;grid-template-columns:minmax(0,1fr) 365px;gap:16px;padding:16px}}
.v700-left,.v700-right{{background:#fff;border:1px solid #D8E7FB;border-radius:14px;overflow:hidden}}
.v700-left-head{{padding:14px 18px 8px 18px}}.v700-title2{{color:#0047B8;font-size:21px;font-weight:1000}}
.v700-tag{{display:inline-block;margin-top:10px;background:#0057D9;color:#fff;font-size:13px;font-weight:1000;border-radius:7px;padding:8px 12px}}
#doorCanvasV700{{width:100%;height:500px;display:block}}
.v700-access-head{{background:#0057D9;color:white;padding:13px 15px;font-size:16px;font-weight:1000}}
.v700-acc-card{{margin:10px;border:2px solid #D8E7FB;border-radius:12px;padding:10px;min-height:128px;display:grid;grid-template-columns:105px 1fr 28px;gap:10px;align-items:center;background:#fff}}
.v700-acc-card.active{{border-color:#0057D9;background:#EAF3FF;box-shadow:0 0 0 3px rgba(0,87,217,.13)}}
.v700-acc-img{{width:96px;height:96px}}.v700-acc-title{{color:#0047B8;font-size:15px;font-weight:1000;margin-bottom:7px}}
.v700-acc-text{{color:#071124;font-size:12px;line-height:1.45;font-weight:800}}
.v700-check{{width:24px;height:24px;border-radius:6px;border:2px solid #0057D9;display:flex;align-items:center;justify-content:center;color:#0057D9;font-weight:1000}}
.v700-acc-card.active .v700-check{{background:#0057D9;color:white}}
.v700-metrics{{border-top:1px solid #D8E7FB;background:#FBFDFF;display:grid;grid-template-columns:repeat(6,1fr)}}
.v700-metric{{padding:12px 8px;border-right:1px solid #D8E7FB;min-height:76px;text-align:center;color:#06245C;font-weight:900}}
.v700-metric:last-child{{border-right:0}}.v700-metric b{{display:block;color:#0057D9;font-size:17px;margin-top:4px}}.v700-metric small{{display:block;color:#465B78;font-size:10px;margin-top:3px}}
</style></head>
<body>
<div class="v700-wrap">
  <div class="v700-body">
    <div class="v700-left">
      <div class="v700-left-head"><div class="v700-title2">V700 - {titolo_schema}</div><div class="v700-tag">AUTOMAZIONE</div></div>
      <canvas id="doorCanvasV700" width="1000" height="500"></canvas>
    </div>
    <div class="v700-right">
      <div class="v700-access-head">ACCESSORI E SERVIZI</div>
      <div class="v700-acc-card {'active' if elettro else ''}"><canvas class="v700-acc-img" id="elettroIcon" width="96" height="96"></canvas><div><div class="v700-acc-title">ELETTROBLOCCO</div><div class="v700-acc-text">Accessorio per blocco anta in chiusura. Si inserisce automaticamente nel preventivo.</div></div><div class="v700-check">{'✓' if elettro else ''}</div></div>
      <div class="v700-acc-card {'active' if radar else ''}"><canvas class="v700-acc-img" id="radarIcon" width="96" height="96"></canvas><div><div class="v700-acc-title">RADAR SICUREZZA LATERALE</div><div class="v700-acc-text">Previene schiacciamento e impatto. Conforme EN16005.</div></div><div class="v700-check">{'✓' if radar else ''}</div></div>
      <div class="v700-acc-card {'active' if allaccio else ''}"><canvas class="v700-acc-img" id="serviceIcon" width="96" height="96"></canvas><div><div class="v700-acc-title">ALLACCIO E COLLAUDO SA-TEC</div><div class="v700-acc-text">Cacciavite, collaudo e certificazione. Logo EN16005 incluso.</div></div><div class="v700-check">{'✓' if allaccio else ''}</div></div>
    </div>
  </div>
  <div class="v700-metrics">
    <div class="v700-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div><div class="v700-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div><div class="v700-metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div><div class="v700-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div><div class="v700-metric">Portata<b>120 kg</b><small>Per anta</small></div><div class="v700-metric">Velocità<b>0,6 m/s</b><small>Regolabile</small></div>
  </div>
</div>
<script>
const dueAnte={due_ante_js}; const luce={luce}; const altezza={altezza}; const traversaMm={int(traversa*1000)};
function rr(ctx,x,y,w,h,r,fill,stroke){{ctx.beginPath();ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);ctx.quadraticCurveTo(x+w,y,x+w,y+r);ctx.lineTo(x+w,y+h-r);ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);ctx.lineTo(x+r,y+h);ctx.quadraticCurveTo(x,y+h,x,y+h-r);ctx.lineTo(x,y+r);ctx.quadraticCurveTo(x,y,x+r,y);ctx.closePath();if(fill)ctx.fill();if(stroke)ctx.stroke();}}
function line(ctx,x1,y1,x2,y2,c,w){{ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}}
function txt(ctx,t,x,y,s,c,a="center",w="900"){{ctx.font=w+" "+s+"px Arial";ctx.fillStyle=c;ctx.textAlign=a;ctx.fillText(t,x,y);}}
function arrow(ctx,x1,y1,x2,y2,c){{line(ctx,x1,y1,x2,y2,c,7);let a=Math.atan2(y2-y1,x2-x1);ctx.fillStyle=c;ctx.beginPath();ctx.moveTo(x2,y2);ctx.lineTo(x2-16*Math.cos(a-Math.PI/6),y2-16*Math.sin(a-Math.PI/6));ctx.lineTo(x2-16*Math.cos(a+Math.PI/6),y2-16*Math.sin(a+Math.PI/6));ctx.closePath();ctx.fill();}}
function glass(ctx,x,y,w,h){{let g=ctx.createLinearGradient(x,y,x+w,y+h);g.addColorStop(0,"rgba(255,255,255,.96)");g.addColorStop(.45,"rgba(205,238,255,.62)");g.addColorStop(1,"rgba(145,215,255,.74)");ctx.fillStyle=g;ctx.strokeStyle="#1D8BFF";ctx.lineWidth=3;rr(ctx,x,y,w,h,4,true,true);line(ctx,x+30,y+12,x+w-38,y+h-36,"rgba(255,255,255,.82)",2);line(ctx,x+75,y+12,x+w-12,y+h-90,"rgba(255,255,255,.55)",2);}}
function drawDoor(){{const c=document.getElementById("doorCanvasV700"),ctx=c.getContext("2d");ctx.clearRect(0,0,1000,500);const fx=105,fy=135,fw=790,fh=245,railX=75,railY=62,railW=850,railH=58;let rg=ctx.createLinearGradient(railX,railY,railX,railY+railH);rg.addColorStop(0,"#eeeeee");rg.addColorStop(.28,"#b9b9b9");rg.addColorStop(.58,"#f7f7f7");rg.addColorStop(1,"#8c8c8c");ctx.fillStyle=rg;ctx.strokeStyle="#222";ctx.lineWidth=2;rr(ctx,railX,railY,railW,railH,3,true,true);line(ctx,railX+22,railY+19,railX+railW-22,railY+19,"#222",3);line(ctx,railX+22,railY+38,railX+railW-22,railY+38,"#555",2);txt(ctx,"sesamo",railX+70,railY+24,12,"#0057D9","center","900");txt(ctx,"SA-TEC",railX+70,railY+44,14,"#0057D9","center","1000");ctx.fillStyle="#111";rr(ctx,railX+railW-150,railY+10,88,38,4,true,false);ctx.fillStyle="#333";rr(ctx,railX+railW-62,railY+16,38,25,4,true,false);txt(ctx,"MOT",railX+railW-43,railY+33,10,"#FFF");function pulley(x){{ctx.fillStyle="#111";ctx.beginPath();ctx.arc(x,railY+29,10,0,Math.PI*2);ctx.fill();ctx.fillStyle="#777";ctx.beginPath();ctx.arc(x,railY+29,4,0,Math.PI*2);ctx.fill();}}[250,300,470,520,680,730].forEach(pulley);function trolley(x){{ctx.fillStyle="#222";rr(ctx,x,railY+49,52,12,3,true,false);line(ctx,x+11,railY+61,x+11,fy+12,"#222",2);line(ctx,x+41,railY+61,x+41,fy+12,"#222",2);}}ctx.strokeStyle="#222";ctx.lineWidth=3;rr(ctx,fx,fy,fw,fh,5,false,true);if(dueAnte){{trolley(310);trolley(625);glass(ctx,165,150,365,218);glass(ctx,530,150,365,218);line(ctx,530,150,530,368,"#003C96",4);arrow(ctx,510,255,430,255,"#148C2E");arrow(ctx,550,255,630,255,"#148C2E");}}else{{trolley(400);trolley(650);glass(ctx,290,150,450,218);arrow(ctx,500,255,660,255,"#148C2E");}}txt(ctx,"APERTURA",520,292,14,"#148C2E");txt(ctx,"AUTOMATICA",520,312,14,"#148C2E");ctx.fillStyle="#D8D8D8";ctx.fillRect(fx-12,fy,12,fh);ctx.fillRect(fx+fw,fy,12,fh);ctx.fillRect(fx-45,fy+fh,fw+90,10);line(ctx,fx-55,fy+fh+14,fx+fw+55,fy+fh+14,"#9A9A9A",3);line(ctx,42,fy,42,fy+fh,"#003C96",2);line(ctx,32,fy,52,fy,"#003C96",2);line(ctx,32,fy+fh,52,fy+fh,"#003C96",2);txt(ctx,"ALTEZZA LUCE",38,255,12,"#003C96","right");txt(ctx,altezza+" mm",38,278,13,"#003C96","right","1000");line(ctx,945,fy-55,945,fy+fh,"#003C96",2);line(ctx,934,fy-55,956,fy-55,"#003C96",2);line(ctx,934,fy+fh,956,fy+fh,"#003C96",2);txt(ctx,"ALTEZZA TOTALE",960,255,12,"#003C96","left");txt(ctx,(altezza+100)+" mm",960,278,13,"#003C96","left","1000");line(ctx,fx+205,415,fx+fw-205,415,"#003C96",2);line(ctx,fx+205,405,fx+205,425,"#003C96",2);line(ctx,fx+fw-205,405,fx+fw-205,425,"#003C96",2);txt(ctx,"LUCE NETTA DI PASSAGGIO",500,409,12,"#003C96");txt(ctx,luce+" mm",500,438,14,"#003C96","center","1000");line(ctx,fx,468,fx+fw,468,"#003C96",2);line(ctx,fx,458,fx,478,"#003C96",2);line(ctx,fx+fw,458,fx+fw,478,"#003C96",2);txt(ctx,"LUNGHEZZA TRAVERSA",500,462,12,"#003C96");txt(ctx,traversaMm+" mm",500,491,14,"#003C96","center","1000");}}
function drawElettro(){{let c=document.getElementById("elettroIcon"),ctx=c.getContext("2d");ctx.clearRect(0,0,96,96);ctx.fillStyle="#111";rr(ctx,10,25,22,52,4,true,false);ctx.fillStyle="#b7b7b7";ctx.strokeStyle="#555";ctx.lineWidth=2;rr(ctx,38,30,38,32,4,true,true);ctx.fillStyle="#333";ctx.fillRect(50,42,12,8);ctx.fillStyle="#777";[20,62,80].forEach((x,i)=>{{ctx.beginPath();ctx.arc(x,14+i*8,4,0,Math.PI*2);ctx.fill();}});ctx.strokeStyle="#111";line(ctx,60,64,90,78,"#111",3);}}
function drawRadar(){{let c=document.getElementById("radarIcon"),ctx=c.getContext("2d");ctx.clearRect(0,0,96,96);let g=ctx.createLinearGradient(18,30,78,68);g.addColorStop(0,"#111");g.addColorStop(.6,"#333");g.addColorStop(1,"#050505");ctx.fillStyle=g;ctx.strokeStyle="#111";ctx.lineWidth=2;rr(ctx,12,30,72,32,8,true,true);ctx.fillStyle="#cc0000";ctx.beginPath();ctx.arc(35,50,3,0,Math.PI*2);ctx.fill();ctx.beginPath();ctx.arc(48,50,3,0,Math.PI*2);ctx.fill();}}
function drawService(){{let c=document.getElementById("serviceIcon"),ctx=c.getContext("2d");ctx.clearRect(0,0,96,96);ctx.strokeStyle="#222";ctx.lineWidth=4;line(ctx,12,72,60,34,"#222",4);ctx.fillStyle="#0A5FD9";rr(ctx,52,28,34,15,8,true,false);ctx.fillStyle="#111";rr(ctx,62,22,15,26,7,true,false);txt(ctx,"EN",48,82,16,"#0057D9","center","1000");txt(ctx,"16005",52,94,12,"#0057D9","center","1000");}}
drawDoor();drawElettro();drawRadar();drawService();
</script>
</body></html>
"""





# =========================
# V701 - RENDER SOLO AUTOMAZIONE PROPORZIONATO
# Accessori rimossi dal disegno: rimangono cliccabili nelle checkbox Streamlit.
# =========================
def disegno_porta_v701(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo_schema = "SCHEMA TECNICO PORTA SCORREVOLE A 2 ANTE" if due_ante else "SCHEMA TECNICO PORTA SCORREVOLE A 1 ANTA"
    due_ante_js = "true" if due_ante else "false"

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
html,body{{
    margin:0;
    padding:0;
    font-family:Arial,Helvetica,sans-serif;
    background:#fff;
    color:#061A40;
}}
.v701-wrap{{
    width:100%;
    background:#fff;
    border:1px solid #D8E7FB;
    border-radius:18px;
    overflow:hidden;
    box-shadow:0 10px 26px rgba(0,42,110,.08);
}}
.v701-head{{
    padding:16px 20px 8px 20px;
}}
.v701-title{{
    color:#0047B8;
    font-size:23px;
    font-weight:1000;
    line-height:1.12;
}}
.v701-tag{{
    display:inline-block;
    margin-top:10px;
    background:#0057D9;
    color:#fff;
    font-size:13px;
    font-weight:1000;
    border-radius:7px;
    padding:8px 12px;
}}
.v701-canvas-box{{
    padding:4px 14px 0 14px;
}}
#doorCanvasV701{{
    width:100%;
    height:520px;
    display:block;
    background:#fff;
    border:1px solid #EDF3FC;
    border-radius:14px;
}}
.v701-metrics{{
    border-top:1px solid #D8E7FB;
    background:#FBFDFF;
    display:grid;
    grid-template-columns:repeat(6,1fr);
}}
.v701-metric{{
    padding:13px 8px;
    border-right:1px solid #D8E7FB;
    min-height:78px;
    text-align:center;
    color:#06245C;
    font-weight:900;
}}
.v701-metric:last-child{{border-right:0}}
.v701-metric b{{
    display:block;
    color:#0057D9;
    font-size:18px;
    margin-top:4px;
}}
.v701-metric small{{
    display:block;
    color:#465B78;
    font-size:10px;
    margin-top:3px;
}}
</style>
</head>
<body>
<div class="v701-wrap">
  <div class="v701-head">
    <div class="v701-title">V701 - {titolo_schema}</div>
    <div class="v701-tag">AUTOMAZIONE</div>
  </div>

  <div class="v701-canvas-box">
    <canvas id="doorCanvasV701" width="1280" height="520"></canvas>
  </div>

  <div class="v701-metrics">
    <div class="v701-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
    <div class="v701-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
    <div class="v701-metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div>
    <div class="v701-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
    <div class="v701-metric">Portata<b>120 kg</b><small>Per anta</small></div>
    <div class="v701-metric">Velocità<b>0,6 m/s</b><small>Regolabile</small></div>
  </div>
</div>

<script>
const dueAnte = {due_ante_js};
const luce = {luce};
const altezza = {altezza};
const traversaMm = {int(traversa*1000)};

function rr(ctx,x,y,w,h,r,fill,stroke){{
    ctx.beginPath();
    ctx.moveTo(x+r,y);
    ctx.lineTo(x+w-r,y);
    ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r);
    ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h);
    ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r);
    ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath();
    if(fill) ctx.fill();
    if(stroke) ctx.stroke();
}}
function line(ctx,x1,y1,x2,y2,c,w){{
    ctx.strokeStyle=c;
    ctx.lineWidth=w;
    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.lineTo(x2,y2);
    ctx.stroke();
}}
function txt(ctx,t,x,y,s,c,a="center",w="900"){{
    ctx.font=w+" "+s+"px Arial";
    ctx.fillStyle=c;
    ctx.textAlign=a;
    ctx.fillText(t,x,y);
}}
function arrow(ctx,x1,y1,x2,y2,c){{
    line(ctx,x1,y1,x2,y2,c,8);
    const a=Math.atan2(y2-y1,x2-x1);
    ctx.fillStyle=c;
    ctx.beginPath();
    ctx.moveTo(x2,y2);
    ctx.lineTo(x2-18*Math.cos(a-Math.PI/6),y2-18*Math.sin(a-Math.PI/6));
    ctx.lineTo(x2-18*Math.cos(a+Math.PI/6),y2-18*Math.sin(a+Math.PI/6));
    ctx.closePath();
    ctx.fill();
}}
function glass(ctx,x,y,w,h){{
    const g=ctx.createLinearGradient(x,y,x+w,y+h);
    g.addColorStop(0,"rgba(255,255,255,.96)");
    g.addColorStop(.42,"rgba(210,240,255,.66)");
    g.addColorStop(1,"rgba(145,215,255,.76)");
    ctx.fillStyle=g;
    ctx.strokeStyle="#1D8BFF";
    ctx.lineWidth=3;
    rr(ctx,x,y,w,h,4,true,true);

    line(ctx,x+35,y+16,x+w-42,y+h-42,"rgba(255,255,255,.82)",3);
    line(ctx,x+88,y+16,x+w-15,y+h-105,"rgba(255,255,255,.55)",2);
}}
function bolt(ctx,x,y){{
    ctx.fillStyle="#2A2A2A";
    ctx.beginPath();
    ctx.arc(x,y,4,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle="#A0A0A0";
    ctx.beginPath();
    ctx.arc(x,y,1.8,0,Math.PI*2);
    ctx.fill();
}}
function drawDoor(){{
    const c=document.getElementById("doorCanvasV701");
    const ctx=c.getContext("2d");
    ctx.clearRect(0,0,1280,520);

    // proporzioni più realistiche e larghe
    const fx=150, fy=138, fw=955, fh=245;
    const railX=105, railY=56, railW=1045, railH=62;

    // sfondo tecnico pulito
    for(let x=40;x<1240;x+=45) line(ctx,x,35,x,500,"rgba(0,87,217,.025)",1);
    for(let y=40;y<500;y+=45) line(ctx,35,y,1245,y,"rgba(0,87,217,.025)",1);

    // ombra traversa
    ctx.shadowColor="rgba(0,0,0,.20)";
    ctx.shadowBlur=12;
    ctx.shadowOffsetY=5;

    // traversa più definita
    const rg=ctx.createLinearGradient(railX,railY,railX,railY+railH);
    rg.addColorStop(0,"#F3F3F3");
    rg.addColorStop(.18,"#AFAFAF");
    rg.addColorStop(.45,"#F9F9F9");
    rg.addColorStop(.72,"#B8B8B8");
    rg.addColorStop(1,"#6F6F6F");
    ctx.fillStyle=rg;
    ctx.strokeStyle="#222";
    ctx.lineWidth=2.5;
    rr(ctx,railX,railY,railW,railH,3,true,true);
    ctx.shadowBlur=0;
    ctx.shadowOffsetY=0;

    // coperchio / binari interni
    line(ctx,railX+28,railY+19,railX+railW-28,railY+19,"#202020",3);
    line(ctx,railX+28,railY+39,railX+railW-28,railY+39,"#555",2);
    line(ctx,railX+28,railY+51,railX+railW-28,railY+51,"#222",1.5);

    txt(ctx,"sesamo",railX+82,railY+24,13,"#0057D9","center","900");
    txt(ctx,"SA-TEC",railX+82,railY+47,16,"#0057D9","center","1000");

    // motore più definito
    ctx.fillStyle="#111";
    rr(ctx,railX+railW-180,railY+11,105,40,5,true,false);
    const mg=ctx.createLinearGradient(railX+railW-175,railY+13,railX+railW-80,railY+50);
    mg.addColorStop(0,"#252525");
    mg.addColorStop(1,"#050505");
    ctx.fillStyle=mg;
    rr(ctx,railX+railW-174,railY+14,92,34,5,true,false);
    ctx.fillStyle="#333";
    rr(ctx,railX+railW-76,railY+19,44,25,4,true,false);
    txt(ctx,"MOT",railX+railW-54,railY+36,10,"#FFF");

    // pulegge, staffe e carrelli
    function pulley(x){{
        ctx.fillStyle="#111";
        ctx.beginPath();
        ctx.arc(x,railY+31,10,0,Math.PI*2);
        ctx.fill();
        ctx.fillStyle="#777";
        ctx.beginPath();
        ctx.arc(x,railY+31,4,0,Math.PI*2);
        ctx.fill();
    }}
    [285,335,540,590,760,810,930].forEach(pulley);

    function bracket(x){{
        ctx.fillStyle="#EAEAEA";
        ctx.strokeStyle="#333";
        ctx.lineWidth=1.5;
        rr(ctx,x,railY+32,34,22,3,true,true);
        bolt(ctx,x+8,railY+39);
        bolt(ctx,x+26,railY+39);
        line(ctx,x+17,railY+54,x+17,fy+12,"#333",2);
    }}
    [255,420,610,785].forEach(bracket);

    function trolley(x){{
        ctx.fillStyle="#222";
        rr(ctx,x,railY+55,58,13,3,true,false);
        line(ctx,x+13,railY+68,x+13,fy+14,"#222",2.5);
        line(ctx,x+45,railY+68,x+45,fy+14,"#222",2.5);
    }}

    // telaio vano
    ctx.strokeStyle="#222";
    ctx.lineWidth=3;
    rr(ctx,fx,fy,fw,fh,5,false,true);

    if(dueAnte){{
        trolley(420);
        trolley(735);
        glass(ctx,215,154,445,214);
        glass(ctx,660,154,445,214);
        line(ctx,660,154,660,368,"#003C96",4);
        arrow(ctx,640,260,545,260,"#148C2E");
        arrow(ctx,680,260,775,260,"#148C2E");
    }} else {{
        trolley(505);
        trolley(790);
        glass(ctx,390,154,540,214);
        arrow(ctx,635,260,820,260,"#148C2E");
    }}

    txt(ctx,"APERTURA",660,297,15,"#148C2E");
    txt(ctx,"AUTOMATICA",660,318,15,"#148C2E");

    // montanti e base
    ctx.fillStyle="#D8D8D8";
    ctx.fillRect(fx-13,fy,13,fh);
    ctx.fillRect(fx+fw,fy,13,fh);
    ctx.fillRect(fx-50,fy+fh,fw+100,11);
    line(ctx,fx-65,fy+fh+16,fx+fw+65,fy+fh+16,"#9A9A9A",3);

    // quote altezza
    line(ctx,70,fy,70,fy+fh,"#003C96",2);
    line(ctx,58,fy,82,fy,"#003C96",2);
    line(ctx,58,fy+fh,82,fy+fh,"#003C96",2);
    txt(ctx,"ALTEZZA LUCE",62,255,13,"#003C96","right");
    txt(ctx,altezza+" mm",62,280,15,"#003C96","right","1000");

    line(ctx,1190,fy-58,1190,fy+fh,"#003C96",2);
    line(ctx,1178,fy-58,1202,fy-58,"#003C96",2);
    line(ctx,1178,fy+fh,1202,fy+fh,"#003C96",2);
    txt(ctx,"ALTEZZA TOTALE",1206,255,13,"#003C96","left");
    txt(ctx,(altezza+100)+" mm",1206,280,15,"#003C96","left","1000");

    // quote orizzontali
    line(ctx,fx+260,426,fx+fw-260,426,"#003C96",2);
    line(ctx,fx+260,415,fx+260,437,"#003C96",2);
    line(ctx,fx+fw-260,415,fx+fw-260,437,"#003C96",2);
    txt(ctx,"LUCE NETTA DI PASSAGGIO",640,421,13,"#003C96");
    txt(ctx,luce+" mm",640,451,16,"#003C96","center","1000");

    line(ctx,fx,482,fx+fw,482,"#003C96",2);
    line(ctx,fx,471,fx,493,"#003C96",2);
    line(ctx,fx+fw,471,fx+fw,493,"#003C96",2);
    txt(ctx,"LUNGHEZZA TRAVERSA",640,477,13,"#003C96");
    txt(ctx,traversaMm+" mm",640,506,16,"#003C96","center","1000");
}}
drawDoor();
</script>
</body>
</html>
"""





# =========================
# V800 - HEADER E RENDER CATALOGO SESAMO / SA-TEC
# =========================
def v800_style():
    st.markdown("""
    <style>
    .stApp{background:linear-gradient(180deg,#F3F8FF 0%,#FFFFFF 72%)!important;}
    .block-container{padding-top:.6rem!important;max-width:1550px!important;}
    .v800-header{background:#FFFFFF;border:1px solid #C9DCF7;border-radius:20px;overflow:hidden;box-shadow:0 10px 26px rgba(0,43,103,.10);margin:6px 0 12px 0;}
    .v800-header-top{display:grid;grid-template-columns:190px minmax(0,1fr) 330px;align-items:center;min-height:128px;background:#FFFFFF;}
    .v800-logo-box{height:128px;border-right:1px solid #D8E7FB;display:flex;align-items:center;justify-content:center;background:#FFFFFF;padding:10px;}
    .v800-logo-img{max-width:145px;max-height:105px;object-fit:contain;}
    .v800-logo-fallback{color:#0057D9;font-size:34px;font-weight:1000;}
    .v800-title-box{padding:18px 26px;}
    .v800-title{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:42px;line-height:1;font-weight:1000;letter-spacing:.3px;}
    .v800-subtitle{color:#475569!important;-webkit-text-fill-color:#475569!important;font-size:17px;font-weight:900;margin-top:10px;letter-spacing:.4px;text-transform:uppercase;}
    .v800-company{border-left:1px solid #D8E7FB;padding:16px 22px;color:#061A40!important;-webkit-text-fill-color:#061A40!important;font-size:14px;line-height:1.55;font-weight:900;}
    .v800-company b{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:15px;}
    .v800-nav{background:linear-gradient(90deg,#003C96,#0057D9);min-height:48px;display:grid;grid-template-columns:repeat(6,1fr);align-items:center;color:#FFFFFF!important;}
    .v800-nav div{text-align:center;font-size:14px;font-weight:1000;color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;border-right:1px solid rgba(255,255,255,.22);}
    .v800-nav div:last-child{border-right:0;}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;border-right:5px solid #F5B301!important;}
    section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] div{color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;}
    section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea,section[data-testid="stSidebar"] [data-baseweb="input"],section[data-testid="stSidebar"] [data-baseweb="input"] *,section[data-testid="stSidebar"] [data-baseweb="select"],section[data-testid="stSidebar"] [data-baseweb="select"] *{background:#FFFFFF!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    .stButton button,.stDownloadButton button{background:#FFFFFF!important;color:#0057D9!important;-webkit-text-fill-color:#0057D9!important;border:2px solid #0057D9!important;border-radius:14px!important;min-height:48px!important;font-size:15px!important;font-weight:1000!important;box-shadow:0 6px 15px rgba(0,87,217,.12)!important;}
    .stButton button:hover,.stDownloadButton button:hover{background:#F5B301!important;color:#111111!important;-webkit-text-fill-color:#111111!important;border-color:#F5B301!important;}
    [data-testid="stCheckbox"] label{background:#FFFFFF!important;border:2px solid #C9DCF7!important;border-radius:14px!important;padding:10px 12px!important;box-shadow:0 4px 12px rgba(0,87,217,.06)!important;transition:all .18s ease!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    [data-testid="stCheckbox"] label:hover{border-color:#0057D9!important;background:#F4F8FF!important;}
    [data-testid="stCheckbox"] label:has(input:checked){background:#EAF3FF!important;border-color:#0057D9!important;box-shadow:0 0 0 3px rgba(0,87,217,.16),0 8px 18px rgba(0,87,217,.12)!important;}
    </style>
    """, unsafe_allow_html=True)

def v800_header():
    st.markdown("""
    <div class="v800-header">
        <div class="v800-header-top">
            <div class="v800-logo-box"><img src="data:image/png;base64,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" class="v800-logo-img"></div>
            <div class="v800-title-box">
                <div class="v800-title">SA-TEC - CONFIGURATORE PORTE AUTOMATICHE</div>
                <div class="v800-subtitle">Tecnologia, sicurezza e soluzioni su misura</div>
            </div>
            <div class="v800-company">
                <b>SA-TEC S.R.L.s</b><br>
                📍 Via L. Settembrini 84<br>
                88046 Lamezia Terme (CZ)<br>
                ☎ 0968-036797<br>
                ✉ sacco.tecnologie@gmail.com
            </div>
        </div>
        <div class="v800-nav">
            <div>⌂ HOME</div><div>⚙ CONFIGURATORE</div><div>▤ CATALOGO</div><div>▥ CODICI</div><div>☏ ASSISTENZA</div><div>⚙ IMPOSTAZIONI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def disegno_porta_v800(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo_schema = "SCORREVOLE AUTOMATICA A 2 ANTE" if due_ante else "SCORREVOLE AUTOMATICA A 1 ANTA"
    due_ante_js = "true" if due_ante else "false"

    return f"""
<!doctype html>
<html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box}}html,body{{margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#fff;color:#061A40}}
.v800-wrap{{width:100%;background:#fff;border:1px solid #D8E7FB;border-radius:18px;overflow:hidden;box-shadow:0 10px 26px rgba(0,42,110,.08)}}
.v800-head{{display:flex;justify-content:space-between;align-items:flex-start;padding:18px 22px 8px 22px}}
.v800-title-local{{color:#0047B8;font-size:24px;font-weight:1000;line-height:1.12}}
.v800-sub-local{{color:#64748B;font-size:13px;font-weight:900;margin-top:6px;text-transform:uppercase;letter-spacing:.4px}}
.v800-brand{{text-align:right;color:#0047B8;font-size:30px;font-weight:1000;line-height:1}}
.v800-brand small{{display:block;color:#475569;font-size:11px;letter-spacing:1.2px;margin-top:4px}}
.v800-canvas-box{{padding:4px 18px 0 18px}}
#doorCanvasV800{{width:100%;height:545px;display:block;background:#fff;border:1px solid #EDF3FC;border-radius:14px}}
.v800-metrics{{border-top:1px solid #D8E7FB;background:#FBFDFF;display:grid;grid-template-columns:repeat(6,1fr)}}
.v800-metric{{padding:13px 8px;border-right:1px solid #D8E7FB;min-height:78px;text-align:center;color:#06245C;font-weight:900}}
.v800-metric:last-child{{border-right:0}}.v800-metric b{{display:block;color:#0057D9;font-size:18px;margin-top:4px}}.v800-metric small{{display:block;color:#465B78;font-size:10px;margin-top:3px}}
</style></head>
<body>
<div class="v800-wrap">
  <div class="v800-head">
    <div><div class="v800-title-local">V800 - SCHEMA TECNICO PORTA {titolo_schema}</div><div class="v800-sub-local">SESAMO POWERCORE PW100 · SA-TEC · Disegno tecnico proporzionato</div></div>
    <div class="v800-brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div>
  </div>
  <div class="v800-canvas-box"><canvas id="doorCanvasV800" width="1360" height="545"></canvas></div>
  <div class="v800-metrics">
    <div class="v800-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
    <div class="v800-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
    <div class="v800-metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div>
    <div class="v800-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
    <div class="v800-metric">Portata<b>120 kg</b><small>Per anta</small></div>
    <div class="v800-metric">Velocità<b>0,6 m/s</b><small>Regolabile</small></div>
  </div>
</div>
<script>
const dueAnte={due_ante_js}; const luce={luce}; const altezza={altezza}; const traversaMm={int(traversa*1000)};
function rr(ctx,x,y,w,h,r,fill,stroke){{ctx.beginPath();ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);ctx.quadraticCurveTo(x+w,y,x+w,y+r);ctx.lineTo(x+w,y+h-r);ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);ctx.lineTo(x+r,y+h);ctx.quadraticCurveTo(x,y+h,x,y+h-r);ctx.lineTo(x,y+r);ctx.quadraticCurveTo(x,y,x+r,y);ctx.closePath();if(fill)ctx.fill();if(stroke)ctx.stroke();}}
function line(ctx,x1,y1,x2,y2,c,w){{ctx.strokeStyle=c;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}}
function txt(ctx,t,x,y,s,c,a="center",w="900"){{ctx.font=w+" "+s+"px Arial";ctx.fillStyle=c;ctx.textAlign=a;ctx.fillText(t,x,y);}}
function arrow(ctx,x1,y1,x2,y2,c){{line(ctx,x1,y1,x2,y2,c,8);const a=Math.atan2(y2-y1,x2-x1);ctx.fillStyle=c;ctx.beginPath();ctx.moveTo(x2,y2);ctx.lineTo(x2-19*Math.cos(a-Math.PI/6),y2-19*Math.sin(a-Math.PI/6));ctx.lineTo(x2-19*Math.cos(a+Math.PI/6),y2-19*Math.sin(a+Math.PI/6));ctx.closePath();ctx.fill();}}
function glass(ctx,x,y,w,h){{const g=ctx.createLinearGradient(x,y,x+w,y+h);g.addColorStop(0,"rgba(255,255,255,.98)");g.addColorStop(.35,"rgba(220,244,255,.72)");g.addColorStop(1,"rgba(145,215,255,.78)");ctx.fillStyle=g;ctx.strokeStyle="#0C82F5";ctx.lineWidth=3;rr(ctx,x,y,w,h,2,true,true);line(ctx,x+34,y+16,x+w-42,y+h-42,"rgba(255,255,255,.86)",3);line(ctx,x+90,y+16,x+w-16,y+h-112,"rgba(255,255,255,.58)",2);}}
function bolt(ctx,x,y){{ctx.fillStyle="#292929";ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();ctx.fillStyle="#A0A0A0";ctx.beginPath();ctx.arc(x,y,1.7,0,Math.PI*2);ctx.fill();}}
function drawDoor(){{
 const c=document.getElementById("doorCanvasV800"),ctx=c.getContext("2d");ctx.clearRect(0,0,1360,545);
 const railX=130,railY=58,railW=1100,railH=70,fx=185,fy=160,fw=990,fh=245;
 for(let x=50;x<1310;x+=50)line(ctx,x,35,x,520,"rgba(0,87,217,.018)",1);
 for(let y=40;y<525;y+=50)line(ctx,45,y,1315,y,"rgba(0,87,217,.018)",1);
 ctx.shadowColor="rgba(0,0,0,.20)";ctx.shadowBlur=13;ctx.shadowOffsetY=6;
 const rg=ctx.createLinearGradient(railX,railY,railX,railY+railH);rg.addColorStop(0,"#FAFAFA");rg.addColorStop(.11,"#D8D8D8");rg.addColorStop(.28,"#A2A2A2");rg.addColorStop(.48,"#F6F6F6");rg.addColorStop(.70,"#BDBDBD");rg.addColorStop(1,"#727272");
 ctx.fillStyle=rg;ctx.strokeStyle="#202020";ctx.lineWidth=2.4;rr(ctx,railX,railY,railW,railH,3,true,true);ctx.shadowBlur=0;ctx.shadowOffsetY=0;
 line(ctx,railX+28,railY+20,railX+railW-28,railY+20,"#242424",3);line(ctx,railX+28,railY+44,railX+railW-28,railY+44,"#505050",2);line(ctx,railX+28,railY+59,railX+railW-28,railY+59,"#222",1.4);
 txt(ctx,"SESAMO",railX+88,railY+28,19,"#0057D9","center","1000");txt(ctx,"SA-TEC",railX+88,railY+55,15,"#0057D9","center","1000");
 ctx.fillStyle="#111";rr(ctx,railX+railW-210,railY+12,128,44,5,true,false);const mg=ctx.createLinearGradient(railX+railW-202,railY+14,railX+railW-95,railY+55);mg.addColorStop(0,"#3A3A3A");mg.addColorStop(.55,"#0F0F0F");mg.addColorStop(1,"#020202");ctx.fillStyle=mg;rr(ctx,railX+railW-202,railY+15,108,38,5,true,false);ctx.fillStyle="#4A4A4A";rr(ctx,railX+railW-90,railY+20,45,27,4,true,false);txt(ctx,"MOT",railX+railW-68,railY+38,11,"#FFF");
 function pulley(x){{ctx.fillStyle="#111";ctx.beginPath();ctx.arc(x,railY+35,11,0,Math.PI*2);ctx.fill();ctx.fillStyle="#777";ctx.beginPath();ctx.arc(x,railY+35,4.5,0,Math.PI*2);ctx.fill();}}[335,392,580,637,820,877,1010].forEach(pulley);line(ctx,335,railY+35,1010,railY+35,"#181818",2.2);
 function bracket(x){{ctx.fillStyle="#E9E9E9";ctx.strokeStyle="#333";ctx.lineWidth=1.5;rr(ctx,x,railY+41,40,24,3,true,true);bolt(ctx,x+10,railY+49);bolt(ctx,x+30,railY+49);line(ctx,x+20,railY+65,x+20,fy+13,"#333",2.4);}}[290,475,660,845,1030].forEach(bracket);
 function trolley(x){{ctx.fillStyle="#1F1F1F";rr(ctx,x,railY+63,62,14,3,true,false);line(ctx,x+14,railY+77,x+14,fy+13,"#202020",2.5);line(ctx,x+48,railY+77,x+48,fy+13,"#202020",2.5);}}
 ctx.strokeStyle="#222";ctx.lineWidth=2.8;rr(ctx,fx,fy,fw,fh,4,false,true);
 if(dueAnte){{trolley(430);trolley(765);glass(ctx,255,176,455,210);glass(ctx,710,176,455,210);line(ctx,710,176,710,386,"#003C96",3.5);arrow(ctx,690,270,585,270,"#148C2E");arrow(ctx,730,270,835,270,"#148C2E");}}else{{trolley(545);trolley(835);glass(ctx,435,176,540,210);arrow(ctx,690,270,875,270,"#148C2E");}}
 txt(ctx,"APERTURA",710,307,15,"#148C2E");txt(ctx,"AUTOMATICA",710,329,15,"#148C2E");
 ctx.fillStyle="#D6D6D6";ctx.fillRect(fx-10,fy,10,fh);ctx.fillRect(fx+fw,fy,10,fh);ctx.fillStyle="#CFCFCF";ctx.fillRect(fx-55,fy+fh,fw+110,10);line(ctx,fx-70,fy+fh+16,fx+fw+70,fy+fh+16,"#9A9A9A",2.8);
 line(ctx,92,fy,92,fy+fh,"#003C96",2);line(ctx,80,fy,104,fy,"#003C96",2);line(ctx,80,fy+fh,104,fy+fh,"#003C96",2);txt(ctx,"ALTEZZA LUCE",84,260,13,"#003C96","right");txt(ctx,altezza+" mm",84,286,15,"#003C96","right","1000");
 line(ctx,1260,fy-65,1260,fy+fh,"#003C96",2);line(ctx,1248,fy-65,1272,fy-65,"#003C96",2);line(ctx,1248,fy+fh,1272,fy+fh,"#003C96",2);txt(ctx,"ALTEZZA TOTALE",1278,260,13,"#003C96","left");txt(ctx,(altezza+100)+" mm",1278,286,15,"#003C96","left","1000");
 line(ctx,fx+280,440,fx+fw-280,440,"#003C96",2);line(ctx,fx+280,429,fx+280,451,"#003C96",2);line(ctx,fx+fw-280,429,fx+fw-280,451,"#003C96",2);txt(ctx,"LUCE NETTA DI PASSAGGIO",680,434,13,"#003C96");txt(ctx,luce+" mm",680,464,16,"#003C96","center","1000");
 line(ctx,fx,502,fx+fw,502,"#003C96",2);line(ctx,fx,491,fx,513,"#003C96",2);line(ctx,fx+fw,491,fx+fw,513,"#003C96",2);txt(ctx,"LUNGHEZZA TRAVERSA",680,497,13,"#003C96");txt(ctx,traversaMm+" mm",680,527,16,"#003C96","center","1000");
}}
drawDoor();
</script>
</body></html>
"""





# =========================
# V802 - SVG STATICO DEFINITIVO SESAMO / SA-TEC
# No Canvas. No Javascript. Immagine diversa garantita.
# =========================
def v802_style():
    st.markdown("""
    <style>
    .stApp{background:linear-gradient(180deg,#F3F8FF 0%,#FFFFFF 72%)!important;}
    .block-container{padding-top:.6rem!important;max-width:1550px!important;}
    .v802-header{background:#FFFFFF;border:1px solid #C9DCF7;border-radius:20px;overflow:hidden;box-shadow:0 10px 26px rgba(0,43,103,.10);margin:6px 0 12px 0;}
    .v802-header-top{display:grid;grid-template-columns:190px minmax(0,1fr) 330px;align-items:center;min-height:128px;background:#FFFFFF;}
    .v802-logo-box{height:128px;border-right:1px solid #D8E7FB;display:flex;align-items:center;justify-content:center;background:#FFFFFF;padding:10px;}
    .v802-logo-img{max-width:145px;max-height:105px;object-fit:contain;}
    .v802-logo-fallback{color:#0057D9;font-size:34px;font-weight:1000;}
    .v802-title-box{padding:18px 26px;}
    .v802-title{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:42px;line-height:1;font-weight:1000;letter-spacing:.3px;}
    .v802-subtitle{color:#475569!important;-webkit-text-fill-color:#475569!important;font-size:17px;font-weight:900;margin-top:10px;letter-spacing:.4px;text-transform:uppercase;}
    .v802-company{border-left:1px solid #D8E7FB;padding:16px 22px;color:#061A40!important;-webkit-text-fill-color:#061A40!important;font-size:14px;line-height:1.55;font-weight:900;}
    .v802-company b{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:15px;}
    .v802-nav{background:linear-gradient(90deg,#003C96,#0057D9);min-height:48px;display:grid;grid-template-columns:repeat(6,1fr);align-items:center;color:#FFFFFF!important;}
    .v802-nav div{text-align:center;font-size:14px;font-weight:1000;color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;border-right:1px solid rgba(255,255,255,.22);}
    .v802-nav div:last-child{border-right:0;}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;border-right:5px solid #F5B301!important;}
    section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] div{color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;}
    section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea,section[data-testid="stSidebar"] [data-baseweb="input"],section[data-testid="stSidebar"] [data-baseweb="input"] *,section[data-testid="stSidebar"] [data-baseweb="select"],section[data-testid="stSidebar"] [data-baseweb="select"] *{background:#FFFFFF!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    .stButton button,.stDownloadButton button{background:#FFFFFF!important;color:#0057D9!important;-webkit-text-fill-color:#0057D9!important;border:2px solid #0057D9!important;border-radius:14px!important;min-height:48px!important;font-size:15px!important;font-weight:1000!important;box-shadow:0 6px 15px rgba(0,87,217,.12)!important;}
    .stButton button:hover,.stDownloadButton button:hover{background:#F5B301!important;color:#111111!important;-webkit-text-fill-color:#111111!important;border-color:#F5B301!important;}
    [data-testid="stCheckbox"] label{background:#FFFFFF!important;border:2px solid #C9DCF7!important;border-radius:14px!important;padding:10px 12px!important;box-shadow:0 4px 12px rgba(0,87,217,.06)!important;transition:all .18s ease!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    [data-testid="stCheckbox"] label:hover{border-color:#0057D9!important;background:#F4F8FF!important;}
    [data-testid="stCheckbox"] label:has(input:checked){background:#EAF3FF!important;border-color:#0057D9!important;box-shadow:0 0 0 3px rgba(0,87,217,.16),0 8px 18px rgba(0,87,217,.12)!important;}
    </style>
    """, unsafe_allow_html=True)

def v802_header():
    st.markdown("""
    <div class="v802-header">
        <div class="v802-header-top">
            <div class="v802-logo-box"><img src="data:image/png;base64,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" class="v802-logo-img"></div>
            <div class="v802-title-box">
                <div class="v802-title">SA-TEC - CONFIGURATORE PORTE AUTOMATICHE</div>
                <div class="v802-subtitle">Tecnologia, sicurezza e soluzioni su misura</div>
            </div>
            <div class="v802-company">
                <b>SA-TEC S.R.L.s</b><br>
                📍 Via L. Settembrini 84<br>
                88046 Lamezia Terme (CZ)<br>
                ☎ 0968-036797<br>
                ✉ sacco.tecnologie@gmail.com
            </div>
        </div>
        <div class="v802-nav">
            <div>⌂ HOME</div><div>⚙ CONFIGURATORE</div><div>▤ CATALOGO</div><div>▥ CODICI</div><div>☏ ASSISTENZA</div><div>⚙ IMPOSTAZIONI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def disegno_porta_v802(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo = "PORTA SCORREVOLE AUTOMATICA A 2 ANTE" if due_ante else "PORTA SCORREVOLE AUTOMATICA A 1 ANTA"

    if due_ante:
        doors_svg = """
        <g id="doors">
            <rect x="260" y="210" width="430" height="220" rx="2" fill="url(#glass)" stroke="#0B82F0" stroke-width="4"/>
            <rect x="690" y="210" width="430" height="220" rx="2" fill="url(#glass)" stroke="#0B82F0" stroke-width="4"/>
            <line x1="690" y1="210" x2="690" y2="430" stroke="#003C96" stroke-width="4"/>
            <path d="M665 315 L560 315" stroke="#148C2E" stroke-width="8" stroke-linecap="round"/>
            <polygon points="560,315 580,303 580,327" fill="#148C2E"/>
            <path d="M715 315 L820 315" stroke="#148C2E" stroke-width="8" stroke-linecap="round"/>
            <polygon points="820,315 800,303 800,327" fill="#148C2E"/>
        </g>
        <g id="hangers">
            <rect x="420" y="148" width="78" height="16" rx="3" fill="#1f1f1f"/>
            <line x1="440" y1="164" x2="440" y2="210" stroke="#222" stroke-width="4"/>
            <line x1="478" y1="164" x2="478" y2="210" stroke="#222" stroke-width="4"/>
            <rect x="795" y="148" width="78" height="16" rx="3" fill="#1f1f1f"/>
            <line x1="815" y1="164" x2="815" y2="210" stroke="#222" stroke-width="4"/>
            <line x1="853" y1="164" x2="853" y2="210" stroke="#222" stroke-width="4"/>
        </g>
        """
    else:
        doors_svg = """
        <g id="doors">
            <rect x="420" y="210" width="560" height="220" rx="2" fill="url(#glass)" stroke="#0B82F0" stroke-width="4"/>
            <path d="M690 315 L875 315" stroke="#148C2E" stroke-width="8" stroke-linecap="round"/>
            <polygon points="875,315 855,303 855,327" fill="#148C2E"/>
        </g>
        <g id="hangers">
            <rect x="540" y="148" width="78" height="16" rx="3" fill="#1f1f1f"/>
            <line x1="560" y1="164" x2="560" y2="210" stroke="#222" stroke-width="4"/>
            <line x1="598" y1="164" x2="598" y2="210" stroke="#222" stroke-width="4"/>
            <rect x="810" y="148" width="78" height="16" rx="3" fill="#1f1f1f"/>
            <line x1="830" y1="164" x2="830" y2="210" stroke="#222" stroke-width="4"/>
            <line x1="868" y1="164" x2="868" y2="210" stroke="#222" stroke-width="4"/>
        </g>
        """

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:white;color:#061A40}}
.sheet{{border:1px solid #D8E7FB;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 10px 26px rgba(0,42,110,.08)}}
.head{{display:flex;justify-content:space-between;align-items:flex-start;padding:18px 22px 8px 22px}}
.title{{color:#0047B8;font-size:24px;font-weight:1000;line-height:1.12}}
.sub{{color:#64748B;font-size:13px;font-weight:900;margin-top:6px;text-transform:uppercase;letter-spacing:.4px}}
.brand{{text-align:right;color:#0047B8;font-size:30px;font-weight:1000;line-height:1}}
.brand small{{display:block;color:#475569;font-size:11px;letter-spacing:1.2px;margin-top:4px}}
.svgbox{{padding:4px 18px 0 18px}}
.metrics{{border-top:1px solid #D8E7FB;background:#FBFDFF;display:grid;grid-template-columns:repeat(6,1fr)}}
.metric{{padding:13px 8px;border-right:1px solid #D8E7FB;min-height:78px;text-align:center;color:#06245C;font-weight:900}}
.metric:last-child{{border-right:0}}
.metric b{{display:block;color:#0057D9;font-size:18px;margin-top:4px}}
.metric small{{display:block;color:#465B78;font-size:10px;margin-top:3px}}
</style>
</head>
<body>
<div class="sheet">
    <div class="head">
        <div>
            <div class="title">V802 - SCHEMA TECNICO {titolo}</div>
            <div class="sub">SESAMO POWERCORE PW100 · SA-TEC · SVG statico definitivo</div>
        </div>
        <div class="brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div>
    </div>

    <div class="svgbox">
        <svg width="100%" height="545" viewBox="0 0 1360 545" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="rail" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#fafafa"/>
                    <stop offset="12%" stop-color="#d8d8d8"/>
                    <stop offset="30%" stop-color="#9f9f9f"/>
                    <stop offset="50%" stop-color="#f6f6f6"/>
                    <stop offset="73%" stop-color="#bdbdbd"/>
                    <stop offset="100%" stop-color="#707070"/>
                </linearGradient>
                <linearGradient id="motor" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#3a3a3a"/>
                    <stop offset="55%" stop-color="#101010"/>
                    <stop offset="100%" stop-color="#020202"/>
                </linearGradient>
                <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#ffffff" stop-opacity=".98"/>
                    <stop offset="42%" stop-color="#d9f1ff" stop-opacity=".72"/>
                    <stop offset="100%" stop-color="#91d7ff" stop-opacity=".78"/>
                </linearGradient>
                <filter id="shadow" x="-10%" y="-20%" width="120%" height="150%">
                    <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000000" flood-opacity=".20"/>
                </filter>
            </defs>

            <rect x="130" y="58" width="1100" height="70" rx="3" fill="url(#rail)" stroke="#202020" stroke-width="2.5" filter="url(#shadow)"/>
            <line x1="158" y1="78" x2="1202" y2="78" stroke="#242424" stroke-width="3"/>
            <line x1="158" y1="102" x2="1202" y2="102" stroke="#505050" stroke-width="2"/>
            <line x1="158" y1="117" x2="1202" y2="117" stroke="#222" stroke-width="1.5"/>
            <text x="218" y="86" fill="#0057D9" font-size="19" font-weight="1000" text-anchor="middle">SESAMO</text>
            <text x="218" y="113" fill="#0057D9" font-size="15" font-weight="1000" text-anchor="middle">SA-TEC</text>

            <rect x="1020" y="70" width="128" height="44" rx="5" fill="#111"/>
            <rect x="1028" y="73" width="108" height="38" rx="5" fill="url(#motor)"/>
            <rect x="1140" y="78" width="45" height="27" rx="4" fill="#4a4a4a"/>
            <text x="1162" y="96" fill="#fff" font-size="11" font-weight="900" text-anchor="middle">MOT</text>

            <g fill="#111">
                <circle cx="335" cy="93" r="11"/><circle cx="392" cy="93" r="11"/>
                <circle cx="580" cy="93" r="11"/><circle cx="637" cy="93" r="11"/>
                <circle cx="820" cy="93" r="11"/><circle cx="877" cy="93" r="11"/>
                <circle cx="1010" cy="93" r="11"/>
            </g>
            <g fill="#777">
                <circle cx="335" cy="93" r="4.5"/><circle cx="392" cy="93" r="4.5"/>
                <circle cx="580" cy="93" r="4.5"/><circle cx="637" cy="93" r="4.5"/>
                <circle cx="820" cy="93" r="4.5"/><circle cx="877" cy="93" r="4.5"/>
                <circle cx="1010" cy="93" r="4.5"/>
            </g>
            <line x1="335" y1="93" x2="1010" y2="93" stroke="#181818" stroke-width="2.2"/>

            <g>
                <rect x="185" y="160" width="990" height="245" rx="4" fill="none" stroke="#222" stroke-width="3"/>
                <rect x="175" y="160" width="10" height="245" fill="#d6d6d6"/>
                <rect x="1175" y="160" width="10" height="245" fill="#d6d6d6"/>
                <rect x="130" y="405" width="1100" height="10" fill="#cfcfcf"/>
                <line x1="115" y1="421" x2="1245" y2="421" stroke="#9a9a9a" stroke-width="3"/>
            </g>

            {doors_svg}

            <text x="710" y="365" fill="#148C2E" font-size="15" font-weight="1000" text-anchor="middle">APERTURA</text>
            <text x="710" y="386" fill="#148C2E" font-size="15" font-weight="1000" text-anchor="middle">AUTOMATICA</text>

            <line x1="92" y1="160" x2="92" y2="405" stroke="#003C96" stroke-width="2"/>
            <line x1="80" y1="160" x2="104" y2="160" stroke="#003C96" stroke-width="2"/>
            <line x1="80" y1="405" x2="104" y2="405" stroke="#003C96" stroke-width="2"/>
            <text x="84" y="260" fill="#003C96" font-size="13" font-weight="900" text-anchor="end">ALTEZZA LUCE</text>
            <text x="84" y="286" fill="#003C96" font-size="15" font-weight="1000" text-anchor="end">{altezza} mm</text>

            <line x1="1260" y1="95" x2="1260" y2="405" stroke="#003C96" stroke-width="2"/>
            <line x1="1248" y1="95" x2="1272" y2="95" stroke="#003C96" stroke-width="2"/>
            <line x1="1248" y1="405" x2="1272" y2="405" stroke="#003C96" stroke-width="2"/>
            <text x="1278" y="260" fill="#003C96" font-size="13" font-weight="900">ALTEZZA TOTALE</text>
            <text x="1278" y="286" fill="#003C96" font-size="15" font-weight="1000">{altezza + 100} mm</text>

            <line x1="465" y1="440" x2="895" y2="440" stroke="#003C96" stroke-width="2"/>
            <line x1="465" y1="429" x2="465" y2="451" stroke="#003C96" stroke-width="2"/>
            <line x1="895" y1="429" x2="895" y2="451" stroke="#003C96" stroke-width="2"/>
            <text x="680" y="434" fill="#003C96" font-size="13" font-weight="900" text-anchor="middle">LUCE NETTA DI PASSAGGIO</text>
            <text x="680" y="464" fill="#003C96" font-size="16" font-weight="1000" text-anchor="middle">{luce} mm</text>

            <line x1="185" y1="502" x2="1175" y2="502" stroke="#003C96" stroke-width="2"/>
            <line x1="185" y1="491" x2="185" y2="513" stroke="#003C96" stroke-width="2"/>
            <line x1="1175" y1="491" x2="1175" y2="513" stroke="#003C96" stroke-width="2"/>
            <text x="680" y="497" fill="#003C96" font-size="13" font-weight="900" text-anchor="middle">LUNGHEZZA TRAVERSA</text>
            <text x="680" y="527" fill="#003C96" font-size="16" font-weight="1000" text-anchor="middle">{int(traversa*1000)} mm</text>
        </svg>
    </div>

    <div class="metrics">
        <div class="metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
        <div class="metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
        <div class="metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div>
        <div class="metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        <div class="metric">Portata<b>120 kg</b><small>Per anta</small></div>
        <div class="metric">Velocità<b>0,6 m/s</b><small>Regolabile</small></div>
    </div>
</div>
</body>
</html>
"""





# =========================
# V1000 PROFESSIONAL SA-TEC / SESAMO
# Render diretto con st.markdown: non usa components, non sparisce.
# =========================
def v1000_style():
    st.markdown('''
    <style>
    .stApp{background:linear-gradient(180deg,#F4F8FF 0%,#FFFFFF 75%)!important;}
    .block-container{padding-top:.6rem!important;max-width:1580px!important;}
    .v1000-header{background:#fff;border:1px solid #C9DCF7;border-radius:20px;overflow:hidden;box-shadow:0 10px 26px rgba(0,43,103,.10);margin:6px 0 12px 0;}
    .v1000-header-top{display:grid;grid-template-columns:190px minmax(0,1fr) 330px;align-items:center;min-height:128px;background:#fff;}
    .v1000-logo-box{height:128px;border-right:1px solid #D8E7FB;display:flex;align-items:center;justify-content:center;background:#fff;padding:10px;}
    .v1000-logo-img{max-width:145px;max-height:105px;object-fit:contain;}
    .v1000-title-box{padding:18px 26px;}.v1000-title{color:#003C96!important;font-size:42px;line-height:1;font-weight:1000;letter-spacing:.3px;}
    .v1000-subtitle{color:#475569!important;font-size:17px;font-weight:900;margin-top:10px;letter-spacing:.4px;text-transform:uppercase;}
    .v1000-company{border-left:1px solid #D8E7FB;padding:16px 22px;color:#061A40!important;font-size:14px;line-height:1.55;font-weight:900;}.v1000-company b{color:#003C96!important;}
    .v1000-nav{background:linear-gradient(90deg,#003C96,#0057D9);min-height:48px;display:grid;grid-template-columns:repeat(6,1fr);align-items:center;color:#fff!important;}
    .v1000-nav div{text-align:center;font-size:14px;font-weight:1000;color:#fff!important;border-right:1px solid rgba(255,255,255,.22);}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;border-right:5px solid #F5B301!important;}
    section[data-testid="stSidebar"] *{color:#fff!important;-webkit-text-fill-color:#fff!important;}
    section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea,section[data-testid="stSidebar"] [data-baseweb="input"],section[data-testid="stSidebar"] [data-baseweb="input"] *,section[data-testid="stSidebar"] [data-baseweb="select"],section[data-testid="stSidebar"] [data-baseweb="select"] *{background:#fff!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    [data-testid="stCheckbox"] label{background:#fff!important;border:2px solid #C9DCF7!important;border-radius:14px!important;padding:10px 12px!important;box-shadow:0 4px 12px rgba(0,87,217,.06)!important;transition:all .18s ease!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    [data-testid="stCheckbox"] label:hover{border-color:#0057D9!important;background:#F4F8FF!important;}
    [data-testid="stCheckbox"] label:has(input:checked){background:#EAF3FF!important;border-color:#0057D9!important;box-shadow:0 0 0 3px rgba(0,87,217,.16),0 8px 18px rgba(0,87,217,.12)!important;}
    .v1000-sheet{background:#fff;border:1px solid #D8E7FB;border-radius:18px;overflow:hidden;box-shadow:0 12px 30px rgba(0,42,110,.10);margin-bottom:12px;}
    .v1000-sheet-head{display:flex;justify-content:space-between;align-items:flex-start;padding:18px 22px 8px 22px;}.v1000-sheet-title{color:#0047B8;font-size:25px;font-weight:1000;line-height:1.12;}.v1000-sheet-sub{color:#64748B;font-size:13px;font-weight:900;margin-top:6px;text-transform:uppercase;letter-spacing:.4px;}
    .v1000-brand{color:#0047B8;font-size:30px;font-weight:1000;text-align:right;line-height:1;}.v1000-brand small{display:block;color:#475569;font-size:11px;letter-spacing:1.2px;margin-top:4px;}
    .v1000-svgbox{padding:4px 18px 0 18px;}.v1000-svgbox svg{width:100%;height:auto;display:block;border:1px solid #EDF3FC;border-radius:14px;background:white;}
    .v1000-metrics{border-top:1px solid #D8E7FB;background:#FBFDFF;display:grid;grid-template-columns:repeat(6,1fr);}.v1000-metric{padding:13px 8px;border-right:1px solid #D8E7FB;min-height:78px;text-align:center;color:#06245C;font-weight:900;}.v1000-metric b{display:block;color:#0057D9;font-size:18px;margin-top:4px;}.v1000-metric small{display:block;color:#465B78;font-size:10px;margin-top:3px;}
    </style>
    ''', unsafe_allow_html=True)

def v1000_header():
    st.markdown('''
    <div class="v1000-header"><div class="v1000-header-top"><div class="v1000-logo-box"><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAT4AAACfCAMAAABX0UX9AAAA81BMVEX/////fQEAAAD/cwD+xKb+dQD+9vD+eQD8////kkX/fABCQkL//v/+bwDT09P+//3/7+b+gSjc3Nzi4uLy8vKlpaV8fHzGxsavr6+9vb1PT0/q6uqYmJj4+PiOjo7W1tZycnJZWVmEhIRra2s0NDQ7OzsrKytjY2PMzMy/v78iIiL9agD/fxb9tIL7vJX5+PJJSUkXFxefn5/99un+rYD/lV79oGD95Nb9qnT+w6f+xJn+ji/73sL70Ln8upL+3sv/uJr+ybP/0rH+ijr9oWb9nFj/hwD/jCf/k0/+fyr9rGv9mEv9nWf7tHz6yqb8iEP63dBy3yr3AAAOEUlEQVR4nO2dCVfjOBLHFYItYRTkkHAGczZHQ0iaDp2wQMg0ge6eyQ473//TrEqHLSdKePuwm43wf982+AL0mypVqSQ5CBUqVKhQoUKFChUqlL0YsZykTF7L5TfafuG8irJOxx8XY8gPw4nTGamNGH3vZmem8MJLq3KxSBAJW9ffyhUvB/EfT/Ix6/dQWCmZCrxuj3CvZbyN/g0uZS9v0SHvJSa+IAiai/wcp4copaRXzgPfv5A7vjtmfbiVXCHo1ssBX3kxr5j0Hkrj83r6PFjIbR7W5zC+AMf4uAsTn58p8M3UGL7L+AI3v/ZdDrHDYXyl0jdGicikOT3WDnIwP4fxBSV8z2jSuBevcN7ZGrM+r08MfCQH73UaH+62k2EweShCxyvS+BQn7I16kh5Fgy7Onp6j+HCzWfI8HMCYVFxgqNfMY9DmIr6g/BCG4fc/noejfiQvEIL+LkYdr0lZ3wt3VgLMCGJMtK7/vT8qrO81CXw83nJ4kOrJ4TxlZLFSLufQ8zmGDyouwcU9SRdBeO78WHmdRIGPhB7GfZKuIVHuvuQG55C1uIYPhRfdNhmbgID+j/o/8wgcjuCjnBC0wr8ZEALGNn6doc4lLvK+KQJ4jJDBsOkTa/GXOzAZNAt8U0Sh33vCuOrbJ24oDx/kMYd6qRP4wF8XYVRR9e0zD4y7NOtcFAUru0jvGVKT6dYHBugHRcXFKtYqSzJVX/Zz1rvIj6CwPptuK8otAd/U5pCfhfXZFMZleI6PTW0NeS7qfTZxfAoM4IM6gf2+HGZ6XcDHfunW/OkTEg2efnYQtTRqUFifVZfarKp+5/EX9nBILQkMzWGywwl8vbLu+x6aZRzgZ0YtjSKoVeCzqb2kmyP4eJfIFkEo6RSJi1V/pYKCd29N/HhCOMp6qtwFfJQsprxSZH+W2xh6wKVshx4u4GPmur6gVL6esmSRoEGW6FzBh5A/TGwKL7XtDaKUkazni5zAR9i/BRZIn/Fde8rAA6r2lwW+SbFkEhcvTamYSl17paLvGxeLx2Pcc1F7xmrtR5yt+TmBD6G+qiQ/EcZ7uBkN6mdbsncCH2UdiQ9SFmYbsGkREmYaPZzAxyipaHzWxoBJCqiMkPZThoUXJ/DxEa70ySkJM89Z1Nw5A4KX2a05cAIfQ+TbTHyIPstV9gQmNNFtJasO0A18lHTxTHyd5p2Mx2LNFbmvZuTALuDjg1myNNv6wiZ+gHXOlMolCP5lNvxcwAfzlMlMm1V9L8C33G+TOuBLJgHYCXzsl2fMtNl0jUuBt9TnAVi3tj3Mov9zAh/6lkwVWcWeYX1QULlpq5Sa93+ZuK8T+EgPz7A+7rNhU1wOvOEjLNfgeQxDnaUMllw5gY+R2/LUyAtLdGF1kGCFvQcq0hfGY8g/b586cgIfIexZlFJs+Ai3vm7CqTzsiVANCWB76a38nMAHhVBhSVbrozxtSdw0KAWLBMYglF/ovXWbmxP4wD9FwbnqTxareE79V9rIvFHYGfjgweSt5VMn8AlBKcBaMiCDdIwNYNORdxdCDv3W7M8ZfJS0L8s2fNS3RYjAuxtwSy2sT4n3Z9HjMLS05aZsndvFd21K3rpTyxl8FLqysGN5K9K9bU1zEJS8R0SeCutLxHrh5CuRGBrZV5XiG9R7a+bsFD56GVrmOcZDh1YQLL65cO8UPv8/tlnKqZPjP94+6nUK30PTNualfEhsbXsG+9ycwUc4pXjUwcSYQoURHlJu8tnR5hA+Pox9KGt8sIuIqjV+UCGFUVuxo3KWGOXDttj65Ppw0TCxrTyj2ry7+BBp4UDho4wMWmovOczxMtS5y8X43MFH2lWcVFz8n+VHvS0aNrTl1fs5gw+1vLhgxchlOSjfGyMQ0iusb6oo90/fqPeRHtiauUySsXx6PyfwQROuvQQfWwp+lEqVZJEujyRhHruh3cDHY4OwN4mPogEWeQrux28FJows5vEqEifw8YHFSE8VwTSamtoIqiHMaah7/GbxCjC7GH2QPZvAx41Pti3AT3qtHyR/tzmYnxv4BqqkJ6rN7FccJbwWidTIjbB25vBcwMdg+ZmxykCGXaVgoJcVEEIeig2pE4L5Wr+qYAl8ZgEeD9t68Ia4+RV72sYELwUnoe7sAF+6OuU9wUuE1MLcYkflhLj1sRsDH7lOMQq8lt5eSUnnR9bmN+/4GCXtJz0XBPjYmIUFFf1OMJ77PWdtfvOOD5EwCbSwyqA1sfGl3JODXyZnxYt9HYa4RRmRoupHE9E1wCM59uA94H1hfWMaGLO43HlfypM7disDcSdnGGX9NoO5x5ea6K76XQuf8qO4k1DxGsQCnxZPWnxsbJEMhtYpXdxRpReKbjN+8fo84+MRlbykeA3/tq0GKiUN7BfWF4vywPFvkwe87dpCrzyIC3+h5YaPig8WRV6YoJqPVt8s38b42kuF82rB6tBUWx5962Y/7yF+hMeOIu9TYsQ3K/D4efwTE9R5fJPMGfWzjR3zjA+RfhI4ghLu2fGV8FPyRC9LeHOOL5X0wauX7Pi8m+SJsFpYn1boJSPYAFbV2503uGvHj4yvsv/I+F4MfJU+H1XYra/UjPFNbFL4wPhY7LtBUBrCXiErvh8lHCYP9TMNvfOMr1012vEIkxpTQkeCj7BOptPl84zvn3JcvQuaBD7UaYrz4kH8DGmPCnyyfPLgxctr1QcC2vEF3i1S6w0ooraazIfDBxNAv5Kw60n7moIPd4l6Fyxl5CXLV9fPLT6EesZ2DSzHFdOc987nMRdugIJ9gU/8zcZrmMG8QFPwBdD5qclelGnnN6/4ELzAIF7vXW7NxFeCzi+W/OCJbBjOKz5G/D8NAoPZ+IJhO/kcgI7c0PGhX0TCiFE4DvSwYiq+Us94djDEHh6OPjI+QlpG1/es9mJNw1fyHkhsfYzQ+0EPtbNYbD+v+HjWl7zHy3shcg/RVOvDI34HFejkp9+RXiajj7nFx6JHMW8BQ1h8T+Q6lqnWV6p2iPg8KFhTxP8Ju+VMVqvNKz6e/8pJW/h/0BVvp5o6aAP9Q9QnURASfr/M6gWwc4wPDaoe9jywIvwUir5tOj7vpv/c9Tk7uniHsyvYA765FLwHyO9fX/cugQbGo8vO1HofKMDY64LvjrTNZoRv+sfTzIMo6XW5CXrli6rP8XFKIPUl/ipUKv/d7o/EycDDM1WyPZ8+9OCgsjjrNb3//4J9u2zQav3R+uPBJ+Hd0kwNu8PZN/yvGn6f+tE+cyL4AGMIC9D3EUSQsZWIWN6rgVI3CJl73+SJ5NaxDwxNX4UDOvnyiTkSo/A/+EcsIRUdUX1jd/esLq9HKynVxB21rd2dlSj5IfqmvT15XNfHcA9FNf20eiQ62+WS98J2ut/V1t+ije0FoYMVONpbSOmIn9r8JL/fr+lHavH1hjg+04cbYlXgiT4UD0Tr+nDtPZqXsw4TVru86atpfPsIHSRHm+qZzfjMljheiX8CHNWuTHzmf4/j+vu0MT9tGq1bOLTg2zUPJS20H59YF8cxvmU4WouvcnyN1I/bjqb+IXOp+lWqeRvj+NbHnFk4axR758KJ+CkxvoVVfrRt4jtKP78564+ZPylL2d+VbV6uK3zL20Jfdg7F4dXh4bH45hTMx0Qs3DHB9zVlb7XYdddP5VfH3Fe6Ie+yIvHdcmNVW1EEovVlbTSNL/DNEeAzHV64c4LvIHW1po2P37XuoPlF27HLRbztGxGK8UmpMADQzhau1vnpKCYh7RbuSvBx7z418NWlmy9HsVEevFdT81C0rK2PJzAizRjDt5rYTPS5oR46NvAJHAa+TWRcrKnHRYCRT500fncbc5SyvoX1uEsat75zebyjQ2ac23z5Kq/Akwa+VKxpKEcWCZ/y473f3MRcFQdGzUfh0xly9CkxKy3JZF8x45myie/EDLWNHflVdJDryf3OyGi4BKjwnR5xAbEkiTvXACWHLSod/zD9U1JqnE7icyp2pPIyMAwzKYEu0ezoloVLK4evqfEKdH4fF1/DzJt5FziOD22YPKATkwNeHky3xDdXDY3PAH38UfChRjICgzRkAh9aMTIR4Cepncaj2Q2Nb/1c3/Vp/8Pg4403igIbSTFF40Po86fkXEP57KaZ9Uh8O7H5be98IHw8I46HqQfK+nY2uVb0dboVk9lV0Db39vYk9oNI4duM0+ldFXAayaAjxrf1fs3MT2fLquUqU1sdv2FTeebJWbrIwD21rvHFw7XPKifUeZ+Jz6m8DyQSFqo8eN+CT9zQUB5sjtikzhS+NV0sOIm0835W1gi/QFr4Vc3yF8yvos/nJwKP6vROY3xqSqK+trAtvlEWpc000Y7Gp4e7+0jjq+kT/Beda1t1SJvgipD5QskAdJS2vkhUS0V3vzXBTek0xqcIb2l8NdVRQplQGeL6uzU1B6nc47CBGrKqfKUgrW1IKVf9Wkc1Iz5zexL6ogxK44tHfBqfHrQc1VaU76+8/kfNkVRXd758rts5ZlkK2vmxihjb4usX+bRKqc/2FD5pbNtRgq+uqOl4czTPs5STGqO1sDperN9IHx8cii878um6PLmm8ckhIA8UMb70XIp7cTfdo629MlW0oHK9M/W0PDrSzivNccXEl57scC9n3kryuJNN20RlUnNZWN5TuYkOn9IWTw41Prh8VU/hM2dCXUyZo419UVI/WBPTQCfLho4hKNe3TgHx+RFv/cYxnD3Vz37+JG7bhn8+cfh0d3/9Kz+/Js6fyBxvdV10gF92nMpZDEX1en3mDOyrN7wi/rir7DKLhXTim4x/wYdRQaxQoUKFChUqVGi2/gvOwTYVZNtaEgAAAABJRU5ErkJggg==" class="v1000-logo-img"></div><div class="v1000-title-box"><div class="v1000-title">SA-TEC - CONFIGURATORE PORTE AUTOMATICHE</div><div class="v1000-subtitle">Preventivo e disegno tecnico</div></div><div class="v1000-company"><b>SA-TEC S.R.L.s</b><br>📍 Via L. Settembrini 84<br>88046 Lamezia Terme (CZ)<br>☎ 0968-036797<br>✉ sacco.tecnologie@gmail.com</div></div><div class="v1000-nav"><div>⌂ HOME</div><div>⚙ CONFIGURATORE</div><div>▤ CATALOGO</div><div>▥ CODICI</div><div>☏ ASSISTENZA</div><div>⚙ IMPOSTAZIONI</div></div></div>
    ''', unsafe_allow_html=True)

def disegno_porta_v1000(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try: luce=int(float(luce_mm))
    except Exception: luce=1600
    try: altezza=int(float(altezza_mm))
    except Exception: altezza=2200
    try: traversa=float(lunghezza_traversa)
    except Exception: traversa=0.0
    due_ante='2' in str(ante or '')
    ante_numero='2 ANTE' if due_ante else '1 ANTA'
    titolo='PORTA SCORREVOLE AUTOMATICA A 2 ANTE' if due_ante else 'PORTA SCORREVOLE AUTOMATICA A 1 ANTA'
    if due_ante:
        ante_svg='''<rect x="250" y="190" width="430" height="245" fill="url(#glass)" stroke="#0B82F0" stroke-width="4"/><rect x="680" y="190" width="430" height="245" fill="url(#glass)" stroke="#0B82F0" stroke-width="4"/><line x1="680" y1="190" x2="680" y2="435" stroke="#003C96" stroke-width="4"/><path d="M660 315 L555 315" stroke="#148C2E" stroke-width="9" stroke-linecap="round"/><polygon points="555,315 577,302 577,328" fill="#148C2E"/><path d="M700 315 L805 315" stroke="#148C2E" stroke-width="9" stroke-linecap="round"/><polygon points="805,315 783,302 783,328" fill="#148C2E"/><rect x="415" y="145" width="82" height="18" rx="4" fill="#111"/><line x1="438" y1="163" x2="438" y2="190" stroke="#111" stroke-width="5"/><line x1="474" y1="163" x2="474" y2="190" stroke="#111" stroke-width="5"/><rect x="785" y="145" width="82" height="18" rx="4" fill="#111"/><line x1="808" y1="163" x2="808" y2="190" stroke="#111" stroke-width="5"/><line x1="844" y1="163" x2="844" y2="190" stroke="#111" stroke-width="5"/>'''
    else:
        ante_svg='''<rect x="390" y="190" width="560" height="245" fill="url(#glass)" stroke="#0B82F0" stroke-width="4"/><path d="M660 315 L845 315" stroke="#148C2E" stroke-width="9" stroke-linecap="round"/><polygon points="845,315 823,302 823,328" fill="#148C2E"/><rect x="515" y="145" width="82" height="18" rx="4" fill="#111"/><line x1="538" y1="163" x2="538" y2="190" stroke="#111" stroke-width="5"/><line x1="574" y1="163" x2="574" y2="190" stroke="#111" stroke-width="5"/><rect x="805" y="145" width="82" height="18" rx="4" fill="#111"/><line x1="828" y1="163" x2="828" y2="190" stroke="#111" stroke-width="5"/><line x1="864" y1="163" x2="864" y2="190" stroke="#111" stroke-width="5"/>'''
    html=f'''
    <div class="v1000-sheet"><div class="v1000-sheet-head"><div><div class="v1000-sheet-title">V1000 PROFESSIONAL - {titolo}</div><div class="v1000-sheet-sub">SESAMO POWERCORE PW100 · SA-TEC · Preventivo e disegno tecnico</div></div><div class="v1000-brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div></div><div class="v1000-svgbox">
    <svg viewBox="0 0 1360 560" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="rail" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fff"/><stop offset="12%" stop-color="#d9d9d9"/><stop offset="30%" stop-color="#9b9b9b"/><stop offset="50%" stop-color="#f7f7f7"/><stop offset="72%" stop-color="#b8b8b8"/><stop offset="100%" stop-color="#6f6f6f"/></linearGradient><linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#fff" stop-opacity=".98"/><stop offset="40%" stop-color="#d9f1ff" stop-opacity=".74"/><stop offset="100%" stop-color="#91d7ff" stop-opacity=".78"/></linearGradient><linearGradient id="motor" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#3A3A3A"/><stop offset="55%" stop-color="#101010"/><stop offset="100%" stop-color="#020202"/></linearGradient><filter id="drop"><feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000" flood-opacity=".20"/></filter></defs>
    <rect x="130" y="60" width="1100" height="76" rx="3" fill="url(#rail)" stroke="#202020" stroke-width="2.5" filter="url(#drop)"/><line x1="160" y1="82" x2="1200" y2="82" stroke="#242424" stroke-width="3"/><line x1="160" y1="108" x2="1200" y2="108" stroke="#505050" stroke-width="2"/><line x1="160" y1="124" x2="1200" y2="124" stroke="#222" stroke-width="1.5"/><text x="220" y="88" fill="#0057D9" font-size="20" font-weight="1000" text-anchor="middle">SESAMO</text><text x="220" y="116" fill="#0057D9" font-size="16" font-weight="1000" text-anchor="middle">SA-TEC</text><rect x="1015" y="74" width="132" height="46" rx="5" fill="#111"/><rect x="1023" y="77" width="112" height="40" rx="5" fill="url(#motor)"/><rect x="1140" y="83" width="45" height="27" rx="4" fill="#4a4a4a"/><text x="1162" y="101" fill="#fff" font-size="11" font-weight="900" text-anchor="middle">MOT</text>
    <line x1="330" y1="98" x2="1010" y2="98" stroke="#181818" stroke-width="2.3"/><g fill="#111"><circle cx="330" cy="98" r="11"/><circle cx="390" cy="98" r="11"/><circle cx="575" cy="98" r="11"/><circle cx="635" cy="98" r="11"/><circle cx="820" cy="98" r="11"/><circle cx="880" cy="98" r="11"/><circle cx="1010" cy="98" r="11"/></g><g fill="#777"><circle cx="330" cy="98" r="4.5"/><circle cx="390" cy="98" r="4.5"/><circle cx="575" cy="98" r="4.5"/><circle cx="635" cy="98" r="4.5"/><circle cx="820" cy="98" r="4.5"/><circle cx="880" cy="98" r="4.5"/><circle cx="1010" cy="98" r="4.5"/></g><g fill="#e9e9e9" stroke="#333" stroke-width="1.5"><rect x="285" y="112" width="42" height="24" rx="3"/><rect x="475" y="112" width="42" height="24" rx="3"/><rect x="660" y="112" width="42" height="24" rx="3"/><rect x="845" y="112" width="42" height="24" rx="3"/><rect x="1030" y="112" width="42" height="24" rx="3"/></g>
    <rect x="185" y="170" width="990" height="275" rx="4" fill="none" stroke="#222" stroke-width="3"/><rect x="175" y="170" width="10" height="275" fill="#d6d6d6"/><rect x="1175" y="170" width="10" height="275" fill="#d6d6d6"/><rect x="130" y="445" width="1100" height="11" fill="#cfcfcf"/><line x1="115" y1="462" x2="1245" y2="462" stroke="#9a9a9a" stroke-width="3"/>{ante_svg}<text x="680" y="365" fill="#148C2E" font-size="16" font-weight="1000" text-anchor="middle">APERTURA</text><text x="680" y="388" fill="#148C2E" font-size="16" font-weight="1000" text-anchor="middle">AUTOMATICA</text>
    <line x1="92" y1="170" x2="92" y2="445" stroke="#003C96" stroke-width="2"/><line x1="80" y1="170" x2="104" y2="170" stroke="#003C96" stroke-width="2"/><line x1="80" y1="445" x2="104" y2="445" stroke="#003C96" stroke-width="2"/><text x="84" y="285" fill="#003C96" font-size="13" font-weight="900" text-anchor="end">ALTEZZA LUCE</text><text x="84" y="312" fill="#003C96" font-size="16" font-weight="1000" text-anchor="end">{altezza} mm</text><line x1="1260" y1="100" x2="1260" y2="445" stroke="#003C96" stroke-width="2"/><line x1="1248" y1="100" x2="1272" y2="100" stroke="#003C96" stroke-width="2"/><line x1="1248" y1="445" x2="1272" y2="445" stroke="#003C96" stroke-width="2"/><text x="1278" y="285" fill="#003C96" font-size="13" font-weight="900">ALTEZZA TOTALE</text><text x="1278" y="312" fill="#003C96" font-size="16" font-weight="1000">{altezza+100} mm</text><line x1="465" y1="480" x2="895" y2="480" stroke="#003C96" stroke-width="2"/><line x1="465" y1="469" x2="465" y2="491" stroke="#003C96" stroke-width="2"/><line x1="895" y1="469" x2="895" y2="491" stroke="#003C96" stroke-width="2"/><text x="680" y="474" fill="#003C96" font-size="13" font-weight="900" text-anchor="middle">LUCE NETTA DI PASSAGGIO</text><text x="680" y="504" fill="#003C96" font-size="16" font-weight="1000" text-anchor="middle">{luce} mm</text><line x1="185" y1="530" x2="1175" y2="530" stroke="#003C96" stroke-width="2"/><line x1="185" y1="519" x2="185" y2="541" stroke="#003C96" stroke-width="2"/><line x1="1175" y1="519" x2="1175" y2="541" stroke="#003C96" stroke-width="2"/><text x="680" y="525" fill="#003C96" font-size="13" font-weight="900" text-anchor="middle">LUNGHEZZA TRAVERSA</text><text x="680" y="555" fill="#003C96" font-size="16" font-weight="1000" text-anchor="middle">{int(traversa*1000)} mm</text></svg></div>
    <div class="v1000-metrics"><div class="v1000-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div><div class="v1000-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div><div class="v1000-metric">Altezza luce<b>{altezza} mm</b><small>Personalizzata</small></div><div class="v1000-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div><div class="v1000-metric">Portata<b>120 kg</b><small>Per anta</small></div><div class="v1000-metric">Velocità<b>0,6 m/s</b><small>Regolabile</small></div></div></div>'''
    return html




# =========================
# V1001 - RENDER SEMPLICE PROFESSIONALE
# Solo traversa rettangolare + ante vetro.
# Niente interno traversa, niente motore, niente carrelli.
# =========================
def v1001_style():
    st.markdown("""
    <style>
    .stApp{background:linear-gradient(180deg,#F4F8FF 0%,#FFFFFF 75%)!important;}
    .block-container{padding-top:.6rem!important;max-width:1500px!important;}
    .v1001-header{background:#fff;border:1px solid #C9DCF7;border-radius:18px;overflow:hidden;box-shadow:0 8px 22px rgba(0,43,103,.10);margin:6px 0 14px 0;}
    .v1001-headtop{display:grid;grid-template-columns:1fr 330px;align-items:center;min-height:112px;}
    .v1001-titlebox{padding:18px 24px;}
    .v1001-title{color:#003C96!important;-webkit-text-fill-color:#003C96!important;font-size:40px;line-height:1;font-weight:1000;}
    .v1001-subtitle{color:#475569!important;-webkit-text-fill-color:#475569!important;font-size:16px;font-weight:900;margin-top:10px;text-transform:uppercase;}
    .v1001-company{border-left:1px solid #D8E7FB;padding:16px 22px;color:#061A40!important;-webkit-text-fill-color:#061A40!important;font-size:14px;line-height:1.55;font-weight:900;}
    .v1001-company b{color:#003C96!important;-webkit-text-fill-color:#003C96!important;}
    .v1001-bar{background:linear-gradient(90deg,#003C96,#0057D9);height:46px;display:flex;align-items:center;justify-content:center;color:white!important;-webkit-text-fill-color:white!important;font-weight:1000;letter-spacing:.3px;}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;border-right:5px solid #F5B301!important;}
    section[data-testid="stSidebar"] *{color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important;}
    section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea,section[data-testid="stSidebar"] [data-baseweb="input"],section[data-testid="stSidebar"] [data-baseweb="input"] *,section[data-testid="stSidebar"] [data-baseweb="select"],section[data-testid="stSidebar"] [data-baseweb="select"] *{background:#FFFFFF!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    .stButton button,.stDownloadButton button{background:#FFFFFF!important;color:#0057D9!important;-webkit-text-fill-color:#0057D9!important;border:2px solid #0057D9!important;border-radius:14px!important;min-height:48px!important;font-size:15px!important;font-weight:1000!important;}
    .stButton button:hover,.stDownloadButton button:hover{background:#F5B301!important;color:#111!important;-webkit-text-fill-color:#111!important;border-color:#F5B301!important;}
    [data-testid="stCheckbox"] label{background:#FFFFFF!important;border:2px solid #C9DCF7!important;border-radius:14px!important;padding:10px 12px!important;color:#071124!important;-webkit-text-fill-color:#071124!important;font-weight:900!important;}
    [data-testid="stCheckbox"] label:has(input:checked){background:#EAF3FF!important;border-color:#0057D9!important;box-shadow:0 0 0 3px rgba(0,87,217,.16)!important;}
    .v1001-sheet{background:#fff;border:1px solid #D8E7FB;border-radius:18px;overflow:hidden;box-shadow:0 10px 26px rgba(0,42,110,.08);margin-bottom:14px;}
    .v1001-sheet-head{display:flex;justify-content:space-between;align-items:flex-start;padding:18px 22px 8px 22px;}
    .v1001-sheet-title{color:#0047B8;font-size:24px;font-weight:1000;}
    .v1001-sheet-sub{color:#64748B;font-size:13px;font-weight:900;margin-top:6px;text-transform:uppercase;}
    .v1001-brand{color:#0047B8;font-size:30px;font-weight:1000;text-align:right;}
    .v1001-brand small{display:block;color:#475569;font-size:11px;letter-spacing:1.2px;margin-top:4px;}
    .v1001-svgbox{padding:4px 18px 0 18px;}
    .v1001-svgbox svg{width:100%;height:auto;display:block;border:1px solid #EDF3FC;border-radius:14px;background:white;}
    .v1001-metrics{border-top:1px solid #D8E7FB;background:#FBFDFF;display:grid;grid-template-columns:repeat(4,1fr);}
    .v1001-metric{padding:13px 8px;border-right:1px solid #D8E7FB;text-align:center;color:#06245C;font-weight:900;}
    .v1001-metric:last-child{border-right:0;}
    .v1001-metric b{display:block;color:#0057D9;font-size:18px;margin-top:4px;}
    .v1001-metric small{display:block;color:#465B78;font-size:10px;margin-top:3px;}
    </style>
    """, unsafe_allow_html=True)

def v1001_header():
    st.markdown("""
    <div class="v1001-header">
        <div class="v1001-headtop">
            <div class="v1001-titlebox">
                <div class="v1001-title">SA-TEC - CONFIGURATORE PORTE AUTOMATICHE</div>
                <div class="v1001-subtitle">Disegno tecnico semplice, pulito e proporzionato</div>
            </div>
            <div class="v1001-company">
                <b>SA-TEC S.R.L.s</b><br>
                Via L. Settembrini 84<br>
                88046 Lamezia Terme (CZ)<br>
                ☎ 0968-036797<br>
                ✉ sacco.tecnologie@gmail.com
            </div>
        </div>
        <div class="v1001-bar">SESAMO POWERCORE PW100 · PREVENTIVO PORTE AUTOMATICHE</div>
    </div>
    """, unsafe_allow_html=True)

def disegno_porta_v1001(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo = "PORTA SCORREVOLE AUTOMATICA A 2 ANTE" if due_ante else "PORTA SCORREVOLE AUTOMATICA A 1 ANTA"

    if due_ante:
        ante_svg = """
        <rect x="235" y="170" width="455" height="250" rx="4" fill="url(#glassDark)" stroke="#0B82F0" stroke-width="4"/>
        <rect x="690" y="170" width="455" height="250" rx="4" fill="url(#glassDark)" stroke="#0B82F0" stroke-width="4"/>
        <line x1="690" y1="170" x2="690" y2="420" stroke="#003C96" stroke-width="5"/>
        <path d="M660 295 L555 295" stroke="#148C2E" stroke-width="9" stroke-linecap="round"/>
        <polygon points="555,295 578,282 578,308" fill="#148C2E"/>
        <path d="M720 295 L825 295" stroke="#148C2E" stroke-width="9" stroke-linecap="round"/>
        <polygon points="825,295 802,282 802,308" fill="#148C2E"/>
        """
    else:
        ante_svg = """
        <rect x="405" y="170" width="560" height="250" rx="4" fill="url(#glassDark)" stroke="#0B82F0" stroke-width="4"/>
        <path d="M650 295 L835 295" stroke="#148C2E" stroke-width="9" stroke-linecap="round"/>
        <polygon points="835,295 812,282 812,308" fill="#148C2E"/>
        """

    html = f"""
    <div class="v1001-sheet">
        <div class="v1001-sheet-head">
            <div>
                <div class="v1001-sheet-title">V1001 - {titolo}</div>
                <div class="v1001-sheet-sub">Solo traversa e ante · niente interno traversa · 1/2 ante automatiche</div>
            </div>
            <div class="v1001-brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div>
        </div>

        <div class="v1001-svgbox">
            <svg viewBox="0 0 1360 520" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="railSimple" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#f7f7f7"/>
                        <stop offset="45%" stop-color="#b8b8b8"/>
                        <stop offset="100%" stop-color="#7c7c7c"/>
                    </linearGradient>
                    <linearGradient id="glassDark" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#ffffff" stop-opacity=".95"/>
                        <stop offset="42%" stop-color="#b9e3ff" stop-opacity=".78"/>
                        <stop offset="100%" stop-color="#5fb6ee" stop-opacity=".82"/>
                    </linearGradient>
                    <filter id="drop2" x="-10%" y="-20%" width="120%" height="150%">
                        <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000" flood-opacity=".18"/>
                    </filter>
                </defs>

                <rect x="150" y="70" width="1060" height="72" rx="4" fill="url(#railSimple)" stroke="#222" stroke-width="2.5" filter="url(#drop2)"/>
                <text x="235" y="112" fill="#0057D9" font-size="28" font-weight="1000" text-anchor="middle">SESAMO</text>
                <text x="1130" y="113" fill="#003C96" font-size="18" font-weight="1000" text-anchor="middle">PW100</text>

                <rect x="185" y="150" width="990" height="290" rx="4" fill="none" stroke="#222" stroke-width="3"/>
                <rect x="175" y="150" width="10" height="290" fill="#d6d6d6"/>
                <rect x="1175" y="150" width="10" height="290" fill="#d6d6d6"/>
                <rect x="130" y="440" width="1100" height="11" fill="#cfcfcf"/>
                <line x1="115" y1="458" x2="1245" y2="458" stroke="#9a9a9a" stroke-width="3"/>

                {ante_svg}

                <text x="680" y="350" fill="#148C2E" font-size="17" font-weight="1000" text-anchor="middle">APERTURA AUTOMATICA</text>

                <line x1="85" y1="150" x2="85" y2="440" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="150" x2="97" y2="150" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="440" x2="97" y2="440" stroke="#003C96" stroke-width="2"/>
                <text x="75" y="290" fill="#003C96" font-size="14" font-weight="900" text-anchor="end">ALTEZZA</text>
                <text x="75" y="316" fill="#003C96" font-size="16" font-weight="1000" text-anchor="end">{altezza} mm</text>

                <line x1="465" y1="475" x2="895" y2="475" stroke="#003C96" stroke-width="2"/>
                <line x1="465" y1="464" x2="465" y2="486" stroke="#003C96" stroke-width="2"/>
                <line x1="895" y1="464" x2="895" y2="486" stroke="#003C96" stroke-width="2"/>
                <text x="680" y="468" fill="#003C96" font-size="14" font-weight="900" text-anchor="middle">LUCE NETTA</text>
                <text x="680" y="500" fill="#003C96" font-size="17" font-weight="1000" text-anchor="middle">{luce} mm</text>
            </svg>
        </div>

        <div class="v1001-metrics">
            <div class="v1001-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
            <div class="v1001-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
            <div class="v1001-metric">Altezza<b>{altezza} mm</b><small>Luce porta</small></div>
            <div class="v1001-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        </div>
    </div>
    """
    return html


v1001_style()
v1001_header()



# =========================
# V1004 - MOCKUP PULITO PROFESSIONALE
# Traversa grande, ante vetro scure, 1/2 ante automatiche.
# =========================
def disegno_porta_v1004(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo = "PORTA SCORREVOLE AUTOMATICA A 2 ANTE" if due_ante else "PORTA SCORREVOLE AUTOMATICA A 1 ANTA"

    if due_ante:
        ante_svg = '''
            <rect x="330" y="188" width="350" height="300" rx="5" fill="url(#glassSoft)" stroke="#0057D9" stroke-width="5"/>
            <rect x="680" y="188" width="350" height="300" rx="5" fill="url(#glassSoft)" stroke="#0057D9" stroke-width="5"/>
            <line x1="680" y1="188" x2="680" y2="488" stroke="#003C96" stroke-width="5"/>
            <path d="M655 340 L555 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
            <polygon points="555,340 578,327 578,353" fill="#0B8F2A"/>
            <path d="M705 340 L805 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
            <polygon points="805,340 782,327 782,353" fill="#0B8F2A"/>
        '''
    else:
        ante_svg = '''
            <rect x="430" y="188" width="510" height="300" rx="5" fill="url(#glassSoft)" stroke="#0057D9" stroke-width="5"/>
            <rect x="685" y="188" width="255" height="300" rx="0" fill="rgba(10,60,90,.08)"/>
            <path d="M600 340 L780 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
            <polygon points="780,340 756,326 756,354" fill="#0B8F2A"/>
        '''

    return f'''
    <div class="v1001-sheet">
        <div class="v1001-sheet-head">
            <div>
                <div class="v1001-sheet-title">V1004 - {titolo}</div>
                <div class="v1001-sheet-sub">Traversa grande · ante vetro scure · grafica pulita</div>
            </div>
            <div class="v1001-brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div>
        </div>

        <div class="v1001-svgbox">
            <svg viewBox="0 0 1360 585" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="railPro" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#eeeeee"/>
                        <stop offset="18%" stop-color="#cfcfcf"/>
                        <stop offset="45%" stop-color="#9a9a9a"/>
                        <stop offset="75%" stop-color="#777777"/>
                        <stop offset="100%" stop-color="#555555"/>
                    </linearGradient>
                    <linearGradient id="glassSoft" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#ffffff" stop-opacity=".92"/>
                        <stop offset="45%" stop-color="#c8eaf7" stop-opacity=".85"/>
                        <stop offset="100%" stop-color="#78b7c9" stop-opacity=".90"/>
                    </linearGradient>
                    <filter id="shadowPro" x="-15%" y="-25%" width="130%" height="170%">
                        <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000000" flood-opacity=".24"/>
                    </filter>
                    <filter id="softShadow" x="-15%" y="-25%" width="130%" height="170%">
                        <feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#000000" flood-opacity=".16"/>
                    </filter>
                </defs>

                <rect x="145" y="60" width="1070" height="96" rx="6" fill="url(#railPro)" stroke="#222" stroke-width="2.5" filter="url(#shadowPro)"/>
                <rect x="155" y="72" width="1050" height="14" rx="3" fill="rgba(255,255,255,.45)"/>
                <rect x="155" y="138" width="1050" height="11" rx="3" fill="rgba(0,0,0,.32)"/>
                <text x="255" y="122" fill="#0057D9" font-size="34" font-weight="1000" text-anchor="middle">SESAMO</text>
                <text x="680" y="121" fill="#ffffff" font-size="22" font-weight="1000" text-anchor="middle">TRAVERSA AUTOMAZIONE</text>
                <text x="1110" y="122" fill="#003C96" font-size="26" font-weight="1000" text-anchor="middle">PW100</text>

                <rect x="190" y="156" width="12" height="352" fill="#c8c8c8" stroke="#777" stroke-width="1"/>
                <rect x="1158" y="156" width="12" height="352" fill="#c8c8c8" stroke="#777" stroke-width="1"/>
                <rect x="185" y="156" width="990" height="352" rx="3" fill="none" stroke="#333" stroke-width="3"/>
                <rect x="130" y="508" width="1100" height="12" fill="#cfcfcf"/>
                <line x1="115" y1="525" x2="1245" y2="525" stroke="#9a9a9a" stroke-width="3"/>

                <g filter="url(#softShadow)">
                    {ante_svg}
                </g>

                <text x="680" y="392" fill="#0B8F2A" font-size="19" font-weight="1000" text-anchor="middle">APERTURA AUTOMATICA</text>

                <line x1="86" y1="188" x2="86" y2="508" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="188" x2="99" y2="188" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="508" x2="99" y2="508" stroke="#003C96" stroke-width="2"/>
                <text x="76" y="335" fill="#003C96" font-size="15" font-weight="900" text-anchor="end">ALTEZZA</text>
                <text x="76" y="365" fill="#003C96" font-size="19" font-weight="1000" text-anchor="end">{altezza} mm</text>

                <line x1="420" y1="545" x2="940" y2="545" stroke="#003C96" stroke-width="2"/>
                <line x1="420" y1="533" x2="420" y2="557" stroke="#003C96" stroke-width="2"/>
                <line x1="940" y1="533" x2="940" y2="557" stroke="#003C96" stroke-width="2"/>
                <text x="680" y="538" fill="#003C96" font-size="15" font-weight="900" text-anchor="middle">LUCE NETTA</text>
                <text x="680" y="574" fill="#003C96" font-size="20" font-weight="1000" text-anchor="middle">{luce} mm</text>
            </svg>
        </div>

        <div class="v1001-metrics">
            <div class="v1001-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
            <div class="v1001-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
            <div class="v1001-metric">Altezza<b>{altezza} mm</b><small>Luce porta</small></div>
            <div class="v1001-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        </div>
    </div>
    '''



# =========================
# V1005 - GRAFICA DEFINITIVA SEMPLICE
# Traversa professionale + anta/e vetro scure.
# =========================
def disegno_porta_v1005(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo = "PORTA SCORREVOLE AUTOMATICA A 2 ANTE" if due_ante else "PORTA SCORREVOLE AUTOMATICA A 1 ANTA"

    if due_ante:
        ante_svg = """
        <rect x="330" y="188" width="350" height="300" rx="5" fill="url(#glassSoft)" stroke="#0057D9" stroke-width="5"/>
        <rect x="680" y="188" width="350" height="300" rx="5" fill="url(#glassSoft)" stroke="#0057D9" stroke-width="5"/>
        <rect x="680" y="188" width="175" height="300" fill="rgba(10,60,90,.08)"/>
        <line x1="680" y1="188" x2="680" y2="488" stroke="#003C96" stroke-width="5"/>
        <path d="M655 340 L555 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
        <polygon points="555,340 578,327 578,353" fill="#0B8F2A"/>
        <path d="M705 340 L805 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
        <polygon points="805,340 782,327 782,353" fill="#0B8F2A"/>
        """
    else:
        ante_svg = """
        <rect x="430" y="188" width="510" height="300" rx="5" fill="url(#glassSoft)" stroke="#0057D9" stroke-width="5"/>
        <rect x="685" y="188" width="255" height="300" fill="rgba(10,60,90,.09)"/>
        <path d="M600 340 L780 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
        <polygon points="780,340 756,326 756,354" fill="#0B8F2A"/>
        """

    return f"""
    <div class="v1001-sheet">
        <div class="v1001-sheet-head">
            <div>
                <div class="v1001-sheet-title">V1005 - {titolo}</div>
                <div class="v1001-sheet-sub">Traversa professionale · ante vetro scure · grafica cliente</div>
            </div>
            <div class="v1001-brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div>
        </div>

        <div class="v1001-svgbox">
            <svg viewBox="0 0 1360 585" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="railPro" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#f4f4f4"/>
                        <stop offset="18%" stop-color="#cfcfcf"/>
                        <stop offset="44%" stop-color="#9a9a9a"/>
                        <stop offset="72%" stop-color="#747474"/>
                        <stop offset="100%" stop-color="#565656"/>
                    </linearGradient>
                    <linearGradient id="glassSoft" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#ffffff" stop-opacity=".94"/>
                        <stop offset="45%" stop-color="#c8eaf7" stop-opacity=".86"/>
                        <stop offset="100%" stop-color="#78b7c9" stop-opacity=".91"/>
                    </linearGradient>
                    <filter id="shadowPro" x="-15%" y="-25%" width="130%" height="170%">
                        <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000000" flood-opacity=".24"/>
                    </filter>
                    <filter id="softShadow" x="-15%" y="-25%" width="130%" height="170%">
                        <feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#000000" flood-opacity=".16"/>
                    </filter>
                </defs>

                <rect x="145" y="60" width="1070" height="96" rx="8" fill="url(#railPro)" stroke="#1b1b1b" stroke-width="2.5" filter="url(#shadowPro)"/>
                <rect x="145" y="60" width="28" height="96" rx="8" fill="#242424"/>
                <rect x="1187" y="60" width="28" height="96" rx="8" fill="#242424"/>
                <rect x="165" y="74" width="1030" height="12" rx="3" fill="rgba(255,255,255,.45)"/>
                <line x1="170" y1="111" x2="1188" y2="111" stroke="#555" stroke-width="3"/>
                <line x1="170" y1="119" x2="1188" y2="119" stroke="#dddddd" stroke-width="1"/>
                <rect x="165" y="138" width="1030" height="11" rx="3" fill="rgba(0,0,0,.33)"/>
                <text x="255" y="122" fill="#0057D9" font-size="34" font-weight="1000" text-anchor="middle">SESAMO</text>
                <text x="680" y="121" fill="#ffffff" font-size="22" font-weight="1000" text-anchor="middle">TRAVERSA AUTOMAZIONE</text>
                <text x="1110" y="122" fill="#003C96" font-size="26" font-weight="1000" text-anchor="middle">PW100</text>

                <rect x="190" y="156" width="12" height="352" fill="#c8c8c8" stroke="#777" stroke-width="1"/>
                <rect x="1158" y="156" width="12" height="352" fill="#c8c8c8" stroke="#777" stroke-width="1"/>
                <rect x="185" y="156" width="990" height="352" rx="3" fill="none" stroke="#333" stroke-width="3"/>
                <rect x="130" y="508" width="1100" height="12" fill="#cfcfcf"/>
                <line x1="115" y1="525" x2="1245" y2="525" stroke="#9a9a9a" stroke-width="3"/>

                <g filter="url(#softShadow)">
                    {ante_svg}
                    <path d="M465 190 L610 190 L900 488 L760 488 Z" fill="white" opacity=".16"/>
                </g>

                <text x="680" y="392" fill="#0B8F2A" font-size="19" font-weight="1000" text-anchor="middle">APERTURA AUTOMATICA</text>

                <line x1="86" y1="188" x2="86" y2="508" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="188" x2="99" y2="188" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="508" x2="99" y2="508" stroke="#003C96" stroke-width="2"/>
                <text x="76" y="335" fill="#003C96" font-size="15" font-weight="900" text-anchor="end">ALTEZZA</text>
                <text x="76" y="365" fill="#003C96" font-size="19" font-weight="1000" text-anchor="end">{altezza} mm</text>

                <line x1="420" y1="545" x2="940" y2="545" stroke="#003C96" stroke-width="2"/>
                <line x1="420" y1="533" x2="420" y2="557" stroke="#003C96" stroke-width="2"/>
                <line x1="940" y1="533" x2="940" y2="557" stroke="#003C96" stroke-width="2"/>
                <text x="680" y="538" fill="#003C96" font-size="15" font-weight="900" text-anchor="middle">LUCE NETTA</text>
                <text x="680" y="574" fill="#003C96" font-size="20" font-weight="1000" text-anchor="middle">{luce} mm</text>
            </svg>
        </div>

        <div class="v1001-metrics">
            <div class="v1001-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
            <div class="v1001-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
            <div class="v1001-metric">Altezza<b>{altezza} mm</b><small>Luce porta</small></div>
            <div class="v1001-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        </div>
    </div>
    """



# =========================
# V1006 - CODICE DEFINITIVO GRAFICA TRAVERSA + ANTE
# =========================
def disegno_porta_v1006(ante, luce_mm, altezza_mm, lunghezza_traversa):
    try:
        luce = int(float(luce_mm))
    except Exception:
        luce = 1600
    try:
        altezza = int(float(altezza_mm))
    except Exception:
        altezza = 2200
    try:
        traversa = float(lunghezza_traversa)
    except Exception:
        traversa = 0.0

    due_ante = "2" in str(ante or "")
    ante_numero = "2 ANTE" if due_ante else "1 ANTA"
    titolo = "PORTA SCORREVOLE AUTOMATICA A 2 ANTE" if due_ante else "PORTA SCORREVOLE AUTOMATICA A 1 ANTA"

    if due_ante:
        ante_svg = """
        <rect x="330" y="188" width="350" height="300" rx="5" fill="url(#glassSoft)" stroke="#003C96" stroke-width="7"/>
        <rect x="340" y="198" width="330" height="280" rx="3" fill="none" stroke="#8FD0F4" stroke-width="2" opacity=".95"/>
        <rect x="680" y="188" width="350" height="300" rx="5" fill="url(#glassSoft)" stroke="#003C96" stroke-width="7"/>
        <rect x="690" y="198" width="330" height="280" rx="3" fill="none" stroke="#8FD0F4" stroke-width="2" opacity=".95"/>
        <rect x="680" y="188" width="175" height="300" fill="rgba(10,60,90,.10)"/>
        <line x1="680" y1="188" x2="680" y2="488" stroke="#0B2D6B" stroke-width="6"/>
        <line x1="668" y1="198" x2="668" y2="478" stroke="#6BBDEB" stroke-width="2" opacity=".95"/>
        <line x1="692" y1="198" x2="692" y2="478" stroke="#6BBDEB" stroke-width="2" opacity=".95"/>
        <path d="M655 340 L555 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
        <polygon points="555,340 578,327 578,353" fill="#0B8F2A"/>
        <path d="M705 340 L805 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
        <polygon points="805,340 782,327 782,353" fill="#0B8F2A"/>
        """
    else:
        ante_svg = """
        <rect x="430" y="188" width="510" height="300" rx="5" fill="url(#glassSoft)" stroke="#003C96" stroke-width="7"/>
        <rect x="440" y="198" width="490" height="280" rx="3" fill="none" stroke="#8FD0F4" stroke-width="2" opacity=".95"/>
        <rect x="685" y="188" width="255" height="300" rx="0" fill="rgba(10,60,90,.10)"/>
        <line x1="932" y1="190" x2="932" y2="486" stroke="#0B2D6B" stroke-width="4"/>
        <line x1="918" y1="200" x2="918" y2="476" stroke="#6BBDEB" stroke-width="2" opacity=".95"/>
        <path d="M600 340 L780 340" stroke="#0B8F2A" stroke-width="9" stroke-linecap="round"/>
        <polygon points="780,340 756,326 756,354" fill="#0B8F2A"/>
        """

    return f"""
    <div class="v1001-sheet">
        <div class="v1001-sheet-head">
            <div>
                <div class="v1001-sheet-title">V1006 - {titolo}</div>
                <div class="v1001-sheet-sub">Traversa professionale · ante vetro scure · grafica definitiva</div>
            </div>
            <div class="v1001-brand">SESAMO<small>THE DOOR TECHNOLOGY</small></div>
        </div>

        <div class="v1001-svgbox">
            <svg viewBox="0 0 1360 585" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="railPro" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#f4f4f4"/>
                        <stop offset="18%" stop-color="#cfcfcf"/>
                        <stop offset="44%" stop-color="#9a9a9a"/>
                        <stop offset="72%" stop-color="#747474"/>
                        <stop offset="100%" stop-color="#565656"/>
                    </linearGradient>
                    <linearGradient id="glassSoft" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#ffffff" stop-opacity=".94"/>
                        <stop offset="45%" stop-color="#c8eaf7" stop-opacity=".86"/>
                        <stop offset="100%" stop-color="#78b7c9" stop-opacity=".91"/>
                    </linearGradient>
                    <filter id="shadowPro" x="-15%" y="-25%" width="130%" height="170%">
                        <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000000" flood-opacity=".24"/>
                    </filter>
                    <filter id="softShadow" x="-15%" y="-25%" width="130%" height="170%">
                        <feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#000000" flood-opacity=".16"/>
                    </filter>
                </defs>

                <rect x="145" y="60" width="1070" height="96" rx="8" fill="url(#railPro)" stroke="#1b1b1b" stroke-width="2.5" filter="url(#shadowPro)"/>
                <rect x="145" y="60" width="28" height="96" rx="8" fill="#242424"/>
                <rect x="1187" y="60" width="28" height="96" rx="8" fill="#242424"/>
                <rect x="165" y="74" width="1030" height="12" rx="3" fill="rgba(255,255,255,.45)"/>
                <line x1="170" y1="111" x2="1188" y2="111" stroke="#555" stroke-width="3"/>
                <line x1="170" y1="119" x2="1188" y2="119" stroke="#dddddd" stroke-width="1"/>
                <rect x="165" y="138" width="1030" height="11" rx="3" fill="rgba(0,0,0,.33)"/>
                <text x="255" y="122" fill="#0057D9" font-size="34" font-weight="1000" text-anchor="middle">SESAMO</text>
                <text x="680" y="121" fill="#ffffff" font-size="22" font-weight="1000" text-anchor="middle">TRAVERSA AUTOMAZIONE</text>
                <text x="1110" y="122" fill="#003C96" font-size="26" font-weight="1000" text-anchor="middle">PW100</text>

                <rect x="190" y="156" width="12" height="352" fill="#c8c8c8" stroke="#777" stroke-width="1"/>
                <rect x="1158" y="156" width="12" height="352" fill="#c8c8c8" stroke="#777" stroke-width="1"/>
                <rect x="185" y="156" width="990" height="352" rx="3" fill="none" stroke="#333" stroke-width="3"/>
                <rect x="130" y="508" width="1100" height="12" fill="#cfcfcf"/>
                <line x1="115" y1="525" x2="1245" y2="525" stroke="#9a9a9a" stroke-width="3"/>

                <g filter="url(#softShadow)">
                    {ante_svg}
                    <path d="M465 190 L610 190 L900 488 L760 488 Z" fill="white" opacity=".16"/>
                </g>

                <text x="680" y="392" fill="#0B8F2A" font-size="19" font-weight="1000" text-anchor="middle">APERTURA AUTOMATICA</text>

                <line x1="86" y1="188" x2="86" y2="508" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="188" x2="99" y2="188" stroke="#003C96" stroke-width="2"/>
                <line x1="73" y1="508" x2="99" y2="508" stroke="#003C96" stroke-width="2"/>
                <text x="76" y="335" fill="#003C96" font-size="15" font-weight="900" text-anchor="end">ALTEZZA</text>
                <text x="76" y="365" fill="#003C96" font-size="19" font-weight="1000" text-anchor="end">{altezza} mm</text>

                <line x1="420" y1="545" x2="940" y2="545" stroke="#003C96" stroke-width="2"/>
                <line x1="420" y1="533" x2="420" y2="557" stroke="#003C96" stroke-width="2"/>
                <line x1="940" y1="533" x2="940" y2="557" stroke="#003C96" stroke-width="2"/>
                <text x="680" y="538" fill="#003C96" font-size="15" font-weight="900" text-anchor="middle">LUCE NETTA</text>
                <text x="680" y="574" fill="#003C96" font-size="20" font-weight="1000" text-anchor="middle">{luce} mm</text>
            </svg>
        </div>

        <div class="v1001-metrics">
            <div class="v1001-metric">Tipologia<b>{ante_numero}</b><small>Scorrevole</small></div>
            <div class="v1001-metric">Luce netta<b>{luce} mm</b><small>Passaggio utile</small></div>
            <div class="v1001-metric">Altezza<b>{altezza} mm</b><small>Luce porta</small></div>
            <div class="v1001-metric">Traversa<b>{int(traversa*1000)} mm</b><small>Lunghezza totale</small></div>
        </div>
    </div>
    """

profilo, nome_utente, utente_codice, dati_utente, ricarico_effettivo = login_box()

# V400: riapplica stile dopo login
v400_style()




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
        <div class="incremento-box-v69">
            <div class="incremento-title-v69">Prezzo vendita</div>
            <div class="incremento-note-v69">Seleziona l’incremento commerciale da applicare al preventivo.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    scelta_extra_label = st.sidebar.select_slider(
        "Incremento prezzo vendita",
        options=labels_extra,
        value=labels_extra[0],
        key="ricarico_extra_utente_step10"
    )

    ricarico_extra_utente = float(scelta_extra_label.replace("+", "").replace("%", ""))

    ricarico_effettivo = min(
        ricarico_base_assegnato + ricarico_extra_utente,
        ricarico_cliente_finale
    )

    st.sidebar.markdown(
        f"""
        <div class="incremento-risultato-v69">
            Incremento selezionato: <b>{ricarico_extra_utente:.0f}%</b>
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
# V102 - CSS ADMIN REALE VISIBILE
# =========================
st.markdown("""
<style>
.stApp{
    background:#f5f7fb!important;
}

/* Sidebar sempre professionale */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#061b35 0%,#0b2a4a 60%,#03152f 100%)!important;
    border-right:4px solid #f5b301!important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="input"] *,
section[data-testid="stSidebar"] [data-baseweb="select"] *{
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    background:#ffffff!important;
}
section[data-testid="stSidebar"] .stButton button{
    background:#ffffff!important;
    color:#06499b!important;
    -webkit-text-fill-color:#06499b!important;
    border-radius:14px!important;
    min-height:48px!important;
    font-weight:900!important;
    border:2px solid rgba(255,255,255,.35)!important;
}
section[data-testid="stSidebar"] .stButton button:hover{
    background:#f5b301!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}

/* Area principale */
.block-container{
    padding-top:1.2rem!important;
}
.block-container,
.block-container *:not(svg):not(path){
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}
.block-container h1,
.block-container h2,
.block-container h3{
    color:#06499b!important;
    -webkit-text-fill-color:#06499b!important;
    font-weight:900!important;
}

/* Admin hero */
.v102-admin-hero{
    background:linear-gradient(135deg,#061b35,#06499b);
    border-radius:26px;
    padding:28px;
    margin:10px 0 22px 0;
    box-shadow:0 14px 32px rgba(6,73,155,.25);
    display:flex;
    justify-content:space-between;
    gap:20px;
    align-items:center;
}
.v102-admin-hero h1{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    font-size:42px!important;
    margin:0!important;
    font-weight:900!important;
}
.v102-admin-hero p{
    color:#dbeafe!important;
    -webkit-text-fill-color:#dbeafe!important;
    font-size:18px!important;
    margin:8px 0 0 0!important;
    font-weight:800!important;
}
.v102-admin-badge{
    background:#f5b301;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    border-radius:20px;
    padding:18px 24px;
    font-size:24px;
    font-weight:900;
    text-align:center;
    min-width:240px;
}

/* Cards e righe */
.v100-title-bar,
.v102-title-bar{
    background:linear-gradient(135deg,#0b2a4a,#06499b)!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    border-radius:18px!important;
    padding:16px 22px!important;
    margin:18px 0 16px 0!important;
    font-size:24px!important;
    font-weight:900!important;
}
.v100-row-card{
    background:#ffffff!important;
    border:1px solid #dbeafe!important;
    border-radius:18px!important;
    box-shadow:0 7px 18px rgba(6,73,155,.09)!important;
}

/* Tabelle */
th{
    background:#06499b!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    font-weight:900!important;
}
td{
    background:#ffffff!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    font-weight:800!important;
}

/* Bottoni */
.stButton button,
.stDownloadButton button{
    border-radius:14px!important;
    min-height:46px!important;
    font-weight:900!important;
}

/* Box sidebar logo */
.v102-side-logo{
    background:rgba(255,255,255,.08);
    border:1px solid rgba(255,255,255,.25);
    border-radius:18px;
    padding:18px;
    text-align:center;
    margin-bottom:14px;
}
.v102-side-logo .brand{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    font-size:38px;
    font-weight:900;
}
.v102-side-logo .sub{
    color:#dbeafe!important;
    -webkit-text-fill-color:#dbeafe!important;
    font-size:13px;
    font-weight:900;
}
</style>
""", unsafe_allow_html=True)




# =========================
# V104 - FIX CONTRASTO ADMIN DEFINITIVO
# =========================
st.markdown("""
<style>

/* SEPARATORE AREA ADMIN */
.v104-admin-separator{
    background:#ffffff!important;
    border:3px solid #06499b!important;
    border-radius:22px!important;
    padding:14px 20px!important;
    margin:24px 0 14px 0!important;
    box-shadow:0 8px 24px rgba(6,73,155,.16)!important;
}
.v104-admin-separator span{
    color:#06499b!important;
    -webkit-text-fill-color:#06499b!important;
    font-size:24px!important;
    font-weight:1000!important;
}

/* HEADER ADMIN - vince su tutti i CSS vecchi */
.v102-admin-hero,
.v104-admin-hero{
    background:linear-gradient(135deg,#061b35 0%,#06499b 55%,#0b5cff 100%)!important;
    border-radius:28px!important;
    padding:34px 38px!important;
    margin:8px 0 16px 0!important;
    box-shadow:0 18px 40px rgba(6,73,155,.32)!important;
    display:flex!important;
    justify-content:space-between!important;
    align-items:center!important;
    min-height:175px!important;
    border:2px solid rgba(255,255,255,.24)!important;
}

/* Titolo bianco forzato */
.v102-admin-hero h1,
.v102-admin-hero h1 *,
.v104-admin-title,
.v104-admin-title *{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    font-size:56px!important;
    font-weight:1000!important;
    letter-spacing:.5px!important;
    margin:0!important;
    line-height:1!important;
    text-shadow:0 4px 12px rgba(0,0,0,.45)!important;
}

/* Sottotitolo bianco forzato */
.v102-admin-hero p,
.v102-admin-hero p *,
.v104-admin-subtitle,
.v104-admin-subtitle *{
    color:#eaf3ff!important;
    -webkit-text-fill-color:#eaf3ff!important;
    font-size:21px!important;
    font-weight:900!important;
    margin:12px 0 0 0!important;
    line-height:1.35!important;
    text-shadow:0 3px 10px rgba(0,0,0,.35)!important;
}

/* Badge giallo */
.v102-admin-badge,
.v104-admin-badge{
    background:linear-gradient(135deg,#ffd84d,#f5b301)!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    border-radius:24px!important;
    padding:24px 34px!important;
    font-size:28px!important;
    font-weight:1000!important;
    text-align:center!important;
    min-width:300px!important;
    box-shadow:0 12px 30px rgba(245,179,1,.42)!important;
    border:4px solid #fff0a8!important;
    line-height:1.25!important;
}

/* Menu admin più evidente */
div[data-testid="stHorizontalBlock"] .stButton button{
    background:linear-gradient(135deg,#06499b,#0b5cff)!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    border-radius:18px!important;
    min-height:66px!important;
    font-size:18px!important;
    font-weight:1000!important;
    border:0!important;
    box-shadow:0 10px 22px rgba(6,73,155,.25)!important;
}
div[data-testid="stHorizontalBlock"] .stButton button:hover{
    background:linear-gradient(135deg,#f5b301,#d68a00)!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}

/* Evita che i vecchi h1/h2 neri vincano dentro header admin */
.block-container .v102-admin-hero h1,
.block-container .v102-admin-hero p,
.block-container .v104-admin-hero h1,
.block-container .v104-admin-hero p{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}

@media(max-width:900px){
    .v102-admin-hero,
    .v104-admin-hero{
        flex-direction:column!important;
        align-items:stretch!important;
    }
    .v102-admin-badge,
    .v104-admin-badge{
        min-width:100%!important;
    }
}

</style>
""", unsafe_allow_html=True)



# =========================
# V105 - MINIMAL PROFESSIONAL ADMIN
# =========================
st.markdown("""
<style>

/* RESET ADMIN PROFESSIONALE */
.stApp{
    background:#F5F7FA!important;
}

.block-container{
    padding-top:1rem!important;
    padding-left:2rem!important;
    padding-right:2rem!important;
}

/* Testi sempre leggibili */
.block-container,
.block-container *:not(svg):not(path){
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}

.block-container h1,
.block-container h2,
.block-container h3{
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    font-weight:900!important;
}

/* SIDEBAR PULITA */
section[data-testid="stSidebar"]{
    background:#0B2A4A!important;
    border-right:4px solid #F5B301!important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}

section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="input"] *,
section[data-testid="stSidebar"] [data-baseweb="select"] *{
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    background:#ffffff!important;
}

section[data-testid="stSidebar"] .stButton button{
    background:#ffffff!important;
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    border:1px solid #D7E3F4!important;
    border-radius:12px!important;
    min-height:44px!important;
    font-weight:900!important;
    box-shadow:none!important;
}

section[data-testid="stSidebar"] .stButton button:hover{
    background:#F5B301!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}

/* HEADER ADMIN MINIMAL */
.v102-admin-hero,
.v104-admin-hero,
.v105-admin-header{
    background:#ffffff!important;
    border:1px solid #D7E3F4!important;
    border-left:8px solid #06499B!important;
    border-radius:18px!important;
    padding:26px 30px!important;
    margin:12px 0 18px 0!important;
    box-shadow:0 8px 22px rgba(6,73,155,.08)!important;
    display:flex!important;
    justify-content:space-between!important;
    align-items:center!important;
    gap:18px!important;
    min-height:130px!important;
}

/* Titolo Admin */
.v102-admin-hero h1,
.v102-admin-hero h1 *,
.v104-admin-title,
.v104-admin-title *,
.v105-admin-title,
.v105-admin-title *{
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    font-size:42px!important;
    font-weight:1000!important;
    letter-spacing:.2px!important;
    line-height:1.05!important;
    margin:0!important;
    text-shadow:none!important;
}

/* Sottotitolo Admin */
.v102-admin-hero p,
.v102-admin-hero p *,
.v104-admin-subtitle,
.v104-admin-subtitle *,
.v105-admin-subtitle,
.v105-admin-subtitle *{
    color:#475569!important;
    -webkit-text-fill-color:#475569!important;
    font-size:18px!important;
    font-weight:800!important;
    line-height:1.35!important;
    margin:8px 0 0 0!important;
    text-shadow:none!important;
}

/* Badge area admin */
.v102-admin-badge,
.v104-admin-badge,
.v105-admin-badge{
    background:#FFF3C4!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    border:2px solid #F5B301!important;
    border-radius:16px!important;
    padding:16px 22px!important;
    font-size:20px!important;
    font-weight:1000!important;
    text-align:center!important;
    min-width:220px!important;
    box-shadow:none!important;
    line-height:1.25!important;
}

/* Separatore vecchio meno invadente */
.v104-admin-separator{
    background:#ffffff!important;
    border:1px solid #D7E3F4!important;
    border-left:6px solid #F5B301!important;
    border-radius:14px!important;
    padding:10px 16px!important;
    margin:12px 0!important;
    box-shadow:none!important;
}
.v104-admin-separator span{
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    font-size:18px!important;
    font-weight:900!important;
}

/* MENU ADMIN */
div[data-testid="stHorizontalBlock"] .stButton button{
    background:#ffffff!important;
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    border:1px solid #D7E3F4!important;
    border-radius:14px!important;
    min-height:54px!important;
    font-size:16px!important;
    font-weight:900!important;
    box-shadow:0 4px 12px rgba(6,73,155,.06)!important;
}

div[data-testid="stHorizontalBlock"] .stButton button:hover{
    background:#06499B!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}

/* TITOLI SEZIONE */
.v100-title-bar,
.v102-title-bar,
.v90-section-title,
.v101-menu-title{
    background:#ffffff!important;
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    border:1px solid #D7E3F4!important;
    border-left:8px solid #06499B!important;
    border-radius:16px!important;
    padding:15px 20px!important;
    margin:18px 0 14px 0!important;
    font-size:23px!important;
    font-weight:1000!important;
    box-shadow:0 6px 16px rgba(6,73,155,.06)!important;
}

/* CRM DASHBOARD IFRAME: contenitore neutro */
iframe{
    border-radius:18px!important;
}

/* CARD PREVENTIVI */
.v100-row-card{
    background:#ffffff!important;
    border:1px solid #D7E3F4!important;
    border-radius:18px!important;
    padding:18px!important;
    margin:14px 0 12px 0!important;
    box-shadow:0 6px 16px rgba(6,73,155,.06)!important;
}

.v100-row-code{
    color:#06499B!important;
    -webkit-text-fill-color:#06499B!important;
    font-size:22px!important;
    font-weight:1000!important;
}

/* TABELLE */
table{
    border-collapse:separate!important;
    border-spacing:0!important;
    width:100%!important;
    border:1px solid #D7E3F4!important;
    border-radius:14px!important;
    overflow:hidden!important;
    background:#ffffff!important;
    box-shadow:0 6px 16px rgba(6,73,155,.05)!important;
}

th{
    background:#0B2A4A!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    font-weight:900!important;
    padding:11px!important;
}

td{
    background:#ffffff!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    font-weight:700!important;
    padding:10px!important;
    border-bottom:1px solid #EEF2F7!important;
}

tr:nth-child(even) td{
    background:#F8FAFC!important;
}

/* INPUT / SELECT */
.block-container input,
.block-container textarea,
.block-container [data-baseweb="input"] *,
.block-container [data-baseweb="select"] *{
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    background:#ffffff!important;
    font-weight:800!important;
}

/* Alert leggibili */
[data-testid="stAlert"],
[data-testid="stAlert"] *{
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    font-weight:800!important;
}

/* Bottoni generali */
.stButton button,
.stDownloadButton button{
    border-radius:12px!important;
    min-height:44px!important;
    font-weight:900!important;
}

/* Evita vecchi gradienti/test-shadow */
.v90-hero,
.v101-top{
    background:#ffffff!important;
    border:1px solid #D7E3F4!important;
    border-left:8px solid #06499B!important;
    box-shadow:0 6px 16px rgba(6,73,155,.06)!important;
}

.v90-hero h1,
.v101-top h1{
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
}

.v90-hero p,
.v101-top p{
    color:#475569!important;
    -webkit-text-fill-color:#475569!important;
}

@media(max-width:900px){
    .v102-admin-hero,
    .v104-admin-hero,
    .v105-admin-header{
        flex-direction:column!important;
        align-items:stretch!important;
    }
    .v102-admin-badge,
    .v104-admin-badge,
    .v105-admin-badge{
        min-width:100%!important;
    }
}
</style>
""", unsafe_allow_html=True)



# =========================
# V106 - ADMIN VIVO + CREA PREVENTIVO
# =========================
st.markdown("""
<style>

/* Colori più vivi */
:root{
    --satec-blue:#06499B;
    --satec-dark:#0B2A4A;
    --satec-orange:#F5B301;
    --satec-bg:#F2F7FF;
}

/* Sfondo */
.stApp{
    background:linear-gradient(180deg,#F2F7FF 0%,#FFFFFF 55%)!important;
}

/* Header Admin più vivo */
.v105-admin-header,
.v106-admin-header{
    background:linear-gradient(135deg,#ffffff 0%,#eef6ff 100%)!important;
    border:1px solid #b9d5f5!important;
    border-left:10px solid #06499B!important;
    border-radius:20px!important;
    padding:28px 32px!important;
    margin:12px 0 18px 0!important;
    box-shadow:0 10px 28px rgba(6,73,155,.14)!important;
}

.v105-admin-title,
.v106-admin-title{
    color:#06499B!important;
    -webkit-text-fill-color:#06499B!important;
    font-size:46px!important;
    font-weight:1000!important;
}

.v105-admin-subtitle,
.v106-admin-subtitle{
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
    font-size:19px!important;
    font-weight:900!important;
}

.v105-admin-badge,
.v106-admin-badge{
    background:linear-gradient(135deg,#F5B301,#FFD766)!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    border:2px solid #e2a300!important;
    border-radius:18px!important;
    box-shadow:0 8px 20px rgba(245,179,1,.25)!important;
}

/* Menu admin più acceso */
div[data-testid="stHorizontalBlock"] .stButton button{
    background:#06499B!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    border:0!important;
    border-radius:14px!important;
    min-height:58px!important;
    font-size:16px!important;
    font-weight:1000!important;
    box-shadow:0 8px 18px rgba(6,73,155,.22)!important;
}

div[data-testid="stHorizontalBlock"] .stButton button:hover{
    background:#F5B301!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}

/* Bottone crea preventivo evidenziato */
button[kind="secondary"]:has(div p){
    font-weight:900!important;
}

/* Titoli sezioni più vivi */
.v100-title-bar,
.v102-title-bar,
.v90-section-title,
.v101-menu-title{
    background:linear-gradient(135deg,#06499B,#0b5cff)!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    border:0!important;
    border-radius:18px!important;
    box-shadow:0 8px 20px rgba(6,73,155,.18)!important;
}

/* Card preventivi */
.v100-row-card{
    border:1px solid #b9d5f5!important;
    border-left:6px solid #06499B!important;
    box-shadow:0 8px 20px rgba(6,73,155,.10)!important;
}

/* Tabelle */
th{
    background:#06499B!important;
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}
tr:nth-child(even) td{
    background:#F2F7FF!important;
}

/* Sidebar viva */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0B2A4A,#06499B)!important;
    border-right:5px solid #F5B301!important;
}

section[data-testid="stSidebar"] .stButton button{
    background:#ffffff!important;
    color:#06499B!important;
    -webkit-text-fill-color:#06499B!important;
    border-radius:14px!important;
    font-weight:1000!important;
}
section[data-testid="stSidebar"] .stButton button:hover{
    background:#F5B301!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}

/* Info box */
[data-testid="stAlert"],
[data-testid="stAlert"] *{
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    font-weight:850!important;
}
</style>
""", unsafe_allow_html=True)



# =========================
# V107 - BOTTONE CREA PREVENTIVO VISIBILE
# =========================
st.markdown("""
<style>
section[data-testid="stSidebar"] .stButton button{
    min-height:50px!important;
    font-size:15px!important;
    font-weight:1000!important;
}
section[data-testid="stSidebar"] .stButton button:hover{
    background:#F5B301!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}
</style>
""", unsafe_allow_html=True)



# =========================
# V111 - GRAFICA DEFINITIVA SA-TEC
# =========================
st.markdown("""
<style>
:root{
    --satec-blue:#0057C8;
    --satec-blue-dark:#003B86;
    --satec-dark:#0B2A4A;
    --satec-orange:#F5B301;
    --satec-bg:#F3F7FF;
    --satec-border:#BFD7F5;
    --satec-text:#111827;
}
.stApp{background:linear-gradient(180deg,#F3F7FF 0%,#FFFFFF 55%)!important;}
.block-container{padding-top:1rem!important;padding-left:2rem!important;padding-right:2rem!important;}
.block-container,.block-container *:not(svg):not(path){color:var(--satec-text)!important;-webkit-text-fill-color:var(--satec-text)!important;}
.block-container h1,.block-container h2,.block-container h3{color:var(--satec-dark)!important;-webkit-text-fill-color:var(--satec-dark)!important;font-weight:1000!important;}

section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B2A4A 0%,#003B86 100%)!important;border-right:5px solid var(--satec-orange)!important;}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3,section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] div{color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;}
section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea,section[data-testid="stSidebar"] [data-baseweb="input"] *,section[data-testid="stSidebar"] [data-baseweb="select"] *{color:var(--satec-text)!important;-webkit-text-fill-color:var(--satec-text)!important;background:#ffffff!important;}

.stButton button,.stDownloadButton button,section[data-testid="stSidebar"] .stButton button{
    background:#ffffff!important;color:var(--satec-blue)!important;-webkit-text-fill-color:var(--satec-blue)!important;
    border:2px solid var(--satec-blue)!important;border-radius:13px!important;min-height:50px!important;
    font-size:15px!important;font-weight:1000!important;box-shadow:0 4px 12px rgba(0,87,200,.08)!important;
    transition:all .16s ease-in-out!important;opacity:1!important;
}
.stButton button *,.stDownloadButton button *,section[data-testid="stSidebar"] .stButton button *{
    color:inherit!important;-webkit-text-fill-color:inherit!important;font-weight:1000!important;opacity:1!important;
}
.stButton button:hover,.stDownloadButton button:hover,section[data-testid="stSidebar"] .stButton button:hover{
    background:var(--satec-orange)!important;color:#111111!important;-webkit-text-fill-color:#111111!important;
    border-color:var(--satec-orange)!important;box-shadow:0 8px 20px rgba(245,179,1,.30)!important;transform:translateY(-1px)!important;
}
.stButton button:focus,.stDownloadButton button:focus,.stButton button:active,.stDownloadButton button:active{
    background:var(--satec-blue)!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;border-color:var(--satec-blue)!important;
}

.v105-admin-header,.v106-admin-header,.v110-admin-header,.v111-admin-header{
    background:#ffffff!important;border:1px solid var(--satec-border)!important;border-left:10px solid var(--satec-blue)!important;
    border-radius:20px!important;padding:28px 32px!important;margin:12px 0 18px 0!important;
    box-shadow:0 10px 26px rgba(0,87,200,.12)!important;display:flex!important;justify-content:space-between!important;align-items:center!important;gap:18px!important;
}
.v105-admin-title,.v106-admin-title,.v110-admin-title,.v111-admin-title{
    color:var(--satec-blue)!important;-webkit-text-fill-color:var(--satec-blue)!important;font-size:44px!important;font-weight:1000!important;line-height:1.05!important;margin:0!important;text-shadow:none!important;
}
.v105-admin-subtitle,.v106-admin-subtitle,.v110-admin-subtitle,.v111-admin-subtitle{
    color:var(--satec-dark)!important;-webkit-text-fill-color:var(--satec-dark)!important;font-size:18px!important;font-weight:900!important;line-height:1.35!important;margin:8px 0 0 0!important;
}
.v105-admin-badge,.v106-admin-badge,.v110-admin-badge,.v111-admin-badge{
    background:#FFF3C4!important;color:#111827!important;-webkit-text-fill-color:#111827!important;border:2px solid var(--satec-orange)!important;border-radius:17px!important;
    padding:16px 24px!important;font-size:20px!important;font-weight:1000!important;text-align:center!important;min-width:230px!important;box-shadow:0 6px 16px rgba(245,179,1,.18)!important;
}
.v100-title-bar,.v102-title-bar,.v90-section-title,.v101-menu-title{
    background:#ffffff!important;color:var(--satec-blue)!important;-webkit-text-fill-color:var(--satec-blue)!important;
    border:1px solid var(--satec-border)!important;border-left:8px solid var(--satec-blue)!important;border-radius:17px!important;
    padding:16px 21px!important;margin:18px 0 14px 0!important;font-size:23px!important;font-weight:1000!important;box-shadow:0 7px 18px rgba(0,87,200,.08)!important;
}
.v100-row-card{background:#ffffff!important;border:1px solid var(--satec-border)!important;border-left:6px solid var(--satec-blue)!important;border-radius:18px!important;padding:18px!important;margin:14px 0 12px 0!important;box-shadow:0 7px 18px rgba(0,87,200,.08)!important;}
.v100-row-code{color:var(--satec-blue)!important;-webkit-text-fill-color:var(--satec-blue)!important;font-size:23px!important;font-weight:1000!important;}
table{border-collapse:separate!important;border-spacing:0!important;width:100%!important;border:1px solid var(--satec-border)!important;border-radius:15px!important;overflow:hidden!important;background:#ffffff!important;box-shadow:0 7px 18px rgba(0,87,200,.06)!important;}
th{background:var(--satec-blue)!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:1000!important;padding:12px!important;}
td{background:#ffffff!important;color:var(--satec-text)!important;-webkit-text-fill-color:var(--satec-text)!important;font-weight:750!important;padding:10px!important;border-bottom:1px solid #EEF2F7!important;}
tr:nth-child(even) td{background:#F3F7FF!important;}
[data-testid="stAlert"],[data-testid="stAlert"] *{color:var(--satec-text)!important;-webkit-text-fill-color:var(--satec-text)!important;font-weight:850!important;}
.block-container input,.block-container textarea,.block-container [data-baseweb="input"] *,.block-container [data-baseweb="select"] *{color:var(--satec-text)!important;-webkit-text-fill-color:var(--satec-text)!important;background:#ffffff!important;font-weight:850!important;}
.v90-hero,.v101-top,.v102-admin-hero,.v104-admin-hero{background:#ffffff!important;border:1px solid var(--satec-border)!important;border-left:8px solid var(--satec-blue)!important;box-shadow:0 7px 18px rgba(0,87,200,.08)!important;}
.v90-hero h1,.v101-top h1,.v102-admin-hero h1,.v104-admin-title{color:var(--satec-blue)!important;-webkit-text-fill-color:var(--satec-blue)!important;text-shadow:none!important;}
.v90-hero p,.v101-top p,.v102-admin-hero p,.v104-admin-subtitle{color:var(--satec-dark)!important;-webkit-text-fill-color:var(--satec-dark)!important;text-shadow:none!important;}
section[data-testid="stSidebar"] [data-testid="stAlert"],section[data-testid="stSidebar"] [data-testid="stAlert"] *{color:#111827!important;-webkit-text-fill-color:#111827!important;}
@media(max-width:900px){
    .v105-admin-header,.v106-admin-header,.v110-admin-header,.v111-admin-header{flex-direction:column!important;align-items:stretch!important;}
    .v105-admin-badge,.v106-admin-badge,.v110-admin-badge,.v111-admin-badge{min-width:100%!important;}
}
</style>
""", unsafe_allow_html=True)


# =========================
# ADMIN V102 - GESTIONALE SUBITO VISIBILE
# =========================

if profilo == "SA-TEC":
    st.sidebar.markdown("---")
    st.sidebar.success("AREA ADMIN ATTIVA")


    st.sidebar.markdown("""
    <div class="v102-side-logo">
        <div class="brand">SA-TEC</div>
        <div class="sub">GESTIONALE ADMIN</div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar.expander("Crea utente manuale", expanded=False):
        utenti_now = carica_tutti_utenti()
        profilo_new = st.selectbox("Profilo nuovo utente", ["CLIENTE", "RIVENDITORE", "GROSSISTA"], key="admin_profilo_new_v102")
        nome_new = st.text_input("Nome", key="admin_nome_new_v102")
        azienda_new = st.text_input("Azienda", key="admin_azienda_new_v102")
        telefono_new = st.text_input("Telefono", key="admin_tel_new_v102")
        email_new = st.text_input("Email", key="admin_email_new_v102")
        ricarico_new = st.number_input(
            "Ricarico %",
            min_value=0.0,
            max_value=100.0,
            value=ricarico_default(profilo_new),
            step=1.0,
            key="admin_ricarico_new_v102"
        )

        if st.button("CREA UTENTE", key="crea_utente_v102", use_container_width=True):
            codice = genera_codice_progressivo(profilo_new, utenti_now)
            pwd = genera_password()
            salva_utente_csv(
                codice,
                pwd,
                profilo_new,
                nome_new,
                azienda_new,
                telefono_new,
                email_new,
                str(ricarico_new)
            )
            st.success("Utente creato")
            st.code(f"Utente: {codice}\nPassword: {pwd}\nProfilo: {profilo_new}\nRicarico: {ricarico_new}%")

    preventivi = carica_preventivi()

    st.markdown("""
    <div class="v111-admin-header">
        <div>
            <div class="v111-admin-title">SA-TEC ADMIN</div>
            <div class="v111-admin-subtitle">Gestionale commerciale porte automatiche · Preventivi · Clienti · Rivenditori</div>
        </div>
        <div class="v111-admin-badge">🛡️ AREA<br>AMMINISTRATIVA</div>
    </div>
    """, unsafe_allow_html=True)

    if "admin_menu_v102" not in st.session_state:
        st.session_state.admin_menu_v102 = "preventivi"

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        if st.button("➕ CREA PREVENTIVO", key="menu_config_v106", use_container_width=True):
            st.session_state.admin_menu_v102 = "configuratore"
            st.rerun()

    with m2:
        if st.button("📋 PREVENTIVI", key="menu_prev_v102", use_container_width=True):
            st.session_state.admin_menu_v102 = "preventivi"
            st.rerun()

    with m3:
        if st.button("👥 CLIENTI", key="menu_cli_v102", use_container_width=True):
            st.session_state.admin_menu_v102 = "clienti"
            st.rerun()

    with m4:
        if st.button("🏪 RIVENDITORI", key="menu_riv_v102", use_container_width=True):
            st.session_state.admin_menu_v102 = "rivenditori"
            st.rerun()

    with m5:
        if st.button("🧪 SIMULAZIONE", key="menu_sim_v102", use_container_width=True):
            st.session_state.admin_menu_v102 = "simulazione"
            st.rerun()

    st.markdown("---")

    if st.session_state.admin_menu_v102 == "configuratore":
        st.markdown('<div class="v102-title-bar">➕ CREA PREVENTIVO DA ADMIN</div>', unsafe_allow_html=True)
        st.info("Modalità Admin: puoi creare un preventivo usando il configuratore sotto. Il preventivo verrà salvato nel CRM.")
        # Non faccio st.stop(): lascio proseguire al configuratore sotto.

    elif st.session_state.admin_menu_v102 == "preventivi":
        v100_render_admin(preventivi)

    elif st.session_state.admin_menu_v102 == "clienti":
        st.markdown('<div class="v102-title-bar">👥 ARCHIVIO CLIENTI</div>', unsafe_allow_html=True)
        clienti = carica_clienti()
        cerca_cliente_dash = st.text_input(
            "Cerca cliente",
            placeholder="Nome, azienda, telefono, email o codice preventivo",
            key="cerca_cliente_dash_v102"
        )
        clienti_filtrati = filtra_clienti_dashboard(clienti, cerca_cliente_dash)

        if not clienti:
            st.info("Nessun cliente salvato ancora.")
        elif not clienti_filtrati:
            st.warning("Nessun cliente trovato.")
        else:
            st.write(f"Clienti trovati: **{len(clienti_filtrati)}**")
            st.markdown(tabella_html_sicura(righe_clienti_dashboard(clienti_filtrati)), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### Elimina cliente")
            st.warning("L'eliminazione rimuove il cliente dall'archivio. I preventivi storici restano.")

            opzioni_clienti = {}
            for c in clienti_filtrati:
                label = label_cliente_elimina(c)
                ident = identificativo_cliente_elimina(c)
                if ident:
                    opzioni_clienti[label] = ident

            if opzioni_clienti:
                cdel1, cdel2, cdel3 = st.columns([2, 1, 1])
                with cdel1:
                    cliente_label_del = st.selectbox(
                        "Cliente da eliminare",
                        list(opzioni_clienti.keys()),
                        key="cliente_del_v102"
                    )
                with cdel2:
                    conferma_elimina_cliente = st.checkbox("Confermo", key="conf_cliente_del_v102")
                with cdel3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("ELIMINA CLIENTE", key="btn_cliente_del_v102", use_container_width=True):
                        if not conferma_elimina_cliente:
                            st.warning("Spunta prima Confermo.")
                        else:
                            ok_cli_del, msg_cli_del = elimina_cliente_admin(opzioni_clienti.get(cliente_label_del, ""))
                            if ok_cli_del:
                                st.success(msg_cli_del)
                                st.rerun()
                            else:
                                st.error(msg_cli_del)

    elif st.session_state.admin_menu_v102 == "rivenditori":
        st.markdown('<div class="v102-title-bar">🏪 RIVENDITORI / GROSSISTI</div>', unsafe_allow_html=True)
        righe_riv = utenti_rivenditori_grossisti()

        if not righe_riv:
            st.info("Nessun rivenditore o grossista presente.")
        else:
            st.markdown(tabella_html_sicura(righe_riv), unsafe_allow_html=True)
            codici_riv = [r["utente"] for r in righe_riv]

            st.markdown("### Modifica ricarico")
            r1, r2, r3 = st.columns([2, 1, 1])
            with r1:
                utente_riv_mod = st.selectbox("Utente", codici_riv, key="riv_mod_v102")
            with r2:
                nuovo_ricarico_riv = st.number_input(
                    "Nuovo ricarico %",
                    min_value=0.0,
                    max_value=200.0,
                    value=30.0,
                    step=1.0,
                    key="ricarico_riv_v102"
                )
            with r3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("AGGIORNA", key="agg_riv_v102", use_container_width=True):
                    ok_riv, err_riv = aggiorna_ricarico_utente_supabase(utente_riv_mod, nuovo_ricarico_riv)
                    if ok_riv:
                        st.success(f"Ricarico aggiornato per {utente_riv_mod}")
                    else:
                        st.error(f"Ricarico non aggiornato: {err_riv}")

            st.markdown("---")
            st.markdown("### Elimina rivenditore / grossista")
            st.warning("L'eliminazione blocca l'accesso dell'utente. Lo storico preventivi resta.")
            d1, d2, d3 = st.columns([2, 1, 1])
            with d1:
                utente_da_eliminare = st.selectbox("Utente da eliminare", codici_riv, key="riv_del_v102")
            with d2:
                conferma_elimina_utente = st.checkbox("Confermo", key="conf_riv_del_v102")
            with d3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ELIMINA UTENTE", key="btn_riv_del_v102", use_container_width=True):
                    if not conferma_elimina_utente:
                        st.warning("Spunta prima Confermo.")
                    else:
                        ok_del_user, msg_del_user = elimina_utente_admin(utente_da_eliminare)
                        if ok_del_user:
                            st.success(msg_del_user)
                            st.rerun()
                        else:
                            st.error(msg_del_user)

    elif st.session_state.admin_menu_v102 == "simulazione":
        st.markdown('<div class="v102-title-bar">🧪 SIMULAZIONE FUNZIONAMENTO</div>', unsafe_allow_html=True)
        st.info("1) Esci da Admin e salva un preventivo come Cliente. 2) Entra come Rivenditore/Grossista e salva un preventivo. 3) Rientra come Admin e controlla preventivi, clienti e rivenditori.")

    if st.session_state.get("admin_menu_v102") != "configuratore":
        st.stop()



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

    components.html(disegno_porta_v1006(ante, luce_mm, altezza_mm, lunghezza_traversa), height=760, scrolling=False)

    # Render vecchio rimosso in V1001
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
h1 {{color:#06499b;font-size:32px;margin:10px 0 2px 0;}}
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
    h1 {{color:#06499b;margin:0;font-size:32px;}}
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

st.caption("Versione V1008 - Ricarico 30%, accessori arrotondati, ante definite")

st.markdown(f"""
<div class="footer">
<div>📍 {AZIENDA}<br>{SEDE}</div>
<div>☎ {TELEFONO}</div>
<div>✉ {EMAIL}</div>
</div>
""", unsafe_allow_html=True)



# =========================
# V305 - CSS FINALE ASSOLUTO A FINE FILE
# =========================
st.markdown("""
<style>
/* V305: vince su tutti perché è l'ultimo CSS del file */

/* HEADER */
.v303-header{
    background:linear-gradient(90deg,#0057D9 0%,#003C96 100%)!important;
    border-radius:18px!important;
    padding:20px 26px!important;
    min-height:120px!important;
    box-shadow:0 12px 30px rgba(0,87,217,.28)!important;
}
.v303-header,
.v303-header div,
.v303-header span,
.v303-header p,
.v303-header h1,
.v303-header h2,
.v303-header h3{
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
    opacity:1!important;
    text-shadow:none!important;
}
.v303-brand{
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
    font-size:50px!important;
    font-weight:1000!important;
    letter-spacing:1.2px!important;
}
.v303-brand-sub{
    color:#EAF3FF!important;
    -webkit-text-fill-color:#EAF3FF!important;
    font-size:14px!important;
    font-weight:1000!important;
    letter-spacing:5px!important;
}
.v303-title-main{
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
    font-size:32px!important;
    font-weight:1000!important;
}
.v303-title-main span{
    color:#F5B301!important;
    -webkit-text-fill-color:#F5B301!important;
}
.v303-title-sub{
    color:#EAF3FF!important;
    -webkit-text-fill-color:#EAF3FF!important;
    font-weight:1000!important;
}
.v303-info,
.v303-info div,
.v303-info span{
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
    font-size:13px!important;
    font-weight:900!important;
}
.v303-sesamo-name{
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
    font-size:30px!important;
    font-weight:1000!important;
}
.v303-sesamo-sub{
    color:#EAF3FF!important;
    -webkit-text-fill-color:#EAF3FF!important;
}
.v303-sesamo-mark,
.v303-product-mark{
    background:#F58220!important;
    color:#071124!important;
    -webkit-text-fill-color:#071124!important;
}

/* PRODOTTO */
.v303-product{
    background:#FFFFFF!important;
    border:1px solid #C9DCF7!important;
    border-radius:16px!important;
    box-shadow:0 8px 22px rgba(0,87,217,.08)!important;
}
.v303-product-title{
    color:#0B2A4A!important;
    -webkit-text-fill-color:#0B2A4A!important;
}
.v303-product-sub{
    color:#334155!important;
    -webkit-text-fill-color:#334155!important;
}
.v303-product-name,
.v303-product-tech{
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
}

/* SIDEBAR */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#002B67 0%,#0057D9 100%)!important;
    border-right:5px solid #F5B301!important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div{
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
}

/* INPUT SIDEBAR */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="input"] *,
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] *{
    background:#FFFFFF!important;
    color:#111827!important;
    -webkit-text-fill-color:#111827!important;
    font-weight:900!important;
}

/* PULSANTI SIDEBAR LOGIN */
section[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] .stButton button *,
section[data-testid="stSidebar"] .stButton button p,
section[data-testid="stSidebar"] .stButton button span,
section[data-testid="stSidebar"] .stButton button div{
    background:#FFFFFF!important;
    color:#0057D9!important;
    -webkit-text-fill-color:#0057D9!important;
    border-color:#FFFFFF!important;
    font-weight:1000!important;
    opacity:1!important;
}
section[data-testid="stSidebar"] .stButton button:hover,
section[data-testid="stSidebar"] .stButton button:hover *,
section[data-testid="stSidebar"] .stButton button:hover p,
section[data-testid="stSidebar"] .stButton button:hover span,
section[data-testid="stSidebar"] .stButton button:hover div{
    background:#F5B301!important;
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    border-color:#F5B301!important;
}

/* PULSANTI ADMIN CENTRALI */
div[data-testid="stHorizontalBlock"] .stButton button,
div[data-testid="stHorizontalBlock"] .stButton button *,
div[data-testid="stHorizontalBlock"] .stButton button p,
div[data-testid="stHorizontalBlock"] .stButton button span,
div[data-testid="stHorizontalBlock"] .stButton button div{
    background:#0057D9!important;
    color:#FFFFFF!important;
    -webkit-text-fill-color:#FFFFFF!important;
    border-color:#0057D9!important;
    font-weight:1000!important;
}
div[data-testid="stHorizontalBlock"] .stButton button:hover,
div[data-testid="stHorizontalBlock"] .stButton button:hover *,
div[data-testid="stHorizontalBlock"] .stButton button:hover p,
div[data-testid="stHorizontalBlock"] .stButton button:hover span,
div[data-testid="stHorizontalBlock"] .stButton button:hover div{
    background:#F5B301!important;
    color:#111111!important;
    -webkit-text-fill-color:#111111!important;
    border-color:#F5B301!important;
}
</style>
""", unsafe_allow_html=True)



# =========================
# V400 - RIAPPLICA CSS A FINE FILE
# =========================
try:
    v400_style()
except Exception:
    pass
