# 🌐 MCP Server for Arista Network Automation

An AI-powered network assistant that bridges natural language queries with Arista switch management through the Model Context Protocol (MCP). Talk to your network infrastructure using plain English in VS Code, Claude, or any MCP-compatible AI assistant.

## 📖 Table of Contents

- [Why This Project Exists](#-why-this-project-exists)
- [What It Does](#-what-it-does)
- [Architecture Overview](#-architecture-overview)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Code Walkthrough](#-code-walkthrough-mcp_serverpy-explained)
- [VS Code Integration](#-vs-code-integration)


## 🤔 Why This Project Exists

### The Problem

Network engineers face daily challenges:
- **Command Memorization**: Different vendors, different syntaxes - `show ip interface brief` vs `show interfaces terse` vs `show interfaces status`
- **Multi-Device Management**: Checking 50 switches means 50 SSH sessions
- **Context Switching**: Jumping between CLI, documentation, and monitoring tools
- **Barrier to Entry**: Junior engineers need months to learn command syntax
- **3 AM Troubleshooting**: When you're half-awake, remembering exact commands is hard

### The Solution

This MCP server transforms network operations from:
```bash
ssh admin@10.0.0.1
Password: ******
switch1>enable
switch1#show interfaces status
switch1#exit
ssh admin@10.0.0.2
# ... repeat for every switch ...
```

To:
```text
You: "Check if any interfaces are down on my switches"
AI: "I found 3 interfaces down: Ethernet4 on spine1, Ethernet8 and Ethernet12 on spine2"
```

## 🎯 What It Does

This MCP server creates a natural language interface to your Arista network infrastructure:

- **Device Health Monitoring**: "Are all my switches running the latest version?"
- **Interface Management**: "Show me traffic on Ethernet1"
- **Routing Verification**: "How many BGP routes on spine1?"
- **Topology Discovery**: "Map my network connections"
- **Multi-Device Queries**: "Check LLDP neighbors on all switches"

All through conversational AI in your favorite tools (VS Code, Claude, ChatGPT with plugins, etc.).

## 🏗️ Architecture Overview

```mermaid
graph LR
    A[VS Code/Claude] -->|Natural Language| B[MCP Server]
    B -->|JSON-RPC| C[FastMCP Framework]
    C -->|Function Calls| D[Tool Handlers]
    D -->|pyeapi| E[Arista eAPI]
    E -->|HTTPS| F[Arista Switches]
    
    style A fill:#e1f5e1
    style B fill:#fff3cd
    style F fill:#cce5ff
```

### Component Breakdown

1. **AI Interface Layer**: VS Code Copilot, Claude, or any MCP client
2. **MCP Server**: Our Python server handling natural language → network commands
3. **FastMCP Framework**: Manages MCP protocol, JSON-RPC communication
4. **pyeapi Library**: Arista's Python SDK for switch communication
5. **Arista eAPI**: RESTful API on Arista switches (HTTPS-based)

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Arista switches with eAPI enabled
- Network connectivity to your switches


### Step 1: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastmcp pyeapi pyyaml python-dotenv
```

### Step 2: Enable eAPI on Arista Switches

SSH to each switch and run:
```bash
configure
management api http-commands
   no shutdown
   protocol https port 443
   no protocol http
end
write memory
```

## ⚙️ Configuration

### 1. Create `devices.yaml`

```yaml
devices:
  spine1:
    hostname: 10.0.0.1
    username: admin
    password: ${ARISTA_PASSWORD}  # Uses environment variable
    transport: https
    
  spine2:
    hostname: 10.0.0.2
    username: admin
    password: ${ARISTA_PASSWORD}
    transport: https
    
  leaf1:
    hostname: 10.0.0.11
    username: admin
    password: ${ARISTA_PASSWORD}
    transport: https
```

### 2. Create `.env` File

```bash
# .env
ARISTA_PASSWORD=your_secure_password_here
MCP_SERVER_PORT=3210
```
## 🔍 Code Walkthrough: `mcp_server.py` Explained

Let's break down the MCP server line by line to understand the what and why:

### 1. Imports and Setup (Lines 1-15)

```python
#!/usr/bin/env python3
"""MCP Server for Arista switches"""

import json
import os
from typing import List, Optional
import yaml
from dotenv import load_dotenv
import pyeapi
from fastmcp import FastMCP
```

**Why these imports?**
- `json`: MCP requires JSON responses for structured data
- `yaml`: Human-readable device configuration (easier than JSON for configs)
- `dotenv`: Security best practice - never hardcode passwords
- `pyeapi`: Arista's official Python library for switch communication
- `FastMCP`: The framework that handles MCP protocol complexity for us

### 2. Environment and Server Initialization (Lines 12-15)

```python
load_dotenv()
mcp = FastMCP("arista-mcp")
```

**Why?**
- `load_dotenv()`: Loads passwords from .env file (keeps secrets out of code)
- `FastMCP("arista-mcp")`: Creates our MCP server with a unique identifier

### 3. Device Configuration Loading (Lines 17-26)

```python
with open('devices.yaml', 'r') as f:
    config = yaml.safe_load(f)

DEVICES = {}
for name, device in config.get('devices', {}).items():
    if 'password' in device and device['password'].startswith('${'):
        var_name = device['password'][2:-1]
        device['password'] = os.getenv(var_name, "")
    DEVICES[name] = device
```

**Why this approach?**
- **YAML for configuration**: More readable than JSON, standard in network automation
- **Environment variable substitution**: `${ARISTA_PASSWORD}` → actual password
- **Security**: Passwords never appear in configuration files
- **Flexibility**: Easy to add/remove devices without code changes

### 4. Connection Manager Class (Lines 28-57)

```python
class AristaManager:
    def __init__(self):
        self.connections = {}
```

**Why a connection manager?**
- **Connection pooling**: Reuse connections instead of creating new ones each time
- **Performance**: SSH/HTTPS handshake is slow (~2 seconds), caching saves time
- **Resource management**: Prevents connection exhaustion on switches

```python
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
```

**Why this logic?**
- **Validation**: Check device exists before connecting
- **Error handling**: Gracefully handle connection failures
- **HTTPS default**: More secure than HTTP

```python
def run_command(self, device_name, command):
    try:
        conn = self.connect(device_name)
        if conn:
            result = conn.execute([command])
            return result['result'][0]
        return {'error': 'Connection failed'}
    except Exception as e:
        return {'error': str(e)}
```

**Why structured error handling?**
- **Consistent responses**: Always return a dict (success or error)
- **Debugging**: Error messages help troubleshoot issues

### 5. MCP Tool: show_version (Lines 61-71)

```python
@mcp.tool()
async def show_version(device_names: Optional[List[str]] = None) -> str:
    """Get version info from switches"""
    if device_names is None:
        device_names = list(DEVICES.keys())
    
    results = {}
    for device in device_names:
        results[device] = manager.run_command(device, 'show version')
    
    return json.dumps(results, indent=2)
```

**Why this tool?**
- **Health check**: Version info tells us uptime, model, serial number
- **Inventory**: Quick audit of all devices
- **Troubleshooting**: "Is this device running the buggy version?"

**Why these design choices?**
- `@mcp.tool()`: Decorator exposes function to AI assistants
- `async`: MCP requires async functions (even if we're not using async internally)
- `Optional[List[str]]`: Can query specific devices or all
- `json.dumps()`: MCP expects string responses, not Python objects

### 6. MCP Tool: show_interfaces (Lines 96-111)

```python
@mcp.tool()
async def show_interfaces(device_names: Optional[List[str]] = None, 
                         interface_name: Optional[str] = None) -> str:
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
```

**Why this flexibility?**
- **Granular queries**: "Show me Ethernet1" vs "Show all interfaces"
- **Performance**: Specific interface queries are faster
- **Natural language**: AI can decide whether to query one or all

**Use cases:**
- "Is Ethernet1 up?" → `show_interfaces(interface_name="Ethernet1")`
- "Show all interfaces on spine1" → `show_interfaces(device_names=["spine1"])`
- "What's the traffic on Management1?" → Specific interface with counters

### 7. MCP Tool: show_ip_routes (Lines 73-82)

```python
@mcp.tool()
async def show_ip_routes(device_names: Optional[List[str]] = None) -> str:
    """Get routing table"""
    # ... implementation ...
```

**Why routing information?**
- **Connectivity verification**: Are routes being learned?
- **Troubleshooting**: Missing routes = connectivity issues
- **BGP monitoring**: How many routes from peers?

### 8. MCP Tool: show_lldp_neighbors (Lines 84-94)

```python
@mcp.tool()
async def show_lldp_neighbors(device_names: Optional[List[str]] = None) -> str:
    """See what's connected to what"""
    # ... implementation ...
```

**Why LLDP?**
- **Topology discovery**: Automatically map physical connections
- **Verification**: Is everything cabled correctly?

### 9. Main Execution Block (Lines 113-118)

```python
if __name__ == "__main__":
    print("Starting MCP Server...")
    print(f"Loaded {len(DEVICES)} devices")
    
    port = int(os.getenv('MCP_SERVER_PORT', 3210))
    mcp.run(transport="http", port=port)
```

**Why these choices?**
- **Configurable port**: Environment variable or default 3210
- **HTTP transport**: Simpler than WebSocket for local development


## 🔧 VS Code Integration

### Step 1: Configure MCP in VS Code

Create `.vscode/mcp.json` in your workspace:

```json
{
    "servers": {
        "arista-network-assistant": {
            "url": "http://localhost:3210/mcp",
            "type": "http",
            "description": "Arista Network MCP Server"
        }
    }
}
```

### Step 2: Start the Server

```bash
# In terminal
python mcp_server.py
```

### Step 3: Use with Copilot

Open Copilot Chat and prefix queries with "Using MCP":
- "Using MCP, show me all interfaces that are down"
- "Using MCP, what's the uptime of my switches?"

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused
```
Error: Connection to 10.0.0.1 refused
```
**Solution**: Enable eAPI on the switch:
```bash
switch# configure
switch(config)# management api http-commands
switch(config-mgmt-api-http-cmds)# no shutdown
```

#### 2. SSL Certificate Error
```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```
**Solution**: For development, disable SSL verification:
```python
conn = pyeapi.connect(host=..., transport='https', verify=False)
```

#### 3. MCP Server Not Found in VS Code
**Solution**: 
- Check server is running: `curl http://localhost:3210/mcp`
- Reload VS Code window
- Check `.vscode/mcp.json` syntax

#### 4. Timeout Errors
```
Error: Command timeout
```
**Solution**: Increase timeout in pyeapi:
```python
conn = pyeapi.connect(host=..., timeout=30)
```


**Built with ❤️ by network engineers, for network engineers**