#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging

logger = logging.getLogger(__file__)
logger.info("Loading LCD 2004 Display")

import os
import re
from time import sleep
from typing import List, Tuple

import RPi.GPIO


class Display:
    """Adapter for a 20x04 LCD using a RPi."""

    _WIDTH, _HEIGHT = 20, 4
    """The size of the LCD display."""

    _DATA: Tuple[int] = (15, 18, 23, 24, 25, 8, 7, 1)
    """GPIO pin for D0-D7 lines, used to send information."""
    _MODE: int = 14
    """GPIO pin for RS line, used to distinguish between data and commands."""
    _ENABLE: int = 4
    """GPIO pin for E line, used to enable communication."""

    def __init__(self):
        """Initialise RPi to communicate with the display."""

        RPi.GPIO.setmode(RPi.GPIO.BCM)  # Use BCM numbering system
        RPi.GPIO.setwarnings(False)
        for pin in tuple(Display._DATA) + (Display._ENABLE, Display._MODE):
            RPi.GPIO.setup(pin, RPi.GPIO.OUT)

        sleep(50e-3)  # Power ON delay
        self._reset()

    def __del__(self):
        """Close the RPi communication with the display."""

        RPi.GPIO.cleanup()

    def display(self, text: str) -> "Display":
        """Show an image on the screen.

        This assumes that the text has no lines longer than 20 characters and
        that there are at most 4 lines (as defined by _WIDTH and _HEIGHT)

        Args:
            text: the text that will be shown

        Returns:
            self
        """

        logger.debug("Update")

        if text is None:
            raise TypeError("The text cannot be None")

        # Normalise new lines from different systems to UNIX style, and split into lines
        lines = re.sub(r"(\r\n|\n\r|\n|\r)", "\n", text).split("\n")

        if len(lines) > Display._HEIGHT:
            raise ValueError("The text has too many lines")

        elif max([len(line) for line in lines]) > Display._WIDTH:
            raise ValueError("The text's lines are too long")

        lines += [""] * (Display._HEIGHT - len(lines))
        lines = [lines[0]] + [lines[2]] + [lines[1]] + [lines[3]]  # Screen receives the lines in this order

        self.clear()
        for line in lines:  # Send one line at a time
            self._send(False, [ord(character) for character in line + " " * (Display._WIDTH - len(line))])

        logger.debug("Updated")

        return self

    def clear(self) -> "Display":
        """Clear the screen.

        Returns:
            self
        """

        logger.debug("Clear")
        self._send(True, [0x01])
        sleep(1e-3)  # Clearing takes time
        logger.debug("Cleared")

        return self

    def _reset(self):
        """Do a hardware reset of the display."""

        logger.debug("Reset")

        RPi.GPIO.output(Display._ENABLE, False)
        self._send(True, [0x30])
        sleep(5e-3)  # First execution takes longer
        self._send(True, [0x30, 0x30, 0x38, 0x0C, 0x06])
        self.clear()

        logger.debug("Reset")

    @staticmethod
    def _send(command: bool, array: List[int]):
        """Send information to the display

        Args:
            command: True if the bytes are a command, False if data
            array: the information to be sent
        """

        logger.debug("Send [{}] as {}".format(", ".join("0x{:02X}".format(byte) for byte in array),
                                              "command" if command else "data"))

        RPi.GPIO.output(Display._MODE, not command)  # Set mode
        for byte in array:
            for i, dx in enumerate(Display._DATA):  # Set byte
                RPi.GPIO.output(dx, ((byte & 0xFF) >> i) & 1)

            # Pulse the enable line to send data
            RPi.GPIO.output(Display._ENABLE, False)
            sleep(1e-6)
            RPi.GPIO.output(Display._ENABLE, True)
            sleep(1e-6)
            RPi.GPIO.output(Display._ENABLE, False)

            sleep(100e-6)  # Wait for execution

        logger.debug("Sent")


# Check that GPIO drivers are reachable
if not os.path.exists("/sys/bus/platform/drivers/gpiomem-bcm2835"):
    raise RuntimeError("GPIO drivers not found")

if __name__ == "__main__":
    # Test the display module

    import sys

    logging.getLogger().setLevel(logging.NOTSET)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("[{levelname:s}] {message:s}", style="{"))
    logging.getLogger().addHandler(console)

    display = Display()
    display.clear()
    display.display("This\nis\na\ntest!")
