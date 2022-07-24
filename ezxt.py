import functools
import math
import os
import threading
import time
from datetime import datetime
from types import NoneType

import pandas as pd
import ccxt

'''
Utility
'''


# Representing different state for the client (used by WrappedGenericExchange)
class ClientState:
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


# List of exchanges with a custom EZXT class
customs = {'binance': 'WrappedBinanceExchange',
           'ftx': 'WrappedFtxExchange'}

'''
decorators & utility functions
'''


# Print a progress bar
def progress_bar(curent: (int, float), total: (int, float), bar_length: int = 100, front: str = ""):
    """
    Prints a progress bar.
    :param curent: Current value.
    :param total: Number of total values.
    :param bar_length: Length of the progress bar.
    :param front: Text to be printed before the progress bar.
    """

    progress = round(curent / total * 100, 2)
    filled = round((progress / 100 * bar_length)) * "█"
    unfilled = round((bar_length - progress / 100 * bar_length)) * "░"

    print(f"\r{front}{Colors.GREEN}[{filled + unfilled}] {Colors.YELLOW}{progress}% [{curent}/{total}]", end="")
    if progress >= 100:
        print("")


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
        if instance.ClientState == ClientState.NOT_AUTHENTICATED:
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


class WrongSizeType(BaseException):
    """
    Exception to be raised when a not implemented type is given to a function
    """

    def __init__(self, size_type):
        """
        Constructor
        :param parameter_name: name of the parameter involved in the exception
        :param required_type:
        """
        super().__init__(
            f"{Colors.ERROR}WrongSizeType exception '{size_type}' is not a valid size type, please refers "
            f"to the documentation at WrappedGenericExchange.get_order_size()")


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
        # check if there is a custom class for the exchange
        name = exchange.__name__.lower()
        if name in customs and self.__class__.__name__ == WrappedGenericExchange.__name__:
            print(f"{Colors.YELLOW} Warning {name} has a custom class provided by EZXT, please use {customs[name]} "
                  f"class instead of WrappedGenericExchange if you don't want to encouter some unexpected issues")

        self.exchange = exchange  # Look at the method docstring
        self.client = exchange({'enableRateLimit': True})  # Store the instanced client
        self.ClientState = ClientState.NOT_AUTHENTICATED  # Store the client state

    # Overrideable
    @only_implemented_types
    def authenticate_client(self, api_key: str, api_secret: str,
                            enable_rate_limit: bool = True):
        """
        Instantiate ccxt client
        :param api_key: api key in your cex settings
        :param api_secret: api secret in your cex settings
        :param enable_rate_limit: True to activate the control of the ratelimit
        """

        self.client = self.exchange({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': enable_rate_limit
        })
        self.ClientState = ClientState.AUTHENTICATED

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
    def get_kline(self, market: str, timeframe: str, since: (str, int, NoneType), limit: (int, NoneType),
                  params: (dict, NoneType) = None) -> pd.DataFrame:
        """
        Download kline for a market
        :param market: example "ETH/USD"
        :param timeframe: usually '1y', '1m', '1d', '1w', '1h'...
        :param since: first candle to download timestamp
        :param limit: number of candles
        :param params: additional parameters
        :return: pandas dataframe
        """
        if params is None:
            params = {}
        kline = self.client.fetch_ohlcv(market, timeframe, since=since, limit=limit, params=params)
        dataframe = pd.DataFrame(kline)
        if dataframe.empty:
            return dataframe
        dataframe.rename(columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'},
                         inplace=True)
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

    # Public API - Multithreading dl & ohlcv file saving
    # Do not use __download__ & __load__ use load_ohlcv instead
    def __download__(self, market: str, timeframe: str, since: (str, int, NoneType), limit: (int, NoneType),
                     output: bool, download_size: int):
        """
        Please do not use this method directly use load_ohlcv instead
        """

        # Sub functions

        def dl(_since, _limit, _request_id, response_dict):
            nonlocal rate_limit_reached
            while True:
                try:
                    response = self.get_kline(market, timeframe, int(_since), _limit)
                    break
                except Exception:
                    rate_limit_reached = True
                    while rate_limit_reached:
                        pass
                    time.sleep(1)

            response_dict[_request_id] = response
            return response_dict

        def rate_limit_handler():
            nonlocal rate_limit_reached, finished
            remaining = 60
            while True:
                if rate_limit_reached:
                    while remaining > 0:
                        # at least one thread turned this parameter on True so we wait 61s
                        progress_bar(request_id, total_length, front=f" rate limit reached waiting for [{remaining}s]") \
                            if output else None
                        time.sleep(1)
                        remaining -= 1
                    remaining = 60
                    rate_limit_reached = False
                time.sleep(1)
                if finished:
                    break
            finished = False

        # Ini
        remainging_candles = limit
        finished = False  # used to stop rate limit thread

        # Part 1 - first set of candles
        dataframe = self.get_kline(market, timeframe, since=since, limit=limit)
        size = len(dataframe)
        if size == 0:
            return dataframe
        remainging_candles -= size
        if remainging_candles <= 0 or len(dataframe) < 2:
            return dataframe

        # Part 2 - requests making
        t0 = dataframe.iloc[0]["timestamp"]  # First timestamp
        t1 = dataframe.iloc[1]["timestamp"]  # Second timestamp
        tx = dataframe.iloc[-1]["timestamp"]  # Last timestamp
        offset = t1 - t0  # time between two df rows
        full_offset = tx - t0  # time between first & last df rows
        requests = []
        last_timestamp = tx  # For the loop
        while remainging_candles > 0:
            last_timestamp += offset
            if last_timestamp > time.time() * 1000:
                remainging_candles = 0
                break
            requests.append((last_timestamp, remainging_candles))
            remainging_candles -= size
            last_timestamp += full_offset
        if len(requests) == 0:
            return dataframe

        # Part 3 - requests sending
        temp_responses = {}
        responses = {}
        responses_expected_length = len(requests)
        total_length = responses_expected_length  # total length of the responses list
        rate_limit_reached = False  # for rate_limit_handler()
        if responses_expected_length > download_size:
            responses_expected_length = download_size

        # Starting rate limit handler thread
        threading.Thread(target=rate_limit_handler).start()

        request_id = 0
        print(f"{Colors.YELLOW}[DataManager] Multithreading Download" if output else None)
        progress_bar(0, total_length)
        scheduled = 0
        for timestamp, limit in requests:
            threading.Thread(target=dl,
                             args=(timestamp, limit, request_id, temp_responses)).start()  # we schedule the request
            request_id += 1  # we increment the request id
            scheduled += 1  # we increment requests amount

            if scheduled == responses_expected_length:  # we wait for the responses
                while not len(temp_responses) == responses_expected_length:
                    pass
                responses.update(temp_responses)  # we merge new responses with the old ones
                temp_responses = {}  # we reset temporary responses
                scheduled = 0
                responses_expected_length = len(requests) - len(responses)  # expected length of the responses list
                if responses_expected_length > download_size:
                    responses_expected_length = download_size
                progress_bar(request_id, total_length) if output else None

        # Merging
        dataframes = [dataframe]
        for i in range(len(responses)):
            dataframes.append(responses[i])

        dataframe = pd.concat(dataframes, ignore_index=True)

        # We are here waiting for the rate limit thread to stop
        finished = True
        while finished:
            pass
        return dataframe

    def __get_file_name__(self, market: str, timeframe: str, since: int, limit: int):
        """
        Generate file name to save / load market data from file system
        :return:
        """
        filename = ""
        filename += market.replace("-", "").replace("/", "") + '_'  # market
        filename += timeframe + '_'  # timeframe
        filename += datetime.fromtimestamp(since / 1000).strftime("%d-%m-%y-%H-%M-%S") + '_'  # since
        filename += ("to_now" if limit == -1 else str(limit) + '_candles') + '.csv'  # limit

        return filename

    @only_implemented_types
    def load_ohlcv(self, market: str, timeframe: str, since: int, limit: int, output: bool = True,
                   download_size: int = 100, path: (str, NoneType) = "data/") -> pd.DataFrame:
        """
        Load ohlcv method work as the get_kline method with some more features:
        - you can very quickly download a lot of candles using multithreading with just one call
        - you can save your data as a csv file to be able to load it from a file when you need it to gain a lot of speed
        - you can pass -1 as the limit to update your data everytime you load it with the last candles,
        the method just download candles you don't have
        :param market: example "BTC/USD"
        :param timeframe: usually '1y', '1m', '1d', '1w', '1h'...
        :param since: first candle to download timestamp
        :param limit: number of candles you want to download, use -1 to download as many candles as possible and to
        update your dataframe with the last candles if you chose to save your data to the filesystem
        :param output: Display download and load informations, nottably the progress bar
        :param download_size: number of requests sheduled at the same time, increase this parameter may cause some
        issues ! Decrease this parameter will make the download slower but you can do it if you encounter some issues.
        :param path: None will disable the data saving to the file system and everytime you call this method,
        data will be downloaded. If you pass a path as a string to this parameter, data will be saved to this path as
        csv files and the method will check to this path if a file exists with data you want to load.
        :return: a pandas dataframe indexed from 0 to your number of candles minus one with these columns :
        timestamp open high low close volume
        """

        # mkdir if path doesn't exist
        if path is not None:
            if not os.path.exists(path):
                os.mkdir(path)

        def append(df):
            """
            This method update a dataframe with new candles
            """
            print(f"{Colors.PURPLE} EZXT is updating your data with new candles {Colors.END}")
            # time between 2 rows + last timestamp
            _since = int(df.iloc[1]["timestamp"] - df.iloc[0]["timestamp"] + df.iloc[-1]["timestamp"])
            _limit = int((time.time() * 1000 - _since) / 60000 + 100)
            _df = self.__download__(market, timeframe, _since, _limit, output=output, download_size=download_size)
            df = pd.concat([df, _df], ignore_index=True)
            return df

        # Check if user want to enable file system
        if path is None:
            # Case 1 - saving to file system disable
            if limit == -1:  # We download in this case as many candles as possible
                now = time.time() * 1000
                limit = int(
                    (now - since) / 60 + 100)  # We could have set here a super high number for the limit parameter
                # but we are doing it here in a cleaner way

            return self.__download__(market, timeframe, since, limit, output, download_size)

            pass
        else:
            # File system enabled, check if our data was already saved in a file
            filename = self.__get_file_name__(market, timeframe, since, limit)
            fullpath = path + filename
            if os.path.exists(fullpath):
                # Case 2 - File system enable, data was already downloaded, we load it
                dataframe = pd.read_csv(fullpath, index_col=0)
                # Check if we have to update the dataframe
                if limit == -1:
                    dataframe = append(dataframe)
                    # We save the new dataframe
                    dataframe.to_csv(path + filename)

                return dataframe
            else:
                # Case 3 - We download & save market data
                filename = self.__get_file_name__(market, timeframe, since, limit)
                if limit == -1:  # We download in this case as many candles as possible
                    limit = int((time.time() * 1000 - since) / 60000 + 100)
                dataframe = self.__download__(market, timeframe, since, limit, output, download_size)
                # We save the new dataframe
                dataframe.to_csv(path + filename)

                return dataframe

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
    @load_markets
    @only_implemented_types
    def get_total_account_value(self, params: (dict, NoneType) = None) -> float:
        """
        This method will return your total wallet value
        :param params: additional parameters
        :return: Your total wallet value as a float
        """
        return self.client.load_accounts()

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
        else:
            raise WrongSizeType

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

    def __init__(self):
        """
        Instantiate ftx ccxt client
        """
        super().__init__(ccxt.ftx)

    # Override
    @only_implemented_types
    def authenticate_client(self, api_key: str, api_secret: str,
                            enable_rate_limit: bool = True, subaccount_name: (str, NoneType) = None):
        """
        Instantiate ccxt client
        :param api_key: api key in your cex settings
        :param api_secret: api secret in your cex settings
        :param enable_rate_limit: True to activate the control of the ratelimit
        :param subaccount_name: the name of the subaccount you want to use
        """

        self.client = self.exchange({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': enable_rate_limit,
            'headers': {'FTX-SUBACCOUNT': subaccount_name}
        })
        self.ClientState = ClientState.AUTHENTICATED
        # Adding an implicit method to get account data
        self.client.define_rest_api({}, "private_get_account", ['/account'])

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

    # Private API - Contract trading ( future )

    @only_authenticated
    @only_implemented_types
    def get_position(self, market: str, parsing: bool = True, params: (dict, NoneType) = None) -> dict:
        """
        This method will return your position on a ftx future market
        :param market: ftx future market, example: "BTC-PERP"
        :param parsing: True if you want EZXT to parse FTX response
        :param params: additional parameters
        :return: if parsing is set to True return a dict with the following keys:
        market, size, side, entryPrice, estimatedLiquidationPrice, collateral
        """
        if params is None:
            params = {}

        response = self.client.fetch_positions([market], params=params)[0]

        if parsing:
            # Parsing if enable
            position = {'market': response['info']['future'],
                        'size': response['info']['size'],
                        'side': response['info']['side'],
                        'entryPrice': response['entryPrice'],
                        'estimatedLiquidationPrice': response['liquidationPrice'],
                        'collateral': response['collateral']}
            return position
        else:
            return response

    @only_authenticated
    @only_implemented_types
    def get_future_order_size(self, market: str, side: str, size_type: str, size: (float, int),
                              price: (float, int, NoneType)
                              = None, params: (dict, NoneType) = None) -> float:
        """
        This method is used to properly get the value to fill the size parameter to post an order on FTX future
        markets
        :param market: example "BTC-PERP"
        :param side: "buy" or "sell"
        :param size_type:
        - currency_1_amount:
        size is in currency 1, for the market "BTC-PERP", you have to fill the size with the amount in BTC you want
        to buy/sell
        - currency_2_amount: size is in currency 2, for the market "BTC-PERP", you have to fill the size
        with the amount in USD you want to buy/sell
        - currency_1_percent: size in percent of your available balance,
        for the market "BTC-PERP", if you have 1 BTC and you want to sell 0.5 BTC for example, you will have to fill
        size parameter with 50 (50% of your 1 BTC)
        - currency_2_percent: size in percent of your available balance,
        for the market "BTC-PERP", if you have 6 USD and you want to buy for 3 USD for example, you will have to fill
        size parameter with 50 (50% of your 6 USD)
        - leverage: size in leverage of your account (e.g 2 is two time your collateral )
        :param size: the value you have to fill depend on the size_type
        :param price: If you don't fill this parameter, the method will get the market price.
        :param params:
        additional parameters
        :return: the size of your order
        """

        if params is None:
            params = {}
        currency_1_name, currency_2_name = market.split("-")[0], "USD"

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
        elif size_type == "leverage":
            usd_size = self.get_total_collateral()
            price = self.get_bid(market)
            size = usd_size * size / price  # Here size represent the leverage
        else:
            raise WrongSizeType

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
    def close_future_position(self, market: str, limit_price: (int, float, NoneType) = None):
        """
        Completly close any open position in a future market
        :param market: future market, ( e.g "BTC-PERP" )
        :param limit_price: If you want to close your position with a limit order, fill this parameter with limit price
        """

        position = self.get_position(market)
        if limit_price is not None:
            self.post_limit_order(market, "buy" if position["side"] == "sell" else "sell", float(position['size']),
                                  limit_price, params={"reduceOnly": True})
        else:
            self.post_market_order(market, "buy" if position["side"] == "sell" else "sell", float(position['size']),
                                   params={"reduceOnly": True})

    # Private API - Stuff

    @only_authenticated
    @only_implemented_types
    def get_account_data(self) -> dict:
        """
        Recover some account informations
        :return: a dict with the following keys: AccountIdentifier, collateral, totalAccountValue
        """
        response = self.client.private_get_account()['result']
        data = {'accountIdentifier': response['accountIdentifier'],
                'collateral': response['collateral'],
                'totalAccountValue': response['totalAccountValue']}

        return data

    @only_authenticated
    @only_implemented_types
    def get_total_account_value(self) -> float:
        """
        Get total account value
        :return: total account value as a float
        """

        return float(self.get_account_data()['totalAccountValue'])

    @only_authenticated
    @only_implemented_types
    def get_total_collateral(self) -> float:
        """
        Get total account collateral
        :return: total account collateral as a float
        """

        return float(self.get_account_data()['collateral'])


class WrappedBinanceClient(WrappedGenericExchange):

    def __init__(self):
        """
        Instantiate ftx ccxt client
        """
        super().__init__(ccxt.binance)

    @only_authenticated
    def enable_testnet(self):
        """
        Enable the testnet
        :return:
        """
        self.client.set_sandbox_mode(True)
