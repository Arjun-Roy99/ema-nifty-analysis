import streamlit as st

# Page config
st.set_page_config(page_title="NIFTY Stock Analysis Hub", layout="wide")

# App title and description
st.title("📊 NIFTY Golden Cross Screener Hub")
st.write("""
Welcome to the **NIFTY Golden Cross Screener Hub**

Choose one of the modules below to get started:
""")

st.markdown("---")

# Create two columns for layout
col1, col2 = st.columns(2)

# Button 1: Golden Cross Screener
with col1:
    st.subheader("✨ NIFTY 100 Golden Cross Screener")
    st.write("""
    Scan **NIFTY 50 + NIFTY Next 50** stocks for a **Golden Cross pattern**
    (EMA5 > EMA9 > EMA14) within the last few days.
    """)
    if st.button("🔍 Scan NIFTY 100"):
        st.switch_page("pages/2_NIFTY 100 Screener.py")

# Button 2: Stock Compare or another feature
with col2:
    st.subheader("✨ NIFTY Smallcap 250 Golden Cross Screener")
    st.write("""
    Scan **NIFTY Smallcap 250** stocks for a **Golden Cross pattern**
    (EMA5 > EMA9 > EMA14) within the last few days.
    """)
    if st.button("🔍 Scan NIFTY Smallcap 250"):
        st.switch_page("pages/3_NIFTY Smallcap 250 Screener.py")

st.markdown("---")
st.caption("Built by AR99 | Data powered by Yahoo Finance")
