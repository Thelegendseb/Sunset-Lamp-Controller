import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    # Open a file for writing
    with open("ble_devices.txt", "w") as file:
        file.write("Scanning for BLE devices (10 seconds)...\n")
        devices = await BleakScanner.discover(timeout=10.0)

        for d in devices:
            name = d.name or "(no name)"
            file.write(f"Address: {d.address} | RSSI: {d.rssi} dBm | Name: {name}\n")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
