"""
Stock Trading Advisor - Main Application
Entry point for running the trading advisor system
"""

import sys
import argparse
from datetime import datetime
from typing import Dict, List
import logging
from config import trading_config, system_config
from data_collector import DataCollector, DataValidator
from indicators import TechnicalIndicators, SignalGenerator
from notifications import NotificationManager

# Set up logging
logging.basicConfig(
    level=getattr(logging, system_config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(system_config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class StockAdvisor:
    """Main Stock Trading Advisor Application"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.validator = DataValidator()
        self.notifier = NotificationManager()
        self.watchlist = trading_config.STOCK_WATCHLIST
        
        self._print_header()
    
    def _print_header(self):
        """Print application header"""
        print("=" * 70)
        print("📈 STOCK TRADING ADVISOR SYSTEM")
        print("=" * 70)
        print(f"Mode: {'PAPER TRADING ✓' if system_config.PAPER_TRADING else 'LIVE TRADING ⚠️'}")
        print(f"Watchlist: {len(self.watchlist)} stocks")
        print(f"Min Buy Confidence: {trading_config.MIN_BUY_CONFIDENCE*100:.0f}%")
        print(f"Stop Loss: {trading_config.STOP_LOSS_PERCENTAGE*100:.0f}% | Take Profit: {trading_config.TAKE_PROFIT_PERCENTAGE*100:.0f}%")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        logger.info("Stock Advisor initialized")
    
    def analyze_stock(self, symbol: str, verbose: bool = True) -> Dict:
        """
        Analyze a single stock and generate buy/sell signals
        
        Args:
            symbol: Stock ticker
            verbose: Print detailed output
        
        Returns:
            Dict with analysis results
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"Analyzing: {symbol}")
            print(f"{'='*70}")
        
        try:
            # Fetch historical data (6 months for good technical analysis)
            df = self.collector.get_stock_price_yfinance(symbol, period='6mo')
            
            if df.empty:
                error_msg = f"No data available for {symbol}"
                logger.warning(error_msg)
                if verbose:
                    print(f"✗ {error_msg}")
                return {'symbol': symbol, 'error': 'No data'}
            
            # Validate and clean data
            df = self.validator.validate_price_data(df)
            
            if df.empty:
                error_msg = f"No valid data after cleaning for {symbol}"
                logger.warning(error_msg)
                if verbose:
                    print(f"✗ {error_msg}")
                return {'symbol': symbol, 'error': 'Invalid data'}
            
            # Get current price info
            current_price = float(df['close'].iloc[-1])
            previous_close = float(df['close'].iloc[-2]) if len(df) > 1 else current_price
            price_change = ((current_price - previous_close) / previous_close) * 100
            
            if verbose:
                print(f"Current Price: ${current_price:.2f} ({price_change:+.2f}%)")
                print(f"Data Points: {len(df)} days")
            
            # Add technical indicators
            df = TechnicalIndicators.add_all_indicators(df)
            
            # Generate trading signals
            df = SignalGenerator.generate_signals(df)
            
            # Get latest signal
            latest = df.iloc[-1]
            
            # Build result dictionary
            result = {
                'symbol': symbol,
                'price': current_price,
                'change_pct': price_change,
                'volume': int(latest['volume']) if 'volume' in latest else 0,
                'rsi': float(latest['rsi']) if 'rsi' in latest and not pd.isna(latest['rsi']) else 50,
                'macd': float(latest['macd']) if 'macd' in latest and not pd.isna(latest['macd']) else 0,
                'signal': int(latest['signal']),
                'signal_strength': float(latest['signal_strength']),
                'signal_reasons': str(latest['signal_reasons']),
                'sma_20': float(latest['sma_20']) if 'sma_20' in latest and not pd.isna(latest['sma_20']) else 0,
                'sma_50': float(latest['sma_50']) if 'sma_50' in latest and not pd.isna(latest['sma_50']) else 0,
            }
            
            # Process strong BUY signals
            if latest['signal'] == 1 and latest['signal_strength'] >= trading_config.MIN_BUY_CONFIDENCE:
                if verbose:
                    print(f"\n🟢 BUY SIGNAL DETECTED!")
                    print(f"   Confidence: {latest['signal_strength']*100:.1f}%")
                    print(f"   Reasons: {latest['signal_reasons']}")
                    print(f"   RSI: {result['rsi']:.2f}")
                    print(f"   MACD: {result['macd']:.4f}")
                
                # Calculate price targets
                stop_loss, target_price = SignalGenerator.calculate_price_targets(current_price, 1)
                
                result['action'] = 'BUY'
                result['target_price'] = target_price
                result['stop_loss'] = stop_loss
                
                # Send notification
                try:
                    self.notifier.notify_buy_signal(
                        symbol=symbol,
                        price=current_price,
                        confidence=latest['signal_strength'],
                        reasons=latest['signal_reasons'],
                        target_price=target_price
                    )
                except Exception as e:
                    logger.error(f"Error sending buy notification: {e}")
            
            # Process strong SELL signals
            elif latest['signal'] == -1 and latest['signal_strength'] >= trading_config.MIN_SELL_CONFIDENCE:
                if verbose:
                    print(f"\n🔴 SELL SIGNAL DETECTED!")
                    print(f"   Confidence: {latest['signal_strength']*100:.1f}%")
                    print(f"   Reasons: {latest['signal_reasons']}")
                    print(f"   RSI: {result['rsi']:.2f}")
                    print(f"   MACD: {result['macd']:.4f}")
                
                result['action'] = 'SELL'
                
                # Send notification
                try:
                    self.notifier.notify_sell_signal(
                        symbol=symbol,
                        price=current_price,
                        confidence=latest['signal_strength'],
                        reasons=latest['signal_reasons']
                    )
                except Exception as e:
                    logger.error(f"Error sending sell notification: {e}")
            
            # No strong signal
            else:
                if verbose:
                    print(f"\n⚪ No strong signal")
                    print(f"   RSI: {result['rsi']:.2f}")
                    print(f"   MACD: {result['macd']:.4f}")
                    print(f"   Signal strength: {latest['signal_strength']*100:.1f}%")
                
                result['action'] = 'HOLD'
            
            logger.info(f"Analyzed {symbol}: {result['action']} (confidence: {result['signal_strength']*100:.0f}%)")
            return result
        
        except Exception as e:
            error_msg = f"Error analyzing {symbol}: {str(e)}"
            logger.error(error_msg)
            if verbose:
                print(f"✗ {error_msg}")
            return {'symbol': symbol, 'error': str(e)}
    
    def scan_watchlist(self) -> List[Dict]:
        """Scan all stocks in watchlist for trading signals"""
        print(f"\n{'='*70}")
        print(f"SCANNING WATCHLIST ({len(self.watchlist)} stocks)")
        print(f"{'='*70}")
        logger.info(f"Starting watchlist scan: {len(self.watchlist)} stocks")
        
        results = []
        buy_signals = []
        sell_signals = []
        errors = 0
        
        for i, symbol in enumerate(self.watchlist, 1):
            print(f"\n[{i}/{len(self.watchlist)}] {symbol}...", end=' ')
            
            try:
                result = self.analyze_stock(symbol, verbose=False)
                results.append(result)
                
                if 'error' not in result:
                    if result['action'] == 'BUY':
                        buy_signals.append(result)
                        print(f"🟢 BUY (Confidence: {result['signal_strength']*100:.0f}%)")
                    elif result['action'] == 'SELL':
                        sell_signals.append(result)
                        print(f"🔴 SELL (Confidence: {result['signal_strength']*100:.0f}%)")
                    else:
                        print(f"⚪ HOLD")
                else:
                    errors += 1
                    print(f"✗ Error: {result.get('error', 'Unknown')}")
            
            except Exception as e:
                errors += 1
                logger.error(f"Error scanning {symbol}: {e}")
                print(f"✗ Exception: {str(e)[:50]}")
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"SCAN COMPLETE")
        print(f"{'='*70}")
        print(f"Analyzed: {len(results)} stocks")
        print(f"Buy Signals: {len(buy_signals)}")
        print(f"Sell Signals: {len(sell_signals)}")
        print(f"Errors: {errors}")
        
        # Display buy opportunities
        if buy_signals:
            print(f"\n🟢 BUY OPPORTUNITIES (sorted by confidence):")
            buy_signals.sort(key=lambda x: x['signal_strength'], reverse=True)
            for signal in buy_signals:
                print(f"   {signal['symbol']:6s} ${signal['price']:8.2f} "
                      f"Confidence: {signal['signal_strength']*100:3.0f}% | "
                      f"RSI: {signal['rsi']:5.1f} | "
                      f"{signal['signal_reasons']}")
                if 'target_price' in signal:
                    print(f"          Target: ${signal['target_price']:.2f} | "
                          f"Stop Loss: ${signal['stop_loss']:.2f}")
        
        # Display sell recommendations
        if sell_signals:
            print(f"\n🔴 SELL RECOMMENDATIONS (sorted by confidence):")
            sell_signals.sort(key=lambda x: x['signal_strength'], reverse=True)
            for signal in sell_signals:
                print(f"   {signal['symbol']:6s} ${signal['price']:8.2f} "
                      f"Confidence: {signal['signal_strength']*100:3.0f}% | "
                      f"RSI: {signal['rsi']:5.1f} | "
                      f"{signal['signal_reasons']}")
        
        logger.info(f"Watchlist scan complete: {len(buy_signals)} BUY, {len(sell_signals)} SELL")
        return results
    
    def get_stock_recommendation(self, symbol: str):
        """Get detailed recommendation for a specific stock"""
        result = self.analyze_stock(symbol, verbose=True)
        
        if 'error' in result:
            print(f"\n✗ Unable to analyze {symbol}: {result['error']}")
            return
        
        # Print recommendation summary
        print(f"\n{'='*70}")
        print(f"RECOMMENDATION FOR {symbol}")
        print(f"{'='*70}")
        
        if result['action'] == 'BUY':
            print(f"✅ Recommendation: BUY")
            print(f"💰 Entry Price: ${result['price']:.2f}")
            print(f"🎯 Target Price: ${result.get('target_price', 0):.2f} "
                  f"(+{trading_config.TAKE_PROFIT_PERCENTAGE*100:.0f}%)")
            print(f"🛑 Stop Loss: ${result.get('stop_loss', 0):.2f} "
                  f"(-{trading_config.STOP_LOSS_PERCENTAGE*100:.0f}%)")
            print(f"📊 Confidence: {result['signal_strength']*100:.1f}%")
            print(f"📋 Reasons: {result['signal_reasons']}")
        
        elif result['action'] == 'SELL':
            print(f"⛔ Recommendation: SELL")
            print(f"💰 Current Price: ${result['price']:.2f}")
            print(f"📊 Confidence: {result['signal_strength']*100:.1f}%")
            print(f"📋 Reasons: {result['signal_reasons']}")
        
        else:
            print(f"⏸️  Recommendation: HOLD / WAIT")
            print(f"💰 Current Price: ${result['price']:.2f}")
            print(f"📊 Signal Strength: {result['signal_strength']*100:.1f}% "
                  f"(needs ≥{trading_config.MIN_BUY_CONFIDENCE*100:.0f}%)")
            print(f"📋 Current State: RSI={result['rsi']:.1f}, MACD={result['macd']:.4f}")
            print(f"\n💡 No strong signal at this time. Keep monitoring.")
        
        print(f"{'='*70}")
        logger.info(f"Recommendation for {symbol}: {result['action']}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Stock Trading Advisor - Intelligent stock analysis and trading signals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --scan                  # Scan entire watchlist
  python main.py --stock AAPL            # Analyze Apple stock
  python main.py --stock TSLA MSFT GOOGL # Analyze multiple stocks
  python main.py --watchlist             # Show current watchlist
        """
    )
    
    parser.add_argument('--scan', action='store_true', 
                       help='Scan entire watchlist for signals')
    parser.add_argument('--stock', type=str, nargs='+', metavar='SYMBOL',
                       help='Analyze specific stock(s) (e.g., AAPL MSFT GOOGL)')
    parser.add_argument('--watchlist', action='store_true', 
                       help='Show current watchlist')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output with detailed analysis')
    
    args = parser.parse_args()
    
    try:
        advisor = StockAdvisor()
        
        # Show watchlist
        if args.watchlist:
            print("\n" + "="*70)
            print("CURRENT WATCHLIST")
            print("="*70)
            for i, symbol in enumerate(advisor.watchlist, 1):
                print(f"  {i:2d}. {symbol}")
            print(f"\nTotal: {len(advisor.watchlist)} stocks")
            print("="*70)
        
        # Analyze specific stocks
        elif args.stock:
            for symbol in args.stock:
                advisor.get_stock_recommendation(symbol.upper())
        
        # Scan watchlist
        elif args.scan:
            advisor.scan_watchlist()
        
        # No arguments - show help
        else:
            parser.print_help()
            print("\n" + "="*70)
            print("QUICK START")
            print("="*70)
            print("1. Analyze a stock:    python main.py --stock AAPL")
            print("2. Scan watchlist:     python main.py --scan")
            print("3. View watchlist:     python main.py --watchlist")
            print("="*70)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        logger.info("Application interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        logger.exception("Fatal error in main application")
        sys.exit(1)


if __name__ == "__main__":
    import pandas as pd  # Import here to avoid issues
    main()