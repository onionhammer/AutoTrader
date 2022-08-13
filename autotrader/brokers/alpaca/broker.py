from autotrader.brokers.trading import Order
from autotrader.brokers.broker_utils import BrokerUtils
import alpaca_trade_api as api
import decimal

"""
Notes:
    - Public methods are called from outside the broker module, and so must
      retain functionality of input arguments. If necessary, they can simply
      be wrapper methods.
    - Private methods are broker-specific.
"""

class Broker:
    def __init__(self, alpaca_config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor.
        """
        self.ENDPOINT = alpaca_config["ENDPOINT"]
        self.API_KEY = alpaca_config["API_KEY"]
        self.SECRET_KEY = alpaca_config["SECRET_KEY"]
        
        # Initialize Alpaca API
        self.alpaca = api.REST(self.API_KEY, self.SECRET_KEY, self.ENDPOINT)

        self.utils = utils if utils is not None else BrokerUtils()
        
        # Unpack config and connect to broker-side API
        
    
    def __repr__(self):
        return 'AutoTrader-Alpaca Broker interface'
    
    
    def __str__(self):
        return 'AutoTrader-Alpaca Broker interface'
    
    
    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account.
        """
        account = self.alpaca.get_account()
        return float(account.portfolio_value)
    
    
    def get_balance(self) -> float:
        """Returns account balance.
        """
        account = self.alpaca.get_account()
        return float(account.equity) # or cash or buying_power?
        
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order.
        """
        # Call order to set order time
        order()
        
        # Submit order to broker
        if order.order_type == 'market':
            self._place_market_order(order)
        # TODO
        # elif order.order_type == 'stop-limit':
        #     self._place_stop_limit_order(order)
        # elif order.order_type == 'limit':
        #     self._place_limit_order(order)
        # elif order.order_type == 'close':
        #     self._close_position(order)
        else:
            print("Order type not recognised.")
    
    
    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.
        """
        pass
    
    
    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels order by order ID.
        """
        pass
    
    
    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account. 
        """
        pass
    
    
    def get_trade_details(self, trade_ID: str) -> dict:
        """Returns the details of the trade specified by trade_ID.
        """
        pass
    
    
    def get_positions(self, instrument: str = None, **kwargs) -> dict:
        """Gets the current positions open on the account.
        
        Parameters
        ----------
        instrument : str, optional
            The trading instrument name (symbol). The default is None.
            
        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        pass
    
    
    # Define here any private methods to support the public methods above
    
    def check_trade_size(self, instrument: str, units: float) -> float:
        """Checks the requested trade size against the minimum trade size 
        allowed for the currency pair.
        """
        asset = self.alpaca.get_asset(instrument)

        if asset.fractionable:
            min_trade_increment = decimal.Decimal(asset.min_trade_increment)
            decimals = abs(int(min_trade_increment.as_tuple().exponent))
            return round(units, decimals)
        else:
            return round(units, 0)
    
    
    def _place_market_order(self, order: Order):
        # Check position size
        size = self.check_trade_size(order.instrument, 
                                     order.size)

        self.alpaca.submit_order(
            symbol=order.instrument,
            qty=order.direction * size,
            side='buy',
            type='trailing_stop',
            time_in_force='day',
        )
        pass