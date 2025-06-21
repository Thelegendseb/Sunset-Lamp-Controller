import asyncio
import time
import random
from bleak import BleakClient
from lightController import set_color, ADDRESS

async def test_primary_colors():
    """Test primary and secondary colors with different brightness levels"""
    print(f"🔌 Connecting to device: {ADDRESS}")
    
    try:
        async with BleakClient(ADDRESS) as client:
            print("✅ Connected successfully")
            
            # Test primary colors
            print("\n🎨 Testing primary colors...")
            primaries = [
                ("Red", 255, 0, 0),
                ("Green", 0, 255, 0),
                ("Blue", 0, 0, 255)
            ]
            
            for name, r, g, b in primaries:
                print(f"\nTesting {name}")
                await set_color(client, r, g, b)
                await asyncio.sleep(1.5)
            
            # Test brightness levels on white
            print("\n💡 Testing brightness levels on white...")
            for brightness in [100, 75, 50, 25, 10, 5]:
                print(f"Brightness: {brightness}%")
                await set_color(client, 255, 255, 255, brightness=brightness)
                await asyncio.sleep(1)
            
            # Fade from black to white
            print("\n🌓 Fading from black to white...")
            steps = 10
            for i in range(steps + 1):
                value = int((255 * i) / steps)
                await set_color(client, value, value, value)
                await asyncio.sleep(0.3)
            
            # RGB color cycle
            print("\n🌈 RGB color cycle...")
            for i in range(0, 101, 20):  # 0, 20, 40, 60, 80, 100
                t = i / 100.0
                # Simple RGB rotation formula
                r = int(255 * abs(1 - 3 * t if t >= 1/3 and t < 2/3 else 2 - 3 * t if t >= 2/3 else 3 * t))
                g = int(255 * abs(1 - 3 * (t - 1/3) if t >= 2/3 else 3 * (t - 1/3)))
                b = int(255 * abs(3 * (t - 2/3) if t < 2/3 else 3 - 3 * (t - 2/3)))
                
                await set_color(client, r, g, b)
                await asyncio.sleep(0.5)
            
            # Random color flash
            print("\n✨ Random color flashes...")
            for _ in range(5):
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                await set_color(client, r, g, b)
                await asyncio.sleep(0.7)
            
            # Return to white at the end
            print("\n⚪ Returning to white")
            await set_color(client, 255, 255, 255)
            
            print("\n✅ Color test complete!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

async def test_color_temperature():
    """Test different color temperatures (warm to cool white)"""
    print(f"🔌 Connecting to device: {ADDRESS}")
    
    try:
        async with BleakClient(ADDRESS) as client:
            print("✅ Connected successfully")
            
            # Test color temperatures
            print("\n🌡️ Testing color temperatures...")
            
            # Warm white (yellowish)
            print("Warm white")
            await set_color(client, 255, 223, 120)  # Warm white
            await asyncio.sleep(2)
            
            # Neutral white
            print("Neutral white")
            await set_color(client, 255, 255, 255)  # Pure white
            await asyncio.sleep(2)
            
            # Cool white (bluish)
            print("Cool white")
            await set_color(client, 220, 235, 255)  # Cool white
            await asyncio.sleep(2)
            
            # Gradual shift from warm to cool
            print("\n🌈 Shifting from warm to cool white...")
            steps = 10
            for i in range(steps + 1):
                # Interpolate between warm and cool
                r = int(255 - (35 * i / steps))
                g = int(223 + (12 * i / steps))
                b = int(120 + (135 * i / steps))
                
                await set_color(client, r, g, b)
                await asyncio.sleep(0.5)
            
            print("\n✅ Color temperature test complete!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    print("🔍 Starting Light Controller Test")
    print("Choose a test:")
    print("1. Primary Colors & Effects")
    print("2. Color Temperature Test")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        asyncio.run(test_primary_colors())
    elif choice == "2":
        asyncio.run(test_color_temperature())
    else:
        print("❌ Invalid choice, please enter 1 or 2")