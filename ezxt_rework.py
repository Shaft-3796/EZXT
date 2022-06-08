import functools
import math
import pandas as pd
import ccxt

'''
Utility class
'''


# Representing different state for the client (used by wrapped_exchange)
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


'''
Core
'''


# Template class representing a wrapped exchange
class Wrapped_exchange:

    def __init__(self, exchange):
        """
        Template class representing a wrapped exchange
        :param exchange: a ccxt exchange ( a class not an object ), ccxt.ftx for example.
        """
        self.exchange = exchange  # Look at the method docstring
        self.client = None  # Store the instanced client
        self.client_state = Client_state.NOT_INSTANTIATED  # Store the client state

    # Overrideable
    def instantiate_client(self, api_key: str = None, api_secret: str = None, enable_rate_limit: bool = True):
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
    def get_bid(self, market: str, params: dict = {}) -> int:
        """
        Return bid price of a market
        :param market: Example: "BTC/USD"
        :param params: Additional parameters
        :return:
        """
        return int(self.client.fetch_ticker(market, params=params)["bid"])

    @load_markets
    def get_ask(self, market: str, params: dict = {}) -> int:
        """
        Return ask price of a market
        :param market: Example: "BTC/USD"
        :param params: Additional parameters
        :return:
        """
        return int(self.client.fetch_ticker(market, params=params)["ask"])

    def get_klines(self, market: str, timeframe: str, limit: int, params: dict = {}) -> pd.DataFrame:
        """
        Download klines for a market
        :param market: example "ETH/USD"
        :param timeframe: usually '1y', '1m', '1d', '1w', '1h', '15M'
        :param limit:
        :param params:
        :return:
        """
        klines = self.exchange.fetch_ohlcv(market, timeframe, limit=limit)
        dataframe = pd.DataFrame(klines)
        dataframe.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close'}, inplace=True)
        dataframe.pop(5)
        dataframe.drop(index=dataframe.index[-1], axis=0, inplace=True)
        return dataframe

