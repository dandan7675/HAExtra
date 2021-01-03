"""
Platform for a Generic Modbus Thermostat.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.modbus/
"""

import logging
import struct

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    SUPPORT_AUX_HEAT, SUPPORT_FAN_MODE, SUPPORT_PRESET_MODE, SUPPORT_SWING_MODE,
    SUPPORT_TARGET_HUMIDITY, SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_HEAT_COOL,
    HVAC_MODE_AUTO,  HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY,
    CURRENT_HVAC_OFF, CURRENT_HVAC_HEAT, CURRENT_HVAC_COOL, CURRENT_HVAC_IDLE,
    CURRENT_HVAC_DRY, CURRENT_HVAC_FAN,
)
from homeassistant.const import (
    CONF_NAME, CONF_SLAVE, CONF_OFFSET, CONF_STRUCTURE, ATTR_TEMPERATURE)
from homeassistant.components.modbus.const import (
    CONF_HUB, DEFAULT_HUB, MODBUS_DOMAIN)
from homeassistant.helpers.event import async_call_later
import homeassistant.components.modbus as modbus
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['modbus']

CONF_AUX_HEAT_OFF_VALUE = 'aux_heat_off_value'
CONF_AUX_HEAT_ON_VALUE = 'aux_heat_on_value'
CONF_COUNT = 'count'
CONF_DATA_TYPE = 'data_type'
CONF_FAN_MODES = 'fan_modes'
CONF_HVAC_MODES = 'hvac_modes'
CONF_HVAC_OFF_VALUE = 'hvac_off_value'
CONF_HVAC_ON_VALUE = 'hvac_on_value'
CONF_PRESET_MODES = 'preset_mode'
CONF_REGISTER = 'register'
CONF_REGISTER_TYPE = 'register_type'
CONF_REGISTERS = 'registers'
CONF_REVERSE_ORDER = 'reverse_order'
CONF_SCALE = 'scale'
CONF_SWING_MODES = 'swing_modes'

REG_AUX_HEAT = 'aux_heat'
REG_FAN_MODE = 'fan_mode'
REG_HUMIDITY = 'humidity'
REG_HVAC_MODE = 'hvac_mode'
REG_HVAC_OFF = 'hvac_off'
REG_PRESET_MODE = 'preset_mode'
REG_SWING_MODE = 'swing_mode'
REG_TARGET_HUMIDITY = 'target_humidity'
REG_TARGET_TEMPERATURE = 'target_temperature'
REG_TEMPERATURE = 'temperature'

REGISTER_TYPE_HOLDING = 'holding'
REGISTER_TYPE_INPUT = 'input'
REGISTER_TYPE_COIL = 'coil'

DATA_TYPE_INT = 'int'
DATA_TYPE_UINT = 'uint'
DATA_TYPE_FLOAT = 'float'
DATA_TYPE_CUSTOM = 'custom'

SUPPORTED_FEATURES = {
    REG_AUX_HEAT: SUPPORT_AUX_HEAT,
    REG_FAN_MODE: SUPPORT_FAN_MODE,
    REG_HUMIDITY: 0,
    REG_HVAC_MODE: 0,
    REG_HVAC_OFF: 0,
    REG_PRESET_MODE: SUPPORT_PRESET_MODE,
    REG_SWING_MODE: SUPPORT_SWING_MODE,
    REG_TARGET_HUMIDITY: SUPPORT_TARGET_HUMIDITY,
    REG_TARGET_TEMPERATURE: SUPPORT_TARGET_TEMPERATURE,
    REG_TEMPERATURE: 0,
}

HVAC_ACTIONS = {
    HVAC_MODE_OFF: CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT: CURRENT_HVAC_HEAT,
    HVAC_MODE_COOL: CURRENT_HVAC_COOL,
    HVAC_MODE_HEAT_COOL: CURRENT_HVAC_IDLE,  # ?
    HVAC_MODE_AUTO: CURRENT_HVAC_IDLE,  # ?
    HVAC_MODE_DRY: CURRENT_HVAC_DRY,
    HVAC_MODE_FAN_ONLY: CURRENT_HVAC_FAN,
}

