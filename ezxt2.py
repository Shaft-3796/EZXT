import functools
import math
from types import NoneType

import pandas as pd
import ccxt

'''
Utility class
'''


# Representing different state for the client (used by WrappedGenericExchange)
class Client_state:
    NOT_INSTANTIATED = "client wasn't instanced"
    NOT_AUTHENTICATED = "client was instanced but wasn't linked to any account"
    AUTHENTICATED = "client instanced and linked to an account"


# Terminal colors
class Colors:
    """
    Terminal colors
    """
    LIGHT_YELLOW = '\33[91m'
    LIGHT_GREEN = '\33[93m'
    LIGHT_BLUE = '\33[94m'
    LIGHT_PURPLE = '\33[95m'
    LIGHT_CYAN = '\33[96m'
    LIGHT_WHITE = '\33[97m'
    RED = '\33[31m'
    YELLOW = '\33[33m'
    GREEN = '\33[32m'
    BLUE = '\33[34m'
    PURPLE = '\33[35m'
    CYAN = '\33[36m'
    WHITE = '\33[37m'
    END = '\33[0m'
    ERROR = '\x1b[0;30;41m'


'''
decorators & utility functions
'''


# Match a size with the precision of the market
def truncate(number: float, decimals: int = 0) -> float:
    """
    Returns a value truncated to a specific number of decimal places.
    :param number: number to truncate
    :param decimals: market precision
    :return: new number
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor


# Load markets before a method
def load_markets(func: callable):
    """
    Load markets before a method
    :param func: function to be decorated
    :return: a function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0]  # we take the object from which the method is called
        instance.client.load_markets()
        return func(*args, **kwargs)

    return wrapper


# Check if the client is authenticated
def only_authenticated(func: callable):
    """
        Check if the client is authenticated
        :param func: function to be decorated
        :return: a function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0]  # we take the object from which the method is called
        if instance.client_state == Client_state.NOT_AUTHENTICATED:
            raise NotAuthenticatedException(func.name)

        return func(*args, **kwargs)

    return wrapper


def only_implemented_types(func):
    """
    Decorator to raise an exception when a not implemented type is given as a parameter to a function
    :param func: function to be decorated
    :return: decorated function
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        parameters = func.__code__.co_varnames
        annotations = func.__annotations__
        arguments = {}
        # making arguments dictionary to put them with their parameter name
        for i in range(len(args)):
            arguments[parameters[i]] = args[i]
        for parameter in kwargs:
            arguments[parameter] = kwargs[parameter]

        # apply verification to all parameters in annotations
        for parameter in annotations:
            if parameter not in arguments:
                continue
            if not isinstance(arguments[parameter], annotations[parameter]):
                raise TypeNotImplemented(parameter, annotations[parameter], type(arguments[parameter]))

        return func(*args, **kwargs)

    return wrapper


'''
exceptions
'''


class NotAuthenticatedException(BaseException):
    """
    raised when a method related to the private API of an exchange is called with a not authenticated client
    """

    def __init__(self, func: callable):
        """
        :param func: a function
        """
        super().__init__(f"{Colors.ERROR}NotAuthenticatedException: you can't call {func.name} because your not "
                         f"authenticated to the private API{Colors.END}")


class TypeNotImplemented(BaseException):
    """
    Exception to be raised when a not implemented type is given to a function
    """

    def __init__(self, parameter_name, required_type, given_type):
        """
        Constructor
        :param parameter_name: name of the parameter involved in the exception
        :param required_type:
        """
        super().__init__(
            f"{Colors.ERROR}TypeNotImplemented exception {given_type} is not implemented for this parameter, parameter "
            f"{parameter_name} must be {required_type}{Colors.END}")


'''
Core
'''


