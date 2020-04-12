# RPi system profiler

A simple Python script for profiling the RPi's system resources and showing them in an lcd 2004 display. Designed with
an RPi4B 2GB model running [OpenMediaVault 5](https://www.openmediavault.org/) in mind, but should work for any other
model as well.

# How does it work

Every 2 seconds, the code queries system information using the
[psutil library](https://psutil.readthedocs.io/en/latest/) such as CPU usage and temperature, network throughput, disk
usage, et cetera. Then it manually converts the data and sends it to the lcd through the GPIO.

# Usage

First, install the required dependencies by running `pip install requirements.txt`. Then simply run `python main.py`,
which will activate a 2 second schedule to constantly update the screen.

This works as long as the RPi stays powered on, but if you want to start the program every time the device turns on you
can do as I did and configure a cron job. Simply type `crontab -e` on a terminal and edit as desired. Here is my
configuration as an example:
```text
# * * * * * command to execute
# │ │ │ │ └ day of the week (1 - 7 Mon to Sun; or 0 - 6 Sun to Sat)
# │ │ │ └── month (1 - 12)
# │ │ └──── day of the month (1 - 31)
# │ └────── hour (0 - 23)
# └──────── minute (0 - 59)
#
# @reboot, @yearly, @monthly, @weekly, @daily, @hourly can be used instead of
# the pattern.
# Do not forget new line at the end of the file!
# See crontab.guru for help.
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:"
MAILTO=""

@reboot python /home/pi/lcd/main.py

```
