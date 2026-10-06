
## Introduction

## Quick Start

### Client configuration (linux)

Create udev rule to allow applications to access the c3-proxy from userspace.

```bash
sudo echo 'SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="00dd", GROUP="plugdev", MODE="0666"' >> /etc/udev/rules.d/99-mcp2221a.rules && \
sudo udevadm control --reload && \
```
It may be necessary to restart your computer after running the above command.

### Starting the software

(first time) Create a python virtual environment for this project
```
cd /path/to/oresat-c3-proxy-software
python -m venv .venv
```
Activate the virtual environment
```
cd /path/to/oresat-c3-proxy-software
source ./venv/bin/activate
```
Updating packages
TBD: DON'T KNOW HOW pyproject.toml WORKS

### Using the software

Ensure the virtual environment has been activated.
start the software
```
python src/main.py
```
#### user interface
- In the `Chip Selector` panel, press the `REFRESH` button at the bottom to detect connected c3-proxy boards.
    if there are multiple c3-proxys connected over usb, then you can select which one you want to interact with by clicking on it's row.
- in the `Opd Menu` panel, press `scan` to detect all the OPD consumers connected to the selected c3-proxy.
    once a card is recognized, 4 OPD functions can be toggled.
    *EN* or enable, tells the OPD circuit to allow the card draw power from the bus.
    *ISP* or in-system-programming, puts the cards micro controller into ISP mode, helpful for flashing in some cases.
    *UART* selects this card for UART communication
    *B-RESET* when asserted the circuit breaker is reset, turn of during normal use




##







