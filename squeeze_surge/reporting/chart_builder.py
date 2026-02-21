"""Chart builder — generates Plotly JSON data for the dashboard."""

import pandas as pd
from datetime import datetime

class ChartBuilder:
    """Creates Plotly-compatible dictionary data for various trading charts."""

    @staticmethod
    def equity_curve(equity_data: list[tuple]) -> dict:
        """Returns Plotly line chart data for an equity curve."""
        if not equity_data:
            return {"x": [], "y": [], "type": "scatter", "name": "Equity"}
        
        x = [str(t[0]) for t in equity_data]
        y = [t[1] for t in equity_data]
        
        return {
            "x": x,
            "y": y,
            "type": "scatter",
            "mode": "lines",
            "name": "Portfolio Value",
            "line": {"color": "#00d1b2", "width": 2},
            "fill": "tozeroy",
            "fillcolor": "rgba(0, 209, 178, 0.1)",
        }

    @staticmethod
    def monthly_returns(trades: list[dict]) -> dict:
        """Returns Plotly bar chart data for monthly P&L."""
        if not trades:
            return {"x": [], "y": [], "type": "bar", "name": "Monthly P&L"}

        df = pd.DataFrame(trades)
        df["exit_time"] = pd.to_datetime(df["exit_time"])
        df = df.dropna(subset=["exit_time"])
        
        if df.empty:
            return {"x": [], "y": [], "type": "bar", "name": "Monthly P&L"}

        df["month"] = df["exit_time"].dt.strftime("%Y-%m")
        monthly = df.groupby("month")["pnl"].sum()

        colors = ["#ff3860" if v < 0 else "#23d160" for v in monthly.values]

        return {
            "x": list(monthly.index),
            "y": [round(v, 2) for v in monthly.values],
            "type": "bar",
            "name": "Monthly P&L",
            "marker": {"color": colors},
        }

    @staticmethod
    def drawdown_chart(equity_data: list[tuple]) -> dict:
        """Returns Plotly line chart data for drawdown percentage."""
        if not equity_data:
            return {"x": [], "y": [], "type": "scatter", "name": "Drawdown"}

        x = [str(t[0]) for t in equity_data]
        balances = [t[1] for t in equity_data]
        
        peak = balances[0]
        drawdowns = []
        for b in balances:
            if b > peak:
                peak = b
            dd = (b - peak) / peak if peak > 0 else 0
            drawdowns.append(round(dd * 100, 2))

        return {
            "x": x,
            "y": drawdowns,
            "type": "scatter",
            "mode": "lines",
            "name": "Drawdown %",
            "line": {"color": "#ff3860", "width": 1},
            "fill": "tozeroy",
            "fillcolor": "rgba(255, 56, 96, 0.1)",
        }

    @staticmethod
    def squeeze_funnel(diagnostics: dict) -> dict:
        """Returns Plotly bar chart data showing the signal filter funnel."""
        stages = [
            "total", "market_hours", "squeeze_active",
            "breakout_during_squeeze", "momentum_confirmed",
            "volume_confirmed", "final_signals"
        ]
        
        labels = [s.replace("_", " ").title() for s in stages]
        values = [diagnostics.get(s, 0) for s in stages]

        return {
            "x": labels,
            "y": values,
            "type": "bar",
            "name": "Filter Funnel",
            "marker": {
                "color": [
                    "#4a4a4a", "#6a6a6a", "#8a8a8a", 
                    "#3273dc", "#00d1b2", "#23d160", "#ffd12b"
                ]
            },
        }
