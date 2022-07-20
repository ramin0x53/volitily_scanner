from flask import Flask, request
import requests
import concurrent.futures

app = Flask(__name__)

lenght = 20
tf = "1d"

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
    html = html + "</p>"
    return html


def getAllSymbols():
    url = "https://api.binance.com/api/v1/exchangeInfo"
    response = requests.get(url)
    data = response.json()
    symbols = []
    for i in data["symbols"]:
        if "USDT" in i["symbol"] and "UPUSDT" not in i["symbol"] and "DOWNUSDT" not in i["symbol"] and "BULLUSDT" not in i["symbol"] and "BEARUSDT" not in i["symbol"]:
            symbols.append(i["symbol"])
    return symbols

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
    symbols = getAllSymbols()
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
