#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import binascii
import sys
import datetime
import time
import os
from influxdb_client import InfluxDBClient, Point
from bleak import BleakScanner
import argparse

# InfluxDB Configuration
BUCKET = "health_data"
ORG = "chromebook"
URL = "http://localhost:8086"
TOKEN = os.environ.get("INFLUXDB_TOKEN")  # Ensure the token is set in the environment

# BLE Device Configuration
TARGET_ADDRESS = "E9:BA:38:40:EF:95"  # Change to your scale's MAC address

# Setup InfluxDB client
client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write_api = client.write_api()

async def scan_and_log_weight(scale_mac):
    while True:
        def callback(device, advertising_data):
            service_data = advertising_data.service_data
            if scale_mac and device.address.lower() != scale_mac:
                return
            if '0000181b-0000-1000-8000-00805f9b34fb' in service_data:
                # Xiaomi Mi Scale V2
                data = binascii.b2a_hex(service_data['0000181b-0000-1000-8000-00805f9b34fb']).decode('ascii')
                data_bytes = bytes.fromhex(data[4:])
                ctrlByte1 = data_bytes[1]
                isStabilized = ctrlByte1 & (1 << 5)
                measured = int((data[28:30] + data[26:28]), 16) * 0.01
                if isStabilized:
                    weight = measured  # Weight in kg
                    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

                    # Log weight to InfluxDB
                    point = (
                        Point("body_metrics")
                        .tag("device", "xiaomi_scale")
                        .field("weight", weight)
                        .time(timestamp)
                    )
                    write_api.write(bucket=BUCKET, org=ORG, record=point)
                    print(f"Weight data sent to InfluxDB: {timestamp}, Weight: {weight:.2f} kg")
                    print("-" * 30)

        print("Scanning for Xiaomi Mi Scale...")
        async with BleakScanner(callback) as scanner:
            await asyncio.sleep(5)

async def main():
    parser = argparse.ArgumentParser(description='Xiaomi Mi Scale Weight Logger')
    parser.add_argument('--mac', type=str, default=TARGET_ADDRESS, help='MAC address of your scale (optional)')
    args = parser.parse_args()

    scale_mac = args.mac.lower() if args.mac else None

    try:
        await scan_and_log_weight(scale_mac)
    except KeyboardInterrupt:
        print("\nExiting script.")
    finally:
        write_api.close()
        client.close()

if __name__ == "__main__":
    asyncio.run(main())

