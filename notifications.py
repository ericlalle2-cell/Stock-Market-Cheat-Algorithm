"""
Notification System
Sends alerts via email, SMS, and other channels with robust error handling
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
import logging
from config import api_config, notification_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages all notification channels with comprehensive error handling"""
    
    def __init__(self):
        self.email_enabled = notification_config.ENABLE_EMAIL and notification_config.USER_EMAIL
        self.sms_enabled = notification_config.ENABLE_SMS and notification_config.USER_PHONE
        self.user_email = notification_config.USER_EMAIL
        self.user_phone = notification_config.USER_PHONE
        
        # Email configuration
        self.email_sender = api_config.EMAIL_SENDER
        self.email_password = api_config.EMAIL_PASSWORD
        self.smtp_server = api_config.EMAIL_SMTP_SERVER
        self.smtp_port = api_config.EMAIL_SMTP_PORT
        
        # Twilio configuration
        self.twilio_sid = api_config.TWILIO_ACCOUNT_SID
        self.twilio_token = api_config.TWILIO_AUTH_TOKEN
        self.twilio_phone = api_config.TWILIO_PHONE
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate notification configuration"""
        if self.email_enabled:
            if not self.email_sender or not self.email_password:
                logger.warning("Email enabled but sender credentials not configured")
                self.email_enabled = False
        
        if self.sms_enabled:
            if not self.twilio_sid or not self.twilio_token:
                logger.warning("SMS enabled but Twilio credentials not configured")
                self.sms_enabled = False
    
    def send_email(self, subject: str, body: str, is_html: bool = False, 
                   recipient: str = None) -> bool:
        """
        Send email notification with comprehensive error handling
        
        Args:
            subject: Email subject line
            body: Email body content
            is_html: Whether body is HTML formatted
            recipient: Email recipient (defaults to user_email)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.email_enabled:
            logger.debug("Email notifications disabled")
            return False
        
        recipient = recipient or self.user_email
        
        if not recipient:
            logger.warning("No email recipient specified")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = recipient
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add body
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type, 'utf-8'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            
            logger.info(f"✓ Email sent: {subject}")
            return True
        
        except smtplib.SMTPAuthenticationError:
            logger.error("Email authentication failed - check credentials")
            return False
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False
    
    def send_sms(self, message: str, recipient: str = None) -> bool:
        """
        Send SMS notification via Twilio with error handling
        
        Args:
            message: SMS message content (max 160 chars recommended)
            recipient: Phone number (defaults to user_phone)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.sms_enabled:
            logger.debug("SMS notifications disabled")
            return False
        
        recipient = recipient or self.user_phone
        
        if not recipient:
            logger.warning("No SMS recipient specified")
            return False
        
        # Truncate message if too long
        if len(message) > 160:
            message = message[:157] + "..."
            logger.warning("SMS message truncated to 160 characters")
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_sid, self.twilio_token)
            
            sms = client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=recipient
            )
            
            logger.info(f"✓ SMS sent: {sms.sid}")
            return True
        
        except ImportError:
            logger.error("Twilio not installed. Install with: pip install twilio")
            self.sms_enabled = False
            return False
        
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    def notify_buy_signal(self, symbol: str, price: float, confidence: float, 
                         reasons: str, target_price: float = None, 
                         stop_loss: float = None) -> bool:
        """
        Send buy signal notification via all enabled channels
        
        Args:
            symbol: Stock ticker symbol
            price: Current stock price
            confidence: Signal confidence (0-1)
            reasons: Reasons for the signal
            target_price: Optional target price
            stop_loss: Optional stop loss price
        
        Returns:
            True if at least one notification sent successfully
        """
        if not notification_config.NOTIFY_ON_BUY_SIGNAL:
            return False
        
        success = False
        
        # Email notification
        if self.email_enabled:
            subject = f"🟢 BUY Signal: {symbol}"
            
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .content {{ padding: 30px; }}
                    .metric {{ display: flex; justify-content: space-between; padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 5px; }}
                    .metric-label {{ font-weight: 600; color: #495057; }}
                    .metric-value {{ font-weight: 700; color: #28a745; }}
                    .highlight {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
                    .button {{ display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🟢 BUY SIGNAL DETECTED</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">High-confidence trading opportunity identified</p>
                    </div>
                    
                    <div class="content">
                        <div class="highlight">
                            <strong style="font-size: 18px;">{symbol}</strong> is showing strong buy signals
                        </div>
                        
                        <div class="metric">
                            <span class="metric-label">Current Price</span>
                            <span class="metric-value">${price:.2f}</span>
                        </div>
                        
                        <div class="metric">
                            <span class="metric-label">Confidence Level</span>
                            <span class="metric-value">{confidence*100:.1f}%</span>
                        </div>
                        
                        {f'''<div class="metric">
                            <span class="metric-label">Target Price</span>
                            <span class="metric-value">${target_price:.2f}</span>
                        </div>''' if target_price else ''}
                        
                        {f'''<div class="metric">
                            <span class="metric-label">Stop Loss</span>
                            <span class="metric-value" style="color: #dc3545;">${stop_loss:.2f}</span>
                        </div>''' if stop_loss else ''}
                        
                        <div class="metric">
                            <span class="metric-label">Signal Reasons</span>
                            <span class="metric-value" style="font-size: 14px;">{reasons}</span>
                        </div>
                        
                        <div class="metric">
                            <span class="metric-label">Generated</span>
                            <span class="metric-value" style="color: #6c757d; font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                        </div>
                        
                        <p style="margin-top: 30px; color: #6c757d; font-size: 14px; line-height: 1.6;">
                            <strong>Next Steps:</strong><br>
                            1. Review the signal and do your own research<br>
                            2. Check current market conditions<br>
                            3. Set your stop-loss at ${stop_loss:.2f if stop_loss else price * 0.95:.2f}<br>
                            4. Consider position sizing based on your portfolio
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated alert from your Stock Trading Advisor</p>
                        <p style="margin-top: 10px; font-size: 11px;">
                            ⚠️ Not financial advice. Always do your own research before trading.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if self.send_email(subject, body, is_html=True):
                success = True
        
        # SMS notification
        if self.sms_enabled:
            sms_message = (
                f"🟢 BUY {symbol} @ ${price:.2f}\n"
                f"Confidence: {confidence*100:.0f}%\n"
                f"Target: ${target_price:.2f if target_price else 0:.2f}\n"
                f"{reasons[:50]}"
            )
            
            if self.send_sms(sms_message):
                success = True
        
        return success
    
    def notify_sell_signal(self, symbol: str, price: float, confidence: float, 
                          reasons: str, profit_loss: float = None, 
                          profit_loss_pct: float = None) -> bool:
        """
        Send sell signal notification via all enabled channels
        
        Args:
            symbol: Stock ticker symbol
            price: Current stock price
            confidence: Signal confidence (0-1)
            reasons: Reasons for the signal
            profit_loss: Dollar amount profit/loss
            profit_loss_pct: Percentage profit/loss
        
        Returns:
            True if at least one notification sent successfully
        """
        if not notification_config.NOTIFY_ON_SELL_SIGNAL:
            return False
        
        success = False
        
        # Determine if profit or loss
        is_profit = profit_loss is None or profit_loss >= 0
        pl_color = "#28a745" if is_profit else "#dc3545"
        pl_emoji = "📈" if is_profit else "📉"
        
        # Email notification
        if self.email_enabled:
            subject = f"🔴 SELL Signal: {symbol}"
            
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .content {{ padding: 30px; }}
                    .metric {{ display: flex; justify-content: space-between; padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 5px; }}
                    .metric-label {{ font-weight: 600; color: #495057; }}
                    .metric-value {{ font-weight: 700; color: #dc3545; }}
                    .highlight {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔴 SELL SIGNAL DETECTED</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Exit signal identified for your position</p>
                    </div>
                    
                    <div class="content">
                        <div class="highlight">
                            <strong style="font-size: 18px;">{symbol}</strong> is showing sell signals
                        </div>
                        
                        <div class="metric">
                            <span class="metric-label">Current Price</span>
                            <span class="metric-value">${price:.2f}</span>
                        </div>
                        
                        <div class="metric">
                            <span class="metric-label">Confidence Level</span>
                            <span class="metric-value">{confidence*100:.1f}%</span>
                        </div>
                        
                        {f'''<div class="metric">
                            <span class="metric-label">Profit/Loss {pl_emoji}</span>
                            <span class="metric-value" style="color: {pl_color};">
                                ${profit_loss:+.2f} ({profit_loss_pct:+.1f}%)
                            </span>
                        </div>''' if profit_loss is not None else ''}
                        
                        <div class="metric">
                            <span class="metric-label">Signal Reasons</span>
                            <span class="metric-value" style="font-size: 14px;">{reasons}</span>
                        </div>
                        
                        <div class="metric">
                            <span class="metric-label">Generated</span>
                            <span class="metric-value" style="color: #6c757d; font-size: 14px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                        </div>
                        
                        <p style="margin-top: 30px; color: #6c757d; font-size: 14px; line-height: 1.6;">
                            <strong>Recommended Action:</strong><br>
                            Consider closing your position in {symbol} at the current price of ${price:.2f}.
                            Review current market conditions and your trading plan before executing.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated alert from your Stock Trading Advisor</p>
                        <p style="margin-top: 10px; font-size: 11px;">
                            ⚠️ Not financial advice. Always do your own research before trading.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if self.send_email(subject, body, is_html=True):
                success = True
        
        # SMS notification
        if self.sms_enabled:
            pl_text = f" P/L: ${profit_loss:+.2f}" if profit_loss is not None else ""
            sms_message = (
                f"🔴 SELL {symbol} @ ${price:.2f}\n"
                f"Confidence: {confidence*100:.0f}%{pl_text}\n"
                f"{reasons[:40]}"
            )
            
            if self.send_sms(sms_message):
                success = True
        
        return success
    
    def notify_daily_summary(self, summary_data: Dict) -> bool:
        """
        Send daily portfolio summary
        
        Args:
            summary_data: Dict containing portfolio metrics
        
        Returns:
            True if sent successfully
        """
        if not notification_config.NOTIFY_DAILY_SUMMARY or not self.email_enabled:
            return False
        
        subject = f"📊 Daily Portfolio Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        daily_return = summary_data.get('daily_return', 0)
        return_color = "#28a745" if daily_return >= 0 else "#dc3545"
        return_emoji = "📈" if daily_return >= 0 else "📉"
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .section {{ margin: 25px 0; }}
                .section-title {{ font-size: 18px; font-weight: 600; color: #495057; margin-bottom: 15px; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                .metric {{ display: flex; justify-content: space-between; padding: 12px; margin: 8px 0; background: #f8f9fa; border-radius: 5px; }}
                .metric-label {{ color: #6c757d; }}
                .metric-value {{ font-weight: 600; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Portfolio Summary</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
                </div>
                
                <div class="content">
                    <div class="section">
                        <div class="section-title">Portfolio Value</div>
                        <div class="metric">
                            <span class="metric-label">Total Value</span>
                            <span class="metric-value">${summary_data.get('total_value', 0):,.2f}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Cash Balance</span>
                            <span class="metric-value">${summary_data.get('cash', 0):,.2f}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Invested Amount</span>
                            <span class="metric-value">${summary_data.get('invested', 0):,.2f}</span>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Performance {return_emoji}</div>
                        <div class="metric">
                            <span class="metric-label">Daily Return</span>
                            <span class="metric-value" style="color: {return_color};">{daily_return:+.2f}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Total Return</span>
                            <span class="metric-value" style="color: {return_color};">{summary_data.get('total_return', 0):+.2f}%</span>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Holdings</div>
                        <div class="metric">
                            <span class="metric-label">Active Positions</span>
                            <span class="metric-value">{summary_data.get('num_positions', 0)}</span>
                        </div>
                    </div>
                    
                    <p style="margin-top: 30px; padding: 15px; background: #e7f3ff; border-radius: 5px; color: #004085; font-size: 14px;">
                        💡 <strong>Tip:</strong> Keep monitoring your positions and stay disciplined with your stop-loss levels.
                    </p>
                </div>
                
                <div class="footer">
                    <p>Generated by Stock Trading Advisor</p>
                    <p style="margin-top: 10px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(subject, body, is_html=True)
    
    def test_notification_system(self) -> Dict[str, bool]:
        """
        Test all notification channels
        
        Returns:
            Dict with results for each channel
        """
        results = {}
        
        # Test email
        if self.email_enabled:
            test_subject = "🧪 Test Email from Stock Trading Advisor"
            test_body = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Test Email Successful! ✅</h2>
                <p>Your email notifications are configured correctly.</p>
                <p>You'll receive alerts when:</p>
                <ul>
                    <li>🟢 Buy signals are detected</li>
                    <li>🔴 Sell signals are detected</li>
                    <li>📊 Daily portfolio summaries (if enabled)</li>
                </ul>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """
            results['email'] = self.send_email(test_subject, test_body, is_html=True)
        else:
            results['email'] = False
            logger.info("Email notifications not configured - skipping test")
        
        # Test SMS
        if self.sms_enabled:
            test_sms = "🧪 Test SMS from Stock Trading Advisor - Notifications configured correctly!"
            results['sms'] = self.send_sms(test_sms)
        else:
            results['sms'] = False
            logger.info("SMS notifications not configured - skipping test")
        
        return results


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Notification System - Test")
    print("=" * 70)
    
    notifier = NotificationManager()
    
    print(f"\nConfiguration Status:")
    print(f"  Email: {'✓ Enabled' if notifier.email_enabled else '✗ Disabled'}")
    print(f"  SMS:   {'✓ Enabled' if notifier.sms_enabled else '✗ Disabled'}")
    
    if not notifier.email_enabled and not notifier.sms_enabled:
        print("\n⚠️  No notifications configured")
        print("To enable notifications:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your email/SMS credentials")
        print("  3. Set ENABLE_EMAIL=true or ENABLE_SMS=true")
    else:
        print("\n" + "=" * 70)
        print("Testing Notifications")
        print("=" * 70)
        
        # Test system
        print("\nSending test notifications...")
        results = notifier.test_notification_system()
        
        print("\nTest Results:")
        for channel, success in results.items():
            status = "✓ Success" if success else "✗ Failed"
            print(f"  {channel.capitalize()}: {status}")
        
        # Test buy signal
        if any(results.values()):
            print("\nSending sample BUY signal...")
            notifier.notify_buy_signal(
                symbol='AAPL',
                price=175.50,
                confidence=0.85,
                reasons='RSI oversold, MACD bullish crossover, High volume',
                target_price=201.83,
                stop_loss=166.73
            )
            
            print("✓ Sample notifications sent!")
    
    print("\n" + "=" * 70)
    print("✓ Notification system test complete!")
    print("=" * 70)