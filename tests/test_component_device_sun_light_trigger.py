"""
tests.test_component_device_sun_light_trigger
~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests device sun light trigger component.
"""
# pylint: disable=too-many-public-methods,protected-access
import os
import unittest

import homeassistant.loader as loader
from homeassistant.const import CONF_PLATFORM
from homeassistant.components import (
    device_tracker, light, sun, device_sun_light_trigger)


from helpers import (
    get_test_home_assistant, ensure_sun_risen, ensure_sun_set,
    trigger_device_tracker_scan)


KNOWN_DEV_PATH = None


def setUpModule():   # pylint: disable=invalid-name
    """ Initalizes a Home Assistant server. """
    global KNOWN_DEV_PATH

    hass = get_test_home_assistant()

    loader.prepare(hass)
    KNOWN_DEV_PATH = hass.config.path(
        device_tracker.KNOWN_DEVICES_FILE)

    hass.stop()

    with open(KNOWN_DEV_PATH, 'w') as fil:
        fil.write('device,name,track,picture\n')
        fil.write('DEV1,device 1,1,http://example.com/dev1.jpg\n')
        fil.write('DEV2,device 2,1,http://example.com/dev2.jpg\n')


def tearDownModule():   # pylint: disable=invalid-name
    """ Stops the Home Assistant server. """
    os.remove(KNOWN_DEV_PATH)


class TestDeviceSunLightTrigger(unittest.TestCase):
    """ Test the device sun light trigger module. """

    def setUp(self):  # pylint: disable=invalid-name
        self.hass = get_test_home_assistant()

        self.scanner = loader.get_component(
            'device_tracker.test').get_scanner(None, None)

        self.scanner.reset()
        self.scanner.come_home('DEV1')

        loader.get_component('light.test').init()

        device_tracker.setup(self.hass, {
            device_tracker.DOMAIN: {CONF_PLATFORM: 'test'}
        })

        light.setup(self.hass, {
            light.DOMAIN: {CONF_PLATFORM: 'test'}
        })

        sun.setup(self.hass, {})

    def tearDown(self):  # pylint: disable=invalid-name
        """ Stop down stuff we started. """
        self.hass.stop()

    def test_lights_on_when_sun_sets(self):
        """ Test lights go on when there is someone home and the sun sets. """

        device_sun_light_trigger.setup(
            self.hass, {device_sun_light_trigger.DOMAIN: {}})

        ensure_sun_risen(self.hass)

        light.turn_off(self.hass)

        self.hass.pool.block_till_done()

        ensure_sun_set(self.hass)

        self.hass.pool.block_till_done()

        self.assertTrue(light.is_on(self.hass))

    def test_lights_turn_off_when_everyone_leaves(self):
        """ Test lights turn off when everyone leaves the house. """
        light.turn_on(self.hass)

        self.hass.pool.block_till_done()

        device_sun_light_trigger.setup(
            self.hass, {device_sun_light_trigger.DOMAIN: {}})

        self.scanner.leave_home('DEV1')

        trigger_device_tracker_scan(self.hass)

        self.hass.pool.block_till_done()

        self.assertFalse(light.is_on(self.hass))

    def test_lights_turn_on_when_coming_home_after_sun_set(self):
        """ Test lights turn on when coming home after sun set. """
        light.turn_off(self.hass)

        ensure_sun_set(self.hass)

        self.hass.pool.block_till_done()

        device_sun_light_trigger.setup(
            self.hass, {device_sun_light_trigger.DOMAIN: {}})

        self.scanner.come_home('DEV2')
        trigger_device_tracker_scan(self.hass)

        self.hass.pool.block_till_done()

        self.assertTrue(light.is_on(self.hass))
