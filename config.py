"""
Stock Trading Advisor - Configuration File
Contains all system settings, API keys, and parameters
"""

import os
from dataclasses import dataclass, field
from typing import List
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables


@dataclass
class APIConfig:
    """API Keys and Endpoints"""
    # Alpha Vantage (Free tier: 25 requests/day)
    ALPHA_VANTAGE_KEY: str = os.getenv('ALPHA_VANTAGE_KEY', 'demo')
    ALPHA_VANTAGE_URL: str = 'https://www.alphavantage.co/query'
    
    # Polygon.io (Paid but affordable)
    POLYGON_KEY: str = os.getenv('POLYGON_KEY', '')
    POLYGON_URL: str = 'https://api.polygon.io'
    
    # News API
    NEWS_API_KEY: str = os.getenv('NEWS_API_KEY', '')
    NEWS_API_URL: str = 'https://newsapi.org/v2'
    
    # Twilio for SMS notifications
    TWILIO_ACCOUNT_SID: str = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE: str = os.getenv('TWILIO_PHONE', '')
    
    # Email for notifications
    EMAIL_SENDER: str = os.getenv('EMAIL_SENDER', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_SMTP_SERVER: str = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT: int = int(os.getenv('EMAIL_SMTP_PORT', '587'))


@dataclass
class DatabaseConfig:
    """Database Settings"""
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'stock_advisor')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'password')
    
    # SQLite fallback (if PostgreSQL not available)
    USE_SQLITE: bool = os.getenv('USE_SQLITE', 'true').lower() == 'true'
    SQLITE_PATH: str = os.getenv('SQLITE_PATH', 'data/stock_advisor.db')
    
    @property
    def connection_string(self) -> str:
        """Get database connection string"""
        if self.USE_SQLITE:
            # Ensure data directory exists
            Path(self.SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{self.SQLITE_PATH}"
        else:
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@dataclass
class TradingConfig:
    """Trading Strategy Parameters"""
    
    # Risk Management
    MAX_POSITION_SIZE: float = float(os.getenv('MAX_POSITION_SIZE', '0.10'))  # 10% max per stock
    STOP_LOSS_PERCENTAGE: float = float(os.getenv('STOP_LOSS_PERCENTAGE', '0.05'))  # 5% stop loss
    TAKE_PROFIT_PERCENTAGE: float = float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.15'))  # 15% take profit
    MAX_DAILY_LOSS: float = float(os.getenv('MAX_DAILY_LOSS', '0.03'))  # 3% max daily loss
    MAX_PORTFOLIO_STOCKS: int = int(os.getenv('MAX_PORTFOLIO_STOCKS', '15'))  # Max 15 stocks
    
    # Signal Confidence Thresholds
    MIN_BUY_CONFIDENCE: float = float(os.getenv('MIN_BUY_CONFIDENCE', '0.75'))  # 75% minimum
    MIN_SELL_CONFIDENCE: float = float(os.getenv('MIN_SELL_CONFIDENCE', '0.70'))  # 70% minimum
    
    # Stock Universe Filters
    MIN_PRICE: float = float(os.getenv('MIN_PRICE', '5.0'))  # Avoid penny stocks
    MAX_PRICE: float = float(os.getenv('MAX_PRICE', '10000.0'))  # Price ceiling
    MIN_VOLUME: int = int(os.getenv('MIN_VOLUME', '1000000'))  # 1M minimum daily volume
    MIN_MARKET_CAP: float = float(os.getenv('MIN_MARKET_CAP', '1000000000'))  # $1B minimum
    
    # Watchlist
    STOCK_WATCHLIST: List[str] = field(default_factory=lambda: [
        # Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'NFLX',
        # Finance
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK',
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'LLY', 'MRK',
        # Consumer
        'WMT', 'HD', 'NKE', 'SBUX', 'MCD', 'KO', 'PEP',
        # Energy
        'XOM', 'CVX', 'COP', 'SLB',
        # Industrial
        'BA', 'CAT', 'GE', 'HON',
        # Payment/FinTech
        'V', 'MA', 'PYPL', 'SQ'
    ])


@dataclass
class IndicatorConfig:
    """Technical Indicator Parameters"""
    
    # Moving Averages
    SMA_SHORT: int = int(os.getenv('SMA_SHORT', '20'))  # 20-day SMA
    SMA_LONG: int = int(os.getenv('SMA_LONG', '50'))    # 50-day SMA
    SMA_LONGER: int = int(os.getenv('SMA_LONGER', '200'))  # 200-day SMA
    EMA_FAST: int = int(os.getenv('EMA_FAST', '12'))    # Fast EMA
    EMA_SLOW: int = int(os.getenv('EMA_SLOW', '26'))    # Slow EMA
    
    # RSI
    RSI_PERIOD: int = int(os.getenv('RSI_PERIOD', '14'))
    RSI_OVERBOUGHT: float = float(os.getenv('RSI_OVERBOUGHT', '70'))
    RSI_OVERSOLD: float = float(os.getenv('RSI_OVERSOLD', '30'))
    
    # MACD
    MACD_SIGNAL: int = int(os.getenv('MACD_SIGNAL', '9'))
    
    # Bollinger Bands
    BB_PERIOD: int = int(os.getenv('BB_PERIOD', '20'))
    BB_STD_DEV: int = int(os.getenv('BB_STD_DEV', '2'))
    
    # Volume
    VOLUME_SMA: int = int(os.getenv('VOLUME_SMA', '20'))
    
    # ATR
    ATR_PERIOD: int = int(os.getenv('ATR_PERIOD', '14'))
    
    # Stochastic
    STOCH_K_PERIOD: int = int(os.getenv('STOCH_K_PERIOD', '14'))
    STOCH_D_PERIOD: int = int(os.getenv('STOCH_D_PERIOD', '3'))
    
    # ADX
    ADX_PERIOD: int = int(os.getenv('ADX_PERIOD', '14'))


@dataclass
class MLConfig:
    """Machine Learning Model Settings"""
    
    # Training
    TRAIN_TEST_SPLIT: float = 0.8
    VALIDATION_SPLIT: float = 0.1
    RANDOM_STATE: int = 42
    
    # Model Parameters
    LOOKBACK_DAYS: int = 60  # Use 60 days of historical data
    PREDICTION_HORIZON: int = 5  # Predict 5 days ahead
    
    # Feature Engineering
    USE_TECHNICAL_INDICATORS: bool = True
    USE_SENTIMENT_ANALYSIS: bool = True
    USE_FUNDAMENTAL_DATA: bool = True
    
    # Ensemble
    ENSEMBLE_MODELS: List[str] = field(default_factory=lambda: [
        'random_forest',
        'xgboost',
        'gradient_boosting'
    ])


@dataclass
class NotificationConfig:
    """Notification Settings"""
    
    # User contact info
    USER_EMAIL: str = os.getenv('USER_EMAIL', '')
    USER_PHONE: str = os.getenv('USER_PHONE', '')
    
    # Notification preferences
    ENABLE_EMAIL: bool = os.getenv('ENABLE_EMAIL', 'false').lower() == 'true'
    ENABLE_SMS: bool = os.getenv('ENABLE_SMS', 'false').lower() == 'true'
    ENABLE_PUSH: bool = False
    
    # Alert thresholds
    NOTIFY_ON_BUY_SIGNAL: bool = True
    NOTIFY_ON_SELL_SIGNAL: bool = True
    NOTIFY_ON_STOP_LOSS: bool = True
    NOTIFY_ON_TAKE_PROFIT: bool = True
    NOTIFY_DAILY_SUMMARY: bool = os.getenv('NOTIFY_DAILY_SUMMARY', 'false').lower() == 'true'


@dataclass
class SystemConfig:
    """System-wide Settings"""
    
    # Operating Mode
    PAPER_TRADING: bool = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    LIVE_TRADING: bool = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    
    # Data Collection
    UPDATE_FREQUENCY_MINUTES: int = int(os.getenv('UPDATE_FREQUENCY_MINUTES', '60'))
    MARKET_HOURS_ONLY: bool = os.getenv('MARKET_HOURS_ONLY', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/stock_advisor.log')
    
    # Backtesting
    BACKTEST_START_DATE: str = os.getenv('BACKTEST_START_DATE', '2020-01-01')
    BACKTEST_END_DATE: str = os.getenv('BACKTEST_END_DATE', '2024-12-31')
    INITIAL_CAPITAL: float = float(os.getenv('INITIAL_CAPITAL', '100000.0'))
    
    def __post_init__(self):
        """Ensure log directory exists"""
        Path(self.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)


# Initialize all configs
api_config = APIConfig()
db_config = DatabaseConfig()
trading_config = TradingConfig()
indicator_config = IndicatorConfig()
ml_config = MLConfig()
notification_config = NotificationConfig()
system_config = SystemConfig()


# Validation function
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check risk management
    if trading_config.STOP_LOSS_PERCENTAGE >= trading_config.TAKE_PROFIT_PERCENTAGE:
        errors.append("Stop loss should be less than take profit percentage")
    
    if trading_config.MAX_POSITION_SIZE > 1.0 or trading_config.MAX_POSITION_SIZE <= 0:
        errors.append("MAX_POSITION_SIZE must be between 0 and 1")
    
    # Check notification config
    if notification_config.ENABLE_EMAIL and not notification_config.USER_EMAIL:
        errors.append("Email enabled but USER_EMAIL not set")
    
    if notification_config.ENABLE_SMS and not notification_config.USER_PHONE:
        errors.append("SMS enabled but USER_PHONE not set")
    
    # Check watchlist
    if not trading_config.STOCK_WATCHLIST:
        errors.append("Watchlist is empty")
    
    if errors:
        print("⚠️ Configuration Warnings:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("Stock Trading Advisor - Configuration")
    print("=" * 70)
    print(f"\n✓ Trading Mode: {'PAPER' if system_config.PAPER_TRADING else 'LIVE'}")
    print(f"✓ Database: {'SQLite' if db_config.USE_SQLITE else 'PostgreSQL'}")
    print(f"✓ Watchlist: {len(trading_config.STOCK_WATCHLIST)} stocks")
    print(f"✓ Email Notifications: {'Enabled' if notification_config.ENABLE_EMAIL else 'Disabled'}")
    print(f"✓ SMS Notifications: {'Enabled' if notification_config.ENABLE_SMS else 'Disabled'}")
    print(f"✓ Stop Loss: {trading_config.STOP_LOSS_PERCENTAGE*100}%")
    print(f"✓ Take Profit: {trading_config.TAKE_PROFIT_PERCENTAGE*100}%")
    print(f"✓ Min Buy Confidence: {trading_config.MIN_BUY_CONFIDENCE*100}%")
    
    print("\n" + "=" * 70)
    validate_config()