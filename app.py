import streamlit as st
import pandas as pd
from pathlib import Path

# 1. SETUP BASE
st.set_page_config(page_title="SA-TEC", layout="wide")

# 2. CSS PULITO E ISOLATO
st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    .auth-box { background: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #38bdf8; }
    .graph-box { background: white; padding: 15px; border-radius: 8px; border: 2px solid #38bdf8; color: black; }
</style>
""", unsafe_allow_html=True)

# 3. LOGICA DI ACCESSO SEMPLIFICATA
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.sidebar.markdown('<div class="auth-box">', unsafe_allow_html=True)
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if user == "ADMIN" and pwd == "SATEC-ADMIN":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.sidebar.error("Credenziali errate")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.title("Sistema di Configurazione Bloccato")
    st.info("Esegui il login dalla barra laterale per sbloccare l'interfaccia.")
else:
    st.title("Area Tecnica SA-TEC")
    st.success("Accesso effettuato correttamente.")
    
    # 4. GRAFICA SICURA (SENZA VARIABILI CHE CRASHANO)
    st.markdown("""
    <div class="graph-box">
        <h3 style="color:black;">Configurazione Automazione</h3>
        <p>Ante: 1 | Luce: 1000mm | Altezza: 2100mm</p>
        <div style="background: #e2e8f0; height: 50px; display: flex; align-items: center; justify-content: center;">
            SCHEMA ANTA MOBILE
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
