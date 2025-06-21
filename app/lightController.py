import asyncio
import binascii
from enum import IntEnum
from Crypto.Cipher import AES
from bleak import BleakClient

# Device address
ADDRESS = "65:91:68:29:E4:DB"

# Target characteristic for light control
CHAR_UUID = "0000ac52-1212-efde-1523-785fedbeda25"

class CommandType(IntEnum):
    JOIN_GROUP_REQUEST = 1
    RGB = 2
    RHYTHM = 3
    TIMER = 4
    RGB_LINE_SEQUENCE = 5
    SPEED = 6
    LIGHT = 7

class PayloadGenerator:
    # Encryption key - directly converted from the C# code
    KEY = bytes([
        0x34, 0x52, 0x2A, 0x5B, 0x7A, 0x6E, 0x49, 0x2C,
        0x08, 0x09, 0x0A, 0x9D, 0x8D, 0x2A, 0x23, 0xF8
    ])
    
    # Static header for requests
    HEADER = bytes([0x54, 0x52, 0x00, 0x57])
    
    # Default group ID
    GROUP_ID = 1
    
    def __init__(self):
        # Create AES encryptor in ECB mode
        self.cipher = AES.new(self.KEY, AES.MODE_ECB)
    
    def get_rgb_payload(self, red, green, blue, brightness=100, speed=100):
        """
        Generate payload for setting a specific color on the lamp
        
        Args:
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
            brightness: Lamp brightness (0-100)
            speed: Effect speed (0-100)
            
        Returns:
            bytes: The encrypted payload to send
        """
        # Create the payload according to the protocol format
        payload = bytearray(16)
        
        # Header
        payload[0:4] = self.HEADER
        
        # Command type (RGB = 2)
        payload[4] = CommandType.RGB
        
        # Group ID
        payload[5] = self.GROUP_ID
        
        # Reserved byte
        payload[6] = 0
        
        # RGB values (note they're swapped in the protocol: GRB)
        payload[7] = red
        payload[8] = green
        payload[9] = blue
        
        # Brightness and speed
        payload[10] = brightness
        payload[11] = speed
        
        # Reserved bytes
        payload[12:16] = [0, 0, 0, 0]
        
        # Encrypt the payload
        result = self.cipher.encrypt(bytes(payload))
        
        return result
    
    def convert_to_hex_string(self, data):
        """Convert bytes to a lowercase hex string"""
        return ''.join(f'{b:02x}' for b in data)

async def set_color(client, red, green, blue, brightness=100, speed=100):
    """
    Set the light to a specific RGB color with the given brightness and speed
    
    Args:
        client: BleakClient instance
        red, green, blue: RGB color components (0-255)
        brightness: Light brightness (0-100)
        speed: Effect speed (0-100)
    """
    generator = PayloadGenerator()
    encrypted_payload = generator.get_rgb_payload(red, green, blue, brightness, speed)
    
    # Log what we're sending
    hex_string = generator.convert_to_hex_string(encrypted_payload)
    print(f"📤 Sending RGB({red},{green},{blue}), Brightness: {brightness}, Speed: {speed}")
    print(f"   Payload: {hex_string}")
    
    # Send the command to the device
    await client.write_gatt_char(CHAR_UUID, encrypted_payload)
    print("✅ Command sent successfully")

async def demo_colors():
    """Demo various colors and effects"""
    print(f"🔌 Connecting to device: {ADDRESS}")
    
    try:
        async with BleakClient(ADDRESS) as client:
            print("✅ Connected successfully")
            
            # Demonstrate some basic colors
            print("\n🎨 Demonstrating basic colors:")
            await set_color(client, 255, 0, 0)  # Red
            await asyncio.sleep(2)
            
            await set_color(client, 0, 255, 0)  # Green
            await asyncio.sleep(2)
            
            await set_color(client, 0, 0, 255)  # Blue
            await asyncio.sleep(2)
            
            await set_color(client, 255, 255, 0)  # Yellow
            await asyncio.sleep(2)
            
            await set_color(client, 255, 0, 255)  # Magenta
            await asyncio.sleep(2)
            
            await set_color(client, 0, 255, 255)  # Cyan
            await asyncio.sleep(2)
            
            # Demonstrate brightness levels
            print("\n💡 Demonstrating brightness levels:")
            for brightness in [20, 50, 100]:
                await set_color(client, 255, 255, 255, brightness=brightness)  # White with changing brightness
                await asyncio.sleep(2)
            
            print("\n🏁 Demo complete")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Make sure to install PyCryptodome: pip install pycryptodome
    asyncio.run(demo_colors())