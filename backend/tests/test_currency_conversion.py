import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.services.currency import CurrencyService

@pytest.mark.asyncio
async def test_parse_budget_string():
    # Test range
    assert CurrencyService.parse_budget_string("USD 100 - 250") == (100.0, 250.0)
    # Test single value
    assert CurrencyService.parse_budget_string("USD 500") == (500.0, 500.0)
    # Test with dots (milhar)
    assert CurrencyService.parse_budget_string("USD 1.000 - 2.500") == (1000.0, 2500.0)
    # Test empty/invalid
    assert CurrencyService.parse_budget_string("") == (None, None)
    assert CurrencyService.parse_budget_string("Something else") == (None, None)

@pytest.mark.asyncio
async def test_convert_to_brl():
    # Mock the rate to be 5.0 for stability
    with patch.object(CurrencyService, 'get_usd_brl_rate', return_value=5.0):
        # Range conversion
        res = await CurrencyService.convert_to_brl("USD 100 - 200")
        assert res == "R$ 500 - 1.000"
        
        # Single value conversion
        res = await CurrencyService.convert_to_brl("USD 100")
        assert res == "R$ 500,00" # Single value uses 2 decimal places in some cases or formatted. 
        # Actually in my implementation for single val I used :.2f
        
        # Test with original BRL (should not change)
        res = await CurrencyService.convert_to_brl("R$ 1.000")
        assert res == "R$ 1.000"

@pytest.mark.asyncio
async def test_formatting_logic():
    # Testing the manual decimal/thousand separator formatting
    with patch.object(CurrencyService, 'get_usd_brl_rate', return_value=5.50):
        res = await CurrencyService.convert_to_brl("USD 1000")
        # 1000 * 5.5 = 5500.00 -> R$ 5.500,00
        assert res == "R$ 5.500,00"
