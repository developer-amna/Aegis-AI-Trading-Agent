import pandas as pd
import numpy as np

class MarketDataCollector:
    def __init__(self):
        pass

    def calculate_rsi(self, prices, period=14):
        """Simple RSI calculation algorithm"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up/down if down != 0 else 0
            rsi[i] = 100. - 100./(1. + rs)

        return float(rsi[-1])

    def fetch_stock_payload(self, symbol: str) -> dict:
        """
        Fetches or simulates current stock metrics (Price, RSI, Sentiment)
        """
        # Simulated payload structure (Replace with yfinance or live API if required)
        mock_prices = [170.0, 171.5, 172.0, 170.8, 173.2, 174.5, 175.0, 174.0, 176.2, 178.0, 177.5, 179.0, 180.5, 182.0, 181.5]
        
        current_price = mock_prices[-1]
        calculated_rsi = self.calculate_rsi(mock_prices)
        
        # Output payload compatible with Task 4 (DebateEngine)
        payload = {
            "symbol": symbol.upper(),
            "price": round(current_price, 2),
            "rsi": round(calculated_rsi, 2),
            "sentiment_score": 0.65,  # Simulated sentiment (-1.0 to 1.0)
            "news_headline": f"Strong quarterly performance reported for {symbol.upper()}."
        }
        
        return payload

if __name__ == "__main__":
    collector = MarketDataCollector()
    data = collector.fetch_stock_payload("NVDA")
    print("Fetched Market Payload:")
    print(data)