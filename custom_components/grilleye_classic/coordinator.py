"""Passive BLE receiver with an independent valid-measurement deadline."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .parser import Reading, parse_payload, payload_from_raw

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GrillEyeData:
    """Latest valid measurement, retaining its timestamp across a timeout."""

    reading: Reading | None = None
    rssi: int | None = None
    last_seen: datetime | None = None
    source: str | None = None
    fresh: bool = False


class GrillEyeCoordinator(DataUpdateCoordinator[GrillEyeData]):
    """Receive every advertisement, including identical temperatures."""

    def __init__(
        self, hass: HomeAssistant, address: str, timeout: int, *, zero_is_valid: bool = False,
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.address = address
        self.timeout = timeout
        self.zero_is_valid = zero_is_valid
        self.data = GrillEyeData()
        self._last_packet_time = float("-inf")
        self._cancel_deadline: Callable[[], None] | None = None
        self._unsubscribers: list[Callable[[], None]] = []

    @callback
    def async_start(self) -> None:
        """Opt into passive non-connectable data and subscribe to every packet.

        Do not bootstrap measurements from cache: a restart must wait for a
        newly received advertisement before showing a current temperature.
        """
        self._unsubscribers.append(bluetooth.async_register_callback(
            self.hass, self._async_changed,
            {"address": self.address, "connectable": False},
            bluetooth.BluetoothScanningMode.PASSIVE,
        ))
        self._unsubscribers.append(bluetooth.async_register_advertisement_callback(
            self.hass, self._async_received, self.address,
        ))

    @callback
    def _async_changed(
        self, info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Passive scan registration only; cached/changed frames are not freshness."""

    @callback
    def _async_received(self, info: bluetooth.BluetoothServiceInfoBleak) -> None:
        """Process a live frame from any local or remote scanner."""
        if info.address.upper() != self.address:
            return
        now = bluetooth.MONOTONIC_TIME()
        age = now - info.time
        if age < -1 or age >= self.timeout or info.time <= self._last_packet_time:
            return
        raw = getattr(info, "raw", None)
        payload = (
            payload_from_raw(raw) if raw is not None
            else info.manufacturer_data.get(0)
        )
        if payload is None or (reading := parse_payload(
            payload, self.address, zero_is_valid=self.zero_is_valid,
        )) is None:
            return
        self._last_packet_time = info.time
        if self._cancel_deadline is not None:
            self._cancel_deadline()
        self._cancel_deadline = async_call_later(
            self.hass, self.timeout - max(age, 0), self._async_expired,
        )
        self.async_set_updated_data(GrillEyeData(
            reading=reading, rssi=info.rssi,
            last_seen=dt_util.utcnow() - timedelta(seconds=max(age, 0)),
            source=info.source, fresh=True,
        ))

    @callback
    def _async_expired(self, _now: datetime) -> None:
        self._cancel_deadline = None
        data = self.data
        self.async_set_updated_data(GrillEyeData(
            reading=data.reading, rssi=data.rssi, last_seen=data.last_seen,
            source=data.source, fresh=False,
        ))

    @callback
    def async_stop(self) -> None:
        """Remove all scanner subscriptions and the deadline."""
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()
        if self._cancel_deadline is not None:
            self._cancel_deadline()
            self._cancel_deadline = None
