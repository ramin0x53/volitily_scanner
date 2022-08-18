from flask import Flask, request
import requests
import concurrent.futures

app = Flask(__name__)

lenght = 20
tf = "1d"
symbols = []

@app.route("/", methods=["GET"])
def hello_world():
    global lenght, tf

    if request.args.get("len") != None:
        lenght = request.args.get("len", type=int)

    if request.args.get("tf") != None:
        tf = request.args.get("tf")

    s = getAllSymbolVol()
    # return f"<p>{s}</p>"

    #retrun s as html
    html = "<p>"
    for i in s:
        html = html + f"{i[0]}:&nbsp&nbsp&nbsp {i[1]}<br>"
        html = html + "--------------------------------------------------------<br>"
    html = html + "</p>"
    return html


def getAllSymbols():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=250&page=1&sparkline=false"

    response = requests.get(url)
    data = response.json()
    result = []
    for token in data:
        if "usd" not in token["symbol"]:
            s = token["symbol"] + "usdt"
            result.append(s.upper())
    

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in result:
            executor.submit(binancecheck, symbol)
    return

def binancecheck(symbol):
    global symbols
    url = "https://api.binance.com/api/v1/klines?interval=1h&limit=1&symbol=" + symbol
    response = requests.get(url)
    d = response.json()
    if type(d) != list:
        return
    symbols.append(symbol)

#Get a symbol historical data from Binance
def getHistoricalData(symbol, interval, limit):
    url = "https://api.binance.com/api/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()

    for line in data:
        # print(line)
        del line[5:]

    for i in range(len(data)):
        for j in range(1, len(data[i])):
            data[i][j] = float(data[i][j])
    return data

def highLowPerc(high, low, candleColor):
    if candleColor == "green":
        return ((high - low)*100) / low
    elif candleColor == "red":
        return ((high - low)*100) / high
    else:
        print("Error: Candle color not recognized")

def openClosePerc(open, close):
    if open <= close:
        return ((close - open)*100) / open
    else:
        return (-(open - close)*100) / open

def averagePerc(data):
    r = 0
    for candle in data:
        if candle[1] <= candle[4]:
            r = r + highLowPerc(candle[2], candle[3], "green")
        else:
            r = r + highLowPerc(candle[2], candle[3], "red")
    return r/len(data)

def calVol(symbol, interval, limit):
    data = getHistoricalData(symbol, interval, limit)
    lastBar = len(data) - 1
    result = openClosePerc(data[lastBar][1], data[lastBar][4])/averagePerc(data)
    return result


def getAllSymbolVol():
    global symbols
    getAllSymbols()
    result = {}

    #fill result with CalVol for each symbol with ThreadPool
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            result[symbol] = executor.submit(calVol, symbol, tf, lenght)

    for n in result:
        result[n] = result[n].result()
    
    #sort result by value
    sortResult = sorted(result.items(), key=lambda x: x[1], reverse=True)

    return sortResult