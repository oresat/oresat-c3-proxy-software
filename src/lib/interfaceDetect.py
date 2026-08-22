import subprocess

errored = False

def runCommand(command):
    try:
        result = subprocess.check_output(command, shell=True, executable="/bin/bash",
                   stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        result = cpe.output
        errored = True

    #finally:
    #TODO: add error handling here
    #    for line in result.splitlines():
    #        print(line.decode())
    return result


mcpResult = runCommand("i2cdetect -l")
mcpDevices = []
#find the lines with MCP2221As in them
if (not errored):
    for line in mcpResult.decode().splitlines():
        if 'MCP2221 usb-i2c bridge' in line:
            #print(line.split()[0])
            mcpDevices.append(line.split()[0])
print(mcpDevices)

errored = False
gpioResult = runCommand("gpiodetect")
gpioDevices = []
if (not errored):
    for line in gpioResult.decode().splitlines():
        if 'mcp2221' in line:
            gpioDevices.append(line.split()[0])
print(gpioDevices)


serialResult = runCommand("udevadm info usb-Microchip_Technology_Inc._MCP2221_USB-I2C_UART_Combo-if00")
serialDevices = []
if (not errored):
    for line in serialResult.decode().splitlines():
        if 'DEVNAME' in line:
            serialDevices.append(line.split()[0])
print(serialDevices)
