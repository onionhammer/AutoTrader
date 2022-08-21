from autotrader.brokers.trading import Order, Position, Trade
from autotrader.brokers.broker_utils import BrokerUtils
import alpaca_trade_api as api
import numpy as np
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
        return float(account.cash) # or equity or buying_power?
        
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order.
        """
        # Call order to set order time
        order()
        
        # Submit order to broker
        if order.order_type == 'market':
            self._place_market_order(order)
        elif order.order_type == 'stop-limit':
            self._place_stop_limit_order(order)
        elif order.order_type == 'limit':
            self._place_limit_order(order)
        elif order.order_type == 'close':
            self._close_position(order)
        else:
            print("Order type not recognised.")
    
    
    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.
        """
        alpaca_orders = self.alpaca.list_orders(
            status='open',
            limit=500,
            symbols=[instrument] if instrument is not None else None
        )

        orders = {}

        for order in alpaca_orders:
            new_order = {
                'id': order.id,
                'status': 'open',
                'order_type': order.type,
                'order_stop_price': order.stop_price,
                'order_limit_price': order.limit_price,
                'direction': 1 if order.side == 'buy' else -1,
                'order_time': order.created_at,
                'instrument': order.symbol,
                'size': order.qty,
                'order_price': None,
                'take_profit': None,
                'take_distance': None,
                'stop_type': None,
                'stop_distance': None,
                'stop_loss': None,
                'related_orders': None,
                'granularity': None,
                'strategy': None,
            }

            orders[order.id] = Order._from_dict(new_order)
            pass

        return orders
    
    
    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels pending order by order ID.
        
        Parameters
        ----------
        order_id : int
            The ID of the order to be concelled.

        Returns
        -------
        list
            A list of the cancelled trades.

        """
        self.alpaca.cancel_order(order_id)
        pass
    
    
    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account. 
        """
        open_trades = {}

        alpaca_trades = self.alpaca.list_orders(
            status='closed',
            limit=500,
            symbols=[instrument] if instrument is not None else None
        )

        for trade in alpaca_trades:
            if trade.status == 'filled':
                new_trade = {
                    'instrument': trade.symbol,
                    'time_filled': trade.filled_at,
                    'fill_price': trade.filled_avg_price,
                    'size': trade.filled_qty,
                    'id': trade.id,
                    'direction': 1 if trade.side == 'buy' else -1,
                    'status': trade.status,
                    'unrealized_PL': trade.unrealized_pl,
                    'order_stop_price': trade.stop_price,
                    'order_limit_price': trade.limit_price,
                }

                open_trades[trade.id] = Trade(new_trade)
        
        return open_trades
    
    
    def get_trade_details(self, trade_ID: str) -> dict:
        """Returns the details of the trade specified by trade_ID.
        WARNING: Deprecated, not implemented
        """
        raise NotImplementedError("Not implemented")
        # order = self.alpaca.get_order(trade_ID)

        # details = {
        #     'id': order.id,
        # }

        # return Trade(details)
    
    
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
        open_positions = {}

        def map_position(position):
            # trade_IDs = []
            side = 'long' if position.side == 'long' else 'short'
            qty = np.sign(position.qty)
            pl = np.sign(position.unrealized_pl)
            pos = {
                'instrument': position.symbol,
                'long_units': qty if side == 'long' else 0,
                'long_PL': pl if side == 'long' else 0,
                'long_margin': None,
                'short_units': qty if side == 'short' else 0,
                'short_PL': pl if side == 'short' else 0,
                # 'short_margin': None,
                # 'total_margin': position.marginUsed,
                # 'trade_IDs': trade_IDs 
            }

            return Position(**pos)

        if instrument is None:
            # Iterate through allPositions and call map_position on each position
            allPositions = self.alpaca.get_positions()
            for pos in allPositions:
                open_positions[pos.symbol] = map_position(pos)
        else:
            pos = self.alpaca.get_position(symbol=instrument)
            open_positions[pos.symbol] = map_position(pos)

        return open_positions
    
    
    # Define here any private methods to support the public methods above
    def _get_precision(self, instrument: str):
        asset = self.alpaca.get_asset(instrument)

        if asset.fractionable:
            min_trade_increment = decimal.Decimal(asset.min_trade_increment)
            decimals = abs(int(min_trade_increment.as_tuple().exponent))
            return decimals
        else:
            return 0

    def _check_precision(self, instrument, price):
        """Modify a price based on required ordering precision for pair.
        """
        N = self._get_precision(instrument)
        corrected_price = round(price, N)
        return corrected_price


    def check_trade_size(self, instrument: str, units: float) -> float:
        """Checks the requested trade size against the minimum trade size 
        allowed for the currency pair.
        """
        precision = self._get_precision(instrument)

        return round(units, precision)
    
    
    def _place_market_order(self, order: Order):
        """Places a market order.
        """
        size = self.check_trade_size(order.instrument, 
                                     order.size)

        self.alpaca.submit_order(
            symbol=order.instrument,
            qty=order.direction * size,
            side='buy' if order.direction > 0 else 'sell',
            type='trailing_stop',
            time_in_force='gtc',
        )
        pass

    def _place_stop_limit_order(self, order: Order):
        """Places stop-limit order.
        """
        size = self.check_trade_size(order.instrument, 
                                     order.size)

        # Create stop limit order
        self.alpaca.submit_order(
            symbol=order.instrument,
            qty=order.direction * size,
            side='buy' if order.direction > 0 else 'sell',
            type='stop_limit',
            time_in_force='gtc',
            limit_price=order.order_limit_price,
            stop_price=order.order_stop_price,
        )
        pass

    def _place_limit_order(self, order: Order):
        """Places limit order.
        """
        size = self.check_trade_size(order.instrument, 
                                     order.size)

        # Create limit order
        self.alpaca.submit_order(
            symbol=order.instrument,
            qty=order.direction * size,
            side='buy' if order.direction > 0 else 'sell',
            type='limit',
            time_in_force='gtc',
            limit_price=order.order_limit_price,
        )
        pass

    def _close_position(self, order: Order):
        """Closes all open positions on an instrument.
        """
        self.alpaca.close_position(symbol=order.instrument)
        pass