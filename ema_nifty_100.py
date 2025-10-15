import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


#Page config

st.set_page_config(page_title="NIFTY 100 Golden Cross Screener", layout = "wide")

st.title("NIFTY 100 Golden Cross Screener")
st.write("""
    This app scans **NIFTY 50 + NIFTY Next 50** stocks for a **Golden Cross** pattern
    (EMA5 > EMA9 > EMA14) that occurred in the **last 5 days**.
    """
)

#Parameters for lookback
lookback_days = st.sidebar.selectbox("Lookback Period (days)", [30, 60, 120], index=1)
show_downloads = st.sidebar.checkbox("Show Stock Data Download Progress", True)
show_all_plots = st.sidebar.checkbox("Show All Matching Stock Charts", True)

#Helper functions
@st.cache_data
def get_tickers():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        )
    }

    #NIFTY 50
    nifty_50_url = "https://en.wikipedia.org/wiki/NIFTY_50"
    response = requests.get(nifty_50_url, headers=headers)
    tables = pd.read_html(response.text)
    nifty_50_table = tables[1]
    tickers_50 = nifty_50_table["Symbol"].tolist()

    # NIFTY NEXT 50
    nifty_next_50_url = "https://en.wikipedia.org/wiki/NIFTY_Next_50"
    response = requests.get(nifty_next_50_url, headers=headers)
    tables = pd.read_html(response.text)
    nifty_next_50_table = tables[2]
    tickers_next_50 = nifty_next_50_table["Symbol"].tolist()

    tickers = [symbol + ".NS" for symbol in tickers_50 + tickers_next_50]
    return tickers

@st.cache_data(show_spinner=False)
def download_data(tickers, start_date, end_date):
    all_data = {}
    counter_text = st.empty()  # placeholder for the counter

    for i,ticker in enumerate(tickers, start = 1):
        try:
            df = yf.download(ticker, start = start_date, end = end_date, progress = False)

            if not df.empty:
                all_data[ticker] = df
            
            counter_text.markdown(f"**Stocks downloaded:** {len(all_data)} / {len(tickers)} — just fetched `{ticker}`")
        except Exception as e:
            st.write(f"Error downloading {ticker} data : {e}")
    return all_data

def find_golden_crosses(all_data):
    final_list = []
    for ticker, df in all_data.items():
        df["EMA5"] = df["Close"].ewm(span = 5, adjust = False).mean()
        df["EMA9"] = df["Close"].ewm(span = 9, adjust = False).mean()
        df["EMA14"] = df["Close"].ewm(span = 14, adjust = False).mean()

        df["golden_cross"] = (
            (df["EMA5"] > df["EMA9"])
            & (df["EMA9"] > df["EMA14"])
            & (df["EMA5"].shift(1) <= df["EMA9"].shift(1))
            & (df["EMA9"].shift(1) <= df["EMA14"].shift(1))
        )

        if df["golden_cross"].tail(5).any():
            final_list.append(ticker)

    return final_list

def plot_stock(df, ticker):
    """
    Plots stock Close price with EMA5, EMA9, EMA14 and marks Golden Cross points.
    Uses Matplotlib for faster rendering and white background.
    Legend is displayed below the plot area without overlapping labels.
    """
    df = df[['Close', 'EMA5', 'EMA9', 'EMA14', 'golden_cross']].dropna().copy()

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('white')   # full background white
    ax.set_facecolor('white')          # plot area background white

    # Plot Close and EMAs
    ax.plot(df.index, df['Close'], label='Close', color='black', linewidth=2)
    ax.plot(df.index, df['EMA5'], label='EMA 5', color='red', linewidth=1.5)
    ax.plot(df.index, df['EMA9'], label='EMA 9', color='blue', linewidth=1.5)
    ax.plot(df.index, df['EMA14'], label='EMA 14', color='goldenrod', linewidth=1.5)

    # Mark Golden Cross points
    cross_points = df[df['golden_cross']]
    ax.scatter(cross_points.index, cross_points['Close'], color='green', s=40, label='Golden Cross', zorder=5)

    # Formatting
    ax.set_title(f"{ticker} — Price with EMAs", fontsize=13, loc='left')
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

#App logic

if st.button(" RUN SCAN "):
    with st.spinner("Fetching data..."):
        tickers = get_tickers()
        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(days = lookback_days)
        all_data = download_data(tickers, start_date, end_date)

    st.success(f"✅ Downloaded data for {len(all_data)} stocks.")

    with st.spinner("Scanning for golden crosses..."):
        final_list = find_golden_crosses(all_data)

    st.subheader(f"✨ Stocks showing a Golden Cross in the last 5 days: {len(final_list)}")
    if final_list:
        st.write(", ".join(final_list))

        if show_all_plots:
            for ticker in final_list:
                with st.expander(f"Show chart for {ticker}"):
                    plot_stock(all_data[ticker], ticker)
    else:
        st.info("No golden crosses found in the selected period.")