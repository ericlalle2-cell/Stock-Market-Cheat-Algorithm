#!/usr/bin/env python3
"""
Stock Trading Advisor - System Test
Comprehensive test to verify all components work correctly
"""

import sys
from datetime import datetime

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_imports():
    """Test all required imports"""
    print_section("TEST 1: Checking Required Imports")
    
    required_modules = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('yfinance', 'yf'),
        ('config', None),
        ('data_collector', None),
        ('indicators', None),
        ('notifications', None),
        ('main', None)
    ]
    
    failed = []
    for module, alias in required_modules:
        try:
            if alias:
                exec(f"import {module} as {alias}")
            else:
                exec(f"import {module}")
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module} - {e}")
            failed.append(module)
    
    if failed:
        print(f"\n⚠️  Missing modules: {', '.join(failed)}")
        print("Install with: pip install pandas numpy yfinance")
        return False
    
    print("\n✓ All required modules available!")
    return True

def test_config():
    """Test configuration"""
    print_section("TEST 2: Checking Configuration")
    
    try:
        from config import (
            api_config, db_config, trading_config, 
            indicator_config, system_config, notification_config
        )
        
        print(f"✓ Trading Mode: {'PAPER' if system_config.PAPER_TRADING else 'LIVE'}")
        print(f"✓ Database: {'SQLite' if db_config.USE_SQLITE else 'PostgreSQL'}")
        print(f"✓ Watchlist: {len(trading_config.STOCK_WATCHLIST)} stocks")
        print(f"✓ Stop Loss: {trading_config.STOP_LOSS_PERCENTAGE*100:.0f}%")
        print(f"✓ Take Profit: {trading_config.TAKE_PROFIT_PERCENTAGE*100:.0f}%")
        print(f"✓ Min Buy Confidence: {trading_config.MIN_BUY_CONFIDENCE*100:.0f}%")
        
        # Validate config
        errors = []
        if trading_config.STOP_LOSS_PERCENTAGE >= trading_config.TAKE_PROFIT_PERCENTAGE:
            errors.append("Stop loss should be less than take profit")
        if not trading_config.STOCK_WATCHLIST:
            errors.append("Watchlist is empty")
        
        if errors:
            print(f"\n⚠️  Configuration issues:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("\n✓ Configuration valid!")
        return True
    
    except Exception as e:
        print(f"\n✗ Configuration error: {e}")
        return False

def test_data_collection():
    """Test data collection"""
    print_section("TEST 3: Testing Data Collection")
    
    try:
        from data_collector import DataCollector, DataValidator
        
        collector = DataCollector()
        validator = DataValidator()
        
        print("Testing with AAPL...")
        
        # Test price fetch
        df = collector.get_stock_price_yfinance('AAPL', period='1mo')
        
        if df.empty:
            print("✗ Failed to fetch data")
            return False
        
        print(f"✓ Fetched {len(df)} data points")
        
        # Test validation
        df = validator.validate_price_data(df)
        print(f"✓ Validated data: {len(df)} valid rows")
        
        # Test real-time price
        rt_price = collector.get_real_time_price('AAPL')
        if rt_price:
            print(f"✓ Real-time price: ${rt_price['current_price']:.2f}")
        else:
            print("⚠️  Could not fetch real-time price")
        
        # Test stock info
        info = collector.get_stock_info('AAPL')
        if info:
            print(f"✓ Company info: {info['name']}")
            print(f"✓ Sector: {info['sector']}")
        else:
            print("⚠️  Could not fetch stock info")
        
        print("\n✓ Data collection working!")
        return True
    
    except Exception as e:
        print(f"\n✗ Data collection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_indicators():
    """Test technical indicators"""
    print_section("TEST 4: Testing Technical Indicators")
    
    try:
        from data_collector import DataCollector
        from indicators import TechnicalIndicators, SignalGenerator
        
        collector = DataCollector()
        
        print("Fetching data for AAPL...")
        df = collector.get_stock_price_yfinance('AAPL', period='6mo')
        
        if df.empty:
            print("✗ No data for testing")
            return False
        
        print(f"✓ Got {len(df)} data points")
        
        # Add indicators
        print("Calculating indicators...")
        df = TechnicalIndicators.add_all_indicators(df)
        
        required_indicators = ['sma_20', 'sma_50', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'atr']
        missing = [ind for ind in required_indicators if ind not in df.columns]
        
        if missing:
            print(f"✗ Missing indicators: {missing}")
            return False
        
        print("✓ All indicators calculated")
        
        # Generate signals
        print("Generating signals...")
        df = SignalGenerator.generate_signals(df)
        
        if 'signal' not in df.columns:
            print("✗ Signal generation failed")
            return False
        
        latest = df.iloc[-1]
        print(f"✓ Latest signal: {latest['signal']}")
        print(f"✓ Signal strength: {latest['signal_strength']*100:.1f}%")
        print(f"✓ RSI: {latest['rsi']:.2f}")
        print(f"✓ MACD: {latest['macd']:.4f}")
        
        print("\n✓ Technical indicators working!")
        return True
    
    except Exception as e:
        print(f"\n✗ Indicator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_app():
    """Test main application"""
    print_section("TEST 5: Testing Main Application")
    
    try:
        from main import StockAdvisor
        
        print("Initializing Stock Advisor...")
        advisor = StockAdvisor()
        
        print("\nTesting stock analysis...")
        result = advisor.analyze_stock('AAPL', verbose=False)
        
        if 'error' in result:
            print(f"✗ Analysis error: {result['error']}")
            return False
        
        print(f"✓ Symbol: {result['symbol']}")
        print(f"✓ Price: ${result['price']:.2f}")
        print(f"✓ Action: {result['action']}")
        print(f"✓ Confidence: {result['signal_strength']*100:.1f}%")
        
        print("\n✓ Main application working!")
        return True
    
    except Exception as e:
        print(f"\n✗ Main app error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("  STOCK TRADING ADVISOR - SYSTEM TEST")
    print("=" * 70)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tests = [
        ("Import Check", test_imports),
        ("Configuration", test_config),
        ("Data Collection", test_data_collection),
        ("Technical Indicators", test_indicators),
        ("Main Application", test_main_app)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10s} {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("  🎉 ALL TESTS PASSED! SYSTEM READY TO USE!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Run: python main.py --stock AAPL")
        print("  2. Or:  python main.py --scan")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ⚠️  SOME TESTS FAILED")
        print("=" * 70)
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install pandas numpy yfinance")
        print("  2. Check internet connection")
        print("  3. Review error messages above")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())