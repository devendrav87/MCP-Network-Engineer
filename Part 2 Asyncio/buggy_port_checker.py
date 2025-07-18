
import asyncio
import socket
import time

# Hosts and ports to check
targets = [
    {"host": "google.com", "port": 80},      # HTTP
    {"host": "google.com", "port": 443},     # HTTPS  
    {"host": "8.8.8.8", "port": 53},         # DNS
    {"host": "github.com", "port": 22},      # SSH
    {"host": "1.1.1.1", "port": 53},         # DNS
    {"host": "example.com", "port": 80},     # HTTP
]

# BUG #1: Missing async keyword
def check_port(host, port):
    """
    Check if a port is open on a host
    """
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        
        # BUG #2: This is blocking operation in async function
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return f"✅ {host}:{port} is OPEN"
        else:
            return f"❌ {host}:{port} is CLOSED"
            
    except Exception as e:
        return f"⚠️  {host}:{port} ERROR: {str(e)}"

async def check_all_ports():
    """
    Check all ports concurrently
    """
    print(f"🔍 Checking {len(targets)} ports...\n")
    
    start_time = time.time()
    
    # Create tasks
    tasks = []
    for target in targets:
        # BUG #3: Not awaiting the coroutine
        task = check_port(target["host"], target["port"])
        tasks.append(task)
    
    # Wait for all checks
    results = await asyncio.gather(*tasks)
    
    # Show results
    print("📋 PORT CHECK RESULTS:")
    print("-" * 40)
    for result in results:
        print(result)
    
    total_time = time.time() - start_time
    print("-" * 40)
    print(f"⏱️  Total time: {total_time:.2f} seconds")

# BUG #4: Wrong way to run asyncio
if __name__ == "__main__":
    print("🌐 Port Checker (Buggy Version)")
    print("=" * 40 + "\n")
    
    # This creates problems
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_all_ports)  # Missing ()
    
    print("\n✅ Done!")

