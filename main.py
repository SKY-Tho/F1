import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import time
import asyncio
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class F1PerformanceAnalyzer:
    def __init__(self):
        # Enable FastF1 cache for better performance
        fastf1.Cache.enable_cache('f1_cache')
        self.current_session = None
        self.live_monitoring = False
        
    def get_available_seasons(self) -> List[int]:
        """Get available seasons for analysis"""
        current_year = datetime.now().year
        return list(range(2018, current_year + 1))
    
    def get_season_schedule(self, year: int) -> pd.DataFrame:
        """Get the race schedule for a given year"""
        try:
            schedule = fastf1.get_event_schedule(year)
            return schedule[['RoundNumber', 'EventName', 'EventDate', 'Country']]
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return pd.DataFrame()
    
    def load_session(self, year: int, round_number: int, session_type: str = 'R'):
        """
        Load a specific session
        session_type: 'FP1', 'FP2', 'FP3', 'Q', 'R' (Race)
        """
        try:
            session = fastf1.get_session(year, round_number, session_type)
            session.load()
            self.current_session = session
            print(f"Loaded {session.event['EventName']} {session_type} session")
            return session
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def get_driver_performance(self, driver_code: str) -> Dict:
        """Get comprehensive driver performance data"""
        if not self.current_session:
            return {}
        
        try:
            driver_laps = self.current_session.laps.pick_driver(driver_code)
            
            # Basic statistics
            fastest_lap = driver_laps.pick_fastest()
            
            performance_data = {
                'driver': driver_code,
                'total_laps': len(driver_laps),
                'fastest_lap_time': fastest_lap['LapTime'] if not fastest_lap.empty else None,
                'fastest_lap_number': fastest_lap['LapNumber'] if not fastest_lap.empty else None,
                'average_lap_time': driver_laps['LapTime'].mean(),
                'sector_times': {
                    'sector_1_avg': driver_laps['Sector1Time'].mean(),
                    'sector_2_avg': driver_laps['Sector2Time'].mean(),
                    'sector_3_avg': driver_laps['Sector3Time'].mean(),
                },
                'top_speed': driver_laps['SpeedST'].max(),
                'compound_usage': driver_laps['Compound'].value_counts().to_dict()
            }
            
            return performance_data
        except Exception as e:
            print(f"Error analyzing driver {driver_code}: {e}")
            return {}
    
    def compare_drivers(self, driver1: str, driver2: str) -> Dict:
        """Compare performance between two drivers"""
        if not self.current_session:
            return {}
        
        try:
            driver1_laps = self.current_session.laps.pick_driver(driver1)
            driver2_laps = self.current_session.laps.pick_driver(driver2)
            
            comparison = {
                'driver1': driver1,
                'driver2': driver2,
                'fastest_lap_diff': (driver1_laps.pick_fastest()['LapTime'] - 
                                   driver2_laps.pick_fastest()['LapTime']).total_seconds(),
                'average_lap_diff': (driver1_laps['LapTime'].mean() - 
                                   driver2_laps['LapTime'].mean()).total_seconds(),
                'top_speed_diff': driver1_laps['SpeedST'].max() - driver2_laps['SpeedST'].max(),
                'consistency': {
                    driver1: driver1_laps['LapTime'].std().total_seconds(),
                    driver2: driver2_laps['LapTime'].std().total_seconds()
                }
            }
            
            return comparison
        except Exception as e:
            print(f"Error comparing drivers: {e}")
            return {}
    
    def analyze_tire_performance(self) -> Dict:
        """Analyze tire compound performance across all drivers"""
        if not self.current_session:
            return {}
        
        try:
            laps = self.current_session.laps
            
            # Group by compound and calculate statistics
            tire_analysis = {}
            for compound in laps['Compound'].unique():
                if pd.isna(compound):
                    continue
                    
                compound_laps = laps[laps['Compound'] == compound]
                tire_analysis[compound] = {
                    'average_lap_time': compound_laps['LapTime'].mean(),
                    'fastest_lap_time': compound_laps['LapTime'].min(),
                    'total_laps': len(compound_laps),
                    'average_degradation': self._calculate_degradation(compound_laps)
                }
            
            return tire_analysis
        except Exception as e:
            print(f"Error analyzing tire performance: {e}")
            return {}
    
    def _calculate_degradation(self, laps: pd.DataFrame) -> float:
        """Calculate tire degradation rate"""
        try:
            if len(laps) < 3:
                return 0.0
            
            # Group by stint and calculate degradation
            degradation_rates = []
            for driver in laps['Driver'].unique():
                driver_laps = laps[laps['Driver'] == driver].sort_values('LapNumber')
                if len(driver_laps) >= 3:
                    # Simple linear degradation calculation
                    lap_times = driver_laps['LapTime'].dt.total_seconds()
                    lap_numbers = driver_laps['LapNumber']
                    degradation = np.polyfit(lap_numbers, lap_times, 1)[0]
                    degradation_rates.append(degradation)
            
            return np.mean(degradation_rates) if degradation_rates else 0.0
        except:
            return 0.0
    
    def generate_lap_time_chart(self, drivers: List[str] = None):
        """Generate lap time comparison chart"""
        if not self.current_session:
            return
        
        try:
            plt.figure(figsize=(15, 8))
            
            if not drivers:
                # Get top 5 drivers by position
                results = self.current_session.results
                drivers = results.head(5)['Abbreviation'].tolist()
            
            for driver in drivers:
                driver_laps = self.current_session.laps.pick_driver(driver)
                if not driver_laps.empty:
                    lap_times = driver_laps['LapTime'].dt.total_seconds()
                    lap_numbers = driver_laps['LapNumber']
                    plt.plot(lap_numbers, lap_times, marker='o', label=driver, linewidth=2)
            
            plt.xlabel('Lap Number')
            plt.ylabel('Lap Time (seconds)')
            plt.title(f'Lap Time Comparison - {self.current_session.event["EventName"]}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Error generating chart: {e}")
    
    def generate_sector_analysis(self, driver: str):
        """Generate sector time analysis for a driver"""
        if not self.current_session:
            return
        
        try:
            driver_laps = self.current_session.laps.pick_driver(driver)
            
            fig, axes = plt.subplots(1, 3, figsize=(18, 6))
            
            sectors = ['Sector1Time', 'Sector2Time', 'Sector3Time']
            sector_names = ['Sector 1', 'Sector 2', 'Sector 3']
            
            for i, (sector, name) in enumerate(zip(sectors, sector_names)):
                sector_times = driver_laps[sector].dt.total_seconds()
                lap_numbers = driver_laps['LapNumber']
                
                axes[i].plot(lap_numbers, sector_times, marker='o', color=f'C{i}')
                axes[i].set_xlabel('Lap Number')
                axes[i].set_ylabel('Sector Time (seconds)')
                axes[i].set_title(f'{name} - {driver}')
                axes[i].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Error generating sector analysis: {e}")
    
    async def monitor_live_session(self, year: int, round_number: int, session_type: str):
        """Monitor an ongoing session (simulated with recent data)"""
        print(f"Starting live monitoring for {year} Round {round_number} {session_type}")
        self.live_monitoring = True
        
        try:
            session = self.load_session(year, round_number, session_type)
            if not session:
                return
            
            # Simulate live monitoring by processing laps incrementally
            all_laps = session.laps
            processed_laps = 0
            
            while self.live_monitoring and processed_laps < len(all_laps):
                # Process next batch of laps
                batch_size = min(5, len(all_laps) - processed_laps)
                current_laps = all_laps.iloc[processed_laps:processed_laps + batch_size]
                
                print(f"\n--- Live Update (Laps {processed_laps + 1}-{processed_laps + batch_size}) ---")
                
                # Show current top 5 positions
                if processed_laps > 10:  # Wait for some data
                    current_standings = self._get_current_standings(all_laps.iloc[:processed_laps + batch_size])
                    print("Current Top 5:")
                    for i, (driver, time) in enumerate(current_standings[:5], 1):
                        print(f"{i}. {driver}: {time}")
                
                processed_laps += batch_size
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except Exception as e:
            print(f"Error in live monitoring: {e}")
        finally:
            self.live_monitoring = False
    
    def _get_current_standings(self, laps: pd.DataFrame) -> List[tuple]:
        """Get current race standings based on lap data"""
        try:
            # Get fastest lap for each driver
            fastest_laps = laps.groupby('Driver')['LapTime'].min().sort_values()
            return [(driver, str(time)) for driver, time in fastest_laps.items()]
        except:
            return []
    
    def stop_live_monitoring(self):
        """Stop live session monitoring"""
        self.live_monitoring = False
        print("Live monitoring stopped")
    
    def export_analysis(self, filename: str):
        """Export current analysis to CSV"""
        if not self.current_session:
            print("No session loaded")
            return
        
        try:
            # Compile comprehensive analysis
            analysis_data = []
            
            for driver in self.current_session.drivers:
                driver_data = self.get_driver_performance(driver)
                if driver_data:
                    analysis_data.append(driver_data)
            
            # Convert to DataFrame and export
            df = pd.json_normalize(analysis_data)
            df.to_csv(filename, index=False)
            print(f"Analysis exported to {filename}")
            
        except Exception as e:
            print(f"Error exporting analysis: {e}")

def main():
    analyzer = F1PerformanceAnalyzer()
    
    print("F1 Performance Analyzer")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. View available seasons")
        print("2. Load session for analysis")
        print("3. Analyze driver performance")
        print("4. Compare two drivers")
        print("5. Analyze tire performance")
        print("6. Generate lap time chart")
        print("7. Generate sector analysis")
        print("8. Start live monitoring")
        print("9. Export analysis")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == "1":
            seasons = analyzer.get_available_seasons()
            print(f"Available seasons: {seasons}")
            
        elif choice == "2":
            year = int(input("Enter year: "))
            schedule = analyzer.get_season_schedule(year)
            print(schedule)
            
            round_num = int(input("Enter round number: "))
            session_type = input("Enter session type (FP1/FP2/FP3/Q/R): ").upper()
            analyzer.load_session(year, round_num, session_type)
            
        elif choice == "3":
            if not analyzer.current_session:
                print("Please load a session first")
                continue
                
            driver = input("Enter driver code (e.g., HAM, VER): ").upper()
            performance = analyzer.get_driver_performance(driver)
            
            if performance:
                print(f"\nPerformance Analysis for {driver}:")
                for key, value in performance.items():
                    print(f"{key}: {value}")
            
        elif choice == "4":
            if not analyzer.current_session:
                print("Please load a session first")
                continue
                
            driver1 = input("Enter first driver code: ").upper()
            driver2 = input("Enter second driver code: ").upper()
            comparison = analyzer.compare_drivers(driver1, driver2)
            
            if comparison:
                print(f"\nComparison between {driver1} and {driver2}:")
                for key, value in comparison.items():
                    print(f"{key}: {value}")
            
        elif choice == "5":
            tire_analysis = analyzer.analyze_tire_performance()
            if tire_analysis:
                print("\nTire Performance Analysis:")
                for compound, data in tire_analysis.items():
                    print(f"\n{compound}:")
                    for key, value in data.items():
                        print(f"  {key}: {value}")
            
        elif choice == "6":
            drivers_input = input("Enter driver codes (comma-separated, or press Enter for top 5): ")
            drivers = [d.strip().upper() for d in drivers_input.split(",")] if drivers_input else None
            analyzer.generate_lap_time_chart(drivers)
            
        elif choice == "7":
            driver = input("Enter driver code: ").upper()
            analyzer.generate_sector_analysis(driver)
            
        elif choice == "8":
            year = int(input("Enter year: "))
            round_num = int(input("Enter round number: "))
            session_type = input("Enter session type: ").upper()
                        
            # Start live monitoring in async context
            try:
                asyncio.run(analyzer.monitor_live_session(year, round_num, session_type))
            except KeyboardInterrupt:
                analyzer.stop_live_monitoring()
                print("\nLive monitoring interrupted by user")
            
        elif choice == "9":
            if not analyzer.current_session:
                print("Please load a session first")
                continue
                
            filename = input("Enter filename (e.g., analysis.csv): ")
            if not filename.endswith('.csv'):
                filename += '.csv'
            analyzer.export_analysis(filename)
            
        elif choice == "0":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
