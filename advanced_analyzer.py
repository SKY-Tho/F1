import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

class AdvancedF1Analyzer:
    def __init__(self):
        fastf1.Cache.enable_cache('f1_cache')
        self.session = None
        
    def load_session(self, year: int, round_number: int, session_type: str):
        """Load session with telemetry data"""
        try:
            self.session = fastf1.get_session(year, round_number, session_type)
            self.session.load(telemetry=True, weather=True, messages=True)
            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    
    def get_telemetry_comparison(self, driver1: str, driver2: str, lap_type: str = 'fastest'):
        """Compare telemetry data between two drivers"""
        if not self.session:
            return None
            
        try:
            # Get laps
            if lap_type == 'fastest':
                lap1 = self.session.laps.pick_driver(driver1).pick_fastest()
                lap2 = self.session.laps.pick_driver(driver2).pick_fastest()
            else:
                lap_num = int(lap_type)
                lap1 = self.session.laps.pick_driver(driver1).pick_lap(lap_num)
                lap2 = self.session.laps.pick_driver(driver2).pick_lap(lap_num)
            
            # Get telemetry
            tel1 = lap1.get_telemetry()
            tel2 = lap2.get_telemetry()
            
            return {
                'driver1': driver1,
                'driver2': driver2,
                'lap1_time': lap1['LapTime'],
                'lap2_time': lap2['LapTime'],
                'telemetry1': tel1,
                'telemetry2': tel2
            }
            
        except Exception as e:
            print(f"Error getting telemetry: {e}")
            return None
    
    def plot_speed_comparison(self, driver1: str, driver2: str):
        """Plot speed comparison between two drivers"""
        comparison = self.get_telemetry_comparison(driver1, driver2)
        if not comparison:
            return
            
        tel1 = comparison['telemetry1']
        tel2 = comparison['telemetry2']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=tel1['Distance'],
            y=tel1['Speed'],
            mode='lines',
            name=f"{driver1} ({comparison['lap1_time']})",
            line=dict(color='red', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=tel2['Distance'],
            y=tel2['Speed'],
            mode='lines',
            name=f"{driver2} ({comparison['lap2_time']})",
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title=f'Speed Comparison: {driver1} vs {driver2}',
            xaxis_title='Distance (m)',
            yaxis_title='Speed (km/h)',
            hovermode='x unified'
        )
        
        fig.show()
    
    def plot_comprehensive_telemetry(self, driver1: str, driver2: str):
        """Plot comprehensive telemetry comparison"""
        comparison = self.get_telemetry_comparison(driver1, driver2)
        if not comparison:
            return
            
        tel1 = comparison['telemetry1']
        tel2 = comparison['telemetry2']
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Speed', 'Throttle', 'Brake', 'Gear'),
            vertical_spacing=0.08
        )
        
        # Speed
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Speed'], 
                                name=f"{driver1} Speed", line=dict(color='red')), row=1, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Speed'], 
                                name=f"{driver2} Speed", line=dict(color='blue')), row=1, col=1)
        
        # Throttle
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Throttle'], 
                                name=f"{driver1} Throttle", line=dict(color='red')), row=2, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Throttle'], 
                                name=f"{driver2} Throttle", line=dict(color='blue')), row=2, col=1)
        
        # Brake
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Brake'], 
                                name=f"{driver1} Brake", line=dict(color='red')), row=3, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Brake'], 
                                name=f"{driver2} Brake", line=dict(color='blue')), row=3, col=1)
        
        # Gear
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['nGear'], 
                                name=f"{driver1} Gear", line=dict(color='red')), row=4, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['nGear'], 
                                name=f"{driver2} Gear", line=dict(color='blue')), row=4, col=1)
        
        fig.update_layout(height=800, title_text=f"Telemetry Comparison: {driver1} vs {driver2}")
        fig.show()
    
    def analyze_cornering_performance(self, driver: str):
        """Analyze cornering performance for a driver"""
        if not self.session:
            return None
            
        try:
            fastest_lap = self.session.laps.pick_driver(driver).pick_fastest()
            telemetry = fastest_lap.get_telemetry()
            
            # Identify corners (where speed drops significantly)
            speed_diff = telemetry['Speed'].diff()
            corners = []
            
            in_corner = False
            corner_start = None
            
            for i, diff in enumerate(speed_diff):
                if diff < -10 and not in_corner:  # Significant deceleration
                    corner_start = i
                    in_corner = True
                elif diff > 5 and in_corner:  # Acceleration out of corner
                    if corner_start is not None:
                        corners.append({
                            'start': corner_start,
                            'end': i,
                            'min_speed': telemetry['Speed'][corner_start:i].min(),
                            'entry_speed': telemetry['Speed'][corner_start],
                            'exit_speed': telemetry['Speed'][i],
                            'distance': telemetry['Distance'][corner_start]
                        })
                    in_corner = False
            
            return {
                'driver': driver,
                'lap_time': fastest_lap['LapTime'],
                'corners': corners,
                'total_corners': len(corners)
            }
            
        except Exception as e:
            print(f"Error analyzing cornering: {e}")
            return None
    
    def get_weather_impact(self):
        """Analyze weather impact on performance"""
        if not self.session:
            return None
            
        try:
            weather = self.session.weather_data
            laps = self.session.laps
            
            # Merge weather data with lap times
            weather_analysis = []
            
            for _, lap in laps.iterrows():
                lap_time = lap['Time']
                # Find closest weather data point
                weather_point = weather[weather['Time'] <= lap_time].iloc[-1] if len(weather[weather['Time'] <= lap_time]) > 0 else weather.iloc[0]
                
                weather_analysis.append({
                    'driver': lap['Driver'],
                    'lap_number': lap['LapNumber'],
                    'lap_time': lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
                    'air_temp': weather_point['AirTemp'],
                    'track_temp': weather_point['TrackTemp'],
                    'humidity': weather_point['Humidity'],
                    'wind_speed': weather_point['WindSpeed'],
                    'rainfall': weather_point['Rainfall']
                })
            
            return pd.DataFrame(weather_analysis)
            
        except Exception as e:
            print(f"Error analyzing weather impact: {e}")
            return None
    
    def plot_weather_correlation(self):
        """Plot correlation between weather and lap times"""
        weather_data = self.get_weather_impact()
        if weather_data is None or weather_data.empty:
            return
            
        # Remove invalid lap times
        weather_data = weather_data.dropna(subset=['lap_time'])
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Air temperature vs lap time
        axes[0,0].scatter(weather_data['air_temp'], weather_data['lap_time'], alpha=0.6)
        axes[0,0].set_xlabel('Air Temperature (°C)')
        axes[0,0].set_ylabel('Lap Time (seconds)')
        axes[0,0].set_title('Air Temperature vs Lap Time')
        
        # Track temperature vs lap time
        axes[0,1].scatter(weather_data['track_temp'], weather_data['lap_time'], alpha=0.6, color='orange')
        axes[0,1].set_xlabel('Track Temperature (°C)')
        axes[0,1].set_ylabel('Lap Time (seconds)')
        axes[0,1].set_title('Track Temperature vs Lap Time')
        
        # Humidity vs lap time
        axes[1,0].scatter(weather_data['humidity'], weather_data['lap_time'], alpha=0.6, color='green')
        axes[1,0].set_xlabel('Humidity (%)')
        axes[1,0].set_ylabel('Lap Time (seconds)')
        axes[1,0].set_title('Humidity vs Lap Time')
        
        # Wind speed vs lap time
        axes[1,1].scatter(weather_data['wind_speed'], weather_data['lap_time'], alpha=0.6, color='red')
        axes[1,1].set_xlabel('Wind Speed (m/s)')
        axes[1,1].set_ylabel('Lap Time (seconds)')
        axes[1,1].set_title('Wind Speed vs Lap Time')
        
        plt.tight_layout()
        plt.show()
    
    def analyze_pit_stop_performance(self):
        """Analyze pit stop performance"""
        if not self.session:
            return None
            
        try:
            laps = self.session.laps
            
            # Identify pit stops (laps with significantly longer times)
            pit_stops = []
            
            for driver in laps['Driver'].unique():
                driver_laps = laps[laps['Driver'] == driver].copy()
                driver_laps = driver_laps.dropna(subset=['LapTime'])
                
                if len(driver_laps) < 3:
                    continue
                
                # Calculate median lap time for reference
                median_time = driver_laps['LapTime'].median().total_seconds()
                
                for _, lap in driver_laps.iterrows():
                    lap_time = lap['LapTime'].total_seconds()
                    
                    # If lap time is significantly longer, it might be a pit stop
                    if lap_time > median_time * 1.5:  # 50% longer than median
                        pit_stops.append({
                            'driver': driver,
                            'lap_number': lap['LapNumber'],
                            'pit_time': lap_time - median_time,
                            'compound_before': driver_laps[driver_laps['LapNumber'] == lap['LapNumber'] - 1]['Compound'].iloc[0] if len(driver_laps[driver_laps['LapNumber'] == lap['LapNumber'] - 1]) > 0 else None,
                            'compound_after': lap['Compound']
                        })
            
            return pd.DataFrame(pit_stops)
            
        except Exception as e:
            print(f"Error analyzing pit stops: {e}")
            return None
    
    def generate_race_pace_analysis(self):
        """Generate comprehensive race pace analysis"""
        if not self.session:
            return None
            
        try:
            laps = self.session.laps
            
            # Calculate race pace (excluding outliers)
            pace_analysis = {}
            
            for driver in laps['Driver'].unique():
                driver_laps = laps[laps['Driver'] == driver].copy()
                driver_laps = driver_laps.dropna(subset=['LapTime'])
                
                if len(driver_laps) < 5:
                    continue
                
                # Remove outliers (pit stops, safety cars, etc.)
                lap_times = driver_laps['LapTime'].dt.total_seconds()
                Q1 = lap_times.quantile(0.25)
                Q3 = lap_times.quantile(0.75)
                IQR = Q3 - Q1
                
                # Filter out outliers
                clean_times = lap_times[(lap_times >= Q1 - 1.5 * IQR) & (lap_times <= Q3 + 1.5 * IQR)]
                
                pace_analysis[driver] = {
                    'average_pace': clean_times.mean(),
                    'consistency': clean_times.std(),
                    'fastest_lap': lap_times.min(),
                    'total_laps': len(driver_laps),
                    'clean_laps': len(clean_times)
                }
            
            return pace_analysis
            
        except Exception as e:
            print(f"Error generating race pace analysis: {e}")
            return None
    
    def export_detailed_analysis(self, filename: str):
        """Export detailed analysis to multiple CSV files"""
        if not self.session:
            print("No session loaded")
            return
            
        try:
            base_filename = filename.replace('.csv', '')
            
            # Export basic lap data
            laps_df = self.session.laps
            laps_df.to_csv(f"{base_filename}_laps.csv", index=False)
            
            # Export weather analysis
            weather_data = self.get_weather_impact()
            if weather_data is not None:
                weather_data.to_csv(f"{base_filename}_weather.csv", index=False)
            
            # Export pit stop analysis
            pit_stops = self.analyze_pit_stop_performance()
            if pit_stops is not None and not pit_stops.empty:
                pit_stops.to_csv(f"{base_filename}_pitstops.csv", index=False)
            
            # Export race pace analysis
            pace_analysis = self.generate_race_pace_analysis()
            if pace_analysis:
                pace_df = pd.DataFrame.from_dict(pace_analysis, orient='index')
                pace_df.to_csv(f"{base_filename}_pace.csv")
            
            # Export session results
            if hasattr(self.session, 'results'):
                self.session.results.to_csv(f"{base_filename}_results.csv", index=False)
            
            print(f"Detailed analysis exported to multiple files with base name: {base_filename}")
            
        except Exception as e:
            print(f"Error exporting detailed analysis: {e}")
    
    def plot_tire_degradation(self, driver: str):
        """Plot tire degradation for a specific driver"""
        if not self.session:
            return
            
        try:
            driver_laps = self.session.laps.pick_driver(driver)
            
            fig = go.Figure()
            
            # Group by compound
            for compound in driver_laps['Compound'].unique():
                if pd.isna(compound):
                    continue
                    
                compound_laps = driver_laps[driver_laps['Compound'] == compound]
                lap_times = compound_laps['LapTime'].dt.total_seconds()
                lap_numbers = compound_laps['LapNumber']
                
                fig.add_trace(go.Scatter(
                    x=lap_numbers,
                    y=lap_times,
                    mode='lines+markers',
                    name=f"{compound}",
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title=f'Tire Degradation - {driver}',
                xaxis_title='Lap Number',
                yaxis_title='Lap Time (seconds)',
                hovermode='x unified'
            )
            
            fig.show()
            
        except Exception as e:
            print(f"Error plotting tire degradation: {e}")
    
    def analyze_braking_points(self, driver: str):
        """Analyze braking points and performance"""
        if not self.session:
            return None
            
        try:
            fastest_lap = self.session.laps.pick_driver(driver).pick_fastest()
            telemetry = fastest_lap.get_telemetry()
            
            # Find braking zones
            brake_threshold = 50  # Brake pressure threshold
            braking_zones = []
            
            in_braking = False
            brake_start = None
            
            for i, brake in enumerate(telemetry['Brake']):
                if brake > brake_threshold and not in_braking:
                    brake_start = i
                    in_braking = True
                elif brake <= brake_threshold and in_braking:
                    if brake_start is not None:
                        braking_zones.append({
                            'start_distance': telemetry['Distance'].iloc[brake_start],
                            'end_distance': telemetry['Distance'].iloc[i],
                            'start_speed': telemetry['Speed'].iloc[brake_start],
                            'end_speed': telemetry['Speed'].iloc[i],
                            'max_brake_pressure': telemetry['Brake'][brake_start:i].max(),
                            'braking_distance': telemetry['Distance'].iloc[i] - telemetry['Distance'].iloc[brake_start]
                        })
                    in_braking = False
            
            return {
                'driver': driver,
                'lap_time': fastest_lap['LapTime'],
                'braking_zones': braking_zones,
                'total_braking_zones': len(braking_zones)
            }
            
        except Exception as e:
            print(f"Error analyzing braking points: {e}")
            return None