# Template class representing a wrapped exchange
class WrappedGenericExchange:

    def __init__(self, exchange):
        """
        Template class representing a wrapped exchange
        :param exchange: a ccxt exchange ( a class not an object ), ccxt.ftx for example.
        """
        self.exchange = exchange  # Look at the method docstring
        self.client = None  # Store the instanced client
        self.client_state = Client_state.NOT_INSTANTIATED  # Store the client state

    # Overrideable
    @only_implemented_types
    def instantiate_client(self, api_key: (str, NoneType) = None, api_secret: (str, NoneType) = None,
                           enable_rate_limit: bool = True):
        """
        Instantiate ccxt client
        :param api_key: api key in your cex settings
        :param api_secret: api secret in your cex settings
        :param enable_rate_limit: True to activate the control of the ratelimit
        """

        if api_key is not None and api_secret is not None:
            self.client = self.exchange({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': enable_rate_limit
            })
            self.client_state = Client_state.AUTHENTICATED
        else:
            self.client = self.exchange({
                'enableRateLimit': enable_rate_limit
            })
            self.client_state = Client_state.NOT_AUTHENTICATED

    # Public API
    @load_markets
    @only_implemented_types
    def get_bid(self, market: str, params: (dict, NoneType) = None) -> int:
        """
        Return bid price of a market
        :param market: Example: "BTC/USD"
        :param params: Additional parameters
        :return: bid price
        """
        if params is None:
            params = {}
        return int(self.client.fetch_ticker(market, params=params)["bid"])

    @load_markets
    @only_implemented_types
    def get_ask(self, market: str, params: (dict, NoneType) = None) -> int:
        """
        Return ask price of a market
        :param market: example: "BTC/USD"
        :param params: additional parameters
        :return: ask price
        """
        if params is None:
            params = {}
        return int(self.client.fetch_ticker(market, params=params)["ask"])

    @only_implemented_types
    def get_kline(self, market: str, timeframe: str, limit: int, params: (dict, NoneType) = None) -> pd.DataFrame:
        """
        Download kline for a market
        :param market: example "ETH/USD"
        :param timeframe: usually '1y', '1m', '1d', '1w', '1h'...
        :param limit: number of candles
        :param params: additional parameters
        :return: pandas dataframe
        """
        if params is None:
            params = {}
        kline = self.client.fetch_ohlcv(market, timeframe, limit=limit, params=params)
        dataframe = pd.DataFrame(kline)
        dataframe.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close'}, inplace=True)
        dataframe.pop(5)
        dataframe.drop(index=dataframe.index[-1], axis=0, inplace=True)
        return dataframe

    @only_implemented_types
    def get_market(self, market: str) -> dict:
        """
        Get some market information
        :param market: example "ETH/USD"
        :return:
        """
        return self.client.market(market)

    @only_implemented_types
    def get_precision(self, market: str, params: (dict, NoneType) = None) -> tuple[float, float]:
        """
        Get the precision of a market and the minimal size
        :param market: example "ETH/USD"
        :param params: additional parameters
        :return: (market precision, minimal size)
        """
        if params is None:
            params = {}
        market = self.get_market(market)
        return float(market["precision"]["amount"]), float(market["limits"]["amount"]["min"])

    # Private API

    @only_authenticated
    @load_markets
    @only_implemented_types
    def get_free_balance(self, token: str, params: (dict, NoneType) = None) -> float:
        """
        # Return available balance of an asset
        :param token: example: 'BTC'
        :param params: additional parameters
        :return: available balance
        """
        if params is None:
            params = {}
        balances = self.client.fetch_balance(params=params)
        balance = balances.get(token, {})
        free = balance.get('free', 0)
        return float(free)

    @only_authenticated
    @load_markets
    @only_implemented_types
    def get_balance(self, token: str, params: (dict, NoneType) = None) -> float:
        """
        # Return total balance of an asset
        :param token: example: 'BTC'
        :param params: additional parameters
        :return: total balance
        """
        if params is None:
            params = {}
        balances = self.client.fetch_balance(params=params)
        balance = balances.get(token, {})
        free = balance.get('total', 0)
        return float(free)

    @only_authenticated
    @only_implemented_types
    def get_order(self, order_id: str, market: str, params: (dict, NoneType) = None) -> dict:
        """
        Get an order as a dict
        :param order_id: order id
        :param market: market example "ETH/USD"
        :param params: additional parameters
        :return: the order
        """
        if params is None:
            params = {}
        return self.client.fetch_order(order_id, market, params=params)

    @only_authenticated
    @only_implemented_types
    def get_all_orders(self, market: str, params: (dict, NoneType) = None) -> list:
        """
        Return all orders of a specific market or not
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: orders
        """
        if params is None:
            params = {}
        return self.client.fetch_orders(symbol=market, params=params)

    @only_authenticated
    @only_implemented_types
    def get_all_open_orders(self, market: str, params: (dict, NoneType) = None) -> list:
        """
        Return all open orders of a specific market or not
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: orders
        """
        if params is None:
            params = {}
        return self.client.fetch_open_orders(symbol=market, params=params)

    @only_authenticated
    @only_implemented_types
    def cancel_order_by_id(self, order_id: str, market: str, params: (dict, NoneType) = None) -> dict:
        """
        Cancel an order by giving his id
        :param order_id: order id as a string
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: the order
        """

        if params is None:
            params = {}
        return self.client.cancel_order(order_id, market, params=params)

    @only_authenticated
    @only_implemented_types
    def cancel_order_by_object(self, order: dict, market: str, params: (dict, NoneType) = None) -> dict:
        """
        Cancel an order by giving the dict returned by get_order() or any methods used to post an order
        :param order: order as a dict
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: the order
        """

        if params is None:
            params = {}
        return self.client.cancel_order(order["info"]["id"], market, params=params)

    @only_authenticated
    @only_implemented_types
    def get_order_status_by_id(self, order_id: str, market: str, params: (dict, NoneType) = None) -> str:
        """
        Get the status of an order by giving his id
        :param order_id: order id as a string
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: the status
        """

        if params is None:
            params = {}
        order = self.get_order(order_id, market, params=params)

        return order["info"]["status"]

    @only_authenticated
    @only_implemented_types
    def get_order_status_by_object(self, order: dict) -> str:
        """
        Get the status of an order by giving the dict returned by get_order() or any methods used to post an order
        :param order: order as a dict
        :return: the status
        """

        return order["info"]["status"]

    @only_authenticated
    @only_implemented_types
    def get_order_size(self, market: str, side: str, size_type: str, size: (float, int), price: (float, int, NoneType)
    = None, params: (dict, NoneType) = None) -> float:
        """
        This method is used to properly get the value to fill the size parameter to post an order
        :param market: example "BTC/USD"
        :param side: "buy" or "sell"
        :param size_type:
        - currency_1_amount: size is in currency 1, for the market "BTC/USD", you have to fill the size with the amount
        in BTC you want to buy/sell
        - currency_2_amount: size is in currency 2, for the market "BTC/USD", you have to fill the size with the amount
        in USD you want to buy/sell
        - currency_1_percent: size in percent of your available balance, for the market "BTC/USD", if you have 1 BTC and
         you want to sell 0.5 BTC for example, you will have to fill size parameter with 50 (50% of your 1 BTC)
        - currency_2_percent: size in percent of your available balance, for the market "BTC/USD", if you have 6 USD and
         you want to buy for 3 USD for example, you will have to fill size parameter with 50 (50% of your 6 USD)
        :param size: the value you have to fill depend on the size_type
        :param price: If you don't fill this parameter, the method will get the market price.
        :param params: additional parameters
        :return: the size of your order
        """

        if params is None:
            params = {}
        currency_1_name, currency_2_name = market.split("/")

        # Getting the price
        if price is None:
            if side == "buy":
                price = self.client.fetch_ticker(market)["bid"]
            else:
                price = self.client.fetch_ticker(market)["ask"]

        # Parsing size_type & size
        if size_type == "currency_2_amount":
            size = size / price
        elif size_type == "currency_2_percent":
            balance = self.get_free_balance(currency_2_name, params=params)  # Getting the balance
            size = size / 100 * balance
            size = size / price
        elif size_type == "currency_1_percent":
            balance = self.get_free_balance(currency_1_name, params=params)  # Getting the balance
            size = size / 100 * balance
        elif size_type == "currency_1_amount":
            pass  # Nothing to do

        size = float(size)

        # Parsing size with market minimum order size
        precision, minimum = self.get_precision(market)
        # precision of the market ( number of digits after the decimal point)
        digits = int(math.sqrt((int(math.log10(precision)) + 1) ** 2)) + 1
        # Apply the precision
        size = truncate(size, digits)
        # Apply the minimum
        if size < minimum:
            return 0

        return size

    @only_authenticated
    @only_implemented_types
    def post_market_order(self, market: str, side: str, size: (float, int), params: (dict, NoneType) = None) -> dict:
        """
        Post a market order
        :param market: example "BTC/USD"
        :param side: "buy" or "sell"
        :param size: the size of the order
        :param params: additional parameters
        :return: the order as a dict
        """

        if params is None:
            params = {}
        if size <= 0:
            return {}

        return self.client.create_order(symbol=market, type="market", side=side, amount=size, params=params)

    @only_authenticated
    @only_implemented_types
    def post_limit_order(self, market: str, side: str, size: (float, int), price: (float, int),
                         params: (dict, NoneType) = None) -> dict:
        """
        Post a limit order
        :param market: example "BTC/USD"
        :param side: "buy" or "sell"
        :param size: the size of the order
        :param price: trigger price of the order
        :param params: additional parameters
        :return: the order as a dict
        """

        if params is None:
            params = {}
        if size <= 0:
            return {}

        return self.client.create_order(symbol=market, type="limit", side=side, amount=size, price=price,
                                          params=params)

    @only_authenticated
    @only_implemented_types
    def post_stop_loss_order(self, market: str, side: str, size: (float, int), price: (float, int),
                             params: (dict, NoneType) = None) -> dict:
        """
        Post a stop order
        :param market: example "BTC/USD"
        :param side: "buy" or "sell"
        :param size: the size of the order
        :param price: trigger price of the order
        :param params: additional parameters
        :return: the order as a dict
        """

        if params is None:
            params = {}
        if size <= 0:
            return {}

        params.update({"stopPrice": price})

        return self.client.create_order(symbol=market, type="stop", side=side, amount=size, price=price,
                                          params=params)

    @only_authenticated
    @only_implemented_types
    def post_take_profit_order(self, market: str, side: str, size: (float, int), price: (float, int),
                               params: (dict, NoneType) = None) -> dict:
        """
        Post a tp order
        :param market: example "BTC/USD"
        :param side: "buy" or "sell"
        :param size: the size of the order
        :param price: trigger price of the order
        :param params: additional parameters
        :return: the order as a dict
        """

        if params is None:
            params = {}
        if size <= 0:
            return {}

        params.update({"triggerPrice": price})

        return self.client.create_order(symbol=market, type='takeProfit', side=side, amount=size,
                                          params=params)


