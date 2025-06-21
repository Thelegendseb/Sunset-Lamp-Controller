# 💡Sunset Lamp Controller

A PyQt6 desktop app I built to control RGB sunset lamps via Bluetooth (BLE). I wanted to have a way to control the light from my computer and I couldn't find any online solutions so I made one!

## What It Does

This app connects to compatible RGB sunset lamps and gives you full control over:
- **Manual Color Selection**: Pick any color using a color wheel
- **Brightness Control**: Adjust brightness from 1-100% with a smooth slider
- **Screen Sync Mode**: Automatically matches your light to the average color of your screen
- **Real-time Updates**: Continuously sends color data to keep your light perfectly synced

## Demo Video

https://github.com/user-attachments/assets/9b1e894c-96e0-4d7b-9ece-55152fd0f9d6



## Important Setup Note

**You MUST disconnect the lamp from your phone's lamp app first.** BLE devices can typically only maintain one active connection at a time. If your phone is connected, this app won't be able to establish a connection. Also make sure its plugged in on the wall and the on button along the wire is correctly toggled.

Here are the two UI styles of the mobile app showing where this toggle off is:

<p align="center">
  <img src="https://github.com/user-attachments/assets/e20b23cf-666c-486e-b090-3a29ff2e56f0" width="50%">
  <img src="https://github.com/user-attachments/assets/cfb1ad2d-af34-41e2-b12a-12d5e50384a9" width="50%">
</p>


## How I Built This

### Step 1: Finding the Device

**[`app/sniff.py`](app/sniff.py)** - First thing I needed was to find the device among all the Bluetooth devices floating around:

```python
async def scan_ble_devices():
    with open("ble_devices.txt", "w") as file:
        file.write("Scanning for BLE devices (10 seconds)...\n")
        devices = await BleakScanner.discover(timeout=10.0)

        for d in devices:
            name = d.name or "(no name)"
            file.write(f"Address: {d.address} | RSSI: {d.rssi} dBm | Name: {name}\n")
```

This just dumps all nearby BLE devices to a text file. Most sunset lamps show up with generic names or just MAC addresses, so you have to do some detective work. My lamp showed up as below:

```
Address: 65:91:68:29:E4:DB | RSSI: -53 dBm | Name: SSL-29E4DB
```

RSSI stands for Received Signal Strength Indicator. It's a measurement of how strong the radio signal is between your device (like your computer) and the Bluetooth device you're scanning for. The lower the number (more negative), the weaker the signal - so -53 dBm means my lamp was pretty close to my computer when I scanned for it. Unfortunately this value isnt very reliable, so just look for an address or name like I've shown above


### Step 2: Understanding the Device

**[`app/gatt.py`](app/gatt.py)** - Once I had the device address, I needed to poke around and see what services and characteristics it had. Services and characteristics of BLE devices are like the organizational structure of BLE devices - services group related functionality together, and characteristics are the specific endpoints you can read from or write to.

In BLE's, these are called "GATT". GATT stands for Generic Attribute Profile, and they provide a way for low energy bluetooth devices to list their services publicly.

```python
async def main():
    print(f"Trying to connect to {ADDRESS}...")
    async with BleakClient(ADDRESS) as client:
        services = await client.get_services()
        print("\n🧩 GATT Services & Characteristics:")
        for service in services:
            print(f"[Service] {service.uuid}")
            for char in service.characteristics:
                print(f"  └─ [Char] {char.uuid} (props: {char.properties})")
```

This revealed the magic characteristic UUID (`0000ac52-1212-efde-1523-785fedbeda25`) that I needed to write to for controlling the light. I wasn't able to determine which service controlled sending colours to the lamp so I have the article linked at the bottom of this README to thank for that.

### Step 3: The Hard Part - The Encryption Protocol

**[`app/lightController.py`](app/lightController.py)** - This was where things got tricky. The device uses AES encryption and a specific payload format that I had to reverse engineer. 

