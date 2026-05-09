"""
Currency conversion helper for Spendo.

Uses the free Open Exchange Rates-compatible endpoint from
exchangerate-api.com (no API key required for the open endpoint).

The rates are cached in Django's default cache for 1 hour to avoid
hammering the free tier.

Base currency: USD  (all Transaction.amount values are stored in USD)
"""
import json
import urllib.request
import urllib.error
from decimal import Decimal, ROUND_HALF_UP
from django.core.cache import cache

# Free endpoint — returns {"base":"USD","rates":{...}}
_RATES_URL = "https://open.er-api.com/v6/latest/USD"
_CACHE_KEY  = "spendo_fx_rates_usd"
_CACHE_TTL  = 3600  # 1 hour

# Curated list of currencies shown in the dropdown (code → display label)
SUPPORTED_CURRENCIES: dict[str, str] = {
    "USD": "🇺🇸 USD – US Dollar",
    "EUR": "🇪🇺 EUR – Euro",
    "GBP": "🇬🇧 GBP – British Pound",
    "EGP": "🇪🇬 EGP – Egyptian Pound",
    "SAR": "🇸🇦 SAR – Saudi Riyal",
    "AED": "🇦🇪 AED – UAE Dirham",
    "JPY": "🇯🇵 JPY – Japanese Yen",
    "CNY": "🇨🇳 CNY – Chinese Yuan",
    "INR": "🇮🇳 INR – Indian Rupee",
    "CAD": "🇨🇦 CAD – Canadian Dollar",
    "AUD": "🇦🇺 AUD – Australian Dollar",
    "CHF": "🇨🇭 CHF – Swiss Franc",
    "MXN": "🇲🇽 MXN – Mexican Peso",
    "BRL": "🇧🇷 BRL – Brazilian Real",
    "TRY": "🇹🇷 TRY – Turkish Lira",
    "KWD": "🇰🇼 KWD – Kuwaiti Dinar",
    "QAR": "🇶🇦 QAR – Qatari Riyal",
    "JOD": "🇯🇴 JOD – Jordanian Dinar",
    "NGN": "🇳🇬 NGN – Nigerian Naira",
    "ZAR": "🇿🇦 ZAR – South African Rand",
}


def _fetch_rates() -> dict:
    """Fetch fresh rates from the API and cache them."""
    try:
        with urllib.request.urlopen(_RATES_URL, timeout=5) as resp:
            payload = json.loads(resp.read().decode())
        rates = payload.get("rates", {})
        if rates:
            cache.set(_CACHE_KEY, rates, _CACHE_TTL)
            return rates
    except Exception:
        pass
    return {}


def get_rates() -> dict:
    """Return cached rates (or fetch if cache is cold). Never raises."""
    rates = cache.get(_CACHE_KEY)
    if not rates:
        rates = _fetch_rates()
    return rates or {}


def to_usd(amount: Decimal, currency: str) -> tuple[Decimal, Decimal]:
    """
    Convert *amount* in *currency* to USD.

    Returns:
        (usd_amount, rate_used)

    If the rate cannot be fetched the original amount is returned with rate=1
    so the app keeps working (graceful degradation).
    """
    currency = (currency or "USD").upper().strip()
    if currency == "USD":
        return amount, Decimal("1")

    rates = get_rates()
    rate = rates.get(currency)
    if not rate:
        # Graceful degradation — save as-is
        return amount, Decimal("1")

    rate_d = Decimal(str(rate))
    usd = (amount / rate_d).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return usd, rate_d
