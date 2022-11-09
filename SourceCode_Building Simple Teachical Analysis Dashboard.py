########## Note
# Before you start, You should make sure to install all of them to avoid errors.
# After running this file, you must go to the terminal and run the command: streamlit run "file"
# In this case: streamlit run K194141740_Tran-Thanh-Phuc_Last-Term.py
# After running that command successfully, Local URL and Network URL will appear.
# Your computer will redirect to the Local URL through your browser.
# Then, you will see this Interactive Dashboard Technical Analysis.

# import the libraries
from matplotlib.pyplot import title
import streamlit as st
st.set_page_config(layout="wide")  # set auto wide mode when run
import numpy as np
import pandas as pd
import datetime as dt
import pandas_datareader as web
from vnstock_data.all_exchange import VnStock
import requests
from bs4 import BeautifulSoup  # library to parse HTML documents
import cufflinks as cf
cf.go_offline()  # configure it for offline use
from plotly.offline import init_notebook_mode
init_notebook_mode(connected=True)
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# get data
option_type = st.sidebar.selectbox("Type", ["Stock (Top 100 on HOSE)", "Stock (Nasdaq 100)", "Cryptocurrency (Top 100)"])
if option_type == "Stock (Nasdaq 100)":
    # get the response in the form of html
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    table_id = "constituents"
    response = requests.get(url)

    # parse data from the html into a beautifulsoup object
    soup = BeautifulSoup(response.text, "html.parser")
    indiatable=soup.find('table',{'id':table_id})
    df_company=pd.read_html(str(indiatable))

    # convert list to dataframe
    df_company=pd.DataFrame(df_company[0])
    ticker = df_company["Ticker"].tolist()
    ticker = sorted(ticker)
    # get name company
    name = df_company[["Company", "Ticker"]]
    name.index = name["Ticker"]
    del name["Ticker"]
    name.rename(columns={"Company": "Name"}, inplace=True)

elif option_type == "Cryptocurrency (Top 100)":
    # get the response in the form of html
    url = "https://coin360.com/coin/"
    table_class = "TableView__Table"
    response = requests.get(url)

    # parse data from the html into a beautifulsoup object
    soup = BeautifulSoup(response.text, "html.parser")
    indiatable=soup.find('table',{'class':table_class})
    df_crypto=pd.read_html(str(indiatable))

    # convert list to dataframe
    df_crypto=pd.DataFrame(df_crypto[0])

    # get symbol
    ticker = df_crypto["Symbol"]
    ticker = ticker.values.tolist()
    for i in range(len(ticker)):
        if "?" in ticker[i]:
            ticker[i] = ticker[i].replace("?", "")
            ticker[i] += "-USD"
    ticker = sorted(ticker)
    # get name cryptocurrency
    name = df_crypto[["Name", "Symbol"]]
    for i in range(len(name["Symbol"])):
        if "?" in name["Symbol"][i]:
            name["Symbol"][i] = name["Symbol"][i].replace("?", "")
            name["Symbol"][i] += "-USD"
    name.index = name["Symbol"]
    del name["Symbol"]
else:
    url = "https://www.tradingview.com/markets/stocks-vietnam/market-movers-large-cap/"
    table_class = "tv-data-table tv-screener-table"
    response = requests.get(url)

    # parse data from the html into a beautifulsoup object
    soup = BeautifulSoup(response.text, "html.parser")
    indiatable=soup.find('table',{'class':table_class})
    df_company=pd.read_html(str(indiatable))

    # convert list to dataframe
    df_company=pd.DataFrame(df_company[0])
    # get tickername column
    lst_ticker = df_company["Unnamed: 0"].tolist()
    # def list to string
    def listtostring(s):    
        # initialize an empty string
        str1 = "" 
        # traverse in the string  
        for ele in s: 
            str1 += (ele + " ")  
        # return string  
        return str1 
        
    # get ticker and name
    ticker = []
    name_lst = []
    for i in range(len(lst_ticker)):
        get_ticker = lst_ticker[i].split(" ")
        if len(get_ticker[0]) == 1:
            ticker.append(get_ticker[1])
            name_lst.append(listtostring(get_ticker[2:]))
        else:
            ticker.append(get_ticker[0])
            name_lst.append(listtostring(get_ticker[1:]))

    name = pd.DataFrame()
    name["Name"] = name_lst
    name["Ticker"] = ticker
    name.index = name["Ticker"]
    del name["Ticker"]
    ticker = sorted(ticker)



