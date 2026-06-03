import time
import sys
import yfinance as yf

# Top holdings within the SOXL ETF
SOXL_COMPONENTS = ["NVDA", "AVGO", "AMD", "MU", "INTC", "MRVL", "QCOM", "TXN", "AMAT", "TSM"]

def fetch_market_caps():
    """Fetches market caps once at startup to determine company weights."""
    print("[Initialization] Fetching market capitalizations to weight stocks...", flush=True)
    market_caps = {}
    total_market_cap = 0
    
    for ticker in SOXL_COMPONENTS:
        try:
            stock = yf.Ticker(ticker)
            mcap = stock.info.get('marketCap')
            if mcap:
                market_caps[ticker] = mcap
                total_market_cap += mcap
            else:
                market_caps[ticker] = 100_000_000_000 
                total_market_cap += 100_000_000_000
        except Exception:
            market_caps[ticker] = 100_000_000_000
            total_market_cap += 100_000_000_000
            
    return market_caps, total_market_cap

def fetch_live_prices():
    """Rapidly fetches individual 1-minute close prices for the assets."""
    prices = {}
    for ticker in SOXL_COMPONENTS:
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period="1d", interval="1m")
            if not todays_data.empty:
                prices[ticker] = todays_data['Close'].iloc[-1]
        except Exception:
            pass 
    return prices

def run_tracking_session():
    print("\n" + "="*75)
    print("   HIGH-FREQUENCY (30s) INDIVIDUAL STOCK TRACKER (WEIGHTED ORDER)   ")
    print("="*75)
    
    market_caps, total_market_cap = fetch_market_caps()
    
    # Sort tickers by weight so mega-caps (like NVDA) always print at the top
    sorted_tickers = sorted(SOXL_COMPONENTS, key=lambda x: market_caps[x], reverse=True)
    
    print("\n[Data Fetch] Pulling initial baseline prices...")
    start_prices = fetch_live_prices()
    last_prices = start_prices.copy()
    
    print(f"\n[Tracking Active] Updates will print every 30 seconds. Press Ctrl+C to halt.")
    print("="*75)

    interval_count = 1
    thirty_seconds = 30

    try:
        while True:
            time.sleep(thirty_seconds)
            current_prices = fetch_live_prices()
            
            print(f"\n--- [Interval #{interval_count} | {interval_count * 30}s Mark] ---")
            print(f"{'Ticker':<7} | {'Weight':<6} | {'Price':<9} | {'30s Move':<16} | {'Session Move':<16}")
            print("-" * 75)
            
            for ticker in sorted_tickers:
                # Calculate weight percentage relative to our tracked basket
                weight_pct = (market_caps[ticker] / total_market_cap) * 100
                
                curr_p = current_prices.get(ticker)
                start_p = start_prices.get(ticker)
                last_p = last_prices.get(ticker)
                
                # Safeguard if a specific ticker fails an API poll interval
                if curr_p is None or start_p is None or last_p is None:
                    print(f"{ticker:<7} | {weight_pct:>5.1f}% | {'Data Lag':<9} | {'--':<16} | {'--':<16}")
                    continue
                
                # Calculate 30-second rolling variation
                diff_30s = curr_p - last_p
                pct_30s = (diff_30s / last_p) * 100 if last_p else 0
                dir_30s = "▲" if diff_30s >= 0 else "▼"
                
                # Calculate cumulative session variation
                diff_sess = curr_p - start_p
                pct_sess = (diff_sess / start_p) * 100 if start_p else 0
                dir_sess = "▲" if diff_sess >= 0 else "▼"
                
                print(f"{ticker:<7} | {weight_pct:>5.1f}% | ${curr_p:>7.2f} | {dir_30s} ${diff_30s:>+5.2f} ({pct_30s:>+5.2f}%) | {dir_sess} ${diff_sess:>+5.2f} ({pct_sess:>+5.2f}%)")
            
            # Save historical state for the next 30-second delta calculation
            last_prices = current_prices.copy()
            interval_count += 1
            print("="*75)

    except KeyboardInterrupt:
        print("\n\nTracking loop paused by user.")

def main():
    while True:
        run_tracking_session()
        print("\n" + "="*75)
        user_choice = input("Press [Enter] to exit, or type 'R' to rerun: ").strip().lower()
        if user_choice != 'r':
            print("\nExiting program. Happy trading!")
            sys.exit()

if __name__ == "__main__":
    main()
