import math


def pct_format(num: float):
    return "{:,.0%}".format(num) if not math.isnan(num) else ""
