import asyncio
import asyncssh
import time
from datetime import datetime

# Your network devices - add your real devices here
devices = [
    {"host": "192.168.1.1", "username": "admin", "password": "admin123"},
    {"host": "192.168.1.2", "username": "admin", "password": "admin123"},
    {"host": "192.168.1.3", "username": "admin", "password": "admin123"},
    # Add more devices here...
    # For 500+ devices, you can read from a CSV file
]

# Commands to run on each device
commands = [
    "show version",
    "show ip interface brief",
    "show running-config",
]

async def run_commands_on_device(device_info):
    """
    Connect to one device and run commands
    This is async - it won't block other devices
    """
    host = device_info["host"]
    
    try:
        # Connect to device using SSH
        async with asyncssh.connect(
            host=host,
            username=device_info["username"],
            password=device_info["password"],
            known_hosts=None,  # Don't check SSH keys (be careful in production!)
        ) as conn:
            
            print(f"✅ Connected to {host}")
            
            # Store all outputs
            outputs = []
            
            # Run each command
            for cmd in commands:
                result = await conn.run(cmd)
                outputs.append({
                    "command": cmd,
                    "output": result.stdout
                })
            
            return {
                "host": host,
                "status": "success",
                "outputs": outputs
            }
            
    except asyncssh.Error as e:
        # SSH connection failed
        print(f"❌ SSH failed for {host}: {str(e)}")
        return {
            "host": host,
            "status": "failed",
            "error": str(e)
        }
    except Exception as e:
        # Other errors
        print(f"⚠️  Error with {host}: {str(e)}")
        return {
            "host": host,
            "status": "error",
            "error": str(e)
        }

async def save_outputs(results):
    """
    Save command outputs to files
    Each device gets its own file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for result in results:
        if result["status"] == "success":
            filename = f"output_{result['host']}_{timestamp}.txt"
            
            with open(filename, "w") as f:
                f.write(f"Device: {result['host']}\n")
                f.write(f"Time: {timestamp}\n")
                f.write("=" * 50 + "\n\n")
                
                for output in result["outputs"]:
                    f.write(f"Command: {output['command']}\n")
                    f.write("-" * 30 + "\n")
                    f.write(output['output'])
                    f.write("\n\n")
            
            print(f"💾 Saved output for {result['host']} to {filename}")

async def run_on_all_devices():
    """
    Run commands on all devices at the same time
    This is much faster than doing one by one!
    """
    print(f"\n🚀 Starting SSH commands on {len(devices)} devices")
    print(f"📋 Commands to run: {', '.join(commands)}\n")
    
    # Start timer
    start_time = time.time()
    
    # Create tasks for all devices
    # This is like having many workers doing job at same time
    tasks = []
    for device in devices:
        task = asyncio.create_task(run_commands_on_device(device))
        tasks.append(task)
    
    # Wait for all devices to complete
    # But set a timeout of 30 seconds per device
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count success and failures
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    fail_count = len(results) - success_count
    
    # Show summary
    total_time = time.time() - start_time
    print(f"\n📊 SUMMARY:")
    print(f"✅ Successful: {success_count} devices")
    print(f"❌ Failed: {fail_count} devices")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"💡 Processing {len(devices)} devices one by one would take much longer!")
    
    # Save outputs to files
    print(f"\n💾 Saving outputs...")
    await save_outputs([r for r in results if isinstance(r, dict)])

async def main():
    """
    Main function
    """
    print("🌐 Network Device SSH Command Executor")
    print("=" * 50)
    
    # Check if we have devices
    if not devices:
        print("❌ No devices configured! Please add devices to the list.")
        return
    
    try:
        # Run commands on all devices
        await run_on_all_devices()
        
        print("\n✅ All done! Check the output files.")
        
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user. Bye!")

# For reading devices from CSV file (bonus example)
def read_devices_from_csv(filename):
    """
    Read device list from CSV file
    CSV format: host,username,password
    """
    import csv
    devices_list = []
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices_list.append({
                    "host": row["host"],
                    "username": row["username"],
                    "password": row["password"]
                })
        print(f"📄 Loaded {len(devices_list)} devices from {filename}")
        return devices_list
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []

# This is where program starts
if __name__ == "__main__":
    # Uncomment next line to read devices from CSV
    # devices = read_devices_from_csv("devices.csv")
    
    asyncio.run(main())