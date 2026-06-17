import streamlit as st
import base64

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
    .price-box { background-color: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3d59; margin-bottom: 20px; color: #333333; }
    .total-box { background-color: #1e3d59; color: white; padding: 35px; border-radius: 8px; box-shadow: 0 4px 15px rgba(30,61,89,0.3); text-align: center; margin-top: 25px; }
    .total-box h1 { color: #ffc13b !important; margin: 15px 0 0 0; font-size: 46px; font-weight: bold; }
    
    .print-button {
        display: block;
        width: 100%;
        text-align: center;
        background-color: #ffffff;
        color: #1e3d59;
        padding: 10px;
        border: 1px solid #1e3d59;
        border-radius: 6px;
        font-weight: bold;
        text-decoration: none;
        font-size: 14px;
        margin-top: 10px;
        cursor: pointer;
    }
    .print-button:hover { background-color: #1e3d59; color: white; text-decoration: none; }
    </style>
""", unsafe_allow_html=True)

# --- LOGO INTEGRATO IN BASE64 (A prova di errore) ---
LOGO_BASE64 = "data:image/jpeg;base64,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
