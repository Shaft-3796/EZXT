# EZXT

### Open source & beginner-friendly ccxt wrapped client for binance & ftx
- [Français](https://github.com/Shaft-3796/EZXT/blob/master/README-FRA.md)

<br>

### Want to contact me ? 👋

https://discord.gg/wfpGXvjj9t

### Want to support my work ? 💰

- paypal: *sh4ft.me@gmail.com*
- usdt (ERC20): *0x17B516E9cA55C330B6b2bd2830042cAf5C7ecD7a*
- btc: *34vo6zxSFYS5QJM6dpr4JLHVEo5vZ5owZH*
- eth: *0xF7f87bc828707354AAfae235dE584F27bDCc9569*

*thanks if you do it 💖*

## What's EZXT ? 📈
 
 **EZXT is a simple client to interact with ftx and binance using ccxt**
 
 ##### Dependencies :

 - Pandas
 - Numpy
 - ccxt
 
 ## Doc 📝

---

#### Initialisation
```python
Client(exchange, api_key=None, api_secret=None, subaccount=None))
```
##### Required parameters:
- exchange: ccxt.binance or ccxt.ftx
##### Optional parameters:
- api_key: your api key
- api_secret: your api secret
- subaccount: your sub-account's name if you're using ftx

---

#### get_bid & get_ask
```python
client.get_ask(market))
client.get_bid(market))
```
##### Required parameters:
- market: the market you want to get the bid/ask for as a string. Example: "BTC/USDT"

---

####  post_market_order & post_limit_order & post_take_profit & post_stop
```python
client.post_market_order(market, side, amount)
client.post_limit_order(market, side, amount, price)
client.post_take_profit(market, side, amount, price)
client.post_stop(market, side, amount, price)
```
##### Required parameters:
- market: the market you want to post an order for as a string. Example: "BTC/USDT"
- side: "buy" or "sell"
- amount: the amount you want to buy/sell as a float. /!\ Use get_buy_size or get_sell_size functions to avoid errors.
- price: with post_limit_order, post_take_profit and post_stop, the price of the order as a float.

---

####  cancel_order
```python
client.cancel_order(order)
```
##### Required parameters:
- order: the order you want to cancel as a dict returned by get_order or get_all_orders methods.

---

####  get_free_balance
```python
client.get_free_balance(market)
```
##### Required parameters:
- market: the market you want to get the free balance for as a string. Example: "BTC/USDT"

---

### get_klines
```python
client.get_klines(market, interval, limit)
```
##### Required parameters:
- market: the market you want to get the klines for as a string. Example: "BTC/USDT"
- interval: the interval you want to get the klines for as a string. Example: "1m" or "1d"
- ##### Optional parameters:
- limit: the number of klines you want to get as an int. By default it's 100.

---

### get_market return some market information
```python
client.get_market(market)
```
##### Required parameters:
- market: the market you want to get the market data for as a string. Example: "BTC/USDT"

---

### get_precision return the precision of the market
```python
client.get_precision(market)
```
##### Required parameters:
- market: the market you want to get the precision for as a string. Example: "BTC/USDT"

---

### get_buy_size return the size of your order properly to avoid errors
```python
client.get_buy_size(market, amount)
```
##### Required parameters:
- market: the market you want to get the buy size for as a string. Example: "BTC/USDT"
- amount: the amount in percent you want to buy of your wallet as an int or a float: Example If you have 1000 usdt, and 
you enter 50 it will return approximately 500
##### Optional parameters:
- price: if you will make a limit order, specify the price of your order as an int or a float.
- free_currency_balance: If you fill it the function will use this amount instead of check your free balance to calculate the size, Example: you can enter 350 on this parameter and 100 on amount parameter, it will return a size of approximately 350.  If you're trading BTC/USDT enter the usdt amount.

---

### get_sell_size return the size of your order properly to avoid errors
```python
client.get_sell_size(market, amount)
```
##### Required parameters:
- market: the market you want to get the buy size for as a string. Example: "BTC/USDT"
- amount: the amount in percent you want to buy of your wallet as an int or a float: Example If you have 1000 usdt, and 
you enter 50 it will return approximately 500
##### Optional parameters:
/!\ There is no price parameter even if you will make a limit order.
- free_currency_balance: If you fill it the function will use this amount instead of check your free balance to calculate the size, Example: you can enter 350 on this parameter and 100 on amount parameter, it will return a size of approximately 350. If you're trading BTC/USDT enter the btc amount.

---

### get_order return the order you want
```python
client.get_order(order_id)
```
##### Required parameters:
- order_id: the id of the order you want to get as an int.

---

### get_all_orders return all your orders as a list
```python
client.get_all_orders()
```
##### Optional parameters:
- market: the market you want to get the orders for as a string. Example: "BTC/USDT".
- open_only: True if you want to get only open orders.

---

### get_order_status return the status of your order, canceled, filled, or open
```python
client.get_order_status(order_id)
```
##### Required parameters:
- order_id: the id of the order you want to get as an int.

---

## Some examples, dm me for more
```python
import math
import ccxt
import pandas as pd
from EZXT import Client

binance_client = Client(ccxt.binance, "api_key", "api_secret")
ftx_client = Client(ccxt.ftx, "api_key", "api_secret")
client = Client(ccxt.binance)

# return ask price of btc/usdt
client.get_ask("BTC/USDT")

# Post a market buy order of 50% of my wallet
size = ftx_client.get_buy_size("BTC/USDT", 50)
ftx_client.post_market_order("BTC/USDT", size, "buy")

# Post a limit sell order of 30 bitcoins
size = ftx_client.get_sell_size("BTC/USDT", 100, 30)
ftx_client.post_limit_order("BTC/USDT", "sell", size, 60000)
````
