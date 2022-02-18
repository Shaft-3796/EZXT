import math
import ccxt
import pandas as pd


# ----------------------------------------------------------------------------------------------------------------------
# A ccxt wrapped client for binance & ftx. Made with <3 by Shaft
# ----------------------------------------------------------------------------------------------------------------------
class Client:
    def __init__(self, exchange, api_key=None, api_secret=None, subaccount=None):
        self.exchange = exchange

        # Initializing with FTX or Binance
        if api_key is not None and api_secret is not None:
            # With FTX
            if subaccount is not None and exchange == ccxt.ftx:
                self.client = exchange({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'headers': {'FTX-SUBACCOUNT': subaccount}
                })
            # With Binance
            else:
                self.client = exchange({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True
                })
        # With ftx or binance without authentication
        else:
            self.client = exchange()

        self.client.load_markets()

    # Return bid market price of an asset
    def get_bid(self, symbol):
        self.exchange.load_markets()
        return self.exchange.fetch_ticker(symbol)["bid"]

    # Return ask market price of an asset
    def get_ask(self, symbol):
        self.exchange.load_markets()
        return self.exchange.fetch_ticker(symbol)["ask"]

    # Post a market order
    def post_market_order(self, symbol, side, amount):
        # return if order size is 0
        if amount == 0:
            return False
        return self.exchange.create_order(symbol=symbol, type='market', side=side, amount=amount)

    # Post a market order
    def post_limit_order(self, symbol, side, amount, price):
        # return if order size is 0
        if amount == 0:
            return False
        return self.exchange.create_limit_order(symbol=symbol, side=side, amount=amount, price=price)

    # Post a stop order
    def post_stop(self, symbol, amount, price):
        # return if order size is 0
        if amount == 0:
            return False
        return self.exchange.create_order(symbol=symbol, type='stop', side="sell", amount=amount,
                                          params={"stopPrice": price})

    # Post a tp order
    def post_take_profit(self, symbol, amount, price):
        # return if order size is 0
        if amount == 0:
            return False
        return self.exchange.create_order(symbol=symbol, type='takeProfit', side="sell", amount=amount,
                                          params={"triggerPrice": price})

    # Cancel and order
    def cancel_order(self, order):
        order_type = order['info']['type']
        if order_type == "stop" or order_type == "take_profit":
            return self.exchange.cancel_order(order["info"]["id"], None,
                                              {'method': 'privateDeleteConditionalOrdersOrderId'})

        return self.exchange.cancel_order(order["info"]["id"], None,
                                          {'method': 'privateDeleteOrdersOrderId'})

    # Return available balance of an asset
    def get_free_balance(self, symbol):
        self.exchange.load_markets()
        balances = self.exchange.fetch_balance()
        balance = balances.get(symbol, {})
        free = balance.get('free', 0)
        return free

    # Return klines as a dataframe of an asset
    def get_klines(self, symbol, interval, limit=100):
        klines = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
        dataframe = pd.DataFrame(klines)
        dataframe.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close'}, inplace=True)
        dataframe.pop(5)
        dataframe.drop(index=dataframe.index[-1], axis=0, inplace=True)
        return dataframe

    # Get market information
    def get_market(self, symbol):
        return self.exchange.market(symbol)

    # Get market precision
    def get_precision(self, symbol):
        market = self.get_market(symbol)
        return market["precision"]["amount"], market["limits"]["amount"]["min"]

    # Calculate the size of a buy position
    def get_buy_size(self, coin, pair, amount, price=None, free_currency_balance=None):

        # get free balance
        if free_currency_balance is None:
            free_currency_balance = self.get_free_balance(coin)

        # apply percentage
        amount = (amount * float(free_currency_balance)) / 100

        # get precision & limit (minimum amount)
        precision, limit = self.get_precision(pair)

        digits = int(math.sqrt((int(math.log10(precision)) + 1) ** 2)) + 1

        # get price
        if price is None:
            price = self.get_ask(pair)

        amount /= price

        # apply precision
        amount = self.truncate(amount, digits)

        # apply limit
        if amount < limit:
            return 0

        return amount

    # Calculate the size of a sell position
    def get_sell_size(self, symbol, pair, amount, free_token_balance=None):

        # get free balance
        if free_token_balance is None:
            free_token_balance = self.get_free_balance(symbol)

        # apply percentage
        amount = (amount * float(free_token_balance)) / 100

        # get precision & limit (minimum amount)
        precision, limit = self.get_precision(pair)

        digits = int(math.sqrt((int(math.log10(precision)) + 1) ** 2)) + 1

        # apply precision
        amount = self.truncate(amount, digits)

        # apply limit
        if amount < limit:
            return 0

        return amount

    # Get an order
    def get_order(self, order, order_id=None):
        if order_id is None:
            order_id = order["info"]["id"]
        return self.exchange.fetch_order(order_id, None, {'method': 'privateGetOrdersOrderId'})

    # Get all orders
    def get_all_orders(self, symbol=None, open_only=True):
        if open_only:
            return self.exchange.fetch_open_orders(symbol=symbol)
        else:
            return self.exchange.fetch_orders(symbol=symbol)

    # Return the status of an order
    def get_order_status(self, order, order_id=None):
        if order_id is None:
            order_id = order["info"]["id"]
            order = self.exchange.fetch_order(order_id, None, {'method': 'privateGetOrdersOrderId'})

        if order["info"]["remaining"] == 0:
            return "filled"
        elif order["info"]["status"] == "open":
            return "open"
        elif order["info"]["status"] == "canceled":
            return "canceled"

    # Used to set precision of a number
    def truncate(self, number, decimals=0):
        """
        Returns a value truncated to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer.")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more.")
        elif decimals == 0:
            return math.trunc(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor
