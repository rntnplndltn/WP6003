#!/usr/bin/python3


import datetime
import asyncio
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

import paho.mqtt.publish as publish

CORR = 18 # Temp Correction Value*10
BROKER = "192.168.4.2"  # Change to your Broker IP!
MQTT_ID = "WP6003_"
MQTT_PORT = 1883        # default port is 1883

SENSOR_UUID = "0000FFF4-0000-1000-8000-00805F9B34FB"
COMMAND_UUID = "0000FFF1-0000-1000-8000-00805F9B34FB"

def notification_handler(sender, data):
    if len(data) == 18:
        msgs = [{'topic': "sensor/temperature", 'payload': (data[6]*256+data[7]+CORR)/10}, ("sensor/CO2", (data[16]*256+data[17]), 0, False), ("sensor/HCHO",(data[12]*256+data[13]), 0, False), ("sensor/TVOC",(data[10]*256+data[11]), 0, False), ("sensor/state","connected", 0, False), ("sensor/address",address, 0, False)]
        publish.multiple(msgs, hostname=BROKER, client_id=MQTT_ID, port=MQTT_PORT)

async def run(address):
    device = await BleakScanner.find_device_by_address(address, timeout=25.0)
    if not device:
	publish.single("sensor/error","not Found", hostname=BROKER, client_id=MQTT_ID, port=MQTT_PORT)
        return

    try:
        async with BleakClient(device) as client:
            await client.start_notify(SENSOR_UUID, notification_handler)
            t = datetime.datetime.now()
# set clock
            write_value = bytearray([0xAA,t.year-2000,t.month,t.day,t.hour,t.minute,t.second])
            await client.write_gatt_char(COMMAND_UUID, write_value)
# get sensor value
            write_value = bytearray([0xAB])
            await client.write_gatt_char(COMMAND_UUID, write_value)
            await asyncio.sleep(1)
            await client.stop_notify(SENSOR_UUID)
    except BleakError:
        publish.single("sensor/error","no Values", hostname=BROKER, client_id=MQTT_ID, port=MQTT_PORT)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("usage: " + sys.argv[0] + " <bluetooth mac address> <unique mqtt id (WP6003_*)>" )
        quit()

    ADDR = sys.argv[1]
    MQTT_ID = MQTT_ID + sys.argv[2]

    address = (
        ADDR
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address))