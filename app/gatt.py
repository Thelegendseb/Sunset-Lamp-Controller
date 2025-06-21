from bleak import BleakClient

# ADDRESS = "65:91:68:29:E4:DB" 

ADDRESS = "EF:92:F8:CD:63:85"  # Replace with your device's address

async def main():
    print(f"Trying to connect to {ADDRESS}...")
    async with BleakClient(ADDRESS) as client:
        services = await client.get_services()
        print("\n🧩 GATT Services & Characteristics:")
        for service in services:
            print(f"[Service] {service.uuid}")
            for char in service.characteristics:
                print(f"  └─ [Char] {char.uuid} (props: {char.properties})")

import asyncio
asyncio.run(main())
