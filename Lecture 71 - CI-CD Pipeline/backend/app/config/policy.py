from typing import Final

RETURN_WINDOW_DAYS: Final = 30

GRACE_PERIOD_END_DAYS: Final = 37

DAMAGE_REASONS: Final = frozenset({"damaged", "defective"})


MAX_REFUNDS_PER_ITEM: Final = 1

WARRANTY_YEARS: Final = {"boots": 1, "jackets": 1, "tents": 2, "backpacks": 2}

REFUND_METHOD: Final = "original payment method"
REFUND_TIMING_BUSINESS_DAYS: Final = (5, 7)

HIGH_VALUE_THRESHOLD_CENTS: Final = 20_000

EMAIL_MATCH_REQUIRED: Final = True