Huge shoutout to [this Russian article on Habr](https://habr.com/ru/articles/722412/) - without this, I would have been completely lost. The author did the heavy lifting of sniffing the actual communication and documenting the encryption process. Seriously saved me weeks of work.

The protocol uses:
- AES encryption with a hardcoded key
- Specific 16-byte payload structure
- GRB color ordering instead of RGB (because why make things simple?)

```python
class PayloadGenerator:
    # This key came from the Russian article's reverse engineering work
    KEY = bytes([
        0x34, 0x52, 0x2A, 0x5B, 0x7A, 0x6E, 0x49, 0x2C,
        0x08, 0x09, 0x0A, 0x9D, 0x8D, 0x2A, 0x23, 0xF8
    ])
    
    def get_rgb_payload(self, red, green, blue, brightness=100, speed=100):
        payload = bytearray(16)
        payload[0:4] = self.HEADER
        payload[4] = CommandType.RGB
        payload[5] = self.GROUP_ID
        payload[7] = red    # Note the GRB ordering in the protocol
        payload[8] = green
        payload[9] = blue
        payload[10] = brightness
        payload[11] = speed
        
        return self.cipher.encrypt(bytes(payload))
```

### Step 4: Making Sure It Actually Works

**[`app/test.py`](app/test.py)** - I built a test suite file to make sure everything worked properly:

```python
async def test_primary_colors():
    async with BleakClient(ADDRESS) as client:
        # Test basic colors
        primaries = [
            ("Red", 255, 0, 0),
            ("Green", 0, 255, 0),
            ("Blue", 0, 0, 255)
        ]
        
        for name, r, g, b in primaries:
            print(f"Testing {name}")
            await set_color(client, r, g, b)
            await asyncio.sleep(1.5)
```

This tests everything I needed like basic colors and brightness levels that I wanted for my implementation.

### Step 5: Screen Sync

I wanted an additional feature that would set the lamps colour to to the average colour of my screen. Its a crude attempt to recreate this effect:

https://www.youtube.com/shorts/UhQu7ntkE2Q

Implementing this involved:
- Grabbing screenshots and calculating average colors
- Enhancing dark colors so they're actually visible on the light by changing the brightness
- Smooth color transitions with interpolation
- Converting screen brightness to lamp brightness

The screen sync basically captures your entire screen, finds the average color, and applies some smart enhancements to make dark scenes look good on the physical light.

### Step 6: The GUI

**[`app/app.py`](app/app.py)** - Finally, I wrapped everything in a PyQt6 interface.

## Will This Work With My Lamp?

I developed this with the QuigoRGBIC Sunset Lamp (Model: SUNLAMP-P), but the protocol seems to be used by multiple manufacturers. If your lamp has similar features or uses a comparable mobile app, there's a decent chance it'll work.

**If it doesn't work right away:**

1. **Different Bluetooth address**: Run [`app/sniff.py`](app/sniff.py) to find your device's MAC address and update the `ADDRESS` variable in [`app/lightController.py`](app/lightController.py)

2. **Different GATT characteristics**: Run [`app/gatt.py`](app/gatt.py) to see if your device uses a different characteristic UUID. Update `CHAR_UUID` if needed.

3. **Test basic functionality**: Use [`app/test.py`](app/test.py) to see if basic color commands work

4. **Protocol differences**: Some manufacturers might use different encryption keys or payload structures. If colors look wrong or nothing happens, you might need to do your own protocol analysis.

## Requirements

```bash
pip install PyQt6 bleak numpy Pillow pycryptodome
```
## Running the App (Forenote)

Because im an unliscenced publisher of this app, windows will automatically flag this before you try to run it. You can bypass this by pressing "Run Anyway". I can't provide further proof that this app doesnt contain malicious content beyond the attached source code, so trust it if you like.

## Running the App

1. Download the executable file from the release
2. Run the executable
3. Press "Connect"

## Running the App Via Python

1. Disconnect your lamp from your phone's lamp app
2. Update the `ADDRESS` in [`app/lightController.py`](app/lightController.py) if needed
3. Run it via the command below

```bash
python app/app.py
```

## Disclaimer

Due to the way the lamp is physically built, multiple colours are shown despite the RGB Values sent. The resulting colour may not always look like what you selected, but its as close as I think is possible due to the physical limitations. The app is not broken, just a consideration of the functinoality of a sunset lamp. This is visibile during the screen sync part of the demo video.

## File Breakdown

- **[`app/app.py`](app/app.py)** - Main GUI application with all the controls
- **[`app/lightController.py`](app/lightController.py)** - Core BLE communication and encryption
- **[`app/gatt.py`](app/gatt.py)** - Tool for exploring device characteristics during development
- **[`app/sniff.py`](app/sniff.py)** - BLE scanner for finding your lamp
- **[`app/test.py`](app/test.py)** - Comprehensive testing suite for validating everything works
