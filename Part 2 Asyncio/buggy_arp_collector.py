
import asyncio
import time

# List of devices to collect ARP from
devices = [
    {"ip": "192.168.1.1", "type": "router"},
    {"ip": "192.168.1.2", "type": "switch"},
    {"ip": "192.168.1.3", "type": "switch"},
    {"ip": "10.0.0.1", "type": "router"},
    {"ip": "10.0.0.2", "type": "switch"},
]

# BUG #1: This function is missing something important
def get_arp_table(device_ip):
    """
    Simulate getting ARP table from device
    In real world, this would SSH to device
    """
    print(f"🔄 Getting ARP table from {device_ip}...")
    
    # Simulate network delay
    time.sleep(2)  # BUG #2: This is blocking! Bad for asyncio
    
    # Fake ARP data
    arp_entries = [
        f"192.168.1.{i} - AA:BB:CC:DD:EE:{i:02X}" 
        for i in range(10, 15)
    ]
    
    return {
        "device": device_ip,
        "entries": arp_entries,
        "count": len(arp_entries)
    }

async def collect_all_arp_tables():
    """
    Collect ARP tables from all devices
    """
    print(f"📊 Collecting ARP from {len(devices)} devices\n")
    
    start_time = time.time()
    
    # BUG #3: This won't work as expected
    tasks = []
    for device in devices:
        # Create task but something is wrong here
        task = get_arp_table(device["ip"])  
        tasks.append(task)
    
    # BUG #4: gather is used wrong
    results = asyncio.gather(tasks)  # This is incorrect!
    
    # Process results
    total_entries = 0
    for result in results:
        print(f"\n📍 Device: {result['device']}")
        print(f"   ARP entries: {result['count']}")
        total_entries += result['count']
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f} seconds")
    print(f"📈 Total ARP entries: {total_entries}")

# BUG #5: Running the async function wrong
def main():
    """
    Main function
    """
    print("🌐 ARP Table Collector (Buggy Version)")
    print("=" * 40)
    
    # This won't work properly
    collect_all_arp_tables()
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()

