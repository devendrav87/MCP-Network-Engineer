#!/usr/bin/env python3
"""
Branch Office Configuration Generator
Generates router and switch configurations for branch offices
"""

import sys
from datetime import datetime


def read_hosts_file(filename='hosts.txt'):
    """Read device information from hosts.txt file"""
    devices = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue
                
                # Parse: ip_address only (for config generation)
                ip_address = line.split(',')[0].strip()
                if ip_address:
                    device = {
                        'ip': ip_address
                    }
                    devices.append(device)
                else:
                    print(f"⚠️  Skipping invalid line: {line}")
    except FileNotFoundError:
        print(f"⚠️  Warning: {filename} not found. Using example devices.")
        # Example devices if no hosts file
        devices = [
            {'ip': '10.50.1.1'},
            {'ip': '10.50.10.2'}
        ]
    
    return devices


def generate_router_config(city_name, device_ip, branch_ip_subnet="10.50"):
    """Generate router configuration"""
    hostname = f"{city_name}-RTR-01"
    wan_ip = f"{branch_ip_subnet}.1.1"
    lan_ip = f"{branch_ip_subnet}.10.1"
    
    config = f"""!
! Router Configuration for {hostname}
! Device IP: {device_ip}
! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
!
hostname {hostname}
!
! WAN Interface
interface GigabitEthernet0/0
 description WAN Interface to ISP
 ip address {wan_ip} 255.255.255.252
 no shutdown
!
! LAN Interface
interface GigabitEthernet0/1
 description LAN Interface to Switch
 ip address {lan_ip} 255.255.255.0
 no shutdown
!
! Default Route
ip route 0.0.0.0 0.0.0.0 {branch_ip_subnet}.1.2
!
! Enable SSH
ip domain-name {city_name.lower()}.local
crypto key generate rsa modulus 2048
ip ssh version 2
!
! Management Access
line vty 0 4
 transport input ssh
 login local
!
! Local User
username admin privilege 15 secret 0 YourSecurePassword123!
!
! Save Configuration
end
write memory
!"""
    
    return config, hostname


def generate_switch_config(city_name, device_ip, branch_ip_subnet="10.50"):
    """Generate switch configuration"""
    hostname = f"{city_name}-SW-01"
    mgmt_ip = f"{branch_ip_subnet}.10.2"
    gateway_ip = f"{branch_ip_subnet}.10.1"
    
    config = f"""!
! Switch Configuration for {hostname}
! Device IP: {device_ip}
! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
!
hostname {hostname}
!
! VLANs
vlan 10
 name Management
!
vlan 20
 name Users
!
vlan 30
 name Printers
!
vlan 40
 name Guest
!
! Management Interface
interface Vlan10
 description Management VLAN
 ip address {mgmt_ip} 255.255.255.0
 no shutdown
!
! Default Gateway
ip default-gateway {gateway_ip}
!
! User Ports (1-20)
interface range GigabitEthernet1/0/1-20
 description User Access Ports
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 spanning-tree bpduguard enable
!
! Printer Ports (21-22)
interface range GigabitEthernet1/0/21-22
 description Printer Ports
 switchport mode access
 switchport access vlan 30
 spanning-tree portfast
!
! Guest Ports (23-24)
interface range GigabitEthernet1/0/23-24
 description Guest Access Ports
 switchport mode access
 switchport access vlan 40
 spanning-tree portfast
 spanning-tree bpduguard enable
!
! Uplink to Router
interface GigabitEthernet1/0/48
 description Uplink to Router
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30,40
!
! Enable SSH
ip domain-name {city_name.lower()}.local
crypto key generate rsa modulus 2048
ip ssh version 2
!
! Management Access
line vty 0 4
 transport input ssh
 login local
!
! Local User
username admin privilege 15 secret 0 YourSecurePassword123!
!
! Save Configuration
end
write memory
!"""
    
    return config, hostname


