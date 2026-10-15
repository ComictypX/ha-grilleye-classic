"""Validate the supplied UI automation examples with HA's real config schema."""

from pathlib import Path

from homeassistant.components.automation import CONFIG_SCHEMA
import pytest
import yaml


@pytest.mark.parametrize("name", ["temperature_alarm.yaml", "reception_alarm.yaml"])
def test_example_schema(name):
    root = Path(__file__).resolve().parents[2]
    automation = yaml.safe_load((root / "examples" / name).read_text(encoding="utf-8"))
    result = CONFIG_SCHEMA({"automation": [automation]})
    assert result["automation"]
