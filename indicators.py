"""
Technical Indicators Module
Calculates technical indicators and generates trading signals
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging
from config import indicator_config, trading_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate all technical indicators with robust error handling"""
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average"""
        if column not in df.columns or df.empty or len(df) < period:
            return pd.Series(dtype=float, index=df.index)
        return df[column].rolling(window=period, min_periods=period).mean()
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        if column not in df.columns or df.empty or len(df) < period:
            return pd.Series(dtype=float, index=df.index)
        return df[column].ewm(span=period, adjust=False, min_periods=period).mean()
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        Returns values between 0-100
        """
        if column not in df.columns or df.empty or len(df) < period + 1:
            return pd.Series(dtype=float, index=df.index)
        
        delta = df[column].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        # Avoid division by zero
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # Neutral RSI for NaN values
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, 
                       signal: int = 9, column: str = 'close') -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if column not in df.columns or df.empty or len(df) < slow:
            empty = pd.Series(dtype=float, index=df.index)
            return {'macd': empty, 'signal': empty, 'histogram': empty}
        
        ema_fast = df[column].ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = df[column].ewm(span=slow, adjust=False, min_periods=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, 
                                   num_std: int = 2, column: str = 'close') -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        if column not in df.columns or df.empty or len(df) < period:
            empty = pd.Series(dtype=float, index=df.index)
            return {'upper': empty, 'middle': empty, 'lower': empty}
        
        sma = df[column].rolling(window=period, min_periods=period).mean()
        std = df[column].rolling(window=period, min_periods=period).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range (volatility measure)"""
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols) or df.empty or len(df) < period + 1:
            return pd.Series(dtype=float, index=df.index)
        
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        if 'close' not in df.columns or 'volume' not in df.columns or df.empty:
            return pd.Series(dtype=float, index=df.index)
        
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, 
                             d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols) or df.empty or len(df) < k_period:
            empty = pd.Series(dtype=float, index=df.index)
            return {'k': empty, 'd': empty}
        
        lowest_low = df['low'].rolling(window=k_period, min_periods=k_period).min()
        highest_high = df['high'].rolling(window=k_period, min_periods=k_period).max()
        
        # Avoid division by zero
        denominator = highest_high - lowest_low
        denominator = denominator.replace(0, np.nan)
        
        k_percent = 100 * ((df['close'] - lowest_low) / denominator)
        d_percent = k_percent.rolling(window=d_period, min_periods=d_period).mean()
        
        return {
            'k': k_percent.fillna(50),
            'd': d_percent.fillna(50)
        }
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (trend strength)"""
        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols) or df.empty or len(df) < period * 2:
            return pd.Series(dtype=float, index=df.index)
        
        # Calculate +DM and -DM
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        pos_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0.0)
        neg_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0.0)
        
        # Calculate ATR
        atr = TechnicalIndicators.calculate_atr(df, period)
        
        # Avoid division by zero
        atr_safe = atr.replace(0, np.nan)
        
        # Calculate directional indicators
        pos_di = 100 * (pos_dm.rolling(window=period, min_periods=period).mean() / atr_safe)
        neg_di = 100 * (neg_dm.rolling(window=period, min_periods=period).mean() / atr_safe)
        
        # Calculate DX and ADX
        di_sum = pos_di + neg_di
        di_sum = di_sum.replace(0, np.nan)
        
        dx = 100 * abs(pos_di - neg_di) / di_sum
        adx = dx.rolling(window=period, min_periods=period).mean()
        
        return adx.fillna(25)  # Neutral ADX for NaN
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame
        
        Args:
            df: Price DataFrame with OHLCV data
        
        Returns:
            DataFrame with all indicators added
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to add_all_indicators")
            return df
        
        df = df.copy()
        
        try:
            # Moving Averages
            df['sma_20'] = TechnicalIndicators.calculate_sma(df, indicator_config.SMA_SHORT)
            df['sma_50'] = TechnicalIndicators.calculate_sma(df, indicator_config.SMA_LONG)
            df['sma_200'] = TechnicalIndicators.calculate_sma(df, indicator_config.SMA_LONGER)
            df['ema_12'] = TechnicalIndicators.calculate_ema(df, indicator_config.EMA_FAST)
            df['ema_26'] = TechnicalIndicators.calculate_ema(df, indicator_config.EMA_SLOW)
            
            # RSI
            df['rsi'] = TechnicalIndicators.calculate_rsi(df, indicator_config.RSI_PERIOD)
            
            # MACD
            macd = TechnicalIndicators.calculate_macd(df)
            df['macd'] = macd['macd']
            df['macd_signal'] = macd['signal']
            df['macd_histogram'] = macd['histogram']
            
            # Bollinger Bands
            bb = TechnicalIndicators.calculate_bollinger_bands(df, indicator_config.BB_PERIOD)
            df['bb_upper'] = bb['upper']
            df['bb_middle'] = bb['middle']
            df['bb_lower'] = bb['lower']
            
            # Volatility
            df['atr'] = TechnicalIndicators.calculate_atr(df, indicator_config.ATR_PERIOD)
            
            # Volume indicators
            if 'volume' in df.columns:
                df['volume_sma'] = df['volume'].rolling(window=indicator_config.VOLUME_SMA, min_periods=indicator_config.VOLUME_SMA).mean()
                df['obv'] = TechnicalIndicators.calculate_obv(df)
            
            # Stochastic
            stoch = TechnicalIndicators.calculate_stochastic(df, indicator_config.STOCH_K_PERIOD, indicator_config.STOCH_D_PERIOD)
            df['stoch_k'] = stoch['k']
            df['stoch_d'] = stoch['d']
            
            # Trend strength
            df['adx'] = TechnicalIndicators.calculate_adx(df, indicator_config.ADX_PERIOD)
            
            logger.debug(f"Added all indicators, {len(df)} rows")
            
        except Exception as e:
            logger.error(f"Error adding indicators: {e}")
        
        return df