DEFAULT_NAME = 'Modbus'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HUB, default=DEFAULT_HUB): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): vol.Any(cv.string, list),

    vol.Optional(CONF_FAN_MODES, default={}): dict,
    vol.Optional(CONF_HVAC_MODES, default={}): dict,
    vol.Optional(CONF_PRESET_MODES, default={}): dict,
    vol.Optional(CONF_SWING_MODES, default={}): dict,
    vol.Optional(CONF_AUX_HEAT_OFF_VALUE, default=0): int,
    vol.Optional(CONF_AUX_HEAT_ON_VALUE, default=1): int,
    vol.Optional(CONF_HVAC_OFF_VALUE, default=0): int,
    vol.Optional(CONF_HVAC_ON_VALUE, default=1): int,

    vol.Optional(REG_AUX_HEAT): dict,
    vol.Optional(REG_FAN_MODE): dict,
    vol.Optional(REG_HUMIDITY): dict,
    vol.Optional(REG_HVAC_MODE): dict,
    vol.Optional(REG_HVAC_OFF): dict,
    vol.Optional(REG_PRESET_MODE): dict,
    vol.Optional(REG_SWING_MODE): dict,
    vol.Optional(REG_TARGET_HUMIDITY): dict,
    vol.Optional(REG_TARGET_TEMPERATURE): dict,
    vol.Optional(REG_TEMPERATURE): dict,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Modbus Thermostat Platform."""
    name = config.get(CONF_NAME)
    hub_name = config.get(CONF_HUB)
    hub = hass.data[MODBUS_DOMAIN][hub_name]

    ModbusClimate._fan_modes = config.get(CONF_FAN_MODES)
    ModbusClimate._hvac_modes = config.get(CONF_HVAC_MODES)
    ModbusClimate._preset_modes = config.get(CONF_PRESET_MODES)
    ModbusClimate._swing_modes = config.get(CONF_SWING_MODES)
    ModbusClimate._unit = hass.config.units.temperature_unit
    ModbusClimate._hvac_off_value = config.get(CONF_HVAC_OFF_VALUE)
    ModbusClimate._hvac_on_value = config.get(CONF_HVAC_ON_VALUE)
    ModbusClimate._aux_heat_on_value = config.get(CONF_AUX_HEAT_ON_VALUE)
    ModbusClimate._aux_heat_off_value = config.get(CONF_AUX_HEAT_OFF_VALUE)

    data_types = {DATA_TYPE_INT: {1: 'h', 2: 'i', 4: 'q'}}
    data_types[DATA_TYPE_UINT] = {1: 'H', 2: 'I', 4: 'Q'}
    data_types[DATA_TYPE_FLOAT] = {1: 'e', 2: 'f', 4: 'd'}

    mods = {}
    for prop in SUPPORTED_FEATURES:
        mod = config.get(prop)
        if not mod:
            continue

        count = mod[CONF_COUNT] if CONF_COUNT in mod else 1
        data_type = mod.get(CONF_DATA_TYPE)
        if data_type != DATA_TYPE_CUSTOM:
            try:
                mod[CONF_STRUCTURE] = '>{}'.format(data_types[DATA_TYPE_INT if data_type is None else data_type][count])
            except KeyError:
                _LOGGER.error("Unable to detect data type for %s", prop)
                continue

        try:
            size = struct.calcsize(mod[CONF_STRUCTURE])
        except struct.error as err:
            _LOGGER.error(
                "Error in sensor %s structure: %s", prop, err)
            continue

        if count * 2 != size:
            _LOGGER.error(
                "Structure size (%d bytes) mismatch registers count "
                "(%d words)", size, count)
            continue

        mods[prop] = mod

    if not mods:
        _LOGGER.error("Invalid config %s: no modbus items", name)
        return

    def has_valid_register(mods, index):
        """Check valid register."""
        for prop in mods:
            registers = mods[prop].get(CONF_REGISTERS)
            if not registers or index >= len(registers):
                return False
        return True

    devices = []
    for index in range(100):
        if not has_valid_register(mods, index):
            break
        devices.append(ModbusClimate(hub, name, mods, index))

    if not devices:
        for prop in mods:
            if CONF_REGISTER not in mods[prop]:
                _LOGGER.error("Invalid config %s/%s: no register", name, prop)
                return
        devices.append(ModbusClimate(hub, name, mods))

    add_devices(devices, True)


class ModbusClimate(ClimateEntity):
    """Representation of a Modbus climate device."""

    _exception = 0

    def __init__(self, hub, name, mods, index=-1):
        """Initialize the climate device."""
        self._hub = hub
        self._name = name[0 if index == -1 else index] if isinstance(name, list) else (name + str(index + 1) if index != -1 else name)
        self._index = index
        self._regs = mods
        self._values = {}
        self._last_on_operation = None
        self._skip_update = False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        features = 0
        for prop in self._regs:
            features |= SUPPORTED_FEATURES[prop]
        return features

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return ModbusClimate._unit

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.get_value(REG_TEMPERATURE)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.get_value(REG_TARGET_TEMPERATURE)

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self.get_value(REG_HUMIDITY)

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self.get_value(REG_TARGET_HUMIDITY)

    @property
    def hvac_action(self):
        """Return current operation ie. heat, cool, idle."""
        return HVAC_ACTIONS[self.hvac_mode]

    @property
    def hvac_mode(self):
        if REG_HVAC_OFF in self._regs:
            if self.get_value(REG_HVAC_OFF) == ModbusClimate._hvac_off_value:
                return HVAC_MODE_OFF
        hvac_mode = self.get_mode(
            ModbusClimate._hvac_modes, REG_HVAC_MODE) or HVAC_MODE_OFF
        if hvac_mode != HVAC_MODE_OFF:
            self._last_on_operation = hvac_mode
        return hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return list(ModbusClimate._hvac_modes)

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self.get_mode(ModbusClimate._fan_modes, REG_FAN_MODE)

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return list(ModbusClimate._fan_modes)

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return self.get_mode(ModbusClimate._swing_modes, REG_SWING_MODE)

    @property
    def swing_modes(self):
        """List of available swing modes."""
        return list(ModbusClimate._swing_modes)

    @property
    def preset_mode(self):
        """Return preset mode setting."""
        return self.get_value(REG_PRESET_MODE)

    @property
    def preset_modes(self):
        """List of available swing modes."""
        return list(ModbusClimate._preset_modes)

    @property
    def is_aux_heat(self):
        """Return true if aux heat is on."""
        return self.get_value(REG_AUX_HEAT) == ModbusClimate._aux_heat_on_value

    def reset(self):
        """Initialize USR module"""
        import socket
        import time
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((self._hub._client.host, self._hub._client.port))
        s.sendall(b'\x55\xAA\x55\x00\x25\x80\x03\xA8')
        s.close()
        time.sleep(1)

    def reconnect(self):
        from pymodbus.client.sync import ModbusTcpClient as ModbusClient
        from pymodbus.transaction import ModbusRtuFramer as ModbusFramer
        self._hub._client.close()
        self._hub._client = ModbusClient(
            host=self._hub._client.host,
            port=self._hub._client.port,
            framer=ModbusFramer,
            timeout=self._hub._client.timeout)
        self._hub._client.connect()

    def update(self):
        """Update state."""
        if self._skip_update:
            self._skip_update = False
            #_LOGGER.debug("Skip update on %s", self._name)
            return

        #_LOGGER.debug("Update on %s", self._name)
        for prop in self._regs:
            mod = self._regs[prop]
            register_type, slave, register, scale, offset = self.register_info(mod)
            count = mod[CONF_COUNT] if CONF_COUNT in mod else 1

            try:
                if register_type == REGISTER_TYPE_COIL:
                    result = self._hub.read_coils(slave, register, count)
                    value = bool(result.bits[0])
                else:
                    if register_type == REGISTER_TYPE_INPUT:
                        result = self._hub.read_input_registers(slave, register, count)
                    else:
                        result = self._hub.read_holding_registers(slave, register, count)

                    val = 0
                    registers = result.registers
                    if mod.get(CONF_REVERSE_ORDER):
                        registers.reverse()

                    byte_string = b''.join([x.to_bytes(2, byteorder='big') for x in registers])
                    val = struct.unpack(mod[CONF_STRUCTURE], byte_string)[0]
                    value = scale * val + offset
            except:
                ModbusClimate._exception += 1
                _LOGGER.debug("Exception %d on %s/%s at %s/slave%s/register%s", ModbusClimate._exception, self._name, prop, register_type, slave, register)
                if ModbusClimate._exception < 4:
                    return
                if ModbusClimate._exception < 10 or ModbusClimate._exception % 10 == 0:
                    if ModbusClimate._exception % 3 == 0:
                        _LOGGER.warn("Reset %s", self._hub._client)
                        self.reset()
                    else:
                        _LOGGER.warn("Reconnect %s", self._hub._client)
                    self.reconnect()
                return

            ModbusClimate._exception = 0
            #_LOGGER.info("Read %s: %s = %f", self.name, prop, value)
            self._values[prop] = value

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            self.set_value(REG_TARGET_TEMPERATURE, temperature)

        # hvac_mode = kwargs.get('hvac_mode')
        # if hvac_mode is not None:
        #     self.set_hvac_mode(hvac_mode)

    def set_humidity(self, humidity):
        """Set new target humidity."""
        self.set_value(REG_TARGET_HUMIDITY, humidity)

    def set_hvac_mode(self, hvac_mode):
        """Set new hvac mode."""
        if REG_HVAC_OFF in self._regs:
            self.set_value(REG_HVAC_OFF, ModbusClimate._hvac_off_value if hvac_mode ==
                           HVAC_MODE_OFF else ModbusClimate._hvac_on_value)
            if hvac_mode == HVAC_MODE_OFF:
                return

        if hvac_mode not in ModbusClimate._hvac_modes:  # Support HomeKit Auto Mode
            best_hvac_mode = self.best_hvac_mode
            _LOGGER.warn("Fix operation mode from %s to %s",
                         hvac_mode, best_hvac_mode)
            hvac_mode = best_hvac_mode
            # current = self.current_temperature
            # target = self.target_temperature
            # hvac_mode = HVAC_MODE_HEAT if current and target and current < target else HVAC_MODE_COOL

        self.set_mode(self._hvac_modes, REG_HVAC_MODE, hvac_mode)

    @property
    def best_hvac_mode(self):
        for mode in (HVAC_MODE_HEAT_COOL, HVAC_MODE_COOL, HVAC_MODE_HEAT):
            if mode in self._hvac_modes:
                return mode
        return None

    def turn_on(self):
        """Turn on."""
        _LOGGER.debug("Turn on with last operation mode: %s",
                      self._last_on_operation)
        self.set_hvac_mode(self._last_on_operation or self.best_hvac_mode)

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        self.set_mode(self._fan_modes, REG_FAN_MODE, fan_mode)

    def set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        self.set_mode(self._swing_modes, REG_SWING_MODE, swing_mode)

    def set_preset_mode(self, preset_mode):
        """Set new hold mode."""
        self.set_value(REG_PRESET_MODE, preset_mode)

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        self.set_value(REG_AUX_HEAT, ModbusClimate._aux_heat_on_value)

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        self.set_value(REG_AUX_HEAT, ModbusClimate._aux_heat_off_value)

    def register_info(self, mod):
        """Get register info."""
        register_type = mod.get(CONF_REGISTER_TYPE)
        register = mod[CONF_REGISTER] \
            if self._index == -1 else mod[CONF_REGISTERS][self._index]
        slave = mod[CONF_SLAVE] if CONF_SLAVE in mod else 1
        scale = mod[CONF_SCALE] if CONF_SCALE in mod else 1
        offset = mod[CONF_OFFSET] if CONF_OFFSET in mod else 0
        return (register_type, slave, register, scale, offset)

    def get_value(self, prop):
        """Get property value."""
        return self._values.get(prop)

    def set_value(self, prop, value):
        """Set property value."""
        mod = self._regs[prop]
        register_type, slave, register, scale, offset = self.register_info(mod)

        self._skip_update = True
        _LOGGER.debug("Write %s: %s = %f", self.name, prop, value)

        if register_type == REGISTER_TYPE_COIL:
            self._hub.write_coil(slave, register, bool(value))
        else:
            val = (value - offset) / scale
            self._hub.write_register(slave, register, int(val))

        self._values[prop] = value
        #self.async_write_ha_state()
        # async_call_later(self.hass, 2, self.async_schedule_update_ha_state)

    def get_mode(self, modes, prop):
        value = self.get_value(prop)
        if value is not None:
            for k, v in modes.items():
                if v == value:
                    #_LOGGER.debug("get_mode: %s for %s", k, prop)
                    return k
        _LOGGER.error("Invalid value %s for %s", value, prop)
        return None

    def set_mode(self, modes, prop, mode):
        if mode in modes:
            self.set_value(prop, modes[mode])
            return
        _LOGGER.error("Invalid mode %s for %s", mode, prop)
