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

# [ ... Inserisci qui tutte le tue costanti, UTENTI_BASE, LISTINI, FUNZIONI UTILI, SUPABASE ... ]
# (Ho mantenuto tutto il tuo codice iniziale, ho solo completato la funzione finale)

def html_export_preventivo_admin(p):
    codice = str(p.get("codice_preventivo", "") or "")
    righe = ""
    campi = [
        ("Codice", "codice_preventivo"), ("Data", "data_ora"), ("Rivenditore / Utente", "utente"),
        ("Profilo", "profilo"), ("Cliente", "cliente_nome"), ("Azienda cliente", "cliente_azienda"),
        ("Telefono", "cliente_telefono"), ("Email", "cliente_email"), ("Configurazione", "configurazione"),
        ("Luce mm", "luce_mm"), ("Altezza mm", "altezza_mm"), ("Traversa m", "traversa_m"),
        ("Elettroblocco", "elettroblocco"), ("Radar sicurezza laterale", "radar_sicurezza_laterale"),
        ("Allaccio / Collaudo", "allaccio"), ("Ricarico totale %", "ricarico_percento"),
        ("Ricarico base %", "ricarico_base_percento"), ("Ricarico extra %", "ricarico_extra_percento"),
        ("Imponibile", "imponibile"), ("IVA", "iva"), ("Totale IVA inclusa", "totale_iva"),
        ("Costo SA-TEC", "costo_satec"), ("Utile lordo", "utile_lordo"),
        ("Margine %", "margine_percento"), ("Stato", "stato"),
    ]

    for label, key in campi:
        righe += f"<tr><th>{label}</th><td>{p.get(key, '')}</td></tr>"

    html = f"""
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
    </style>
    </head>
    <body>
        <div class="head"><h1>Preventivo {codice}</h1></div>
        <table>{righe}</table>
        <div class="footer">Documento generato dal CRM SA-TEC.</div>
    </body>
    </html>
    """
    return html

# [ ... Inserisci qui il resto del tuo codice originale ... ]
