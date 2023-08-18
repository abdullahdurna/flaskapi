from flask import Flask, jsonify
import requests
import talib
import numpy as np

app = Flask(__name__)

BASE_URL = "https://api.binance.com"
COIN_INFO_ENDPOINT = "/api/v3/ticker/24hr"
HISTORICAL_DATA_ENDPOINT = "/api/v3/klines"


@app.route('/')
def hello_world():
    return jsonify(message="Hello, World!")


@app.route('/getCoins')
def get_coins():
    response = requests.get(BASE_URL + COIN_INFO_ENDPOINT)

    if response.status_code != 200:
        return jsonify(error="Failed to retrieve data from Binance"), 500

    coin_data = response.json()
    usdt_pairs = [coin for coin in coin_data if coin['symbol'].endswith("USDT")]
    filtered_data = [{"symbol": coin["symbol"], "price": coin["lastPrice"]} for coin in usdt_pairs]

    return jsonify(filtered_data)


@app.route('/getHistoricalData/<string:symbol>/<string:interval>')
def get_historical_data(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 100
    }

    response = requests.get(BASE_URL + HISTORICAL_DATA_ENDPOINT, params=params)

    if response.status_code != 200:
        return jsonify(error="Failed to retrieve data from Binance"), 500

    data = response.json()
    close_prices = np.array([float(item[4]) for item in data])

    # TA-Lib ile RSI hesaplama
    rsi_value = talib.RSI(close_prices)[-1]  # En son RSI değerini al

    return jsonify({"closePrices": close_prices.tolist(), "rsi": rsi_value})


@app.route('/getOversoldCoins/<string:interval>')
def get_oversold_coins(interval):
    response = requests.get(BASE_URL + COIN_INFO_ENDPOINT)
    if response.status_code != 200:
        return jsonify(error="Failed to retrieve data from Binance"), 500

    coin_data = response.json()
    usdt_pairs = [coin for coin in coin_data if coin['symbol'].endswith("USDT")]

    oversold_coins = []

    for coin in usdt_pairs:
        params = {
            "symbol": coin["symbol"],
            "interval": interval,
            "limit": 100
        }

        response = requests.get(BASE_URL + HISTORICAL_DATA_ENDPOINT, params=params)
        if response.status_code != 200:
            continue

        data = response.json()
        close_prices = np.array([float(item[4]) for item in data])

        rsi_value = talib.RSI(close_prices)[-1]

        if rsi_value < 30:
            oversold_coins.append({"symbol": coin["symbol"], "rsi": rsi_value})

    return jsonify(oversold_coins)


if __name__ == '__main__':
    app.run()
