#!/usr/bin/env python3
"""MCP Server for Arista switches"""

import json
import os
from typing import List, Optional
import yaml
from dotenv import load_dotenv
import pyeapi
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Create MCP server
mcp = FastMCP("arista-mcp")

# Load devices from yaml
with open('devices.yaml', 'r') as f:
    config = yaml.safe_load(f)

DEVICES = {}
for name, device in config.get('devices', {}).items():
    if 'password' in device and device['password'].startswith('${'):
        var_name = device['password'][2:-1]
        device['password'] = os.getenv(var_name, "")
    DEVICES[name] = device

# Simple connection manager
class AristaManager:
    def __init__(self):
        self.connections = {}
    
    def connect(self, device_name):
        if device_name not in DEVICES:
            return None
            
        if device_name not in self.connections:
            device = DEVICES[device_name]
            try:
                conn = pyeapi.connect(
                    host=device['hostname'],
                    username=device['username'],
                    password=device['password'],
                    transport=device.get('transport', 'https')
                )
                self.connections[device_name] = conn
            except:
                return None
        return self.connections[device_name]
    
    def run_command(self, device_name, command):
        try:
            conn = self.connect(device_name)
            if conn:
                result = conn.execute([command])
                return result['result'][0]
            return {'error': 'Connection failed'}
        except Exception as e:
            return {'error': str(e)}

manager = AristaManager()

# MCP Tools
@mcp.tool()
async def show_version(device_names: Optional[List[str]] = None) -> str:
    """Get version info from switches"""
    if device_names is None:
        device_names = list(DEVICES.keys())
    
    results = {}
    for device in device_names:
        results[device] = manager.run_command(device, 'show version')
    
    return json.dumps(results, indent=2)

@mcp.tool()
async def show_ip_routes(device_names: Optional[List[str]] = None) -> str:
    """Get routing table"""
    if device_names is None:
        device_names = list(DEVICES.keys())
    
    results = {}
    for device in device_names:
        results[device] = manager.run_command(device, 'show ip route summary')
    
    return json.dumps(results, indent=2)

@mcp.tool()
async def show_lldp_neighbors(device_names: Optional[List[str]] = None) -> str:
    """See what's connected to what"""
    if device_names is None:
        device_names = list(DEVICES.keys())
    
    results = {}
    for device in device_names:
        results[device] = manager.run_command(device, 'show lldp neighbors')
    
    return json.dumps(results, indent=2)

@mcp.tool()
async def show_interfaces(device_names: Optional[List[str]] = None, interface_name: Optional[str] = None) -> str:
    """Get interface info - all interfaces or specific one"""
    if device_names is None:
        device_names = list(DEVICES.keys())
    
    results = {}
    for device in device_names:
        if interface_name:
            # Get specific interface
            output = manager.run_command(device, f'show interfaces {interface_name}')
        else:
            # Get all interfaces
            output = manager.run_command(device, 'show interfaces')
        results[device] = output
    
    return json.dumps(results, indent=2)

if __name__ == "__main__":
    print("Starting MCP Server...")
    print(f"Loaded {len(DEVICES)} devices")
    
    port = int(os.getenv('MCP_SERVER_PORT', 3210))
    mcp.run(transport="http", port=port)