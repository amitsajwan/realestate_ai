"""PF-7: numbers our code calculates from other facts (level "measured", source "calc"). Code calculates, models write.

The EMI is an illustration: its assumptions (loan share, rate, years) travel with it so a post can state them."""
from typing import Any, Dict, List, Optional

from .facts import Reading

SQFT_PER_GUNTHA = 1089          # 1 guntha = 121 sq yd = 1,089 sq ft (Maharashtra land measure)
SQFT_PER_SQM = 10.7639
EMI_LOAN_SHARE = 0.8            # banks usually lend up to 80% of the value; the buyer pays the rest
EMI_RATE = 8.5                  # % a year: an illustrative home-loan rate, stated on the card
EMI_YEARS = 20


def per_sqft(price_inr: int, sqft: int) -> int:
    return round(price_inr / sqft)


def emi(principal: float, annual_rate_pct: float, years: int) -> int:
    r, n = annual_rate_pct / 12 / 100, years * 12
    return round(principal * r * (1 + r) ** n / ((1 + r) ** n - 1)) if r else round(principal / n)


def guntha(sqft: float) -> float:
    return round(sqft / SQFT_PER_GUNTHA, 2)


def readings(values: Dict[str, Any], now=None) -> List[Reading]:
    """Calculated readings from usable values: price_inr, carpet_sqft or plot_sqft."""
    out: List[Reading] = []
    price: Optional[int] = values.get("price_inr")
    area: Optional[int] = values.get("plot_sqft") or values.get("carpet_sqft")
    if price and area:
        out.append(Reading("price_per_sqft", per_sqft(price, area), "calc", "", now))
    if values.get("plot_sqft"):
        out.append(Reading("plot_guntha", guntha(values["plot_sqft"]), "calc", "", now))
        out.append(Reading("plot_sqm", round(values["plot_sqft"] / SQFT_PER_SQM), "calc", "", now))
    if price and values.get("transaction", "sale") != "rent":
        loan = price * EMI_LOAN_SHARE
        out.append(Reading("emi", {"emi": emi(loan, EMI_RATE, EMI_YEARS), "loan": round(loan), "rate": EMI_RATE,
                                   "years": EMI_YEARS}, "calc", "", now))
    return out
