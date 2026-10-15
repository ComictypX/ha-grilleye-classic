"""Use the real Home Assistant framework with the radio boundary mocked."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow loading custom_components in the HA test harness."""
    yield


@pytest.fixture
def bluetooth_mock():
    """No hardware, D-Bus or radio access in framework tests."""
    with (
        patch("homeassistant.components.bluetooth.async_setup", return_value=True),
        patch("homeassistant.components.bluetooth_adapters.async_setup", return_value=True),
        patch("homeassistant.components.bluetooth.async_register_callback") as changed,
        patch("homeassistant.components.bluetooth.async_register_advertisement_callback") as packets,
        patch("homeassistant.components.bluetooth.async_last_service_info", return_value=None),
    ):
        yield changed, packets
