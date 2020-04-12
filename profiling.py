#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging

logger = logging.getLogger(__file__)
logger.info("Loading system profiling module")

from datetime import timedelta
import os
import psutil
from socket import AF_INET, AF_INET6, AF_PACKET
from time import time
from typing import Any, Dict, List, Tuple, Union


class System:
    """Interfacing class for RPi system profiling."""

    def __init__(self, paths: Union[Tuple[str], List[str]] = ("/",),
                 network_interfaces: Union[Tuple[str], List[str]] = ("wlan0", "eth0")):
        """Ready components for reporting information."""

        self._cpu = self._Cpu()
        self._ram = self._Ram()
        self._disks = {path: self._Disk(path) for path in paths}
        self._networks = {interface: self._Network(interface) for interface in network_interfaces}

    @property
    def cpu(self) -> "_Cpu":
        """Get the reports for the CPU.

        Returns:
            An object with the information on the CPU
        """

        return self._cpu

    @property
    def ram(self) -> "_Ram":
        """Get the reports for the RAM.

        Returns:
            An object with the information on the RAM
        """

        return self._ram

    @property
    def disks(self) -> Dict[str, "_Disk"]:
        """Get the reports for the requested disks.

        Returns:
            A dictionary with the given paths as keys and objects with the
            information of the disk as values
        """

        return self._disks

    @property
    def networks(self) -> Dict[str, "_Network"]:
        """Get the reports for the requested network interfaces.

        Returns:
            A dictionary with the given interfaces as keys and objects with the
            information of the network adapters as values
        """

        return self._networks

    @property
    def uptime(self) -> float:
        """Get the total system uptime.

        Returns:
            A float with the time since boot, in seconds
        """

        return time() - psutil.boot_time()

    def __str__(self) -> str:
        """Get a human readable string representation of the system profiler.

        Returns:
            A string with the information on the system uptime, CPU, RAM, disks,
            and network interfaces
        """

        return "System {" + \
               f"uptime {str(timedelta(seconds=self.uptime))}, " + \
               f"{str(self.cpu)}, " + \
               f"{str(self.ram)}, " + \
               f"[{', '.join(str(disk) for disk in self.disks.values())}], " + \
               f"[{', '.join(str(network) for network in self.networks.values())}]" + \
               "}"

    def __repr__(self) -> str:
        """Get a detailed string representation of the current state of the
        system profiler.

        Returns:
            A string with the information on the system uptime, CPU, RAM, disks,
            and network interfaces
        """

        return "System{" + \
               f"{repr(self.uptime)}," + \
               f"{repr(self.cpu)}," + \
               f"{repr(self.ram)}," + \
               f"[{','.join(repr(disk) for disk in self.disks.values())}]," + \
               f"[{','.join(repr(network) for network in self.networks.values())}]" + \
               "}"

    class _Cpu:
        """Interfacing class for CPU profiling."""

        @property
        def temperature(self) -> float:
            """Get the current temperature of the CPU.

            Returns:
                A float with the temperature, in celsius
            """

            return psutil.sensors_temperatures()["cpu-thermal"][0].current

        @property
        def frequency(self) -> float:
            """Get the current CPU frequency.

            Returns:
                A float with the frequency, in GHz
            """

            return psutil.cpu_freq().current / 1000

        @property
        def usage(self) -> float:
            """Get the current CPU utilisation.

            Returns:
                A float with the percentage of the CPU utilisation, across all
                cores
            """

            return psutil.cpu_percent()

        def __str__(self) -> str:
            """Get a human readable string representation of the CPU profiler.

            Returns:
                A string with the information on the CPU temperature, frequency,
                and usage
            """

            return "CPU {" + \
                   f"temperature {self.temperature:.1f}°C, " + \
                   f"frequency {self.frequency:.2f} GHz, " + \
                   f"usage {self.usage:.1f}%" + \
                   "}"

        def __repr__(self) -> str:
            """Get a detailed string representation of the current state of the
            CPU profiler.

            Returns:
                A string with the information on the CPU temperature, frequency,
                and usage
            """

            return f"CPU{{{self.temperature},{self.frequency},{self.usage}}}"

    class _Ram:
        """Interfacing class for RAM profiling."""

        @property
        def total(self) -> int:
            """Get the total available hardware memory.

            Returns:
                An integer with the amount of total system memory, in Bytes
            """

            return psutil.virtual_memory().total

        @property
        def free(self) -> int:
            """Get the free hardware memory.

            Returns:
                An integer with the amount of free system memory, in Bytes
            """

            return psutil.virtual_memory().available

        @property
        def used(self) -> int:
            """Get the used hardware memory.

            Returns:
                An integer with the amount of used system memory, in Bytes
            """

            return psutil.virtual_memory().used

        @property
        def usage(self) -> float:
            """Get the hardware memory usage.

            Returns:
                A float with the percentage of system memory utilisation
            """

            return 100 * self.used / self.total

        def __str__(self) -> str:
            """Get a human readable string representation of the RAM profiler.

            Returns:
                A string with the information on the RAM total, free, and used
                memory, as well as the memory usage
            """

            total = System._reduce(self.total)
            free = System._reduce(self.free)
            used = System._reduce(self.used)

            return "RAM {" + \
                   f"total {total['value']:.1f} {total['unit']}, " + \
                   f"free {free['value']:.1f} {free['unit']}, " + \
                   f"used {used['value']:.1f} {used['unit']}, " + \
                   f"usage {self.usage:.1f}%" + \
                   "}"

        def __repr__(self) -> str:
            """Get a detailed string representation of the current state of the
            RAM profiler.

            Returns:
                A string with the information on the RAM total, free, and used
                memory, as well as the memory usage
            """

            return f"RAM{{{self.total},{self.free},{self.used},{self.usage}}}"

    class _Disk:
        """Interfacing class for disk profiling."""

        def __init__(self, path: str):
            """Create the profiler for the specified path.

            Args:
                path: a path to mount point of the partition to be profiled
                (e.g. '/dev/sdx')
            """

            if not os.path.exists(path):
                raise ValueError(f"Invalid path '{path}' (expected one of " +
                                 f"{[partition.mountpoint for partition in psutil.disk_partitions()]})")

            self._path = path

        @property
        def total(self) -> int:
            """Get the total partition size.

            Returns:
                An integer with the total size of the partition, in Bytes
            """

            return psutil.disk_usage(self._path).total

        @property
        def free(self) -> int:
            """Get the free partition space.

            Returns:
                An integer with the free space of the partition, in Bytes
            """

            return psutil.disk_usage(self._path).free

        @property
        def used(self) -> int:
            """Get the used partition space.

            Returns:
                An integer with the used space of the partition, in Bytes
            """

            return psutil.disk_usage(self._path).used

        @property
        def usage(self) -> float:
            """Get the partition space usage.

            Returns:
                A float with the percentage of partition space utilisation
            """

            return 100 * self.used / self.total

        def __str__(self) -> str:
            """Get a human readable string representation of the disk profiler.

            Returns:
                A string with the information on the disk path, the total, free,
                and used space, as well as the space usage
            """

            total = System._reduce(self.total)
            free = System._reduce(self.free)
            used = System._reduce(self.used)

            return "DISK {" + \
                   f"path '{self._path}', " + \
                   f"total {total['value']:.1f} {total['unit']}, " + \
                   f"free {free['value']:.1f} {free['unit']}, " + \
                   f"used {used['value']:.1f} {used['unit']}, " + \
                   f"usage {self.usage:.2f}%" + \
                   "}"

        def __repr__(self) -> str:
            """Get a detailed string representation of the current state of the
            disk profiler.

            Returns:
                A string with the information on the disk path, the total, free,
                and used space, as well as the space usage
            """

            return f"DISK{{'{self._path}',{self.total},{self.free},{self.used},{self.usage}}}"

    class _Network:
        """Interfacing class for network profiling."""

        def __init__(self, name: str):
            """Create the profiler for the specified network interface.

            Args:
                name: the name of the network interface to be profiled
                (e.g. 'eth0')
            """

            if name not in psutil.net_if_addrs().keys():
                raise ValueError(f"Invalid network interface name '{name}' (expected one of " +
                                 f"{list(psutil.net_if_addrs().keys())})")

            self._name = name
            self._bytes_sent = None
            self._bytes_received = None

        @property
        def ipv4(self) -> str:
            """Get the IPv4 address of the network adapter.

            Returns:
                A string with the address of the network interface
            """

            return next(iter([x.address for x in psutil.net_if_addrs()[self._name]
                              if x.family is AF_INET]), "N/A")

        @property
        def ipv6(self) -> str:
            """Get the IPv6 address of the network adapter.

            Returns:
                A string with the address of the network interface
            """

            return next(iter([x.address.upper() for x in psutil.net_if_addrs()[self._name]
                              if x.family is AF_INET6]), "N/A")

        @property
        def mac(self) -> str:
            """Get the MAC address of the network adapter.

            Returns:
                A string with the address of the network interface
            """

            return next(iter([x.address.upper() for x in psutil.net_if_addrs()[self._name]
                              if x.family is AF_PACKET]), "N/A")

        @property
        def sent(self) -> int:
            """Get how much information was sent over this network interface
            since the last call

            Returns:
                An integer detailing how many Bytes were sent
            """

            sent = psutil.net_io_counters(pernic=True, nowrap=True)[self._name].bytes_sent
            if self._bytes_sent is None:
                self._bytes_sent = sent

            latest = sent - self._bytes_sent
            self._bytes_sent = sent

            return latest

        @property
        def received(self) -> int:
            """Get how much information was received over this network interface
            since the last call

            Returns:
                An integer detailing how many Bytes were received
            """

            received = psutil.net_io_counters(pernic=True, nowrap=True)[self._name].bytes_sent
            if self._bytes_received is None:
                self._bytes_received = received

            latest = received - self._bytes_received
            self._bytes_received = received

            return latest

        def __str__(self) -> str:
            """Get a human readable string representation of the network
            profiler.

            Returns:
                A string with the information on the network interface name, the
                IPv4, IPv6, and MAC addresses, and the amount of sent and
                received bytes
            """

            # Store values to avoid state change
            bytes_sent = self._bytes_sent
            bytes_received = self._bytes_received

            sent = System._reduce(self.sent)
            received = System._reduce(self.received)

            result = "NETWORK {" + \
                     f"name {self._name}, " + \
                     f"IPv4 {self.ipv4}, " + \
                     f"IPv6 {self.ipv6}, " + \
                     f"MAC {self.mac}, " + \
                     f"sent {sent['value']:.1f} {sent['unit']}, " + \
                     f"received {received['value']:.1f} {received['unit']}" + \
                     "}"

            # Restore state
            self._bytes_sent = bytes_sent
            self._bytes_received = bytes_received

            return result

        def __repr__(self) -> str:
            """Get a detailed string representation of the current state of the
            network profiler.

            Returns:
                A string with the information on the network interface name, the
                IPv4, IPv6, and MAC addresses, and the amount of sent and
                received bytes
            """

            # Store values to avoid state change
            bytes_sent = self._bytes_sent
            bytes_received = self._bytes_received

            result = f"NETWORK{{{self._name},{self.ipv4},{self.ipv6},{self.mac},{self.sent},{self.received}"

            # Restore state
            self._bytes_sent = bytes_sent
            self._bytes_received = bytes_received

            return result

    @staticmethod
    def _reduce(value: int) -> Dict[str, Any]:
        """Reduce the value of bytes to an appropriate unit.

        Args:
            value: A number of bytes to be reduced

        Returns:
            A dictionary with the reduced value and the corresponding unit
        """

        unit = 0
        while abs(value) >= 1024:
            unit += 1
            value /= 1024

        return {"value": value, "unit": ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"][unit]}


if __name__ == "__main__":
    # Test the profiling module

    import sys

    logging.getLogger().setLevel(logging.NOTSET)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("[{levelname:s}] {message:s}", style="{"))
    logging.getLogger().addHandler(console)

    logger.info(str(System()))
