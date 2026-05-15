from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import yfinance as yf


# Input schemas

class StockAnalysisInput(BaseModel):
    """
    Input schema for the fundamental analysis tool.
    Enforces that a ticker symbol is provided as a string.
    """

    ticker: str = Field(
        ...,
        description="The stock ticker symbol to analyze, e.g., 'AAPL' for Apple Inc."
    )


class CompareStocksInput(BaseModel):
    """
    Input schema for the compare stocks tool.
    Requires two distinct tickers: ticker_a and ticker_b.
    """

    ticker_a: str = Field(
        ...,
        description="The first stock ticker to analyze"
    )

    ticker_b: str = Field(
        ...,
        description="The second stock ticker to analyze against"
    )


class FundamentalAnalysisTool(BaseTool):
    """
    This tool acts as a screening analyst, providing raw financial data
    to determine whether a stock is undervalued, overvalued, or volatile.
    """

    name: str = "Fetch Fundamental Metrics"

    description: str = (
        "Fetches key metrics for a specific stock ticker. "
        "Useful for quantitative analysis. Returns JSON-formatted data "
        "including P/E ratio, Beta, Market Cap, EPS, and 52-week high/low."
    )

    args_schema: Type[BaseModel] = StockAnalysisInput

    def _run(self, ticker: str) -> str:
        """
        Executes data fetching from Yahoo Finance.

        Args:
            ticker (str): Stock ticker symbol.

        Returns:
            Stringified dictionary containing selected metrics,
            or an error message if fetching fails.
        """
        try:
            stock = yf.Ticker(ticker)
            info: Dict[str, Any] = stock.info

            metrics = {
                "Ticker": ticker.upper(),
                "Current Price": info.get("currentPrice", "N/A"),
                "Market Cap": info.get("marketCap", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "Forward P/E": info.get("forwardPE", "N/A"),
                "PEG Ratio": info.get("pegRatio", "N/A"),
                "Beta (Volatility)": info.get("beta", "N/A"),
                "EPS (Trailing)": info.get("trailingEps", "N/A"),
                "52-Week High": info.get("fiftyTwoWeekHigh", "N/A"),
                "52-Week Low": info.get("fiftyTwoWeekLow", "N/A"),
                "Analyst Recommendation": info.get("recommendationKey", "N/A"),
            }

            return str(metrics)

        except Exception as e:
            return f"Error fetching data for {ticker}: {str(e)}"


class CompareStocksTool(BaseTool):
    """
    This tool compares two stocks based on their historical performance
    and provides a side-by-side comparison of annual percentage returns.
    """

    name: str = "Compare Two Stocks"

    description: str = (
        "Compares the historical performance of two stocks over the last 365 days. "
        "Returns the percentage gain or loss for each stock."
    )

    args_schema: Type[BaseModel] = CompareStocksInput

    def _run(self, ticker_a: str, ticker_b: str) -> str:
        """
        Fetches historical data and calculates percentage return using:
        ((last_price - first_price) / first_price) * 100
        """
        try:
            tickers = [ticker_a.upper(), ticker_b.upper()]
            data = yf.download(tickers, period="1y", progress=False)["Close"]

            def calculate_return(symbol: str) -> float:
                start_price = data[symbol].dropna().iloc[0]
                end_price = data[symbol].dropna().iloc[-1]
                return ((end_price - start_price) / start_price) * 100

            return_a = calculate_return(ticker_a.upper())
            return_b = calculate_return(ticker_b.upper())

            comparison = {
                ticker_a.upper(): {
                    "1-Year Return (%)": round(return_a, 2)
                },
                ticker_b.upper(): {
                    "1-Year Return (%)": round(return_b, 2)
                },
                "Better Performer": (
                    ticker_a.upper() if return_a > return_b else ticker_b.upper()
                ),
            }

            return str(comparison)

        except Exception as e:
            return f"Error comparing {ticker_a} and {ticker_b}: {str(e)}"