import streamlit as st

st.set_page_config(layout="wide")

# Login ultra-semplice
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("Accesso Riservato")
    u = st.text_input("User")
    p = st.text_input("Password", type="password")
    if st.button("Accedi"):
        if u == "ADMIN" and p == "SATEC-ADMIN":
            st.session_state.auth = True
            st.rerun()
else:
    st.title("Dashboard SATEC")
    st.write("Se vedi questo, il sistema è attivo.")
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()
