"""
Data Collection Module
Fetches stock data from various APIs with robust error handling
"""

import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging
from config import api_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataCollector:
    """Main data collection class with multiple data sources"""
    
    def __init__(self):
        self.alpha_vantage_key = api_config.ALPHA_VANTAGE_KEY
        self.polygon_key = api_config.POLYGON_KEY
        self.news_api_key = api_config.NEWS_API_KEY
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # seconds between requests
        
        # Cache for stock info
        self._info_cache = {}
        self._cache_timeout = 3600  # 1 hour cache
    
    def _rate_limit(self, api_name: str, min_interval: float = None):
        """
        Implement rate limiting to avoid API throttling
        
        Args:
            api_name: Name of the API
            min_interval: Minimum seconds between requests (defaults to class setting)
        """
        interval = min_interval if min_interval is not None else self.min_request_interval
        
        if api_name in self.last_request_time:
            elapsed = time.time() - self.last_request_time[api_name]
            if elapsed < interval:
                sleep_time = interval - elapsed
                time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def get_stock_price_yfinance(self, symbol: str, period: str = '1y', 
                                  interval: str = '1d') -> pd.DataFrame:
        """
        Fetch stock price data using yfinance (FREE and reliable)
        
        Args:
            symbol: Stock ticker symbol
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Data interval ('1m', '5m', '15m', '1h', '1d', '1wk', '1mo')
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            self._rate_limit('yfinance', 0.5)
            
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Standardize column names (lowercase)
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Reset index to make date a column
            df = df.reset_index()
            if 'date' in df.columns:
                df['timestamp'] = df['date']
            elif 'datetime' in df.columns:
                df['timestamp'] = df['datetime']
            
            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✓ Fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} from yfinance: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time price and info for a stock
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Dict with current price info or None if error
        """
        try:
            self._rate_limit('yfinance', 0.5)
            
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Try to get current price from various fields
            current_price = (
                info.get('currentPrice') or 
                info.get('regularMarketPrice') or
                info.get('previousClose') or
                0.0
            )
            
            if current_price == 0.0:
                logger.warning(f"Could not get current price for {symbol}")
                return None
            
            result = {
                'symbol': symbol,
                'current_price': float(current_price),
                'open': float(info.get('open') or info.get('regularMarketOpen') or 0),
                'high': float(info.get('dayHigh') or info.get('regularMarketDayHigh') or 0),
                'low': float(info.get('dayLow') or info.get('regularMarketDayLow') or 0),
                'volume': int(info.get('volume') or info.get('regularMarketVolume') or 0),
                'market_cap': float(info.get('marketCap') or 0),
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Real-time price for {symbol}: ${result['current_price']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get detailed stock information and fundamentals
        
        Args:
            symbol: Stock ticker
            use_cache: Whether to use cached data
        
        Returns:
            Dict with company info, financials, etc.
        """
        try:
            # Check cache
            if use_cache and symbol in self._info_cache:
                cached_time, cached_data = self._info_cache[symbol]
                if time.time() - cached_time < self._cache_timeout:
                    logger.debug(f"Using cached info for {symbol}")
                    return cached_data
            
            self._rate_limit('yfinance', 0.5)
            
            stock = yf.Ticker(symbol)
            info = stock.info
            
            if not info or len(info) < 5:
                logger.warning(f"Limited info available for {symbol}")
                return None
            
            result = {
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName') or symbol,
                'sector': info.get('sector') or 'Unknown',
                'industry': info.get('industry') or 'Unknown',
                'market_cap': float(info.get('marketCap') or 0),
                'pe_ratio': float(info.get('trailingPE') or 0),
                'forward_pe': float(info.get('forwardPE') or 0),
                'peg_ratio': float(info.get('pegRatio') or 0),
                'price_to_book': float(info.get('priceToBook') or 0),
                'dividend_yield': float(info.get('dividendYield') or 0),
                'fifty_two_week_high': float(info.get('fiftyTwoWeekHigh') or 0),
                'fifty_two_week_low': float(info.get('fiftyTwoWeekLow') or 0),
                'avg_volume': int(info.get('averageVolume') or 0),
                'beta': float(info.get('beta') or 0),
                'description': info.get('longBusinessSummary') or '',
                'current_price': float(info.get('currentPrice') or info.get('regularMarketPrice') or 0)
            }
            
            # Cache the result
            self._info_cache[symbol] = (time.time(), result)
            
            logger.debug(f"Retrieved info for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return None
    
    def get_multiple_stocks(self, symbols: List[str], period: str = '1y', 
                           show_progress: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks efficiently
        
        Args:
            symbols: List of ticker symbols
            period: Data period
            show_progress: Whether to show progress
        
        Returns:
            Dict mapping symbol to DataFrame
        """
        results = {}
        total = len(symbols)
        
        for i, symbol in enumerate(symbols, 1):
            if show_progress:
                logger.info(f"Fetching [{i}/{total}] {symbol}...")
            
            df = self.get_stock_price_yfinance(symbol, period)
            
            if not df.empty:
                results[symbol] = df
            
            # Small delay to be nice to the API
            time.sleep(0.5)
        
        logger.info(f"✓ Successfully fetched {len(results)}/{total} stocks")
        return results
    
    def get_historical_data_batch(self, symbols: List[str], start_date: str, 
                                  end_date: str = None) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple symbols between dates
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
        
        Returns:
            Dict mapping symbol to DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        results = {}
        
        for symbol in symbols:
            try:
                self._rate_limit('yfinance', 0.5)
                
                stock = yf.Ticker(symbol)
                df = stock.history(start=start_date, end=end_date)
                
                if not df.empty:
                    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
                    df['symbol'] = symbol
                    df = df.reset_index()
                    
                    if 'date' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['date'])
                    
                    results[symbol] = df
                    logger.debug(f"Fetched {len(df)} records for {symbol}")
                
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue
        
        return results
    
    def get_news_sentiment(self, symbol: str, days_back: int = 7) -> List[Dict]:
        """
        Fetch news articles for sentiment analysis
        
        Args:
            symbol: Stock ticker
            days_back: Number of days to look back
        
        Returns:
            List of news articles with metadata
        """
        if not self.news_api_key or self.news_api_key == '':
            logger.warning("News API key not configured")
            return []
        
        try:
            self._rate_limit('news_api', 1.0)
            
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # Get stock info for company name
            info = self.get_stock_info(symbol)
            company_name = info['name'] if info else symbol
            
            url = f"{api_config.NEWS_API_URL}/everything"
            params = {
                'q': f'"{company_name}" OR {symbol}',
                'from': from_date,
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.news_api_key,
                'pageSize': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                logger.info(f"✓ Found {len(articles)} news articles for {symbol}")
                return articles
            else:
                logger.warning(f"News API returned status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []


class DataValidator:
    """Validates and cleans stock data"""
    
    @staticmethod
    def validate_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean price data with robust error handling
        
        Args:
            df: Raw price DataFrame
        
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        original_len = len(df)
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Ensure numeric types for price columns
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure volume is numeric
        if 'volume' in df.columns:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['volume'] = df['volume'].fillna(0)
        
        # Remove rows with all NaN prices
        df = df.dropna(subset=price_cols, how='all')
        
        # Remove duplicates based on timestamp
        if 'timestamp' in df.columns:
            df = df.drop_duplicates(subset=['timestamp'], keep='first')
        elif df.index.name == 'Date' or df.index.name == 'Datetime':
            df = df[~df.index.duplicated(keep='first')]
        
        # Remove invalid prices (negative or zero)
        for col in price_cols:
            if col in df.columns:
                df = df[df[col] > 0]
        
        # Remove rows where high < low (data error)
        if 'high' in df.columns and 'low' in df.columns:
            df = df[df['high'] >= df['low']]
        
        # Check for price integrity
        if all(col in df.columns for col in ['high', 'low', 'open', 'close']):
            # High should be >= all other prices
            df = df[
                (df['high'] >= df['low']) &
                (df['high'] >= df['open']) &
                (df['high'] >= df['close']) &
                (df['low'] <= df['open']) &
                (df['low'] <= df['close'])
            ]
        
        # Forward fill then backward fill for small gaps
        df = df.fillna(method='ffill', limit=3).fillna(method='bfill', limit=3)
        
        # Sort by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
        else:
            df = df.sort_index()
        
        cleaned_len = len(df)
        if original_len != cleaned_len:
            logger.info(f"Data validation: {original_len} → {cleaned_len} rows (removed {original_len - cleaned_len} invalid rows)")
        
        return df
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, column: str = 'close', 
                       std_threshold: float = 4.0) -> pd.Series:
        """
        Detect outliers using z-score method
        
        Args:
            df: Price DataFrame
            column: Column to check for outliers
            std_threshold: Number of standard deviations for outlier detection
        
        Returns:
            Boolean series indicating outliers (True = outlier)
        """
        if df.empty or column not in df.columns:
            return pd.Series(dtype=bool)
        
        mean = df[column].mean()
        std = df[column].std()
        
        if std == 0:
            return pd.Series([False] * len(df), index=df.index)
        
        z_scores = (df[column] - mean) / std
        outliers = abs(z_scores) > std_threshold
        
        if outliers.any():
            logger.info(f"Detected {outliers.sum()} outliers in {column}")
        
        return outliers
    
    @staticmethod
    def fill_missing_data(df: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
        """
        Fill missing data intelligently
        
        Args:
            df: DataFrame with potential missing values
            method: Fill method ('ffill', 'bfill', 'interpolate')
        
        Returns:
            DataFrame with filled values
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        if method == 'ffill':
            df = df.fillna(method='ffill', limit=5)
        elif method == 'bfill':
            df = df.fillna(method='bfill', limit=5)
        elif method == 'interpolate':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit=5)
        
        return df


# Example usage and testing
if __name__ == "__main__":
    from config import trading_config
    
    collector = DataCollector()
    validator = DataValidator()
    
    print("=" * 70)
    print("Stock Data Collector - Test Run")
    print("=" * 70)
    
    # Test with a few stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        print(f"\n{'='*70}")
        print(f"Testing: {symbol}")
        print(f"{'='*70}")
        
        # Get price data
        df = collector.get_stock_price_yfinance(symbol, period='1mo')
        
        if not df.empty:
            # Validate
            df = validator.validate_price_data(df)
            
            print(f"✓ Data points: {len(df)}")
            print(f"✓ Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"✓ Latest close: ${df['close'].iloc[-1]:.2f}")
            print(f"✓ Average volume: {df['volume'].mean():,.0f}")
        
        # Get real-time price
        rt_price = collector.get_real_time_price(symbol)
        if rt_price:
            print(f"✓ Real-time price: ${rt_price['current_price']:.2f}")
            print(f"✓ Market cap: ${rt_price['market_cap']:,.0f}")
        
        # Get company info
        info = collector.get_stock_info(symbol)
        if info:
            print(f"✓ Company: {info['name']}")
            print(f"✓ Sector: {info['sector']}")
            print(f"✓ P/E Ratio: {info['pe_ratio']:.2f}")
    
    print("\n" + "=" * 70)
    print("✓ Data collection test complete!")
    print("=" * 70)