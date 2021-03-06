"""Support for Homekit sensors."""
from homekit.model.characteristics import CharacteristicsTypes

from homeassistant.const import DEVICE_CLASS_BATTERY, TEMP_CELSIUS

from . import KNOWN_DEVICES, HomeKitEntity

HUMIDITY_ICON = "mdi:water-percent"
TEMP_C_ICON = "mdi:thermometer"
BRIGHTNESS_ICON = "mdi:brightness-6"
CO2_ICON = "mdi:periodic-table-co2"

UNIT_PERCENT = "%"
UNIT_LUX = "lux"
UNIT_CO2 = "ppm"


class HomeKitHumiditySensor(HomeKitEntity):
    """Representation of a Homekit humidity sensor."""

    def __init__(self, *args):
        """Initialise the entity."""
        super().__init__(*args)
        self._state = None

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT]

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Humidity"

    @property
    def icon(self):
        """Return the sensor icon."""
        return HUMIDITY_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return UNIT_PERCENT

    def _update_relative_humidity_current(self, value):
        self._state = value

    @property
    def state(self):
        """Return the current humidity."""
        return self._state


class HomeKitTemperatureSensor(HomeKitEntity):
    """Representation of a Homekit temperature sensor."""

    def __init__(self, *args):
        """Initialise the entity."""
        super().__init__(*args)
        self._state = None

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.TEMPERATURE_CURRENT]

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Temperature"

    @property
    def icon(self):
        """Return the sensor icon."""
        return TEMP_C_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return TEMP_CELSIUS

    def _update_temperature_current(self, value):
        self._state = value

    @property
    def state(self):
        """Return the current temperature in Celsius."""
        return self._state


class HomeKitLightSensor(HomeKitEntity):
    """Representation of a Homekit light level sensor."""

    def __init__(self, *args):
        """Initialise the entity."""
        super().__init__(*args)
        self._state = None

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.LIGHT_LEVEL_CURRENT]

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Light Level"

    @property
    def icon(self):
        """Return the sensor icon."""
        return BRIGHTNESS_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return UNIT_LUX

    def _update_light_level_current(self, value):
        self._state = value

    @property
    def state(self):
        """Return the current light level in lux."""
        return self._state


class HomeKitCarbonDioxideSensor(HomeKitEntity):
    """Representation of a Homekit Carbon Dioxide sensor."""

    def __init__(self, *args):
        """Initialise the entity."""
        super().__init__(*args)
        self._state = None

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [CharacteristicsTypes.CARBON_DIOXIDE_LEVEL]

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} CO2"

    @property
    def icon(self):
        """Return the sensor icon."""
        return CO2_ICON

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return UNIT_CO2

    def _update_carbon_dioxide_level(self, value):
        self._state = value

    @property
    def state(self):
        """Return the current CO2 level in ppm."""
        return self._state


class HomeKitBatterySensor(HomeKitEntity):
    """Representation of a Homekit battery sensor."""

    def __init__(self, *args):
        """Initialise the entity."""
        super().__init__(*args)
        self._state = None
        self._low_battery = False
        self._charging = False

    def get_characteristic_types(self):
        """Define the homekit characteristics the entity is tracking."""
        return [
            CharacteristicsTypes.BATTERY_LEVEL,
            CharacteristicsTypes.STATUS_LO_BATT,
            CharacteristicsTypes.CHARGING_STATE,
        ]

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_BATTERY

    @property
    def name(self):
        """Return the name of the device."""
        return f"{super().name} Battery"

    @property
    def icon(self):
        """Return the sensor icon."""
        if not self.available or self.state is None:
            return "mdi:battery-unknown"

        # This is similar to the logic in helpers.icon, but we have delegated the
        # decision about what mdi:battery-alert is to the device.
        icon = "mdi:battery"
        if self._charging and self.state > 10:
            percentage = int(round(self.state / 20 - 0.01)) * 20
            icon += f"-charging-{percentage}"
        elif self._charging:
            icon += "-outline"
        elif self._low_battery:
            icon += "-alert"
        elif self.state < 95:
            percentage = max(int(round(self.state / 10 - 0.01)) * 10, 10)
            icon += f"-{percentage}"

        return icon

    @property
    def unit_of_measurement(self):
        """Return units for the sensor."""
        return UNIT_PERCENT

    def _update_battery_level(self, value):
        self._state = value

    def _update_status_lo_batt(self, value):
        self._low_battery = value == 1

    def _update_charging_state(self, value):
        # 0 = not charging
        # 1 = charging
        # 2 = not chargeable
        self._charging = value == 1

    @property
    def state(self):
        """Return the current battery level percentage."""
        return self._state


ENTITY_TYPES = {
    "humidity": HomeKitHumiditySensor,
    "temperature": HomeKitTemperatureSensor,
    "light": HomeKitLightSensor,
    "carbon-dioxide": HomeKitCarbonDioxideSensor,
    "battery": HomeKitBatterySensor,
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Homekit sensors."""
    hkid = config_entry.data["AccessoryPairingID"]
    conn = hass.data[KNOWN_DEVICES][hkid]

    def async_add_service(aid, service):
        entity_class = ENTITY_TYPES.get(service["stype"])
        if not entity_class:
            return False
        info = {"aid": aid, "iid": service["iid"]}
        async_add_entities([entity_class(conn, info)], True)
        return True

    conn.add_listener(async_add_service)
