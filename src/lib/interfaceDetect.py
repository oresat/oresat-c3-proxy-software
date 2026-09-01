




#mcpResult = runCommand("i2cdetect -l")
#mcpDevices = []
##find the lines with MCP2221As in them
#if (not errored):
#    for line in mcpResult.decode().splitlines():
#        if 'MCP2221 usb-i2c bridge' in line:
#            #print(line.split()[0])
#            mcpDevices.append(line.split()[0])
#print(mcpDevices)
#
#errored = False
#gpioResult = runCommand("gpiodetect")
#gpioDevices = []
#if (not errored):
#    for line in gpioResult.decode().splitlines():
#        if 'mcp2221' in line:
#            gpioDevices.append(line.split()[0])
#print(gpioDevices)
#
#
##hopefully minor revisions of the MCP2221a don't screw this kind of thing up
#serialDevices = []
#if (not errored):
#    for file in Path("/dev/serial/by-path").iterdir():
#        thisResult = runCommand(f"udevadm info --query=property --property=ID_MODEL --property=DEVNAME {str(file)}")
#        if (thisResult.find("MCP2221_USB-I2C_UART_Combo".encode()) > 0):
#            startIndex = thisResult.find("DEVNAME".encode())
#            endIndex = thisResult.find("\n".encode(), startIndex)
#            serialDevice = thisResult[startIndex:endIndex].decode().split("=")[1]
#            if serialDevice not in serialDevices:
#                serialDevices.append(serialDevice)
#
#print(serialDevices[::-1])
