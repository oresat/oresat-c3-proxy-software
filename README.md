

## Adding the udev rule

`/etc/udev/rules.d/99-mcp2221a.rules`

```bash
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="00dd", GROUP="plugdev", MODE="0666"
```

Load new rules with `sudo udevadm control --reload` or reboot computer.
