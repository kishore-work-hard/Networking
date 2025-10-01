#!/usr/bin/env python3

import asyncio
import subprocess
import csv
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import signal
import sys


class SimpleNetworkMonitor:
    def __init__(self, csv_file: str, ping_interval: int = 30):
        self.devices = self._load_devices(csv_file)
        self.ping_interval = ping_interval
        self.device_states = {}  # Track current online/offline state
        self.outage_data = {}    # Track outages per location
        self.active_outages = {} # Track ongoing outages
        self.shutdown_requested = False
        self.current_day = None  # Track what day we're monitoring
        
        self._setup_logging()
        self._setup_signal_handlers()
        self._initialize_day_data()
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime to readable string format"""
        return dt.strftime("%m/%d/%Y %H:%M:%S")
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string back to datetime object"""
        try:
            return datetime.strptime(timestamp_str, "%m/%d/%Y %H:%M:%S")
        except ValueError:
            # Fallback for old ISO format data
            return datetime.fromisoformat(timestamp_str.replace('T', ' ').split('.')[0])
    
    def _load_devices(self, csv_file: str) -> Dict[str, str]:
        """Load devices from CSV file - returns {ip: location}"""
        devices = {}
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    location = row['location'].strip()
                    ip = row['device'].strip()
                    devices[ip] = location
            print(f"Loaded {len(devices)} devices for monitoring")
        except Exception as e:
            print(f"Error loading devices: {e}")
            raise
        return devices
    
    def _setup_logging(self):
        """Setup basic logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
    
    def _setup_signal_handlers(self):
        """Handle shutdown signals"""
        def signal_handler(signum, frame):
            print("\nShutdown requested...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _initialize_day_data(self):
        """Initialize data for current day"""
        today = datetime.now().strftime('%Y%m%d')
        self.current_day = today
        
        # Load existing data for today
        data_file = Path(f"outages/outages_{today}.json")
        
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    self.outage_data = json.load(f)
                print(f"Loaded existing data for {today}")
            except Exception as e:
                print(f"Error loading existing data: {e}")
                self.outage_data = {}
        else:
            self.outage_data = {}
            print(f"Starting fresh monitoring for {today}")
    
    def _check_day_rollover(self):
        """Check if we've rolled over to a new day and reset data if needed"""
        today = datetime.now().strftime('%Y%m%d')
        
        if today != self.current_day:
            print(f"\n🗓️  Day rollover detected: {self.current_day} -> {today}")
            
            # Save final data for the previous day
            self._save_daily_data()
            
            # Handle any active outages - they continue into the new day
            if self.active_outages:
                print(f"Carrying over {len(self.active_outages)} active outages to new day")
                
                # Save references to active outages
                continuing_outages = {}
                for ip, outage_info in self.active_outages.items():
                    continuing_outages[ip] = {
                        'location': outage_info['location'],
                        'offline_timestamp': outage_info['offline_timestamp'],
                        'offline_at': outage_info['offline_at']
                    }
            
            # Reset for new day
            self.current_day = today
            self.outage_data = {}
            self.active_outages = {}
            
            # Re-create active outages for new day
            if 'continuing_outages' in locals():
                for ip, outage_info in continuing_outages.items():
                    location = outage_info['location']
                    
                    # Initialize location data if needed
                    if location not in self.outage_data:
                        self.outage_data[location] = []
                    
                    # Create new outage record for new day
                    outage_record = {
                        'offline_at': outage_info['offline_at'],  # Original time from previous day
                        'online_at': None,
                        'offline_for': 'ONGOING (continues from previous day)'
                    }
                    
                    self.outage_data[location].append(outage_record)
                    
                    # Restore to active outages
                    self.active_outages[ip] = {
                        'location': location,
                        'offline_at': outage_info['offline_at'],
                        'offline_timestamp': outage_info['offline_timestamp'],
                        'record_index': len(self.outage_data[location]) - 1
                    }
            
            # Update logging for new day
            self._setup_logging()
            print(f"✅ Successfully reset for new day: {today}")
    
    async def _ping_device(self, ip: str) -> bool:
        """Ping a device and return True if online"""
        try:
            cmd = ["ping", "-c", "1", "-W", "3", ip]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await result.wait()
            return result.returncode == 0
        except Exception:
            return False
    
    async def _confirm_offline(self, ip: str) -> bool:
        """Double-check if device is really offline after 2 seconds"""
        print(f"Confirming offline status for {self.devices[ip]} ({ip})...")
        await asyncio.sleep(2)
        
        # Try 3 times to be sure
        for i in range(3):
            if await self._ping_device(ip):
                print(f"False alarm - {self.devices[ip]} ({ip}) is actually online")
                return False
            await asyncio.sleep(1)
        
        print(f"Confirmed - {self.devices[ip]} ({ip}) is offline")
        return True
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes} minutes {secs} seconds"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours} hours {minutes} minutes {secs} seconds"
    
    def _record_outage_start(self, ip: str, location: str):
        """Record when a device goes offline"""
        now = datetime.now()
        
        # Initialize location data if needed
        if location not in self.outage_data:
            self.outage_data[location] = []
        
        # Create outage record immediately (with ongoing status)
        outage_record = {
            'offline_at': self._format_timestamp(now),
            'online_at': None,  # Still offline
            'offline_for': 'ONGOING'
        }
        
        # Add to outage data immediately
        self.outage_data[location].append(outage_record)
        
        # Record active outage with reference to the record index
        self.active_outages[ip] = {
            'location': location,
            'offline_at': self._format_timestamp(now),
            'offline_timestamp': now.timestamp(),
            'record_index': len(self.outage_data[location]) - 1  # Index of the record we just added
        }
        
        logging.warning(f"OUTAGE STARTED: {location} ({ip}) went offline at {now.strftime('%H:%M:%S')}")
    
    def _record_outage_end(self, ip: str):
        """Record when a device comes back online"""
        if ip not in self.active_outages:
            return
        
        now = datetime.now()
        outage = self.active_outages.pop(ip)
        
        # Calculate offline duration
        offline_duration = now.timestamp() - outage['offline_timestamp']
        
        # Update the existing record in outage_data
        location = outage['location']
        record_index = outage['record_index']
        
        # Update the record we created when outage started
        self.outage_data[location][record_index].update({
            'online_at': self._format_timestamp(now),
            'offline_for': self._format_duration(offline_duration)
        })
        
        offline_time = self._parse_timestamp(outage['offline_at']).strftime('%H:%M:%S')
        online_time = now.strftime('%H:%M:%S')
        
        logging.info(f"RECOVERY: {location} ({ip}) back online at {online_time} (was offline from {offline_time} - {self._format_duration(offline_duration)})")
    
    def _save_daily_data(self):
        """Save outage data to daily JSON file"""
        try:
            outages_dir = Path("outages")
            outages_dir.mkdir(exist_ok=True)
            
            # Use current_day instead of recalculating to avoid confusion during rollover
            filename = outages_dir / f"outages_{self.current_day}.json"
            
            # Update ongoing outages with current duration before saving
            current_time = datetime.now()
            for ip, outage_info in self.active_outages.items():
                location = outage_info['location']
                record_index = outage_info['record_index']
                offline_duration = current_time.timestamp() - outage_info['offline_timestamp']
                
                # Update the ongoing outage duration
                self.outage_data[location][record_index]['offline_for'] = f"ONGOING ({self._format_duration(offline_duration)})"
            
            with open(filename, 'w') as f:
                json.dump(self.outage_data, f, indent=2)
            
        except Exception as e:
            logging.error(f"Error saving data: {e}")
    
    async def _monitor_all_devices(self):
        """Monitor all devices in one cycle"""
        tasks = []
        for ip in self.devices.keys():
            task = self._monitor_single_device(ip)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _monitor_single_device(self, ip: str):
        """Monitor a single device"""
        location = self.devices[ip]
        is_online = await self._ping_device(ip)
        previous_state = self.device_states.get(ip, True)
        
        # State change detection
        if previous_state and not is_online:
            # Device went offline - confirm it
            if await self._confirm_offline(ip):
                self._record_outage_start(ip, location)
                self.device_states[ip] = False
        
        elif not previous_state and is_online:
            # Device came back online
            self._record_outage_end(ip)
            self.device_states[ip] = True
        
        elif ip not in self.device_states:
            # First time checking this device
            self.device_states[ip] = is_online
            if not is_online:
                # Device is offline from startup
                if await self._confirm_offline(ip):
                    self._record_outage_start(ip, location)
    
    async def start_monitoring(self):
        """Start the monitoring process"""
        print(f"Starting network monitoring for {len(self.devices)} devices")
        print(f"Ping interval: {self.ping_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while not self.shutdown_requested:
                # Check for day rollover before each monitoring cycle
                self._check_day_rollover()
                
                start_time = time.time()
                
                # Monitor all devices
                await self._monitor_all_devices()
                
                # Save data every cycle
                self._save_daily_data()
                
                # Show status
                online = sum(1 for state in self.device_states.values() if state)
                offline = len(self.device_states) - online
                active_outages = len(self.active_outages)
                
                elapsed = time.time() - start_time
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Online: {online}, Offline: {offline}, Active outages: {active_outages} (scan took {elapsed:.1f}s)")
                
                # Wait for next cycle
                await asyncio.sleep(max(0, self.ping_interval - elapsed))
        
        except Exception as e:
            logging.error(f"Monitoring error: {e}")
        
        finally:
            # Final save and summary
            self._save_daily_data()
            self._print_summary()
    
    def _print_summary(self):
        """Print final summary"""
        print("\n" + "="*50)
        print("MONITORING SESSION SUMMARY")
        print("="*50)
        
        total_outages = sum(len(outages) for outages in self.outage_data.values())
        print(f"Total outages today: {total_outages}")
        print(f"Active outages: {len(self.active_outages)}")
        
        if self.outage_data:
            print("\nOutages by location:")
            for location, outages in self.outage_data.items():
                print(f"  {location}: {len(outages)} outages")
        
        print(f"\nData saved to: outages/outages_{self.current_day}.json")


def main():
    try:
        # Configuration
        CSV_FILE = 'devices.csv'
        PING_INTERVAL = 3  # seconds
        
        monitor = SimpleNetworkMonitor(CSV_FILE, PING_INTERVAL)
        asyncio.run(monitor.start_monitoring())
        
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