class SignalGenerator:
    """Generate trading signals from technical indicators"""
    
    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on multiple technical indicators
        
        Args:
            df: DataFrame with technical indicators
        
        Returns:
            DataFrame with signal columns added
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Initialize signal columns
        df['signal'] = 0  # 0 = neutral, 1 = buy, -1 = sell
        df['signal_strength'] = 0.0  # 0 to 1
        df['signal_reasons'] = ''
        
        # Individual indicator signals
        df['rsi_signal'] = 0
        df['macd_signal_ind'] = 0
        df['ma_signal'] = 0
        df['bb_signal'] = 0
        df['stoch_signal'] = 0
        df['volume_signal'] = 0
        
        # RSI signals (oversold = buy, overbought = sell)
        if 'rsi' in df.columns:
            df.loc[df['rsi'] < indicator_config.RSI_OVERSOLD, 'rsi_signal'] = 1
            df.loc[df['rsi'] > indicator_config.RSI_OVERBOUGHT, 'rsi_signal'] = -1
        
        # MACD crossover signals
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            # Bullish crossover
            df.loc[(df['macd'] > df['macd_signal']) & 
                   (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'macd_signal_ind'] = 1
            # Bearish crossover
            df.loc[(df['macd'] < df['macd_signal']) & 
                   (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'macd_signal_ind'] = -1
        
        # Moving average crossover (Golden Cross / Death Cross)
        if 'sma_20' in df.columns and 'sma_50' in df.columns:
            # Golden Cross: short MA crosses above long MA
            df.loc[(df['sma_20'] > df['sma_50']) & 
                   (df['sma_20'].shift(1) <= df['sma_50'].shift(1)), 'ma_signal'] = 1
            # Death Cross: short MA crosses below long MA
            df.loc[(df['sma_20'] < df['sma_50']) & 
                   (df['sma_20'].shift(1) >= df['sma_50'].shift(1)), 'ma_signal'] = -1
        
        # Bollinger Bands signals
        if all(col in df.columns for col in ['close', 'bb_upper', 'bb_lower']):
            df.loc[df['close'] < df['bb_lower'], 'bb_signal'] = 1  # Oversold
            df.loc[df['close'] > df['bb_upper'], 'bb_signal'] = -1  # Overbought
        
        # Stochastic signals
        if 'stoch_k' in df.columns:
            df.loc[df['stoch_k'] < 20, 'stoch_signal'] = 1  # Oversold
            df.loc[df['stoch_k'] > 80, 'stoch_signal'] = -1  # Overbought
        
        # Volume confirmation
        if 'volume' in df.columns and 'volume_sma' in df.columns:
            # High volume compared to average
            df.loc[df['volume'] > df['volume_sma'] * 1.5, 'volume_signal'] = 1
        
        # Combine signals with weights
        signal_sum = (
            df['rsi_signal'] * 1.0 +
            df['macd_signal_ind'] * 1.2 +
            df['ma_signal'] * 1.5 +
            df['bb_signal'] * 0.8 +
            df['stoch_signal'] * 0.8
        )
        
        # Apply volume confirmation (boost signal if high volume)
        signal_sum = signal_sum * (1 + df['volume_signal'] * 0.2)
        
        # Strong BUY: weighted sum >= 3.0
        buy_mask = signal_sum >= 3.0
        df.loc[buy_mask, 'signal'] = 1
        df.loc[buy_mask, 'signal_strength'] = (signal_sum[buy_mask] / 6.0).clip(0, 1)
        
        # Strong SELL: weighted sum <= -3.0
        sell_mask = signal_sum <= -3.0
        df.loc[sell_mask, 'signal'] = -1
        df.loc[sell_mask, 'signal_strength'] = (-signal_sum[sell_mask] / 6.0).clip(0, 1)
        
        # Generate reasons for signals
        for idx in df[df['signal'] != 0].index:
            reasons = []
            
            if df.loc[idx, 'rsi_signal'] == df.loc[idx, 'signal']:
                rsi_val = df.loc[idx, 'rsi']
                reasons.append(f'RSI({rsi_val:.1f})')
            
            if df.loc[idx, 'macd_signal_ind'] == df.loc[idx, 'signal']:
                reasons.append('MACD Cross')
            
            if df.loc[idx, 'ma_signal'] == df.loc[idx, 'signal']:
                reasons.append('MA Cross')
            
            if df.loc[idx, 'bb_signal'] == df.loc[idx, 'signal']:
                reasons.append('Bollinger')
            
            if df.loc[idx, 'stoch_signal'] == df.loc[idx, 'signal']:
                reasons.append('Stochastic')
            
            if df.loc[idx, 'volume_signal'] > 0:
                reasons.append('High Volume')
            
            df.loc[idx, 'signal_reasons'] = ', '.join(reasons) if reasons else 'Multiple Indicators'
        
        logger.debug(f"Generated signals: {(df['signal'] == 1).sum()} BUY, {(df['signal'] == -1).sum()} SELL")
        
        return df
    
    @staticmethod
    def calculate_price_targets(current_price: float, signal_type: int) -> Tuple[float, float]:
        """
        Calculate stop-loss and take-profit targets
        
        Args:
            current_price: Current stock price
            signal_type: 1 for buy, -1 for sell
        
        Returns:
            Tuple of (stop_loss_price, take_profit_price)
        """
        if signal_type == 1:  # BUY
            stop_loss = current_price * (1 - trading_config.STOP_LOSS_PERCENTAGE)
            take_profit = current_price * (1 + trading_config.TAKE_PROFIT_PERCENTAGE)
        else:  # SELL (for shorting, not typically used)
            stop_loss = current_price * (1 + trading_config.STOP_LOSS_PERCENTAGE)
            take_profit = current_price * (1 - trading_config.TAKE_PROFIT_PERCENTAGE)
        
        return round(stop_loss, 2), round(take_profit, 2)


# Example usage and testing
if __name__ == "__main__":
    from data_collector import DataCollector
    
    print("=" * 70)
    print("Technical Indicators - Test Run")
    print("=" * 70)
    
    collector = DataCollector()
    
    # Fetch data
    symbol = 'AAPL'
    print(f"\nFetching data for {symbol}...")
    df = collector.get_stock_price_yfinance(symbol, period='6mo')
    
    if not df.empty:
        print(f"✓ Fetched {len(df)} records")
        
        # Add all indicators
        print("\nCalculating technical indicators...")
        df = TechnicalIndicators.add_all_indicators(df)
        print(f"✓ Added all indicators")
        
        # Generate signals
        print("\nGenerating trading signals...")
        df = SignalGenerator.generate_signals(df)
        print(f"✓ Generated signals")
        
        # Display recent data
        print("\n" + "=" * 70)
        print("Recent Technical Data:")
        print("=" * 70)
        cols_to_show = ['close', 'rsi', 'macd', 'sma_20', 'sma_50', 'signal', 'signal_strength']
        available_cols = [col for col in cols_to_show if col in df.columns]
        print(df[available_cols].tail(10).to_string())
        
        # Show signals
        signals = df[df['signal'] != 0].tail(10)
        if not signals.empty:
            print("\n" + "=" * 70)
            print("Recent Signals:")
            print("=" * 70)
            for idx, row in signals.iterrows():
                signal_type = "🟢 BUY" if row['signal'] == 1 else "🔴 SELL"
                print(f"{signal_type} at ${row['close']:.2f}")
                print(f"  Confidence: {row['signal_strength']*100:.1f}%")
                print(f"  Reasons: {row['signal_reasons']}")
                
                if row['signal'] == 1:
                    stop_loss, take_profit = SignalGenerator.calculate_price_targets(row['close'], 1)
                    print(f"  Stop Loss: ${stop_loss:.2f}")
                    print(f"  Take Profit: ${take_profit:.2f}")
                print()
        else:
            print("\nNo strong signals found in recent data")
    
    print("=" * 70)
    print("✓ Technical indicators test complete!")
    print("=" * 70)