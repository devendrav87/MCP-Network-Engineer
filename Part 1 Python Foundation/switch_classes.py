"""
Improved Switch Class - Network Engineer Version
More realistic switch behavior with proper networking practices
"""

class Switch:
    def __init__(self, hostname, management_ip, management_vlan=10):
        self.hostname = hostname
        self.management_ip = management_ip
        self.management_vlan = management_vlan
        
        # Initialize with standard VLANs
        self.vlans = {
            1: {"name": "default", "ports": []},
            management_vlan: {"name": "MGMT", "ports": []}
        }
        
        # Initialize 48 ports (more realistic)
        self.interfaces = {}
        
        # Initialize config history
        self.config_history = []
        
        # Access ports (1-44)
        for i in range(1, 45):
            self.interfaces[f"Gi1/0/{i}"] = {
                "status": "down",
                "mode": "access", 
                "vlan": 1,
                "description": "",
                "port_security": False,
                "speed": "auto",
                "duplex": "auto"
            }
        
        # Uplink/trunk ports (45-48)
        for i in range(45, 49):
            self.interfaces[f"Gi1/0/{i}"] = {
                "status": "down",
                "mode": "trunk",
                "allowed_vlans": "all",
                "native_vlan": 1,
                "description": "",
                "speed": "1000",
                "duplex": "full"
            }
    
    def add_vlan(self, vlan_id, name):
        """
        Add a VLAN - but smartly! No duplicates, no invalid IDs.
        This is like the switch checking your command before accepting it.
        """
        # Check if VLAN ID is valid (1-4094, just like real switches)
        if not 1 <= vlan_id <= 4094:
            print(f"❌ Error: VLAN ID must be 1-4094, got {vlan_id}")
            return False
        
        # Check if VLAN already exists (prevent duplicates automatically!)
        if vlan_id in self.vlans:
            print(f"⚠️  VLAN {vlan_id} already exists as '{self.vlans[vlan_id]['name']}'")
            return False
        
        # Add the VLAN
        self.vlans[vlan_id] = {"name": name, "ports": []}
        self.config_history.append(f"Added VLAN {vlan_id} ({name})")
        print(f"✅ Created VLAN {vlan_id}: {name}")
        return True
    
    
    def configure_trunk_port(self, interface, allowed_vlans="all", native_vlan=1):
        """Configure trunk port with proper validation"""
        if interface not in self.interfaces:
            print(f"❌ Interface {interface} doesn't exist")
            return False
            
        self.interfaces[interface]["mode"] = "trunk"
        self.interfaces[interface]["allowed_vlans"] = allowed_vlans
        self.interfaces[interface]["native_vlan"] = native_vlan
        self.interfaces[interface]["status"] = "up"
        
        print(f"✅ Configured {interface} as trunk (native VLAN {native_vlan})")
        return True
    
    def configure_port(self, interface, vlan=None, mode="access", description=""):
        """Configure an interface with VLAN assignment"""
        if interface not in self.interfaces:
            print(f"❌ Interface {interface} doesn't exist")
            return False
            
        port = self.interfaces[interface]
        
        if mode == "access" and vlan:
            if vlan not in self.vlans:
                print(f"❌ VLAN {vlan} doesn't exist")
                return False
            port["mode"] = "access"
            port["vlan"] = vlan
            port["status"] = "up"
            
            # Update VLAN membership
            self.vlans[vlan]["ports"].append(interface)
            
        port["description"] = description
        
        print(f"✅ Configured {interface}: VLAN {vlan}, {description}")
        return True
    
    def configure_port_security(self, interface, max_mac=2):
        """Add port security to access ports only"""
        if interface not in self.interfaces:
            print(f"❌ Interface {interface} doesn't exist")
            return False
            
        if self.interfaces[interface]["mode"] != "access":
            print(f"❌ Port security only for access ports")
            return False
            
        self.interfaces[interface]["port_security"] = True
        self.interfaces[interface]["max_mac"] = max_mac
        
        print(f"✅ Port security enabled on {interface} (max {max_mac} MACs)")
        return True
    
    def generate_config(self):
        """Generate config with proper network engineering practices"""
        from datetime import datetime
        
        config = f"""!
! Switch Configuration - {self.hostname}
! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
!
service password-encryption
service timestamps log datetime msec
!
hostname {self.hostname}
!
spanning-tree mode rapid-pvst
spanning-tree extend system-id
!
! VLANs
"""
        # Add VLANs
        for vlan_id, vlan_info in self.vlans.items():
            if vlan_id != 1:
                config += f"""vlan {vlan_id}
 name {vlan_info['name']}
!
"""
        
        # Management interface (NOT VLAN 1!)
        config += f"""!
interface Vlan{self.management_vlan}
 description Management Interface
 ip address {self.management_ip} 255.255.255.0
 no shutdown
!
"""
        
        # Configure interfaces
        for interface, settings in self.interfaces.items():
            config += f"interface {interface}\n"
            
            if settings.get("description"):
                config += f" description {settings['description']}\n"
            
            # Speed and duplex
            config += f" speed {settings.get('speed', 'auto')}\n"
            config += f" duplex {settings.get('duplex', 'auto')}\n"
            
            if settings["mode"] == "access":
                config += f" switchport mode access\n"
                config += f" switchport access vlan {settings['vlan']}\n"
                
                # Port security for access ports
                if settings.get("port_security"):
                    config += " switchport port-security\n"
                    config += f" switchport port-security maximum {settings.get('max_mac', 2)}\n"
                    config += " switchport port-security violation restrict\n"
                    config += " switchport port-security aging time 5\n"
                
                # Only portfast on access ports!
                config += " spanning-tree portfast\n"
                config += " spanning-tree bpduguard enable\n"
                
            elif settings["mode"] == "trunk":
                config += " switchport trunk encapsulation dot1q\n"
                config += " switchport mode trunk\n"
                config += f" switchport trunk native vlan {settings.get('native_vlan', 1)}\n"
                
                if settings.get("allowed_vlans") != "all":
                    config += f" switchport trunk allowed vlan {settings['allowed_vlans']}\n"
            
            # Shutdown status
            if settings["status"] == "up":
                config += " no shutdown\n"
            else:
                config += " shutdown\n"
            
            config += "!\n"
        
        # Security and access
        config += """!
! AAA and Security
aaa new-model
!
ip domain-name local.net
crypto key generate rsa modulus 2048
ip ssh version 2
ip ssh time-out 60
!
line con 0
 logging synchronous
 exec-timeout 15 0
line vty 0 15
 transport input ssh
 exec-timeout 15 0
!
! DHCP Snooping
ip dhcp snooping
ip dhcp snooping vlan 10,20,30
no ip dhcp snooping information option
!
end
"""
        
        filename = f"{self.hostname}_config.txt"
        with open(filename, 'w') as f:
            f.write(config)
            
        print(f"💾 Config saved to: {filename}")
        return config

# Quick demo
if __name__ == "__main__":
    # Create switch with management VLAN 10 (not VLAN 1!)
    sw = Switch("ACCESS-SW-01", "10.10.10.2", management_vlan=10)
    
    # Add VLANs
    sw.add_vlan(20, "USERS")
    sw.add_vlan(30, "SERVERS") 
    sw.add_vlan(40, "GUEST")
    sw.add_vlan(50, "VOICE")
    
    # Configure access ports with security
    sw.configure_port("Gi1/0/1", vlan=20, description="User PC")
    sw.configure_port_security("Gi1/0/1", max_mac=1)
    
    # Configure trunk to core
    sw.configure_trunk_port("Gi1/0/48", allowed_vlans="10,20,30,40,50", native_vlan=999)
    
    # Generate config
    sw.generate_config()