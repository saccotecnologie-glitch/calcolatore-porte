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

# --- LOGO INTEGRATO IN BASE64 ---
LOGO_BASE64 = """data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAEAAgADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4T1l5WFlmZ2nuJnNzd4XFcxFx1XV2daXh5mgo6h0anq8hYHY2R1l5Wl9ced3hXl6f3yGkoWGh4iJiouMjY6Pk5SVl5fYW5ydnP15f3h5G1hbXFxeX1RUXV3UXV5fWGlqa2xtbm9sc3V1dnd4eXp7fH19f319f3h9f/aAAwDAQACEQMRAD8A9/ooooAKKKACiiuF+Jvji88FaPaSafbRy3N1IUEkwJSMAZPA6n059fSgDuqK8i8MfHCyurSWPxFEba7hiMiSQRllnI/hA7N6Z49xWbafH2b7epvNDjFmXwTFMfMVfXkYJ9uPrQB7fRWBofjHQPEgxpmpRSyxoZlhX6qefx6VvUAFFFFABRRmigAorz74ofEWfwVbWltp8EUuB/vK9/P0A9PrXBp+0BqyXayNpli9vgbosup98Nk/yNAHv8ASZqrpmoQ6rpdX9lBstfwiHqP8/l1rn/HHjGz8F+H5NQuAs07HZBbB8NK/p0OAByT/jQB1GaM0yKQSwpIBgOoYAnPWnd6AFooooAKKKKACiiigAoopM0ALRSZpaACiiigA00319ertZtsMUZDSSt/dUf16CgDod1G6vFNf8Aj9Y3Wl3dtpGmXsczoY/NuCgVCepGGOe/Y/TvXK+H/jjrejwTQX8S6mCuYXuHO6Nh0yepB+uffFAH0pmjNeHeD/jrNNdyxeKYoY4pHzFcWyECP/ZZc5I9+te2wTRXEKTQSpLC6hkkRgVYHoQRwRQA+iiigAoooo clubTdBf/8QAnRAAAgEDAwUBAQEBAQAAAAAAAAECEwESECExIDBAUWEiMhRCcYH/2gAIAQEAAT8A7txbIidD0Y79idRIdZ/Sdf6KtR+SpUfkUpN7sz0PWiZk8iLwORV8K1YvIii+FmR9DFlCgY9iXCHshvIlihUvIorIihQowIs/pEos7D3EqZExE9w7Z/6Yshf4J4EqZ7GReEInwXwNfO9FiyYFEnwPgejIsidH2mRFiP2EskXwXwh6IifBfCHoiJ8F8EORPhC0RE+FmC6IsidF8IuhmDIn81S7mO4Ww9D66I9GBy9EOR99idWMe/YnUSP3YnUfkeR7shbNisP4WZH0SgZ3Hsh6IivZkURfCHsh/CHshvB/wBTyIdwth6MiyJ/NcsWbXF0N9w66vAun1omZPJF9D6Hsh/CHsh7EofT+6vCsh7E6X1uB7EqMWSN9FEXwXwZ8DFl0M/pEosie3fV4VkfYnUfknXf0q1H5KtR+SpUfik6XuyMvRHlC0RPhC0REfCzoeSLIdw9GPhC0REfC+CzoeiLE+FmC6IsRPhC6Is/pEosj/wBLoZidL0Y76pdxC0XwPQun1omPAnmhaF0vVD2Q9idUOROnGPPYnUhbyVWMY9fPQu6uh99Xgsh7EqlWOf3UqVSpVKnH+C6Xky
