"""Position sizer — risk-based share count calculation."""


class PositionSizer:
    """Calculate the number of shares based on fixed-percentage risk.

    Risk formula
    ------------
    risk_amount  = account_balance × risk_pct
    risk_per_share = abs(entry_price - stop_loss)
    shares = floor(risk_amount / risk_per_share)
    """

    def calculate(
        self,
        account_balance: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float,
    ) -> int:
        """Return integer share count risking *risk_pct* of *account_balance*.

        Parameters
        ----------
        account_balance : float
            Total account equity.
        risk_pct : float
            Fraction of balance to risk (e.g. 0.01 = 1 %).
        entry_price : float
            Planned entry price.
        stop_loss : float
            Planned stop-loss price.

        Returns
        -------
        int
            Number of shares (always >= 0).
        """
        if account_balance <= 0:
            raise ValueError("account_balance must be positive")
        if risk_pct <= 0 or risk_pct > 1:
            raise ValueError("risk_pct must be in (0, 1]")
        if entry_price <= 0 or stop_loss <= 0:
            raise ValueError("entry_price and stop_loss must be positive")

        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            raise ValueError("entry_price and stop_loss must differ")

        risk_amount = account_balance * risk_pct
        shares = int(risk_amount / risk_per_share)
        return max(shares, 0)
