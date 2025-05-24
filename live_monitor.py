import asyncio
import websockets
import json
import time
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional
import threading
import pandas as pd

class LiveF1Monitor:
    def __init__(self):
        self.is_monitoring = False
        self.session_data = {}
        self.callbacks = []
        self.update_interval = 5  # seconds
        
    def add_callback(self, callback):
        """Add callback function for live updates"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, data):
        """Notify all registered callbacks with new data"""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in callback: {e}")
    
    async def start_monitoring(self, session_info: Dict):
        """Start monitoring a live session"""
        self.is_monitoring = True
        self.session_data = {
            'session_info': session_info,
            'start_time': datetime.now(),
            'lap_data': {},
            'timing_data': {},
            'weather_data': {},
            'track_status': 'GREEN'
        }
        
        print(f"Starting live monitoring for {session_info}")
        
        try:
            while self.is_monitoring:
                # Simulate fetching live data (in real implementation, this would connect to F1 API)
                live_data = await self._fetch_live_data()
                
                if live_data:
                    self._process_live_data(live_data)
                    self._notify_callbacks(live_data)
                
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            print(f"Error in live monitoring: {e}")
        finally:
            self.is_monitoring = False
    
    async def _fetch_live_data(self) -> Optional[Dict]:
        """Fetch live data from F1 API (simulated)"""
        try:
            # This is a simulation - in real implementation, you would connect to:
            # - F1 Live Timing API
            # - Ergast API for session data
            # - Official F1 data feeds
            
            current_time = datetime.now()
            session_time = (current_time - self.session_data['start_time']).total_seconds()
            
            # Simulate live timing data
            simulated_data = {
                'timestamp': current_time.isoformat(),
                'session_time': session_time,
                'drivers': self._generate_simulated_timing(),
                'weather': self._generate_simulated_weather(),
                'track_status': self._get_simulated_track_status(),
                'session_status': 'ACTIVE' if session_time < 5400 else 'FINISHED'  # 90 minutes
            }
            
            return simulated_data
            
        except Exception as e:
            print(f"Error fetching live data: {e}")
            return None
    
    def _generate_simulated_timing(self) -> List[Dict]:
        """Generate simulated timing data"""
        drivers = ['HAM', 'VER', 'LEC', 'RUS', 'SAI', 'NOR', 'PER', 'ALO', 'OCO', 'GAS']
        timing_data = []
        
        base_time = 90.0  # Base lap time in seconds
        
        for i, driver in enumerate(drivers):
            # Add some randomness and driver-specific performance
            lap_time = base_time + (i * 0.3) + (time.time() % 10) * 0.1
            
            timing_data.append({
                'driver': driver,
                'position': i + 1,
                'last_lap_time': f"{int(lap_time // 60)}:{lap_time % 60:06.3f}",
                'best_lap_time': f"{int((lap_time - 0.5) // 60)}:{(lap_time - 0.5) % 60:06.3f}",
                'gap_to_leader': f"+{i * 0.8:.3f}" if i > 0 else "LEADER",
                'sector_1': f"{20 + i * 0.1:.3f}",
                'sector_2': f"{35 + i * 0.15:.3f}",
                'sector_3': f"{25 + i * 0.12:.3f}",
                'speed_trap': f"{320 - i * 2}",
                'tire_compound': 'MEDIUM',
                'tire_age': int(time.time() % 30),
                'pit_stops': int(time.time() % 3)
            })
        
        return timing_data
    
    def _generate_simulated_weather(self) -> Dict:
        """Generate simulated weather data"""
        return {
            'air_temperature': 25.0 + (time.time() % 100) * 0.1,
            'track_temperature': 35.0 + (time.time() % 100) * 0.15,
            'humidity': 60.0 + (time.time() % 50) * 0.2,
            'wind_speed': 5.0 + (time.time() % 20) * 0.1,
            'wind_direction': int(time.time() % 360),
            'rainfall': 0.0,
            'pressure': 1013.25
        }
    
    def _get_simulated_track_status(self) -> str:
        """Get simulated track status"""
        statuses = ['GREEN', 'YELLOW', 'RED', 'SC', 'VSC']
        # Mostly green flag
        if time.time() % 100 < 85:
            return 'GREEN'
        else:
            return statuses[int(time.time() % len(statuses))]
    
    def _process_live_data(self, data: Dict):
        """Process and store live data"""
        timestamp = data['timestamp']
        
        # Update session data
        self.session_data['timing_data'][timestamp] = data['drivers']
        self.session_data['weather_data'][timestamp] = data['weather']
        self.session_data['track_status'] = data['track_status']
        
        # Keep only last 100 data points to manage memory
        if len(self.session_data['timing_data']) > 100:
            oldest_key = min(self.session_data['timing_data'].keys())
            del self.session_data['timing_data'][oldest_key]
            del self.session_data['weather_data'][oldest_key]
    
    def stop_monitoring(self):
        """Stop live monitoring"""
        self.is_monitoring = False
        print("Live monitoring stopped")
    
    def get_current_standings(self) -> List[Dict]:
        """Get current race standings"""
        if not self.session_data['timing_data']:
            return []
        
        latest_timestamp = max(self.session_data['timing_data'].keys())
        return self.session_data['timing_data'][latest_timestamp]
    
    def get_driver_history(self, driver: str, data_points: int = 20) -> Dict:
        """Get historical data for a specific driver"""
        history = {
            'timestamps': [],
            'lap_times': [],
            'positions': [],
            'gaps': [],
            'tire_ages': []
        }
        
        timestamps = sorted(self.session_data['timing_data'].keys())[-data_points:]
        
        for timestamp in timestamps:
            timing_data = self.session_data['timing_data'][timestamp]
            
            for driver_data in timing_data:
                if driver_data['driver'] == driver:
                    history['timestamps'].append(timestamp)
                    history['lap_times'].append(driver_data['last_lap_time'])
                    history['positions'].append(driver_data['position'])
                    history['gaps'].append(driver_data['gap_to_leader'])
                    history['tire_ages'].append(driver_data['tire_age'])
                    break
        
        return history
    
    def get_weather_history(self, data_points: int = 20) -> Dict:
        """Get weather history"""
        history = {
            'timestamps': [],
            'air_temp': [],
            'track_temp': [],
            'humidity': [],
            'wind_speed': [],
            'rainfall': []
        }
        
        timestamps = sorted(self.session_data['weather_data'].keys())[-data_points:]
        
        for timestamp in timestamps:
            weather_data = self.session_data['weather_data'][timestamp]
            history['timestamps'].append(timestamp)
            history['air_temp'].append(weather_data['air_temperature'])
            history['track_temp'].append(weather_data['track_temperature'])
            history['humidity'].append(weather_data['humidity'])
            history['wind_speed'].append(weather_data['wind_speed'])
            history['rainfall'].append(weather_data['rainfall'])
        
        return history
    
    def get_session_statistics(self) -> Dict:
        """Get session statistics"""
        if not self.session_data['timing_data']:
            return {}
        
        latest_data = self.get_current_standings()
        
        stats = {
            'session_duration': (datetime.now() - self.session_data['start_time']).total_seconds(),
            'total_updates': len(self.session_data['timing_data']),
            'current_leader': latest_data[0]['driver'] if latest_data else None,
            'fastest_lap': min([d['best_lap_time'] for d in latest_data]) if latest_data else None,
            'total_drivers': len(latest_data) if latest_data else 0
        }
        
        return stats
    
    def export_live_session(self, filename: str):
        """Export live session data"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.session_data, f, indent=2, default=str)
            print(f"Live session data exported to {filename}")
        except Exception as e:
            print(f"Error exporting live session: {e}")
    
    def create_live_dataframe(self) -> pd.DataFrame:
        """Create a pandas DataFrame from live timing data"""
        try:
            all_data = []
            
            for timestamp, drivers in self.session_data['timing_data'].items():
                for driver_data in drivers:
                    row = driver_data.copy()
                    row['timestamp'] = timestamp
                    all_data.append(row)
            
            return pd.DataFrame(all_data)
        except Exception as e:
            print(f"Error creating DataFrame: {e}")
            return pd.DataFrame()

