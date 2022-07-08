import time
import ezxt2
from ezxt2 import Colors

"""
This module contains a set of unit tests functions for ezxt2.py
"""


class UnitTest:
    """
    Used to run unit tests
    """

    def __init__(self, wrapped_client, market: str = "BTC/USDT", stable="USDT"):
        """
        Initialize the unit test class
        :param wrapped_client: Your wrapped client, instantiated, authenticated or not, inherited of
        ezxt2.WrappedGenericExchange
        :param market: The market used for the unit tests
        :param stable: Stablecoin or token to get the balance of
        """
        self.wrapped_client = wrapped_client
        self.market = market
        self.stable = stable

    def public_test(self):
        """
        Run public endpoints tests
        """
        print(f"{Colors.PURPLE}| Unit tests for public endpoints on {self.wrapped_client.exchange.__name__} |")

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
        print(f"{Colors.GREEN}✅ bid/ask")
        print(f"{Colors.GREEN}✅ kline")
        print(f"{Colors.GREEN}✅ market")
        print(f"{Colors.GREEN}✅ precision")

    def private_test(self):
        """
        Run private endpoints tests
        """
        print(f"{Colors.PURPLE}| Unit tests for private endpoints {self.wrapped_client.exchange.__name__} |")

        print("\n")

        # balance
        balance = self.wrapped_client.get_balance(self.stable)
        print(f"{Colors.GREEN}-> balance test passed: {balance}")
        free_balance = self.wrapped_client.get_free_balance(self.stable)
        print(f"{Colors.GREEN}-> free balance test passed: {free_balance}")

        # Orders
        buy_price = self.wrapped_client.get_bid(self.market) * 0.1
        buy_price_sl = self.wrapped_client.get_bid(self.market) * 10
        size = self.wrapped_client.get_order_size(self.market, "buy", "currency_2_percent", 100, buy_price)
        order = self.wrapped_client.post_limit_order(self.market, "buy", size, buy_price)
        print(f"{Colors.GREEN}-> limit order test passed: {order}")

        orders = self.wrapped_client.get_all_open_orders(market=self.market)
        print(f"{Colors.GREEN}-> get order test passed: {orders}")

        status = self.wrapped_client.get_order_status_by_object(order)
        print(f"{Colors.GREEN}-> get order status test passed: {status}")

        time.sleep(5)

        self.wrapped_client.cancel_order_by_object(order, self.market)
        print(f"{Colors.GREEN}-> cancel order test passed")

        order = self.wrapped_client.post_take_profit_order(self.market, "buy", size, buy_price)
        print(f"{Colors.GREEN}-> take profit order test passed: {order}")
        self.wrapped_client.cancel_order_by_object(order, self.market)

        order = self.wrapped_client.post_stop_loss_order(self.market, "buy", size, buy_price_sl)
        print(f"{Colors.GREEN}-> stop loss order test passed: {order}")
        self.wrapped_client.cancel_order_by_object(order, self.market)

        print(f"{Colors.PURPLE}Unit tests for private endpoints passed")
        print(f"{Colors.GREEN}✅ balance")
        print(f"{Colors.GREEN}✅ free balance")
        print(f"{Colors.GREEN}✅ limit orders")
        print(f"{Colors.GREEN}✅ take profit orders")
        print(f"{Colors.GREEN}✅ stop loss orders")
        print(f"{Colors.GREEN}✅ get orders")
        print(f"{Colors.GREEN}✅ cancel orders")


ut = UnitTest(ezxt2.WrappedBinanceClient(), market="BTC/USDT")
ut.public_test()
