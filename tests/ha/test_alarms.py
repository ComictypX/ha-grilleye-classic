"""Execute the distributed blueprint with real HA automations, helpers and timers.

Only temperatures/reception and the notification destination are simulated.
No test sends a phone notification or changes the user's Home Assistant.
"""

from datetime import timedelta
from pathlib import Path

import pytest

from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA, ValidationStatus, async_validate_config_item,
)
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import callback
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util, yaml as yaml_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

ROOT = Path(__file__).resolve().parents[2]
PROBE = "sensor.grilleye_probe_1"
RECEPTION = "binary_sensor.grilleye_receiving"
ARMED = "input_boolean.grill_active"
QUIET = "timer.probe_1_quiet"


def blueprint_config(**overrides):
    blueprint = Blueprint(
        yaml_util.load_yaml_dict(ROOT / "blueprints/automation/grilleye_probe_alarm.yaml"),
        expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    assert blueprint.validate() is None
    values = {
        "probe": PROBE, "receiving": RECEPTION, "armed": ARMED, "snooze": QUIET,
        "upper": 80, "lower": 50, "lower_enabled": True,
        "notify_actions": [{"action": "alarm_test.record", "data": {
            "reason": "{{ alarm_reason }}", "message": "{{ alarm_message }}",
            "title": "{{ alarm_title }}", "probe": "{{ alarm_probe }}",
        }}],
    }
    values.update(overrides)
    if values.get("notify_actions") is None:
        values.pop("notify_actions")
    inputs = BlueprintInputs(blueprint, {
        "id": "grilleye_alarm_" + values["probe"].split(".")[1],
        "alias": "Grill alarm " + values["probe"],
        "use_blueprint": {"path": "grilleye/probe.yaml", "input": values},
    })
    inputs.validate()
    return inputs.async_substitute()


def set_probe(hass, value, *, probe=PROBE, unit="°C"):
    hass.states.async_set(probe, str(value), {
        "unit_of_measurement": unit, "friendly_name": "GrillEye Fühler",
    })


async def setup_alarm(hass, freezer, *, value=60, reception="on", armed=False, configs=None):
    freezer.move_to("2026-10-15T12:00:00+00:00")
    calls = []

    @callback
    def record(call):
        calls.append(dict(call.data))

    hass.services.async_register("alarm_test", "record", record)
    assert await async_setup_component(hass, "persistent_notification", {})
    set_probe(hass, value)
    hass.states.async_set(RECEPTION, reception)
    assert await async_setup_component(hass, "input_boolean", {
        "input_boolean": {"grill_active": {"name": "Grill active", "initial": armed}},
    })
    assert await async_setup_component(hass, "timer", {"timer": {
        "probe_1_quiet": {"duration": "00:05:00", "restore": True},
        "probe_2_quiet": {"duration": "00:05:00", "restore": True},
    }})
    configs = configs if configs is not None else [blueprint_config()]
    for config in configs:
        validated = await async_validate_config_item(hass, "automation", config)
        assert validated.validation_status == ValidationStatus.OK, validated.validation_error
    assert await async_setup_component(hass, "automation", {"automation": configs})
    await hass.async_start()
    await hass.async_block_till_done()
    return calls


async def arm(hass, on=True):
    await hass.services.async_call("input_boolean", "turn_on" if on else "turn_off", {
        "entity_id": ARMED,
    }, blocking=True)
    await hass.async_block_till_done()


async def quiet(hass, action="start", entity=QUIET):
    await hass.services.async_call("timer", action, {"entity_id": entity}, blocking=True)
    await hass.async_block_till_done()


async def advance(hass, freezer, seconds):
    future = dt_util.utcnow() + timedelta(seconds=seconds)
    freezer.move_to(future)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()


@pytest.mark.parametrize(("value", "reason"), [
    (80, "upper"), (80.1, "upper"), (50, "lower"), (49.9, "lower"),
    ("unknown", "probe"), ("unavailable", "probe"), ("nan", "probe"),
])
async def test_arming_already_faulted_inclusive_limits(hass, freezer, value, reason):
    calls = await setup_alarm(hass, freezer, value=value)
    assert calls == []
    await arm(hass)
    assert calls[-1]["reason"] == reason
    assert calls[-1]["probe"] == PROBE
    assert "GrillEye" in calls[-1]["title"]


async def test_crossing_and_changing_temperature_does_not_spam(hass, freezer):
    calls = await setup_alarm(hass, freezer)
    await arm(hass)
    assert calls == []
    set_probe(hass, 80)
    await hass.async_block_till_done()
    assert calls[-1]["reason"] == "upper"
    count = len(calls)
    for value in (80, 81, 82, 83, 90):
        set_probe(hass, value)
        await hass.async_block_till_done()
    assert len(calls) == count
    await advance(hass, freezer, 60)
    assert len(calls) == count + 1
    set_probe(hass, 60)
    await hass.async_block_till_done()
    count = len(calls)
    await advance(hass, freezer, 60)
    assert len(calls) == count
    set_probe(hass, 50)
    await hass.async_block_till_done()
    assert calls[-1]["reason"] == "lower"


async def test_repeat_interval_is_respected(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90, configs=[blueprint_config(repeat_minutes=5)])
    await arm(hass)
    count = len(calls)
    await advance(hass, freezer, 60)
    assert len(calls) == count
    await advance(hass, freezer, 240)
    assert len(calls) == count + 1


async def test_quiet_expires_with_real_timer_and_resumes(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90)
    await arm(hass)
    await quiet(hass)
    assert hass.states.get(QUIET).state == "active"
    count = len(calls)
    await advance(hass, freezer, 60)
    assert len(calls) == count
    await advance(hass, freezer, 240)
    assert hass.states.get(QUIET).state == "idle"
    assert len(calls) > count
    assert calls[-1]["reason"] == "upper"


@pytest.mark.parametrize("fault", ["reception", "probe"])
async def test_fault_bypasses_temperature_acknowledgement(hass, freezer, fault):
    calls = await setup_alarm(hass, freezer, value=90)
    await arm(hass)
    await quiet(hass)
    count = len(calls)
    if fault == "reception":
        hass.states.async_set(RECEPTION, "off")
    else:
        set_probe(hass, "unavailable")
    await hass.async_block_till_done()
    assert len(calls) > count
    assert calls[-1]["reason"] == fault
    count = len(calls)
    await advance(hass, freezer, 60)
    assert len(calls) > count


async def test_disarm_cancels_quiet_and_stops_alerts(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90)
    await arm(hass)
    await quiet(hass)
    await arm(hass, False)
    assert hass.states.get(QUIET).state == "idle"
    count = len(calls)
    await advance(hass, freezer, 360)
    assert len(calls) == count
    await arm(hass)
    assert len(calls) > count


async def test_clear_cancels_quiet_for_next_alarm_episode(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90)
    await arm(hass)
    await quiet(hass)
    set_probe(hass, 60)
    await hass.async_block_till_done()
    assert hass.states.get(QUIET).state == "idle"
    count = len(calls)
    set_probe(hass, 80)
    await hass.async_block_till_done()
    assert len(calls) > count


@pytest.mark.parametrize(("value", "reception", "reason"), [
    (90, "on", "upper"), (60, "off", "reception"),
    ("unavailable", "on", "probe"),
])
async def test_startup_with_armed_helper_checks_current_state(hass, freezer, value, reception, reason):
    calls = await setup_alarm(hass, freezer, value=value, reception=reception, armed=True)
    assert calls
    assert calls[-1]["reason"] == reason


async def test_automation_reload_and_recovery(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90)
    await arm(hass)
    count = len(calls)
    hass.bus.async_fire("automation_reloaded")
    await hass.async_block_till_done()
    assert len(calls) > count
    hass.states.async_set(RECEPTION, "off")
    await hass.async_block_till_done()
    assert calls[-1]["reason"] == "reception"
    hass.states.async_set(RECEPTION, "on")
    await hass.async_block_till_done()
    assert calls[-1]["reason"] == "upper"


@pytest.mark.parametrize(("overrides", "unit"), [
    ({"lower": 100, "upper": 80}, "°C"),
    ({"lower": 80, "upper": 80}, "°C"),
    ({}, "°F"),
])
async def test_invalid_limits_and_unit_mismatch_alert(hass, freezer, overrides, unit):
    calls = await setup_alarm(hass, freezer, configs=[blueprint_config(**overrides)])
    set_probe(hass, 60, unit=unit)
    await hass.async_block_till_done()
    await arm(hass)
    assert calls[-1]["reason"] == "configuration"


async def test_fahrenheit_and_disabled_temperature_limits(hass, freezer):
    calls = await setup_alarm(hass, freezer, configs=[blueprint_config(
        expected_unit="°F", upper=176, lower=122,
    )])
    set_probe(hass, 176, unit="°F")
    await hass.async_block_till_done()
    await arm(hass)
    assert calls[-1]["reason"] == "upper"
    assert "°F" in calls[-1]["message"]


async def test_disabled_limits_still_monitor_reception(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90, configs=[blueprint_config(
        upper_enabled=False, lower_enabled=False,
    )])
    await arm(hass)
    assert calls == []
    hass.states.async_set(RECEPTION, "off")
    await hass.async_block_till_done()
    assert calls[-1]["reason"] == "reception"


async def test_packet_diagnostics_do_not_repeat_notifications(hass, freezer):
    calls = await setup_alarm(hass, freezer, value=90)
    await arm(hass)
    count = len(calls)
    for timestamp in range(10):
        hass.states.async_set(RECEPTION, "on", {"last_seen": timestamp})
        await hass.async_block_till_done()
    assert len(calls) == count


async def test_two_probe_instances_have_independent_quiet_timers(hass, freezer):
    probe2 = "sensor.grilleye_probe_2"
    set_probe(hass, 90, probe=probe2)
    calls = await setup_alarm(hass, freezer, value=90, configs=[
        blueprint_config(), blueprint_config(probe=probe2, snooze="timer.probe_2_quiet"),
    ])
    await arm(hass)
    assert {call["probe"] for call in calls} == {PROBE, probe2}
    await quiet(hass)
    calls.clear()
    await advance(hass, freezer, 60)
    assert calls
    assert {call["probe"] for call in calls} == {probe2}


async def test_default_action_creates_real_persistent_notification(hass, freezer):
    from homeassistant.components.persistent_notification import async_register_callback
    notifications = {}
    unsubscribe = async_register_callback(hass, lambda update_type, updates: notifications.update(updates))
    config = blueprint_config(notify_actions=None)
    await setup_alarm(hass, freezer, value=90, configs=[config])
    await arm(hass)
    expected_id = "grilleye_" + PROBE.replace(".", "_")
    assert expected_id in notifications
    await advance(hass, freezer, 60)
    assert list(notifications) == [expected_id]
    unsubscribe()