# create indicators
indicator = ["None","Bollinger Bands","MA", "MACD", "MFI", "OBV", "RSI"]
# create selectbox in sidebar
option_symbol = st.sidebar.selectbox("Symbol", ticker)
option_indi = st.sidebar.selectbox("Indicator", indicator)
option_periods = 0
option_periods_slow = 0
option_periods_signal = 0
option_overbought = 0
option_oversold = 0

if option_indi == "None":
    option_periods = 0
    option_periods_slow = 0
    option_periods_signal = 0
    option_overbought = 0
    option_oversold = 0
elif option_indi == "MACD":
    option_periods = st.sidebar.slider("Fast Period", min_value=2, max_value=251, value=12)
    option_periods_slow = st.sidebar.slider("Slow Period", min_value=2, max_value=251, value=26)
    option_periods_signal = st.sidebar.slider("MACD Period", min_value=2, max_value=251, value=9)
elif option_indi == "MA":
    option_periods = st.sidebar.slider("Fast Period", min_value=2, max_value=251, value=30)
    option_periods_slow = st.sidebar.slider("Slow Period", min_value=2, max_value=251, value=100)
elif option_indi == "OBV" or option_indi == "Bollinger Bands":
    option_periods = st.sidebar.slider("Period", min_value=2, max_value=251, value=14)
else:
    option_periods = st.sidebar.slider("Period", min_value=2, max_value=251, value=14)
    option_oversold = st.sidebar.slider("Over Sold", min_value=10, max_value=40, value=30, step=10)
    option_overbought = st.sidebar.slider("Over Bought", min_value=60, max_value=90, value=70, step=10)
    

option_start = st.sidebar.date_input("Start Date", dt.date(2021,1,1))
option_end = st.sidebar.date_input("End Date")

