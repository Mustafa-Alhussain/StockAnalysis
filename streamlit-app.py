import requests
import pandas as pd
import streamlit as st
import yfinance as yf
import streamlit as st
import cufflinks as cf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# URL to the JSON file
url = "https://www.saudiexchange.sa/tadawul.eportal.theme.helper/TickerServlet"

@st.cache_data()  # Cache data for 15 minutes (900 seconds)
def load_stock_data():
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the JSON data from the response
        json_data = response.json()

        # Create a DataFrame from the JSON data
        df = pd.DataFrame(json_data)
        lst = df['stockData'].values.tolist()
        # Extract stockData column as a DataFrame
        df = pd.DataFrame(lst)
        # Convert specific columns to desired data types
        df['pk_rf_company'] = df['pk_rf_company'].astype(int)
        df['noOfTrades'] = df['noOfTrades'].astype(int)
        df['turnOver'] = df['turnOver'].astype(float)
        df['volumeTraded'] = df['volumeTraded'].astype(int)
        df['aveTradeSize'] = df['aveTradeSize'].astype(float)
        df['change'] = df['change'].astype(float)
        df['changePercent'] = df['changePercent'].astype(float)
        df['lastTradePrice'] = df['lastTradePrice'].astype(float)

        # Rename columns
        df = df.rename(columns={
            'pk_rf_company': 'ticker',
            'companyShortNameEn': 'EnglishName',
            'companyShortNameAr': 'ArabicName'
        })
        df = df.sort_values(by='ticker', ascending=True, ignore_index=True)

        return df

@st.cache_data()  # Cache data for 15 minutes (900 seconds)
def get_stock_data(ticker):
    # Get the ticker symbol
    ticker_symbol = str(ticker) + '.SR'
    # Download the ticker data for the selected ticker
    ticker_data = yf.download(ticker_symbol, period='10y')

    return ticker_data

# Set page config
st.set_page_config(page_title='Stock Data', page_icon=':chart_with_upwards_trend:', layout='wide')

# Create the app layout
st.title('Stock Data')

# Ticker selection dropdown
df = load_stock_data()

# Ticker selection dropdown
df = load_stock_data()
selected_ticker = st.selectbox('Select Ticker', options=df[['ArabicName', 'ticker']].apply(lambda x: f"{x['ArabicName']} ({x['ticker']})", axis=1).tolist())
selected_ticker = int((selected_ticker.split()[-1])[1:-1])
# Filter the DataFrame based on the selected ticker
selected_ticker_data = df[df['ticker'] == selected_ticker]

if not selected_ticker_data.empty:
    # Download the ticker data for the selected ticker
    ticker_data = get_stock_data(selected_ticker)

    # Get the high price, low price, and previous close price
    high_price = round(ticker_data['High'].iloc[-1], 2)
    low_price = round(ticker_data['Low'].iloc[-1], 2)
    previous_close_price = round(ticker_data['Close'].iloc[-2], 2)
    open_price_today = round(ticker_data['Open'].iloc[-1], 2)
    high_52_weeks = round(ticker_data['High'].max(), 2)
    low_52_weeks = round(ticker_data['Low'].min(), 2)

    # Create a dictionary with the stock data
    stock_data = {
        'Name': selected_ticker_data['ArabicName'].iloc[0],
        'Price': selected_ticker_data['lastTradePrice'].iloc[0],
        'High Price': high_price,
        'Low Price': low_price,
        'Previous Close Price': previous_close_price,
        'Today\'s Open Price': open_price_today,
        '52-Week High': high_52_weeks,
        '52-Week Low': low_52_weeks
    }

    # Display the stock data as a table
    st.table(pd.DataFrame(stock_data, index=[selected_ticker]))

    # Create QuantFig object for the stock price chart
    qf = cf.QuantFig(ticker_data, title=f"{selected_ticker_data['ArabicName'].iloc[0]} Stock Price", name='Stock Price', up_color='green', down_color='red')

    # Add moving averages
    qf.add_sma(periods=14, column='Close', width=2, color='blue')
    qf.add_sma([10, 50], width=2, color=['blue', 'red'])

    # Add RSI
    qf.add_rsi(periods=14, color='green')

    # Add Bollinger Bands
    qf.add_bollinger_bands(periods=20, boll_std=2, colors=['orange', 'grey'], fill=True)

    # Add volume
    qf.add_volume()

    # Add MACD
    qf.add_macd()

    # Plot the chart
    fig = qf.iplot(asFigure=True)

    # Update the layout to set the width
    fig.update_layout(width=1100, height = 700)

    # Display the stock price chart
    st.plotly_chart(fig)

    # Explanations for the indicators
    st.markdown('## Indicators Explanation')
    st.markdown('''
    - Open, High, Low, Close (OHLC): These are the four basic data points used to create a candlestick chart. The "open" and "close" prices represent the opening and closing prices for a given period, while the "high" and "low" prices represent the highest and lowest prices that occurred during that same period.
    - Volume: This shows the total number of shares or contracts traded during a given period. High trading volumes often indicate high levels of interest in a particular stock or market.
    - Relative Strength Index (RSI): This is a momentum indicator that measures the magnitude of recent price changes to evaluate overbought or oversold conditions in the price of a stock or other asset.
    - Moving Average Convergence Divergence (MACD): This is a trend-following momentum indicator that shows the relationship between two moving averages of a security's price.
    - Simple Moving Average (SMA): This is a technical analysis tool that calculates the average price of a security over a specific time period. SMA can be used to determine the direction of the trend or to identify potential areas of support and resistance.
    - Bollinger Bands: These are a type of statistical chart characterizing the prices and volatility over time of a financial instrument or commodity. Bollinger Bands use a moving average and two standard deviations, which provides a relative definition of high and low prices.
    ''')

