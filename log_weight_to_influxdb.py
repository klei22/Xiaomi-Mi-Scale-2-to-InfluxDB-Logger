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
from device_address import device_address

# InfluxDB Configuration
BUCKET = "health_data"
ORG = "chromebook"
URL = "http://localhost:8086"
TOKEN = os.environ.get("INFLUXDB_TOKEN")  # Ensure the token is set in the environment

# BLE Device Configuration
WEIGHT_SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"  # Xiaomi Mi Scale V2 service UUID

# Replace 'AA:BB:CC:DD:EE:FF' with your scale's MAC address
SCALE_MAC_ADDRESS = device_address.lower()  # Replace with your scale's MAC address

# Setup InfluxDB client
client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write_api = client.write_api()

async def discover_and_log_weight():
    last_send_time = 0  # Initialize last_send_time in the function scope
    while True:
        print("Scanning for Xiaomi Mi Body Composition Scale 2...")
        devices = await BleakScanner.discover(timeout=5)
        mi_scale_address = None

        for device in devices:
            # Check if the device is our scale
            if device.address.lower() == SCALE_MAC_ADDRESS:
                mi_scale_address = device.address
                print(f"Found Xiaomi Mi Scale 2 at address: {mi_scale_address}")
                break

        if not mi_scale_address:
            print("Mi Scale 2 not found. Make sure the scale is active and nearby.")
            await asyncio.sleep(5)
            continue

        # Start scanning for advertisements from the scale
        measurement_received = False  # Flag to check if a valid measurement was received

        def callback(device, advertising_data):
            nonlocal measurement_received, last_send_time  # Declare nonlocal variables
            if device.address.lower() != SCALE_MAC_ADDRESS:
                return
            service_data = advertising_data.service_data
            if WEIGHT_SERVICE_UUID in service_data:
                data = binascii.b2a_hex(service_data[WEIGHT_SERVICE_UUID]).decode('ascii')
                data = "1b18" + data  # For consistency
                data_bytes = bytes.fromhex(data[4:])

                # Control Byte
                ctrlByte1 = data_bytes[1]
                isStabilized = ctrlByte1 & (1 << 5)
                isWeightRemoved = ctrlByte1 & (1 << 7)

                if not isStabilized or isWeightRemoved:
                    print("Measurement not stabilized or weight removed.")
                    return

                # Units
                measunit = data[4:6]
                unit = ''
                if measunit == "03":
                    unit = 'lbs'
                elif measunit == "02":
                    unit = 'kg'
                else:
                    print("Unknown measurement unit.")
                    return

                # Extract weight
                measured = int((data[28:30] + data[26:28]), 16) * 0.01

                # Adjust weight based on unit
                if unit == 'kg':
                    weight_kg = measured / 2
                    weight_lbs = weight_kg * 2.20462
                elif unit == 'lbs':
                    weight_lbs = measured * 0.453592  # Convert to kg first
                    weight_kg = weight_lbs / 2.20462
                else:
                    print("Invalid unit.")
                    return

                # Check if weight is within the reasonable range
                if weight_kg > 50 and weight_lbs < 300:
                    current_time = time.time()
                    # Check if at least 10 seconds have passed since last send
                    if current_time - last_send_time >= 10:
                        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

                        # Log weight in both kg and lbs to InfluxDB
                        point = (
                            Point("body_metrics")
                            .tag("device", "xiaomi_scale")
                            .field("weight_kg", weight_kg)
                            .field("weight_lbs", weight_lbs)
                            .time(timestamp)
                        )
                        write_api.write(bucket=BUCKET, org=ORG, record=point)
                        print(f"Weight data sent to InfluxDB: {timestamp}, Weight: {weight_kg:.2f} kg, {weight_lbs:.2f} lbs")
                        print("-" * 30)
                        last_send_time = current_time  # Update last send time
                        measurement_received = True
                    else:
                        print("Waiting 10 seconds before sending next measurement.")
                else:
                    print(f"Weight out of reasonable range: {weight_kg:.2f} kg, {weight_lbs:.2f} lbs")

        try:
            scanner = BleakScanner(callback)
            await scanner.start()
            print("Listening for weight data...")

            # Listen for up to 30 seconds or until a valid measurement is received
            timeout = 30
            start_time = time.time()
            while not measurement_received and time.time() - start_time < timeout:
                await asyncio.sleep(1)

            await scanner.stop()
            print("Stopped listening for weight data.")

            if measurement_received:
                # After successful send, wait for 10 seconds
                print("Waiting for 10 seconds after successful send.")
                await asyncio.sleep(10)
            else:
                print("No valid measurement received.")
                # Wait a shorter time before trying again
                await asyncio.sleep(5)

        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(5)

async def main():
    try:
        await discover_and_log_weight()
    except KeyboardInterrupt:
        print("\nExiting script.")
    finally:
        write_api.close()
        client.close()

if __name__ == "__main__":
    asyncio.run(main())