'''
Exchanges
'''


class WrappedFtxClient(WrappedGenericExchange):

    def __init__(self, api_key: (str, NoneType) = None, api_secret: (str, NoneType) = None,
                 enable_rate_limit: bool = True, subaccount_name: (str, NoneType) = None):
        """
        Instantiate ftx ccxt client
        :param api_key: api key in your cex settings
        :param api_secret: api secret in your cex settings
        :param enable_rate_limit: True to activate the control of the ratelimit
        :param subaccount_name: the name of the subaccount you want to use
        """
        super().__init__(ccxt.ftx)
        self.instantiate_client(api_key, api_secret, enable_rate_limit, subaccount_name)

    # Override
    @only_implemented_types
    def instantiate_client(self, api_key: (str, NoneType) = None, api_secret: (str, NoneType) = None,
                           enable_rate_limit: bool = True, subaccount_name: (str, NoneType) = None):
        """
        Instantiate ccxt client
        :param api_key: api key in your cex settings
        :param api_secret: api secret in your cex settings
        :param enable_rate_limit: True to activate the control of the ratelimit
        :param subaccount_name: the name of the subaccount you want to use
        """

        if api_key is not None and api_secret is not None:
            self.client = self.exchange({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': enable_rate_limit,
                'headers': {'FTX-SUBACCOUNT': subaccount_name}
            })
            self.client_state = Client_state.AUTHENTICATED
        else:
            self.client = self.exchange({
                'enableRateLimit': enable_rate_limit
            })
            self.client_state = Client_state.NOT_AUTHENTICATED

    # Override
    @only_authenticated
    @only_implemented_types
    def get_order(self, order_id: str, market: str, params: (dict, NoneType) = None) -> dict:
        """
        Get an order as a dict
        :param order_id: order id
        :param market: market example "ETH/USD"
        :param params: additional parameters
        :return: the order
        """
        if params is None:
            params = {}
        params.update({'method': 'privateGetOrdersOrderId'})
        return self.client.fetch_order(order_id, market, params=params)

    # Override
    @only_authenticated
    @only_implemented_types
    def cancel_order_by_id(self, order_id: str, market: str, params: (dict, NoneType) = None) -> dict:
        """
        Cancel an order by giving his id
        :param order_id: order id as a string
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: the order
        """
        if params is None:
            params = {}
        order = self.get_order(order_id, market)
        order_type = order['info']['type']
        if order_type == "stop" or order_type == "take_profit":
            params.update({'method': 'privateDeleteConditionalOrdersOrderId'})
        else:
            params.update({'method': 'privateDeleteOrdersOrderId'})

        return self.client.cancel_order(order_id, market, params=params)

    # Override
    @only_authenticated
    @only_implemented_types
    def cancel_order_by_object(self, order: dict, market: str, params: (dict, NoneType) = None) -> dict:
        """
        Cancel an order by giving the dict returned by get_order() or any methods used to post an order
        :param order: order as a dict
        :param market: example "BTC/USD"
        :param params: additional parameters
        :return: the order
        """
        if params is None:
            params = {}
        order_type = order['info']['type']
        if order_type == "stop" or order_type == "take_profit":
            params.update({'method': 'privateDeleteConditionalOrdersOrderId'})
        else:
            params.update({'method': 'privateDeleteOrdersOrderId'})

        return self.client.cancel_order(order["info"]["id"], market, params=params)
    

class WrappedBinanceClient(WrappedGenericExchange):

    def __init__(self, api_key: (str, NoneType) = None, api_secret: (str, NoneType) = None,
                 enable_rate_limit: bool = True, testnet: bool = False):
        """
        Instantiate ftx ccxt client
        :param api_key: api key in your cex settings
        :param api_secret: api secret in your cex settings
        :param enable_rate_limit: True to activate the control of the ratelimit
        :param testnet: True to use the testnet
        """
        super().__init__(ccxt.binance)
        self.instantiate_client(api_key, api_secret, enable_rate_limit)
        if testnet:
            self.client.set_sandbox_mode(True)
