import  streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

#Page config

st.set_page_config(page_title = "NIFTY 250 Smallcap Golden Cross Screener", layout = "wide")

st.title("NIFTY Smallcap 250 Golden Cross Screener")
st.write("""
    This app scans **NIFTY Smallcap 250** stocks for a **Golden Cross** pattern (STMA > MTMA > LTMA) that occurred in the **last 5 days**.
    """)

#Parameters for lookback and cache clear button
lookback_days = st.sidebar.selectbox("Lookback Period (days)", [30, 60, 120, 180, 240, 300], index=1)
short_term_days = st.sidebar.slider("Short-term range:", min_value = 3, max_value = 50, value = 5)
medium_term_days = st.sidebar.slider("Medium-term range:", min_value = 5, max_value = 150, value = 9)
long_term_days = st.sidebar.slider("Long-term range:", min_value = 9, max_value = 200, value = 14)
ma_type = st.sidebar.pills("Select type of moving average:",["EMA", "SMA"], selection_mode="single", default = "EMA")
show_downloads = st.sidebar.checkbox("Show Stock Data Download Progress", True)
show_all_plots = st.sidebar.checkbox("Plot Charts (check to generate plots)", True)
if st.sidebar.button("🧹 Clear Cache"):
    st.cache_data.clear()
    st.success("Cache cleared successfully!")

#Helper functions
@st.cache_data(ttl = 3600)
def get_tickers():

    csv_path = os.path.join(os.path.dirname(__file__), "ind_niftysmallcap250list.csv")
    nifty_smallcap_250_table = pd.read_csv(csv_path)

    tickers_smallcap_250 = nifty_smallcap_250_table['Symbol'].tolist()

    #Convert symbols to Yahoo Finance format
    tickers = [symbol + '.NS' for symbol in tickers_smallcap_250]
    return tickers

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_ticker_data(ticker, start_date, end_date):
    return yf.download(ticker, start = start_date, end = end_date, progress = False)

def download_data(tickers, start_date, end_date):
    all_data = {}
    counter_text = st.empty()  # placeholder for the counter

    for i,ticker in enumerate(tickers, start = 1):
        try:
            df = fetch_ticker_data(ticker, start_date, end_date)

            if not df.empty:
                all_data[ticker] = df
            
            if show_downloads == True:
                counter_text.markdown(f"**Stocks downloaded:** {len(all_data)} / {len(tickers)} — just fetched `{ticker}`")
        except Exception as e:
            st.write(f"Error downloading {ticker} data : {e}")
    return all_data

# Calculate EMAs and generate trading signals
def find_golden_crosses(all_data, ma_type, short_term_days_input, medium_term_days_input, long_term_days_input):
    final_list = []
    for ticker, df in all_data.items():

        if ma_type == "EMA": #Exponential short, medium and long-term moving averages
    
            df["STMA"] = df["Close"].ewm(span = short_term_days_input, adjust = False).mean()
            df["MTMA"] = df["Close"].ewm(span = medium_term_days_input, adjust = False).mean()
            df["LTMA"] = df["Close"].ewm(span = long_term_days_input, adjust = False).mean()

        else: #Simple short, medium and long-term moving averages

            df["STMA"] = df["Close"].rolling(window = short_term_days_input).mean()
            df["MTMA"] = df["Close"].rolling(window = medium_term_days_input).mean()
            df["LTMA"] = df["Close"].rolling(window = long_term_days_input).mean()

        df["golden_cross"] = (
            (df["STMA"] > df["MTMA"])
            & (df["MTMA"] > df["LTMA"])
            & (df["STMA"].shift(1) <= df["MTMA"].shift(1))
            & (df["MTMA"].shift(1) <= df["LTMA"].shift(1))
        )

        if df["golden_cross"].tail(5).any():
            final_list.append(ticker)

    return final_list


def plot_stock(df, ticker, ma_type_input):
    """
    Plots stock Close price with STMA, MTMA and LTMA and marks Golden Cross points.
    Uses Matplotlib for faster rendering and white background.
    Legend is displayed below the plot area without overlapping labels.
    """
    df = df[['Close', 'STMA', 'MTMA', 'LTMA', 'golden_cross']].dropna().copy()

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('white')   # full background white
    ax.set_facecolor('white')          # plot area background white

    # Plot Close and MAs
    ax.plot(df.index, df['Close'], label='Close', color='black', linewidth=2)
    ax.plot(df.index, df['STMA'], label='STMA', color='red', linewidth=1.5)
    ax.plot(df.index, df['MTMA'], label='MTMA', color='blue', linewidth=1.5)
    ax.plot(df.index, df['LTMA'], label='LTMA', color='goldenrod', linewidth=1.5)

    # Mark Golden Cross points
    cross_points = df[df['golden_cross']]
    ax.scatter(cross_points.index, cross_points['Close'], color='green', s=40, label='Golden Cross', zorder=5)

    # Formatting
    ax.set_title(f"{ticker} — Price with {ma_type_input}s", fontsize=13, loc='left')
    ax.set_xlabel("Date", labelpad=10)  # add space below x-axis label
    ax.set_ylabel("Price (INR)")

    # Legend below the plot (centered, smaller font, non-overlapping)
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.35),  # moved slightly further down
        ncol=4,
        frameon=False,
        fontsize=9
    )

    # Grid and x-axis formatting
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate()

    # Adjust layout so nothing gets clipped (important for Streamlit)
    plt.subplots_adjust(bottom=0.38)

    st.pyplot(fig)
    plt.close(fig)

def check_validity_of_inputs():

    if not (short_term_days < medium_term_days < long_term_days):
        return False
    if long_term_days > lookback_days:
        return False
    
    return True

#App logic

if st.button(" RUN SCAN "):

    with st.spinner("Checking input validity..."):
        if not check_validity_of_inputs():
            st.error("Invalid inputs - kindly fix the window lengths/lookback ranges and try again")
            st.stop()    

    with st.spinner("Fetching data..."):
        tickers = get_tickers()
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days = lookback_days)
        all_data = download_data(tickers, start_date, end_date)

    st.success(f"✅ Downloaded data for {len(all_data)} stocks.")

    with st.spinner("Scanning for golden crosses..."):
        final_list = find_golden_crosses(all_data, ma_type, short_term_days, medium_term_days, long_term_days)

    st.subheader(f"✨ Stocks showing a Golden Cross in the last 5 days: {len(final_list)}")
    if final_list:
        st.write(", ".join(final_list))

        if show_all_plots:
            for ticker in final_list:
                with st.expander(f"Show chart for {ticker}"):
                    plot_stock(all_data[ticker], ticker, ma_type)
                    
    else:
        st.info("No golden crosses found in the selected period.")