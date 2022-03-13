#!/usr/bin/env python3

import time

from gpiozero import OutputDevice
from os import getenv

from prometheus_client import start_http_server, Gauge

ON_THRESHOLD = int(getenv('ON_THRESHOLD',"65"))  # (degrees Celsius) Fan kicks on at this temperature.
OFF_THRESHOLD = int(getenv('OFF_THRESHOLD', "55"))  # (degress Celsius) Fan shuts off at this temperature.
SLEEP_INTERVAL = int(getenv('SLEEP_INTERVAL', "5"))  # (seconds) How often we check the core temperature.
GPIO_PIN = int(getenv('GPIO_PIN', '17'))  # Which GPIO pin you're using to control the fan.
PROMETHEUS_PORT = int(getenv('PROMETHEUS_PORT', '8000')) # Which PORT Prometheus will open to expose the metrics.


fan_status = Gauge('fancontrol_fan_state', 'State of the raspberry pi fan. 0 = OFF, 1 = ON')
measure_temp = Gauge('fancontrol_temperature', 'Measure temperature')
g_on_threshold = Gauge('fancontrol_on_threshold', 'Threshold to turn on raspberry pi fan')
g_off_threshold = Gauge('fancontrol_off_threshold', 'Threshold to turn off raspberry pi fan')
g_sleep_interval = Gauge('fancontrol_sleep_interval', 'How often fancontrol will check the core temperature')
g_gpio_pin = Gauge('fancontrol_gpio_pin', 'Which GPIO pin fancontrol is using to control the fan')

def get_temp():
    """Get the core temperature.

    Read file from /sys to get CPU temp in temp in C *1000

    Returns:
        int: The core temperature in thousanths of degrees Celsius.
    """
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        temp_str = f.read()

    try:
        return int(temp_str) / 1000
    except (IndexError, ValueError,) as e:
        raise RuntimeError('Could not parse temperature output.') from e

if __name__ == '__main__':
    start_http_server(PROMETHEUS_PORT)
    g_on_threshold.set(ON_THRESHOLD)
    g_off_threshold.set(OFF_THRESHOLD)
    g_sleep_interval.set(SLEEP_INTERVAL)
    g_gpio_pin.set(GPIO_PIN)
    # Validate the on and off thresholds
    if OFF_THRESHOLD >= ON_THRESHOLD:
        raise RuntimeError('OFF_THRESHOLD must be less than ON_THRESHOLD')

    fan = OutputDevice(GPIO_PIN)

    while True:
        temp = get_temp()
        measure_temp.set(temp)

        # Start the fan if the temperature has reached the limit and the fan
        # isn't already running.
        # NOTE: `fan.value` returns 1 for "on" and 0 for "off"
        if temp > ON_THRESHOLD and not fan.value:
            fan.on()
            fan_status.set(1)

        # Stop the fan if the fan is running and the temperature has dropped
        # to 10 degrees below the limit.
        elif fan.value and temp < OFF_THRESHOLD:
            fan.off()
            fan_status.set(0)

        time.sleep(SLEEP_INTERVAL)
