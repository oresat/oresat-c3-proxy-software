#!/bin/python3
from periphery import GPIO
from periphery import I2C

#line0 = GPIO("/dev/gpiochip2", 1, "out")
#line0.write(0)

i2c = I2C("/dev/i2c-27")
#msgs = [I2C.Message([0x01, 0x00]), I2C.Message([0x00], read=True)]
#i2c.transfer(0x50, msgs)
#print("0x100: 0x({:02x}".format(msgs[1].data[0]))



print("this is the c3-proxy riser software for the MDC and development machines")