def test(symbol, indicator, start, end, period, period_slow, period_signal, overbought, oversold, type):
    if type == "Stock (Top 100 on HOSE)":
        cookies = {"vts_usr_lg":"F1ED60F2507CE5F2E3E6A81669EA65857EB57ACB376840C73CDF10C43923C464AA42A0F7\
            019669C72DBE306E2BDACD63951BC63600B9AC754338EF5CAC16956B9E9909E830319150EE2F1D0FAF2A9484FE68AF\
                4A9FA8BECF01BAF54A18D919C5105332F7F3B70B1A9376E259F58913BFB14E2F6A5C5BC994C006E6F2DB0B156A4\
                    B7F463F048B957ED024016EE37543F5",
        "__RequestVerificationToken":"1_Waqh8PDWVN4qyRMz6Okrxr2hUEljm0tEJvbBY5AoaQ8PCctY1X6dsxvD0Do1xmxPlz8H\
            qlNGtBQHIX4owX4RE83MPwrEK0f09pleKX3HY1",
        "language":"en-US"
        }
        vndata = VnStock(cookies)
        start = str(start)
        end = str(end)
        date_start = start.split("-")
        start = date_start[1] + "-" + date_start[2] + "-" + date_start[0]
        date_end = end.split("-")
        end = date_end[1] + "-" + date_end[2] + "-" + date_end[0]
        df = vndata.price(f"{symbol}", start, end)
        
    else:
        df = web.DataReader(f"{symbol}", "yahoo", start, end)

    if indicator == "None":  # stock price and trading volume

        fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
        fig.add_trace(go.Scatter(x=df.index, y=df["Adj Close"], mode="lines", name="Price (USD)", \
            line=dict(color="blue")), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Trading Volume", \
            marker_color="blue"), row=2, col=1)
        fig.update_xaxes(title="Date", row=1, col=1)
        fig.update_xaxes(title="Date", row=2, col=1)
        fig.update_layout(title="Stock Price and Trading Volume", autosize=False, width=1200, height=700)

        return fig

    elif indicator == "OBV":  # create OBV indicator
        
        # option_periods = st.sidebar.slider("Period", min_value=2, max_value=251, value=20)
        OBV = []
        OBV.append(0)
        for i in range(1, len(df["Adj Close"])):
            if df["Adj Close"][i] > df["Adj Close"][i-1]:
                OBV.append(OBV[-1] + df.Volume[i])
            elif df["Adj Close"][i] < df["Adj Close"][i-1]:
                OBV.append(OBV[-1] - df.Volume[i])
            else:
                OBV.append(OBV[-1])

        # Store OBV and OBV_EMA
        df_obv = df.copy()
        df_obv["OBV"] = OBV
        df_obv["OBV_EMA"] = df_obv["OBV"].ewm(span=period).mean()

        def get_signal_OBV(signal, col1, col2):  # def signal
            buy_signal = []
            sell_signal = []
            flag = 0
            for i in range(len(signal)):
                if signal[col1][i] > signal[col2][i] and flag != 1:
                    buy_signal.append(signal["Adj Close"][i])
                    sell_signal.append(np.nan)
                    flag = 1
                elif signal[col1][i] < signal[col2][i] and flag != -1:
                    buy_signal.append(np.nan)
                    sell_signal.append(signal["Adj Close"][i])
                    flag = -1
                else:
                    buy_signal.append(np.nan)
                    sell_signal.append(np.nan)
            return buy_signal, sell_signal

        # get signal
        df_obv["Buy"] = get_signal_OBV(df_obv, "OBV", "OBV_EMA")[0]
        df_obv["Sell"] = get_signal_OBV(df_obv, "OBV", "OBV_EMA")[1]

        # initialize figure with subplots
        fig = make_subplots(rows=2, cols=1)
        # add traces
        # figure 1
        fig.add_trace(go.Scatter(x=df_obv.index, y=df_obv["Adj Close"], mode="lines", name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_obv.index, y=df_obv["Buy"], mode="markers", \
            name="Buy Signal", marker=dict(color="green", symbol="arrow-up")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_obv.index, y=df_obv["Sell"], mode="markers", \
            name="Sell Signal", marker=dict(color="red", symbol="arrow-down")), row=1, col=1)
        # figure 2
        fig.add_trace(go.Scatter(x=df_obv.index, y=df_obv["OBV"], mode="lines", name="OBV", line=dict(color="orange")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_obv.index, y=df_obv["OBV_EMA"], mode="lines", name="OBV_EMA", line=dict(color="purple")), row=2, col=1)
        fig.update_xaxes(title="Date", row=1, col=1)
        fig.update_yaxes(title="USD", row=1, col=1)
        fig.update_xaxes(title="Date", row=2, col=1)
        fig.update_layout(title="OBV Indicator", autosize=False, width=1200, height=900)

        return fig

    elif indicator == "Bollinger Bands":  # create Bollinger Bands indicator

        # calculate the SMA
        df["SMA"] = df["Adj Close"].rolling(window=period).mean()
        # get the Standard Deviation
        df["STD"] = df["Adj Close"].rolling(window=period).std()
        # calculate the upper Bollinger Bands
        df["Upper"] = df["SMA"] + 2*df["STD"]
        # calculate the lower Bollinger Bands
        df["Lower"] = df["SMA"] - 2*df["STD"]

        df_bb = df[period-1:]

        def get_signal_BollingerBands(data):  # def signal
            buy_signal = []
            sell_signal = []
            for i in range(len(data["Adj Close"])):
                if data["Adj Close"][i] > data["Upper"][i]:
                    buy_signal.append(np.nan)
                    sell_signal.append(data["Adj Close"][i])
                elif data["Adj Close"][i] < data["Lower"][i]:
                    buy_signal.append(data["Adj Close"][i])
                    sell_signal.append(np.nan)
                else:
                    buy_signal.append(np.nan)
                    sell_signal.append(np.nan)
            return buy_signal, sell_signal

        # get signal
        df_bb["Buy"] = get_signal_BollingerBands(df_bb)[0]
        df_bb["Sell"] = get_signal_BollingerBands(df_bb)[1]

        # initialize figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb["Upper"], fill=None, mode="lines", name="The Upper", \
            line=dict(color="lightgray")))
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb["Lower"], fill="tonexty", mode="lines", \
            name="The Lower", fillcolor="lightgray", line=dict(color="lightgray")))
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb["Adj Close"], mode="lines", name="Price", \
            line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb["SMA"], mode="lines", name="SMA", line=dict(color="yellow")))
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb["Buy"], mode="markers", \
            name="Buy Signal", marker=dict(color="green", symbol="arrow-up")))
        fig.add_trace(go.Scatter(x=df_bb.index, y=df_bb["Sell"], mode="markers", \
            name="Sell Signal", marker=dict(color="red", symbol="arrow-down")))
        fig.update_layout(title="Bollinger Bands Indicator", xaxis_title="Date", \
            yaxis_title="USD", autosize=False, width=1200, height=500)

        return fig

    elif indicator == "RSI":  # create RSI indicator

        delta = df["Adj Close"].diff(1)
        delta.dropna(inplace=True)
        
        positive = delta.copy()
        negative = delta.copy()
        positive[positive < 0] = 0
        negative[negative > 0] = 0

        average_gain = positive.rolling(window=period).mean()
        average_loss = abs(negative.rolling(window=period).mean())
        relative_strength = average_gain / average_loss
        RSI = 100 - (100 / (1 + relative_strength))

        df_rsi = pd.DataFrame()
        df_rsi["Adj Close"] = df["Adj Close"].copy()
        df_rsi["RSI"] = RSI  # add RSI column

        def get_signal_RSI(dt, high, low):  # def signal
            buy_signals = []
            sell_signals = []
            for i in range(len(dt["RSI"])):
                if dt["RSI"][i] > high:
                    buy_signals.append(np.nan)
                    sell_signals.append(dt["Adj Close"][i])
                elif dt["RSI"][i] < low:
                    buy_signals.append(dt["Adj Close"][i])
                    sell_signals.append(np.nan)
                else:
                    buy_signals.append(np.nan)
                    sell_signals.append(np.nan)
            return buy_signals, sell_signals

        # get signal
        df_rsi["Buy"] = get_signal_RSI(df_rsi, overbought, oversold)[0]
        df_rsi["Sell"] = get_signal_RSI(df_rsi, overbought, oversold)[1]
        
        # initialize figure with subplots
        fig = make_subplots(rows=2, cols=1)
        # add traces
        # figure 1
        fig.add_trace(go.Scatter(x=df_rsi.index, y=df_rsi["Adj Close"], mode="lines", \
            name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_rsi.index, y=df_rsi["Buy"], mode="markers", name="Buy Signal", \
            marker=dict(color="green", symbol="arrow-up")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_rsi.index, y=df_rsi["Sell"], mode="markers", name="Sell Signal", \
            marker=dict(color="red", symbol="arrow-down")), row=1, col=1)
        # figure 2
        fig.add_trace(go.Scatter(x=df_rsi.index, y=df_rsi["RSI"], mode="lines", name="RSI"), row=2, col=1)
        fig.add_hline(y=overbought, line=dict(color="green", dash="dash", width=1), row=2, col=1)
        fig.add_hline(y=oversold, line=dict(color="green", dash="dash", width=1), row=2, col=1)
        # update properties
        fig.update_xaxes(title="Date", row=1, col=1)
        fig.update_yaxes(title="USD", row=1, col=1)
        fig.update_xaxes(title="Date", row=2, col=1)
        fig.update_layout(title="RSI Indicator", autosize=False, width=1200, height=900)
        
        return fig

    elif indicator == "MA":  # create MA indicator

        ma_1 = period
        ma_2 = period_slow
        df[f"SMA_{ma_1}"] = df["Adj Close"].rolling(window=ma_1).mean()
        df[f"SMA_{ma_2}"] = df["Adj Close"].rolling(window=ma_2).mean()
        df = df.iloc[ma_2:]

        # create signal
        buy_signal = []
        sell_signal = []
        trigger = 0
        for i in range(len(df)):
            if df[f"SMA_{ma_1}"].iloc[i] > df[f"SMA_{ma_2}"].iloc[i] and trigger != 1:
                buy_signal.append(df["Adj Close"].iloc[i])
                sell_signal.append(np.nan)
                trigger = 1
            elif df[f"SMA_{ma_1}"].iloc[i] < df[f"SMA_{ma_2}"].iloc[i] and trigger != -1:
                buy_signal.append(np.nan)
                sell_signal.append(df["Adj Close"].iloc[i])
                trigger = -1
            else:
                buy_signal.append(np.nan)
                sell_signal.append(np.nan)

        # get signal
        df["Buy"] = buy_signal
        df["Sell"] = sell_signal

        # initialize figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Adj Close"], mode="lines", name="Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df[f"SMA_{ma_1}"], mode="lines", name=f"SMA_{ma_1}", \
            line=dict(color="orange", dash="dash", width=0.9)))
        fig.add_trace(go.Scatter(x=df.index, y=df[f"SMA_{ma_2}"], mode="lines", name=f"SMA_{ma_2}", \
            line=dict(color="black", dash="dash", width=0.9)))
        fig.add_trace(go.Scatter(x=df.index, y=df["Buy"], mode="markers", \
            name="Buy Signal", marker=dict(color="green", symbol="arrow-up")))
        fig.add_trace(go.Scatter(x=df.index, y=df["Sell"], mode="markers", \
            name="Sell Signal", marker=dict(color="red", symbol="arrow-down")))
        fig.update_layout(title="MA Indicator", xaxis_title="Date", yaxis_title="USD", autosize=False, width=1200, height=500)

        return fig

    # build MACD indicator
    elif indicator == "MACD":  
        ShortEMA = df["Adj Close"].ewm(span=period, adjust=False).mean()
        LongEMA = df["Adj Close"].ewm(span=period_slow, adjust=False).mean()
        MACD = ShortEMA - LongEMA
        signal = MACD.ewm(span=period_signal, adjust=False).mean()

        df["MACD"] = MACD
        df["Signal Line"] = signal

        def buy_sell(signal):  # def signal
            buy = []
            sell = []
            flag = 0

            for i in range(0, len(signal)):
                if signal["MACD"][i] > signal["Signal Line"][i]:
                    sell.append(np.nan)
                    if flag != 1:
                        buy.append(signal["Adj Close"][i])
                        flag = 1
                    else:
                        buy.append(np.nan)
                elif signal["MACD"][i] < signal["Signal Line"][i]:
                    buy.append(np.nan)
                    if flag != -1:
                        sell.append(signal["Adj Close"][i])
                        flag = -1
                    else:
                        sell.append(np.nan)
                else:
                    buy.append(np.nan)
                    sell.append(np.nan)

            return buy, sell

        # get signal
        df["Buy_Signal_Price"] = buy_sell(df)[0]
        df["Sell_Signal_Price"] = buy_sell(df)[1]

        # initialize figure with subplots
        fig = make_subplots(rows=2, cols=1)
        # add traces
        # figure 1
        fig.add_trace(go.Scatter(x=df.index, y=df["Adj Close"], mode="lines", name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Buy_Signal_Price"], mode="markers", \
            name="Buy Signal", marker=dict(color="green", symbol="arrow-up")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Sell_Signal_Price"], mode="markers", \
            name="Sell Signal", marker=dict(color="red", symbol="arrow-down")), row=1, col=1)
        # figure 2
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD", line=dict(color="purple")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Signal Line"], mode="lines", name="Signal Line", line=dict(color="orange")), row=2, col=1)
        # update properties
        fig.update_xaxes(title="Date", row=1, col=1)
        fig.update_yaxes(title="USD", row=1, col=1)
        fig.update_xaxes(title="Date", row=2, col=1)
        fig.update_layout(title="MACD Indicator", autosize=False, width=1200, height=900)

        return fig

    # create MFI indicator
    else:

        typical_price = (df["Adj Close"] + df["High"] + df["Low"]) / 3 # caculate typical price
        # option_periods = st.sidebar.slider("Period", min_value=2, max_value=251, value=14)
        money_flow = typical_price * df["Volume"]  # caculate money flow
        positive_flow = []
        negative_flow = []

        # loop through the typical price
        for i in range(1, len(typical_price)):
            if typical_price[i] > typical_price[i-1]:
                positive_flow.append(money_flow[i-1])
                negative_flow.append(0)
            elif typical_price[i] < typical_price[i-1]:
                negative_flow.append(money_flow[i - 1])
                positive_flow.append(0)
            else:
                positive_flow.append(0)
                negative_flow.append(0)

        # get all of the positive and negative money flows within the time period
        positive_mf = []
        negative_mf = []
        for i in range(period-1, len(positive_flow)):
            positive_mf.append(sum(positive_flow[i + 1 - period:i + 1]))
        for i in range(period-1, len(negative_flow)):
            negative_mf.append(sum(negative_flow[i + 1 - period:i + 1]))

        # caculate MFI
        mfi = 100 * (np.array(positive_mf)/(np.array(positive_mf)+np.array(negative_mf)))
        df_mfi = pd.DataFrame()
        df_mfi["MFI"] = mfi
        new_df = df[period:]
        new_df["MFI"] = mfi

        def get_signal(data, high, low):  # def signal
            buy_signals = []
            sell_signals = []
            for i in range(len(data["MFI"])):
                if data["MFI"][i] > high:
                    buy_signals.append(np.nan)
                    sell_signals.append(data["Adj Close"][i])
                elif data["MFI"][i] < low:
                    buy_signals.append(data["Adj Close"][i])
                    sell_signals.append(np.nan)
                else:
                    buy_signals.append(np.nan)
                    sell_signals.append(np.nan)
            return buy_signals, sell_signals

        # get signal
        new_df["Buy"] = get_signal(new_df, overbought, oversold)[0]
        new_df["Sell"] = get_signal(new_df, overbought, oversold)[1]

        # initialize figure with subplots
        fig = make_subplots(rows=2, cols=1)
        # add traces
        # figure 1
        fig.add_trace(go.Scatter(x=new_df.index, y=new_df["Adj Close"], mode="lines", name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=new_df.index, y=new_df["Buy"], mode="markers", name="Buy Signal", \
            marker=dict(color="green", symbol="arrow-up")), row=1, col=1)
        fig.add_trace(go.Scatter(x=new_df.index, y=new_df["Sell"], mode="markers", name="Sell Signal", \
            marker=dict(color="red", symbol="arrow-down")), row=1, col=1)
        # figure 2
        fig.add_trace(go.Scatter(x=new_df.index, y=new_df["MFI"], mode="lines", name="MFI"), row=2, col=1)
        fig.add_hline(y=overbought, line=dict(color="green", dash="dash", width=1), row=2, col=1)
        fig.add_hline(y=oversold, line=dict(color="green", dash="dash", width=1), row=2, col=1)
        # update properties
        fig.update_xaxes(title="Date", row=1, col=1)
        fig.update_yaxes(title="USD", row=1, col=1)
        fig.update_xaxes(title="Date", row=2, col=1)
        fig.update_layout(title="MFI Indicator", autosize=False, width=1200, height=900)

        return fig
        

# st.set_option('deprecation.showPyplotGlobalUse', False)
sub = "" + name.loc[option_symbol].at["Name"]
st.subheader(f"{sub} : {option_symbol}")
st.plotly_chart(test(option_symbol, option_indi, option_start, option_end, option_periods, option_periods_slow, \
    option_periods_signal, option_overbought, option_oversold, option_type), use_container_width=True)
st.write("Author: Tran Thanh Phuc")
st.write("Code: K194141740")
st.write("Email: phuctt19414c@st.uel.edu.vn")
# st.write(type(option_end))
# st.write(option_end)


# st.title("This is the title")
# st.header("This is header")
# st.write("This is write")

# some_dictionary = {
#     "key": "value",
#     "key2": "value2"
# }
# some_list = [1, 2, 3]
# st.write(some_dictionary)
# st.write(some_list)

# st.sidebar.write("This is a sidebar")