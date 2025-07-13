#!/usr/bin/env python3
"""
Network Interface Error Checker
Written by a Network Engineer for Network Engineers
Simple, reliable, and gets the job done!
"""

from netmiko import ConnectHandler
from datetime import datetime
import sys

def read_hosts_file(filename='hosts.txt'):
    """Read device information from hosts.txt file"""
    devices = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                # Skip comments and empty lines
                line = line.strip()
                if line and not line.startswith('#'):
                    # Split the line: ip,username,password,device_type
                    parts = line.split(',')
                    if len(parts) == 4:
                        device = {
                            'ip': parts[0].strip(),
                            'username': parts[1].strip(),
                            'password': parts[2].strip(),
                            'device_type': parts[3].strip()
                        }
                        devices.append(device)
    except FileNotFoundError:
        print(f"ERROR: Cannot find {filename}")
        print("Make sure hosts.txt is in the same folder as this script")
        sys.exit(1)
    
    return devices

def show_interfaces_with_errors(error_threshold=100):
    """
    Connect to multiple switches and check interface errors
    Just like 'show interface | include errors' but better!
    """
    
    print("\n" + "="*60)
    print(f"INTERFACE ERROR CHECKER - Threshold: {error_threshold} errors")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Read devices from hosts.txt
    devices = read_hosts_file()
    
    if not devices:
        print("ERROR: No devices found in hosts.txt")
        return
    
    print(f"Found {len(devices)} devices to check\n")
    
    # Track if we found any problems
    total_problems = 0
    
    # Connect to each device
    for device_info in devices:
        print(f"Connecting to {device_info['ip']}...", end='', flush=True)
        
        try:
            # Make SSH connection using Netmiko
            connection = ConnectHandler(**device_info)
            print(" [CONNECTED]")
            
            # Get hostname for better output
            hostname = connection.find_prompt()[:-1]  # Remove # or > from prompt
            
            # Run command to check interface errors
            # This command works on most Cisco devices
            output = connection.send_command('show interfaces | include line protocol|input errors|output errors|CRC')
            
            # Parse the output
            lines = output.split('\n')
            current_interface = None
            
            for line in lines:
                # Check if this is an interface line
                if 'line protocol' in line:
                    # Extract interface name
                    current_interface = line.split()[0]
                
                # Check for error lines
                elif 'input errors' in line and current_interface:
                    # Extract error count
                    # Line format: "     12345 input errors, 0 CRC, 0 frame..."
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        error_count = int(parts[0])
                        
                        # Only show if above threshold
                        if error_count > error_threshold:
                            print(f"\n  PROBLEM FOUND on {hostname}")
                            print(f"  Interface: {current_interface}")
                            print(f"  Input Errors: {error_count}")
                            print(f"  Action: Check physical connection/cable/SFP")
                            total_problems += 1
            
            # Also check interface status for down interfaces
            int_status = connection.send_command('show ip interface brief | exclude unassigned')
            print(f"\n  Quick Interface Status for {hostname}:")
            print("  " + "-"*40)
            
            for line in int_status.split('\n')[1:]:  # Skip header
                if line and 'down' in line.lower():
                    print(f"  WARNING: {line.strip()}")
            
            # Disconnect
            connection.disconnect()
            print(f"  Disconnected from {hostname}\n")
            
        except Exception as e:
            print(f" [FAILED]")
            print(f"  Error: {str(e)}")
            print(f"  Check: IP reachability, credentials, SSH enabled\n")
            continue
    
    # Summary
    print("\n" + "="*60)
    if total_problems == 0:
        print("SUMMARY: All interfaces look good! No errors above threshold.")
    else:
        print(f"SUMMARY: Found {total_problems} interfaces with high error counts!")
        print("         Check those interfaces ASAP!")
    print("="*60 + "\n")

def main():
    """Main function - keep it simple!"""
    print("\nStarting Interface Error Checker...")
    print("Make sure hosts.txt is configured with your devices\n")
    
    # You can change the threshold here
    # 100 errors is a good starting point
    show_interfaces_with_errors(error_threshold=100)
    
    # Want to check for ANY errors? Use this instead:
    # show_interfaces_with_errors(error_threshold=0)

if __name__ == "__main__":
    main()