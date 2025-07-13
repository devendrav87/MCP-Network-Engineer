#!/usr/bin/env python3
"""
Network Switch Configuration Backup Script
Written by a Network Engineer for Network Engineers
Purpose: Automated backup of switch configurations using SSH
"""

from netmiko import ConnectHandler
from datetime import datetime
import os
import sys
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)

def read_hosts_file(filename='hosts.txt'):
    """Read device information from hosts.txt file"""
    devices = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for line_num, row in enumerate(reader, 1):
                # Skip comments and empty lines
                if not row or row[0].strip().startswith('#'):
                    continue
                
                if len(row) < 4:
                    logging.warning(f"Line {line_num}: Skipping incomplete entry")
                    continue
                
                device = {
                    'device_type': row[3].strip(),
                    'ip': row[0].strip(),
                    'username': row[1].strip(),
                    'password': row[2].strip(),
                    'port': 22,
                    'timeout': 30,
                    'global_delay_factor': 2
                }
                devices.append(device)
                print(device)
        logging.info(f"Loaded {len(devices)} devices from {filename}")
        return devices
        
    except FileNotFoundError:
        logging.error(f"Error: {filename} not found!")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading hosts file: {str(e)}")
        sys.exit(1)

def create_backup_folder():
    """Create backup folder with current date"""
    today = datetime.now().strftime("%Y-%m-%d")
    backup_folder = f"backups/{today}"
    
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        logging.info(f"Created backup folder: {backup_folder}")
    
    return backup_folder

def backup_single_device(device, backup_folder, retry_count=3):
    """Backup configuration for a single device with retry logic"""
    hostname = device.get('hostname', device['ip'])
    
    for attempt in range(retry_count):
        try:
            # Connect to device
            logging.info(f"Connecting to {hostname} ({device['ip']})...")
            connection = ConnectHandler(**device)
            
            # Enter enable mode if needed
            if connection.check_enable_mode() is False:
                connection.enable()
            
            # Get running configuration
            logging.info(f"Retrieving configuration from {hostname}...")
            config_output = connection.send_command('show running-config')
            
            # For some devices, might need different command
            if not config_output or len(config_output) < 100:
                config_output = connection.send_command('show run')
            
            # Disconnect
            connection.disconnect()
            
            # Save configuration to file
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{backup_folder}/{hostname}_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"! Backup of {hostname} ({device['ip']})\n")
                f.write(f"! Backup taken on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"! Device type: {device['device_type']}\n")
                f.write("!\n")
                f.write(config_output)
            
            logging.info(f"✅ SUCCESS: {hostname} backed up to {filename}")
            return {'status': 'success', 'device': hostname, 'filename': filename}
            
        except Exception as e:
            logging.error(f"❌ FAILED: {hostname} - Attempt {attempt + 1}/{retry_count}: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(5)  # Wait before retry
            else:
                return {'status': 'failed', 'device': hostname, 'error': str(e)}

def backup_all_switches_parallel(max_workers=5):
    """Backup all switches in parallel for faster execution"""
    # Read devices from file
    devices = read_hosts_file()
    
    if not devices:
        logging.error("No devices found in hosts.txt")
        return
    
    # Create backup folder
    backup_folder = create_backup_folder()
    
    # Summary statistics
    results = {'success': [], 'failed': []}
    
    logging.info(f"\n{'='*60}")
    logging.info(f"Starting backup for {len(devices)} devices")
    logging.info(f"{'='*60}\n")
    
    # Backup devices in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_device = {
            executor.submit(backup_single_device, device, backup_folder): device 
            for device in devices
        }
        
        for future in as_completed(future_to_device):
            result = future.result()
            if result['status'] == 'success':
                results['success'].append(result)
            else:
                results['failed'].append(result)
    
    # Print summary
    logging.info(f"\n{'='*60}")
    logging.info(f"BACKUP SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"Total devices: {len(devices)}")
    logging.info(f"Successful: {len(results['success'])}")
    logging.info(f"Failed: {len(results['failed'])}")
    
    if results['failed']:
        logging.info(f"\nFailed devices:")
        for device in results['failed']:
            logging.info(f"  - {device['device']}: {device['error']}")
    
    logging.info(f"\nBackups saved in: {backup_folder}")
    logging.info(f"{'='*60}\n")

def main():
    """Main function"""
    try:
        # Check if hosts.txt exists
        if not os.path.exists('hosts.txt'):
            logging.error("Error: hosts.txt file not found!")
            logging.info("Please create a hosts.txt file with device information.")
            logging.info("Format: ip_address,username,password,device_type")
            sys.exit(1)
        
        # Run backup
        backup_all_switches_parallel()
        
    except KeyboardInterrupt:
        logging.info("\nBackup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()