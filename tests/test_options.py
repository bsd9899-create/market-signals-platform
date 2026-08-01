"""
tests/test_options.py
--------------------------
اختبار حقيقي لطبقة الخيارات - MockOptionsProvider فقط (بلا أي API خارجي).
"""

from __future__ import annotations

import inspect

import pytest

from app.infrastructure.options.exceptions import OptionsUnavailableError
from app.infrastructure.options.liquidity import LiquidityLevel, classify_liquidity
from app.infrastructure.options.models import OptionContract
from app.infrastructure.options.providers import mock_provider as mock_provider_module
from app.infrastructure.options.providers.mock_provider import MockOptionsProvider
from app.infrastructure.options.services.options_service import OptionsService


def test_mock_options_provider_returns_chain_with_contracts() -> None:
    provider = MockOptionsProvider()
    chain = provider.get_option_chain("AAPL")
    assert chain.symbol == "AAPL"
    assert len(chain.contracts) > 0
    assert all(c.option_type in ("CALL", "PUT") for c in chain.contracts)


def test_mock_options_provider_greeks_placeholder_fields_present() -> None:
    provider = MockOptionsProvider()
    chain = provider.get_option_chain("AAPL")
    contract = chain.contracts[0]
    assert isinstance(contract.gamma, float)
    assert isinstance(contract.theta, float)
    assert isinstance(contract.vega, float)
    assert isinstance(contract.rho, float)


def test_mock_options_provider_invalid_expiration_raises() -> None:
    provider = MockOptionsProvider()
    with pytest.raises(OptionsUnavailableError):
        provider.get_option_chain("AAPL", expiration="1999-01-01")


def test_mock_options_provider_get_expirations() -> None:
    provider = MockOptionsProvider()
    expirations = provider.get_expirations("AAPL")
    assert len(expirations) == 3


def test_mock_options_provider_health_check() -> None:
    assert MockOptionsProvider().health_check() is True


def test_mock_options_provider_no_network_dependency() -> None:
    source = inspect.getsource(mock_provider_module)
    for forbidden in ("requests", "httpx", "urllib", "socket", "aiohttp"):
        assert forbidden not in source


def test_options_service_delegates_to_provider() -> None:
    service = OptionsService(MockOptionsProvider())
    chain = service.get_option_chain("AAPL")
    assert chain.symbol == "AAPL"


def test_options_service_health_check() -> None:
    assert OptionsService(MockOptionsProvider()).health_check() is True


def _contract(volume: int, open_interest: int) -> OptionContract:
    return OptionContract(
        symbol="AAPL", option_type="CALL", strike=100, expiration="2026-12-31",
        bid=1.0, ask=1.1, last=1.05, volume=volume, open_interest=open_interest, implied_volatility=0.3, delta=0.5,
    )


def test_classify_liquidity_high() -> None:
    assert classify_liquidity(_contract(volume=600, open_interest=1200)) == LiquidityLevel.HIGH


def test_classify_liquidity_low_by_volume() -> None:
    assert classify_liquidity(_contract(volume=10, open_interest=1200)) == LiquidityLevel.LOW


def test_classify_liquidity_low_by_open_interest() -> None:
    assert classify_liquidity(_contract(volume=600, open_interest=50)) == LiquidityLevel.LOW


def test_classify_liquidity_medium() -> None:
    assert classify_liquidity(_contract(volume=200, open_interest=500)) == LiquidityLevel.MEDIUM