def configure_branch_office(city_name, branch_ip_subnet="10.50"):
    """Main function to generate branch office configurations"""
    print(f"\n{'='*60}")
    print(f"🏢 BRANCH OFFICE CONFIGURATION GENERATOR")
    print(f"📍 Location: {city_name}")
    print(f"🌐 IP Subnet: {branch_ip_subnet}.0.0/16")
    print(f"{'='*60}")
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Read devices from hosts file
    devices = read_hosts_file()
    
    print(f"\n📋 Found {len(devices)} devices")
    
    # Generate configurations
    configs_generated = 0
    
    for i, device in enumerate(devices):
        device_num = i + 1
        
        # Determine device type (odd = router, even = switch)
        if device_num % 2 == 1:
            # Router
            print(f"\n📡 Generating ROUTER configuration #{device_num//2 + 1}")
            config, hostname = generate_router_config(city_name, device['ip'], branch_ip_subnet)
            filename = f"{city_name}_router_{device_num//2 + 1}_config.txt"
        else:
            # Switch
            print(f"\n🔌 Generating SWITCH configuration #{device_num//2}")
            config, hostname = generate_switch_config(city_name, device['ip'], branch_ip_subnet)
            filename = f"{city_name}_switch_{device_num//2}_config.txt"
        
        # Save configuration
        with open(filename, 'w') as f:
            f.write(config)
        
        print(f"   ✅ Generated: {filename}")
        print(f"   📋 Hostname: {hostname}")
        print(f"   🌐 Device IP: {device['ip']}")
        configs_generated += 1
    
    # Generate summary file
    summary_filename = f"{city_name}_deployment_summary.txt"
    with open(summary_filename, 'w') as f:
        f.write(f"Branch Office Deployment Summary\n")
        f.write(f"{'='*40}\n")
        f.write(f"Location: {city_name}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"IP Subnet: {branch_ip_subnet}.0.0/16\n\n")
        f.write(f"Network Design:\n")
        f.write(f"  WAN Subnet: {branch_ip_subnet}.1.0/30\n")
        f.write(f"  LAN Subnet: {branch_ip_subnet}.10.0/24\n")
        f.write(f"  Router LAN IP: {branch_ip_subnet}.10.1\n")
        f.write(f"  Switch MGMT IP: {branch_ip_subnet}.10.2\n\n")
        f.write(f"VLANs:\n")
        f.write(f"  VLAN 10: Management\n")
        f.write(f"  VLAN 20: Users\n")
        f.write(f"  VLAN 30: Printers\n")
        f.write(f"  VLAN 40: Guest\n\n")
        f.write(f"Generated Files:\n")
        for i in range(configs_generated):
            if i % 2 == 0:
                f.write(f"  - {city_name}_router_{i//2 + 1}_config.txt\n")
            else:
                f.write(f"  - {city_name}_switch_{i//2 + 1}_config.txt\n")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 CONFIGURATION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Generated {configs_generated} configurations")
    print(f"📄 Summary saved to: {summary_filename}")
    print(f"\n📁 Generated files:")
    for i in range(configs_generated):
        if i % 2 == 0:
            print(f"   - {city_name}_router_{i//2 + 1}_config.txt")
        else:
            print(f"   - {city_name}_switch_{i//2 + 1}_config.txt")
    print(f"   - {summary_filename}")
    print(f"\n💡 Next steps:")
    print(f"   1. Review the generated configurations")
    print(f"   2. Update passwords and secrets")
    print(f"   3. Copy/paste configs to devices via console")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python configure-branch-office.py <city_name> [branch_ip_subnet]")
        print("Example: python configure-branch-office.py Dallas 10.50")
        print("         python configure-branch-office.py Austin 10.51")
        sys.exit(1)
    
    city_name = sys.argv[1]
    branch_ip_subnet = sys.argv[2] if len(sys.argv) > 2 else "10.50"
    
    # Run configuration generator
    configure_branch_office(city_name, branch_ip_subnet)