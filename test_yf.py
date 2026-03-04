import yfinance as yf

for symbol in ["GC=F", "CL=F", "BTC-USD"]:
    ticker = yf.Ticker(symbol)
    print(f"\n{symbol}:")
    print("regularMarketPrice:", ticker.info.get('regularMarketPrice'))
    print("currentPrice:", ticker.info.get('currentPrice'))
    hist = ticker.history(period="1d")
    if not hist.empty:
        print("hist Close:", hist['Close'].iloc[-1])
