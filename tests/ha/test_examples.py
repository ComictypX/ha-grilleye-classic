"""Validate the supplied UI automation examples with HA's real config schema."""

from pathlib import Path

from homeassistant.components.automation.config import async_validate_config_item, ValidationStatus
import pytest
import yaml


@pytest.mark.parametrize("name", ["temperature_alarm.yaml", "reception_alarm.yaml"])
async def test_example_schema(hass, name):
    root = Path(__file__).resolve().parents[2]
    automation = yaml.safe_load((root / "examples" / name).read_text(encoding="utf-8"))
    result = await async_validate_config_item(hass, "automation", automation)
    assert result.validation_status == ValidationStatus.OK