class LiveDataCallback:
    """Example callback class for handling live data updates"""
    
    def __init__(self, name: str):
        self.name = name
        self.update_count = 0
    
    def __call__(self, data: Dict):
        """Handle live data update"""
        self.update_count += 1
        
        print(f"\n--- {self.name} Update #{self.update_count} ---")
        print(f"Time: {data['timestamp']}")
        print(f"Track Status: {data['track_status']}")
        
        # Show top 3 positions
        drivers = data['drivers'][:3]
        print("Top 3:")
        for driver in drivers:
            print(f"  {driver['position']}. {driver['driver']} - {driver['last_lap_time']} ({driver['gap_to_leader']})")
        
        # Show weather
        weather = data['weather']
        print(f"Weather: Air {weather['air_temperature']:.1f}°C, Track {weather['track_temperature']:.1f}°C")

class LiveAnalyticsCallback:
    """Advanced callback for live analytics"""
    
    def __init__(self, name: str):
        self.name = name
        self.update_count = 0
        self.position_changes = {}
        self.lap_time_trends = {}
        
    def __call__(self, data: Dict):
        """Handle live data update with analytics"""
        self.update_count += 1
        
        # Track position changes
        for driver_data in data['drivers']:
            driver = driver_data['driver']
            position = driver_data['position']
            
            if driver in self.position_changes:
                prev_position = self.position_changes[driver][-1] if self.position_changes[driver] else position
                if prev_position != position:
                    change = prev_position - position
                    print(f"📈 {driver} moved {'up' if change > 0 else 'down'} {abs(change)} position(s)")
            
            if driver not in self.position_changes:
                self.position_changes[driver] = []
            self.position_changes[driver].append(position)
            
            # Track lap time trends
            if driver not in self.lap_time_trends:
                self.lap_time_trends[driver] = []
            self.lap_time_trends[driver].append(driver_data['last_lap_time'])
        
        # Detect fastest lap
        current_times = [d['last_lap_time'] for d in data['drivers']]
        fastest_driver = min(data['drivers'], key=lambda x: x['last_lap_time'])
        print(f"🏁 Fastest lap this update: {fastest_driver['driver']} - {fastest_driver['last_lap_time']}")
