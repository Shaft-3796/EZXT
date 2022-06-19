import ccxt

import ezxt2
from ezxt2 import Colors
"""
This module contains a set of unit tests functions for ezxt2.py
"""


class UnitTest:
    """
    Used to run unit tests
    """
    def __init__(self, wrapped_client, market: str = "BTC/USDT"):
        """
        Initialize the unit test class
        :param wrapped_client: Your wrapped client, instantiated, authenticated or not, inherited of
        ezxt2.WrappedGenericExchange
        :param market: The market used for the unit tests
        """
        self.wrapped_client = wrapped_client
        self.market = market

    def public_test(self):
        """
        Run public endpoints tests
        """
        print(f"{Colors.PURPLE}| Unit tests for public endpoints |")
        print(f"{Colors.LIGHT_PURPLE}-> {self.wrapped_client.exchange.__name__}")

        print("\n")

        # bid & ask
        bid = self.wrapped_client.get_bid(self.market)
        ask = self.wrapped_client.get_ask(self.market)
        print(f"{Colors.GREEN}-> bid/ask test passed: {bid}/{ask}")

        # kline
        kline = self.wrapped_client.get_kline(self.market, "1d", 1000)
        print(f"{Colors.GREEN}-> kline test passed: {kline}")

        # market
        market = self.wrapped_client.get_market(self.market)
        print(f"{Colors.GREEN}-> market test passed: {market}")

        # precision
        precision = self.wrapped_client.get_precision(self.market)
        print(f"{Colors.GREEN}-> precision test passed: {precision}")

        print("\n")

        print(f"{Colors.PURPLE}Unit tests for public endpoints  passed")
        print(f"{Colors.LIGHT_PURPLE}-> {self.wrapped_client.exchange.__name__}")


ut = UnitTest(ezxt2.WrappedBinanceClient())
ut.public_test()




