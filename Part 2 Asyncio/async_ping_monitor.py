import asyncio
import subprocess
import time
from datetime import datetime

# List of devices to ping - you can add your routers, switches here
devices = [
    "8.8.8.8",        # Google DNS
    "1.1.1.1",        # Cloudflare DNS
    "192.168.1.1",    # Your router maybe?
    "10.0.0.1",       # Another device
    "8.8.4.4",        # Google DNS 2
]

async def ping_device(device_ip):
    """
    This function pings one device
    It's async so it doesn't block other pings
    """
    # We will try to ping 2 times
    ping_command = ["ping", "-c", "2", "-W", "1", device_ip]
    
    try:
        # Run ping command
        process = await asyncio.create_subprocess_exec(
            *ping_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for ping to finish
        stdout, stderr = await process.communicate()
        
        # Check if ping worked (return code 0 means success)
        if process.returncode == 0:
            return f"✅ {device_ip} is UP"
        else:
            return f"❌ {device_ip} is DOWN"
            
    except Exception as e:
        # Something went wrong
        return f"⚠️  {device_ip} ERROR: {str(e)}"

async def monitor_all_devices():
    """
    This function monitors all devices at the same time
    That's the magic of asyncio!
    """
    print(f"\n🔍 Starting ping monitor at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 Monitoring {len(devices)} devices...\n")
    
    # Start timer to see how fast we are
    start_time = time.time()
    
    # Create tasks for all devices at once
    # This is like asking 5 people to do work at same time
    tasks = []
    for device in devices:
        task = asyncio.create_task(ping_device(device))
        tasks.append(task)
    
    # Wait for all pings to complete
    results = await asyncio.gather(*tasks)
    
    # Show results
    print("📋 PING RESULTS:")
    print("-" * 40)
    for result in results:
        print(result)
    
    # Show how long it took
    total_time = time.time() - start_time
    print("-" * 40)
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"💡 Without asyncio, this would take ~{len(devices) * 2} seconds!")

async def main():
    """
    Main function that runs forever
    It pings all devices every 10 seconds
    """
    print("🚀 Network Ping Monitor Started!")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Monitor all devices
            await monitor_all_devices()
            
            # Wait 10 seconds before next round
            print("\n💤 Waiting 10 seconds for next check...\n")
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n👋 Ping monitor stopped by user. Bye!")

# This is where program starts
if __name__ == "__main__":
    asyncio.run(main())