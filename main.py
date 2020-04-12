#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging.handlers
import logging
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

path = os.path.dirname(__file__)

logging.getLogger().setLevel(logging.NOTSET)
logging.captureWarnings(False)

# Silence scheduling messages
logging.getLogger("apscheduler.scheduler").setLevel(logging.ERROR)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("[{levelname:s}] {message:s}", style="{"))
logging.getLogger().addHandler(console)

if not os.path.exists(os.path.join(os.path.dirname(__file__), "res/logs/")):
    os.makedirs(os.path.join(os.path.dirname(__file__), "res/logs/"))
file = logging.handlers.RotatingFileHandler(filename=os.path.join(path, "res/logs/lcd.log"),
                                            maxBytes=1 << 20, backupCount=10)
file.setLevel(logging.DEBUG)
file.setFormatter(logging.Formatter("[{levelname:s}]({asctime:s} {name:s}) {message:s}", style="{"))
logging.getLogger().addHandler(file)

logger = logging.getLogger(__file__)
logger.info("Initialising program")

from datetime import datetime

from lcd2004 import Display
from profiling import System

# Configuration
dt = 2  # Seconds between updates
max_speed = 82 * 1024 * 1024  # 82 MiB/s, from empirical data
path = "/path/to/mount/point"  # Drive to profile


def update(profiler: System, display: Display):
    """Update the display with the updated profiler data.

    Args:
        profiler: a profiling class that provides data about the system
        display: an interface for a 2004 lcd display, to show the profiling data
    """

    logger.debug("Updating@" + datetime.now().isoformat())

    cpu_temperature = profiler.cpu.temperature
    cpu_usage = profiler.cpu.usage
    disk_usage = profiler.disks[path].usage
    network_usage = (profiler.networks["eth0"].sent + profiler.networks["eth0"].received) / dt  # B/s
    ipv4 = profiler.networks["eth0"].ipv4

    logger.debug(f"TEMPERATURE {cpu_temperature:.1f}°C " +
                 f"CPU {cpu_usage}% " +
                 f"DISK {disk_usage}% " +
                 f"NETWORK {network_usage} B/s")

    network_usage = 100 * min(network_usage / max_speed, 1)  # %

    lines = [f"{cpu_temperature:3.1f}C{ipv4:>15s}",
             "C" + "\u00FF" * round(19 * cpu_usage / 100),
             "N" + "\u00FF" * round(19 * network_usage / 100),
             "D" + "\u00FF" * round(19 * disk_usage / 100)]
    display.display("\n".join(lines))

    logger.debug("Updated@" + datetime.now().isoformat())


# Create a display and profiler and schedule it to update indefinitely
profiler = System(paths=(path,))
display = Display()
scheduler = BlockingScheduler()

try:
    scheduler.add_job(update, args=(profiler, display), trigger="cron", second=f"*/{int(dt)}")
    scheduler.start()

except (KeyboardInterrupt, SystemExit) as cause:
    logger.exception(cause)

finally:
    scheduler.shutdown()
    logging.shutdown()
