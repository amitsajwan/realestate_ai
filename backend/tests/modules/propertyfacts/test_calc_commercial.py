"""An office is not sold on a home loan: no EMI sum for it, and none read back from facts gathered before this rule."""
from app.modules.propertyfacts import calc


def test_a_shop_or_office_gets_no_emi_and_a_flat_still_does():
    keys = lambda kind: [r.key for r in calc.readings({"price_inr": 5_500_000, "carpet_sqft": 445, "property_type": kind})]
    assert "emi" not in keys("office") and "emi" not in keys("shop")
    assert "emi" in keys("apartment")
