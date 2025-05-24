import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Try to import custom modules, but provide fallbacks
try:
    from main import F1PerformanceAnalyzer
except ImportError:
    st.error("main.py not found. Please make sure main.py is in the same directory.")
    st.stop()

try:
    from advanced_analyzer import AdvancedF1Analyzer
except ImportError:
    # Create a placeholder class
    class AdvancedF1Analyzer:
        def __init__(self):
            self.session = None

try:
    from live_monitor import LiveF1Monitor, LiveDataCallback
except ImportError:
    # Create placeholder classes
    class LiveF1Monitor:
        def __init__(self):
            self.is_monitoring = False
            self.session_data = {}
    
    class LiveDataCallback:
        def __init__(self, name):
            self.name = name

class F1Dashboard:
    def __init__(self):
        try:
            self.analyzer = F1PerformanceAnalyzer()
            self.advanced_analyzer = AdvancedF1Analyzer()
            self.live_monitor = LiveF1Monitor()
        except Exception as e:
            st.error(f"Error initializing: {e}")
            st.stop()
        
    def run_dashboard(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(
            page_title="F1 Performance Analyzer",
            page_icon="🏎️",
            layout="wide"
        )
        
        st.title("🏎️ F1 Performance Analyzer Dashboard")
        st.markdown("---")
        
        # Sidebar for navigation
        st.sidebar.title("🏁 Navigation")
        page = st.sidebar.selectbox(
            "Choose a page",
            ["🏠 Home", "📊 Session Analysis", "🔴 Live Monitoring", "🔧 Advanced Telemetry", "🌤️ Weather Analysis", "📈 Historical Comparison"]
        )
        
        # Route to appropriate page
        if page == "🏠 Home":
            self.home_page()
        elif page == "📊 Session Analysis":
            self.session_analysis_page()
        elif page == "🔴 Live Monitoring":
            self.live_monitoring_page()
        elif page == "🔧 Advanced Telemetry":
            self.advanced_telemetry_page()
        elif page == "🌤️ Weather Analysis":
            self.weather_analysis_page()
        elif page == "📈 Historical Comparison":
            self.historical_comparison_page()
    
    def home_page(self):
        """Home page"""
        st.header("🏠 Welcome to F1 Performance Analyzer")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🏎️ Features Available:
            
            - **📊 Session Analysis**: Load and analyze F1 session data
            - **🔴 Live Monitoring**: Real-time race monitoring (demo)
            - **🔧 Advanced Telemetry**: Detailed car performance analysis
            - **🌤️ Weather Analysis**: Weather impact on lap times
            - **📈 Historical Comparison**: Compare seasons and drivers
            
            ### 🚀 Getting Started:
            1. Click on **Session Analysis** in the sidebar
            2. Select a year, race, and session
            3. Load the data and start analyzing!
            
            ### ⚠️ Note:
            First-time data loading may take several minutes as F1 data is downloaded.
            """)
        
        with col2:
            st.info("💡 **Tip**: Start with recent seasons (2023-2024) for faster loading!")
            
            # System status
            st.subheader("🔧 System Status")
            
            try:
                seasons = self.analyzer.get_available_seasons()
                st.success(f"✅ Data Access: {len(seasons)} seasons")
            except Exception as e:
                st.error(f"❌ Data Access Error: {str(e)}")
            
            if hasattr(st.session_state, 'session_loaded') and st.session_state.session_loaded:
                st.success("✅ Session Loaded")
            else:
                st.info("ℹ️ No Session Loaded")
    
    def session_analysis_page(self):
        """Session analysis page"""
        st.header("📊 Session Analysis")
        
        # Initialize session state
        if 'session_loaded' not in st.session_state:
            st.session_state.session_loaded = False
        
        # Session selection
        st.subheader("🔧 Session Selection")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                seasons = self.analyzer.get_available_seasons()
                year = st.selectbox("📅 Year", seasons, index=len(seasons)-1)
            except Exception as e:
                st.error(f"Error loading seasons: {e}")
                return
        
        with col2:
            try:
                schedule = self.analyzer.get_season_schedule(year)
                if not schedule.empty:
                    race_options = [f"Round {row['RoundNumber']}: {row['EventName']}" 
                                  for _, row in schedule.iterrows()]
                    selected_race = st.selectbox("🏁 Race", race_options)
                    round_number = int(selected_race.split(":")[0].replace("Round ", ""))
                else:
                    st.error("No schedule data available for this year")
                    return
            except Exception as e:
                st.error(f"Error loading schedule: {e}")
                return
        
        with col3:
            session_type = st.selectbox("🏎️ Session", ["FP1", "FP2", "FP3", "Q", "R"])
        
        # Load session
        st.markdown("---")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🚀 Load Session", type="primary"):
                with st.spinner("Loading session data... Please wait..."):
                    try:
                        success = self.analyzer.load_session(year, round_number, session_type)
                        if success:
                            st.session_state.session_loaded = True
                            st.success("✅ Session loaded successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to load session")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        with col2:
            if st.session_state.session_loaded:
                st.success("✅ Session is loaded and ready for analysis!")
            else:
                st.info("ℹ️ Click 'Load Session' to begin analysis")
        
        # Display analysis if session is loaded
        if st.session_state.session_loaded:
            st.markdown("---")
            self.display_session_analysis()
    
    def display_session_analysis(self):
        """Display session analysis"""
        if not self.analyzer.current_session:
            st.warning("No session data available")
            return
        
        session = self.analyzer.current_session
        
        # Session info
        st.subheader("📋 Session Information")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏁 Event", session.event['EventName'])
        with col2:
            st.metric("🏎️ Session", session.name)
        with col3:
            st.metric("📅 Date", session.date.strftime("%Y-%m-%d"))
        with col4:
            st.metric("🔢 Total Laps", len(session.laps))
        
        # Driver selection
        st.subheader("👥 Driver Analysis")
        
        drivers = list(session.drivers)
        selected_drivers = st.multiselect(
            "Select drivers to analyze:",
            drivers,
            default=drivers[:5] if len(drivers) >= 5 else drivers
        )
        
        if selected_drivers:
            # Lap times chart
            st.subheader("⏱️ Lap Time Comparison")
            
            fig = go.Figure()
            
            colors = px.colors.qualitative.Set1
            
            for i, driver in enumerate(selected_drivers):
                try:
                    driver_laps = session.laps.pick_driver(driver)
                    valid_laps = driver_laps.dropna(subset=['LapTime'])
                    
                    if not valid_laps.empty:
                        lap_times = valid_laps['LapTime'].dt.total_seconds()
                        lap_numbers = valid_laps['LapNumber']
                        
                        fig.add_trace(go.Scatter(
                            x=lap_numbers,
                            y=lap_times,
                            mode='lines+markers',
                            name=driver,
                            line=dict(width=2, color=colors[i % len(colors)]),
                            hovertemplate=f'{driver}<br>Lap: %{{x}}<br>Time: %{{y:.3f}}s<extra></extra>'
                        ))
                except Exception as e:
                    st.warning(f"Could not load data for {driver}: {e}")
            
            fig.update_layout(
                title='Lap Time Comparison',
                xaxis_title='Lap Number',
                yaxis_title='Lap Time (seconds)',
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance summary
            st.subheader("📊 Performance Summary")
            
            performance_data = []
            
            for driver in selected_drivers:
                try:
                    driver_laps = session.laps.pick_driver(driver)
                    valid_laps = driver_laps.dropna(subset=['LapTime'])
                    
                    if not valid_laps.empty:
                        lap_times = valid_laps['LapTime'].dt.total_seconds()
                        
                        performance_data.append({
                            'Driver': driver,
                            'Total Laps': len(valid_laps),
                            'Fastest Lap': f"{lap_times.min():.3f}s",
                            'Average Lap': f"{lap_times.mean():.3f}s",
                            'Consistency (Std)': f"{lap_times.std():.3f}s"
                        })
                except Exception as e:
                    st.warning(f"Could not analyze {driver}: {e}")
            
            if performance_data:
                df = pd.DataFrame(performance_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.info("Select drivers to see analysis")
    
    def live_monitoring_page(self):
        """Live monitoring page"""
        st.header("🔴 Live Session Monitoring")
        st.info("🚧 This is a demonstration of live monitoring capabilities")
        
        # Demo controls
        col1, col2 = st.columns(2)
        
        with col1:
            session_name = st.text_input("Session Name", "Demo Session")
            session_type = st.selectbox("Session Type", ["Practice", "Qualifying", "Race"])
        
        with col2:
            update_interval = st.slider("Update Interval (seconds)", 1, 10, 3)
        
        # Demo data
        if st.button("🚀 Start Demo Monitoring"):
            st.success("Demo monitoring started!")
            
            # Create demo standings
            demo_data = {
                'Pos': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'Driver': ['HAM', 'VER', 'LEC', 'RUS', 'SAI', 'NOR', 'PER', 'ALO', 'OCO', 'GAS'],
                'Last Lap': ['1:23.456', '1:23.789', '1:24.123', '1:24.456', '1:24.789', 
                           '1:25.123', '1:25.456', '1:25.789', '1:26.123', '1:26.456'],
                'Gap': ['Leader', '+0.333', '+0.667', '+1.000', '+1.333', 
                       '+1.667', '+2.000', '+2.333', '+2.667', '+3.000'],
                'Tire': ['MEDIUM', 'HARD', 'MEDIUM', 'HARD', 'MEDIUM', 
                        'HARD', 'MEDIUM', 'HARD', 'MEDIUM', 'HARD']
            }
            
            df = pd.DataFrame(demo_data)
            st.dataframe(df, use_container_width=True)
            
            # Demo chart
            fig = go.Figure()
            
            for i, driver in enumerate(df['Driver'][:5]):
                # Generate some random position data
                laps = list(range(1, 21))
                positions = [i+1 + np.random.randint(-1, 2) for _ in laps]
                positions = [max(1, min(10, pos)) for pos in positions]  # Keep in range 1-10
                
                fig.add_trace(go.Scatter(
                    x=laps,
                    y=positions,
                    mode='lines+markers',
                    name=driver,
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title='Position Changes (Demo)',
                xaxis_title='Lap',
                yaxis_title='Position',
                yaxis=dict(autorange='reversed'),  # Reverse y-axis so position 1 is at top
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def advanced_telemetry_page(self):
        """Advanced telemetry analysis page"""
        st.header("🔧 Advanced Telemetry Analysis")
        
        if not hasattr(st.session_state, 'session_loaded') or not st.session_state.session_loaded:
            st.warning("⚠️ Please load a session first in the Session Analysis page")
            st.info("💡 Go to Session Analysis → Load a session → Return here for telemetry analysis")
            return
        
        if not self.analyzer.current_session:
            st.error("❌ No session data available")
            return
        
        # Copy session to advanced analyzer
        self.advanced_analyzer.session = self.analyzer.current_session
        
        st.success("✅ Session loaded! Advanced telemetry analysis available.")
        
        # Driver selection for telemetry comparison
        drivers = list(self.analyzer.current_session.drivers)
        
        st.subheader("👥 Driver Comparison")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            driver1 = st.selectbox("Driver 1", drivers, key="tel_driver1")
        with col2:
            driver2 = st.selectbox("Driver 2", drivers, 
                                 index=1 if len(drivers) > 1 else 0, 
                                 key="tel_driver2")
        with col3:
            lap_type = st.selectbox("Lap Type", ["fastest", "1", "2", "3", "4", "5"])
        
        if st.button("🔍 Generate Telemetry Comparison"):
            if driver1 == driver2:
                st.warning("⚠️ Please select two different drivers")
                return
                
            with st.spinner("Generating telemetry analysis..."):
                try:
                    comparison = self.advanced_analyzer.get_telemetry_comparison(driver1, driver2, lap_type)
                    
                    if comparison:
                        st.success("✅ Telemetry comparison generated!")
                        self.display_telemetry_comparison(comparison)
                    else:
                        st.error("❌ Failed to generate telemetry comparison")
                except Exception as e:
                    st.error(f"❌ Error generating telemetry: {e}")
        
        # Additional analysis options
        st.markdown("---")
        st.subheader("🔬 Additional Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏎️ Cornering Analysis"):
                selected_driver = st.selectbox("Select Driver for Cornering Analysis", drivers, key="corner_driver")
                try:
                    cornering_data = self.advanced_analyzer.analyze_cornering_performance(selected_driver)
                    if cornering_data:
                        self.display_cornering_analysis(cornering_data)
                    else:
                        st.error("❌ No cornering data available")
                except Exception as e:
                    st.error(f"❌ Error in cornering analysis: {e}")
        
        with col2:
            if st.button("🛑 Braking Analysis"):
                st.info("🚧 Braking analysis feature coming soon!")
        
        with col3:
            if st.button("🏁 Tire Degradation"):
                selected_driver = st.selectbox("Select Driver for Tire Analysis", drivers, key="tire_driver")
                try:
                    self.plot_tire_degradation_streamlit(selected_driver)
                except Exception as e:
                    st.error(f"❌ Error in tire analysis: {e}")
    
    def display_telemetry_comparison(self, comparison):
        """Display telemetry comparison results"""
        st.subheader(f"🔍 Telemetry Comparison: {comparison['driver1']} vs {comparison['driver2']}")
        
        # Lap time comparison
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"🏎️ {comparison['driver1']} Lap Time", str(comparison['lap1_time']))
        with col2:
            st.metric(f"🏎️ {comparison['driver2']} Lap Time", str(comparison['lap2_time']))
        with col3:
            # Calculate time difference
            try:
                time1 = comparison['lap1_time'].total_seconds()
                time2 = comparison['lap2_time'].total_seconds()
                diff = abs(time1 - time2)
                faster_driver = comparison['driver1'] if time1 < time2 else comparison['driver2']
                st.metric(f"⚡ Faster Driver", f"{faster_driver} by {diff:.3f}s")
            except:
                st.metric("⚡ Time Difference", "N/A")
        
        # Telemetry plots
        tel1 = comparison['telemetry1']
        tel2 = comparison['telemetry2']
        
        # Speed comparison
        st.subheader("🚀 Speed Comparison")
        fig_speed = go.Figure()
        
        fig_speed.add_trace(go.Scatter(
            x=tel1['Distance'], y=tel1['Speed'],
            name=comparison['driver1'], 
            line=dict(color='red', width=2),
            hovertemplate=f"{comparison['driver1']}<br>Distance: %{{x}}m<br>Speed: %{{y}} km/h<extra></extra>"
        ))
        
        fig_speed.add_trace(go.Scatter(
            x=tel2['Distance'], y=tel2['Speed'],
            name=comparison['driver2'], 
            line=dict(color='blue', width=2),
            hovertemplate=f"{comparison['driver2']}<br>Distance: %{{x}}m<br>Speed: %{{y}} km/h<extra></extra>"
        ))
        
        fig_speed.update_layout(
            title='Speed Comparison',
            xaxis_title='Distance (m)',
            yaxis_title='Speed (km/h)',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_speed, use_container_width=True)
        
        # Comprehensive telemetry
        st.subheader("📊 Comprehensive Telemetry")
        
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Speed (km/h)', 'Throttle (%)', 'Brake (%)', 'Gear'),
            vertical_spacing=0.08
        )
        
        # Speed
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Speed'], 
                                name=f"{comparison['driver1']} Speed", 
                                line=dict(color='red', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Speed'], 
                                name=f"{comparison['driver2']} Speed", 
                                line=dict(color='blue', width=2)), row=1, col=1)
        
        # Throttle
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Throttle'], 
                                name=f"{comparison['driver1']} Throttle", 
                                line=dict(color='red', width=2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Throttle'], 
                                name=f"{comparison['driver2']} Throttle", 
                                line=dict(color='blue', width=2)), row=2, col=1)
        
        # Brake
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Brake'], 
                                name=f"{comparison['driver1']} Brake", 
                                line=dict(color='red', width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Brake'], 
                                name=f"{comparison['driver2']} Brake", 
                                line=dict(color='blue', width=2)), row=3, col=1)
        
        # Gear
        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['nGear'], 
                                name=f"{comparison['driver1']} Gear", 
                                line=dict(color='red', width=2)), row=4, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['nGear'], 
                                name=f"{comparison['driver2']} Gear", 
                                line=dict(color='blue', width=2)), row=4, col=1)
        
        fig.update_layout(height=800, title_text="Comprehensive Telemetry Comparison", showlegend=False)
        fig.update_xaxes(title_text="Distance (m)", row=4, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_cornering_analysis(self, cornering_data):
        """Display cornering analysis results"""
        st.subheader(f"🏎️ Cornering Analysis: {cornering_data['driver']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("⏱️ Lap Time", str(cornering_data['lap_time']))
        with col2:
            st.metric("🔄 Total Corners", cornering_data['total_corners'])
        
        if cornering_data['corners']:
            corners_df = pd.DataFrame(cornering_data['corners'])
            corners_df['corner_number'] = range(1, len(corners_df) + 1)
            
            # Reorder columns for better display
            display_columns = ['corner_number', 'distance', 'entry_speed', 'min_speed', 'exit_speed']
            available_columns = [col for col in display_columns if col in corners_df.columns]
            
            st.dataframe(corners_df[available_columns], use_container_width=True)
            
            # Corner speed visualization
            if len(corners_df) > 0:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=corners_df['corner_number'],
                    y=corners_df['entry_speed'],
                    mode='lines+markers',
                    name='Entry Speed',
                    line=dict(color='green', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=corners_df['corner_number'],
                    y=corners_df['min_speed'],
                    mode='lines+markers',
                    name='Minimum Speed',
                    line=dict(color='red', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=corners_df['corner_number'],
                    y=corners_df['exit_speed'],
                    mode='lines+markers',
                    name='Exit Speed',
                    line=dict(color='blue', width=2)
                ))
                
                fig.update_layout(
                    title='Corner Speed Analysis',
                    xaxis_title='Corner Number',
                    yaxis_title='Speed (km/h)',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No corner data available for this lap")
    
    def plot_tire_degradation_streamlit(self, driver):
        """Plot tire degradation in Streamlit"""
        if not self.advanced_analyzer.session:
            st.error("No session data available")
            return
        
        try:
            driver_laps = self.advanced_analyzer.session.laps.pick_driver(driver)
            
            if driver_laps.empty:
                st.warning(f"No lap data available for {driver}")
                return
            
            fig = go.Figure()
            
            # Group by compound
            compounds = driver_laps['Compound'].dropna().unique()
            
            if len(compounds) == 0:
                st.warning(f"No tire compound data available for {driver}")
                return
            
            colors = px.colors.qualitative.Set1
            
            for i, compound in enumerate(compounds):
                compound_laps = driver_laps[driver_laps['Compound'] == compound]
                valid_laps = compound_laps.dropna(subset=['LapTime'])
                
                if not valid_laps.empty:
                    lap_times = valid_laps['LapTime'].dt.total_seconds()
                    lap_numbers = valid_laps['LapNumber']
                    
                    fig.add_trace(go.Scatter(
                        x=lap_numbers,
                        y=lap_times,
                        mode='lines+markers',
                        name=f"{compound}",
                        line=dict(width=2, color=colors[i % len(colors)]),
                        hovertemplate=f'{compound}<br>Lap: %{{x}}<br>Time: %{{y:.3f}}s<extra></extra>'
                    ))
            
            fig.update_layout(
                title=f'Tire Degradation - {driver}',
                xaxis_title='Lap Number',
                yaxis_title='Lap Time (seconds)',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error plotting tire degradation: {e}")
    
    def weather_analysis_page(self):
        """Weather analysis page"""
        st.header("🌤️ Weather Impact Analysis")
        
        if not hasattr(st.session_state, 'session_loaded') or not st.session_state.session_loaded:
            st.warning("⚠️ Please load a session first in the Session Analysis page")
            st.info("💡 Go to Session Analysis → Load a session → Return here for weather analysis")
            return
        
        if not self.advanced_analyzer.session:
            self.advanced_analyzer.session = self.analyzer.current_session
        
        st.success("✅ Session loaded! Weather analysis available.")
        
        if st.button("🌦️ Generate Weather Analysis"):
            with st.spinner("Analyzing weather impact..."):
                try:
                    weather_data = self.advanced_analyzer.get_weather_impact()
                    
                    if weather_data is not None and not weather_data.empty:
                        st.success("✅ Weather analysis generated!")
                        self.display_weather_analysis(weather_data)
                    else:
                        st.warning("⚠️ No weather data available for this session")
                except Exception as e:
                    st.error(f"❌ Error analyzing weather: {e}")
    
    def display_weather_analysis(self, weather_data):
        """Display weather analysis results"""
        # Remove invalid lap times
        clean_data = weather_data.dropna(subset=['lap_time'])
        
        if clean_data.empty:
            st.warning("No valid lap time data available for weather analysis")
            return
        
        st.subheader("🌡️ Weather Conditions Summary")
        
        # Weather summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ Avg Air Temp", f"{clean_data['air_temp'].mean():.1f}°C")
        with col2:
            st.metric("🏁 Avg Track Temp", f"{clean_data['track_temp'].mean():.1f}°C")
        with col3:
            st.metric("💧 Avg Humidity", f"{clean_data['humidity'].mean():.1f}%")
        with col4:
            st.metric("💨 Avg Wind Speed", f"{clean_data['wind_speed'].mean():.1f} m/s")
        
        # Weather correlation plots
        st.subheader("📊 Weather Impact on Lap Times")
        
        # Create 2x2 subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Air Temperature vs Lap Time', 'Track Temperature vs Lap Time',
                          'Humidity vs Lap Time', 'Wind Speed vs Lap Time'),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Air temperature vs lap time
        fig.add_trace(go.Scatter(
            x=clean_data['air_temp'], 
            y=clean_data['lap_time'],
            mode='markers',
            name='Air Temp',
            marker=dict(color='blue', size=6, opacity=0.6),
            hovertemplate='Air Temp: %{x}°C<br>Lap Time: %{y:.3f}s<extra></extra>'
        ), row=1, col=1)
        
        # Track temperature vs lap time
        fig.add_trace(go.Scatter(
            x=clean_data['track_temp'], 
            y=clean_data['lap_time'],
            mode='markers',
            name='Track Temp',
            marker=dict(color='orange', size=6, opacity=0.6),
            hovertemplate='Track Temp: %{x}°C<br>Lap Time: %{y:.3f}s<extra></extra>'
        ), row=1, col=2)
        
        # Humidity vs lap time
        fig.add_trace(go.Scatter(
            x=clean_data['humidity'], 
            y=clean_data['lap_time'],
            mode='markers',
            name='Humidity',
            marker=dict(color='green', size=6, opacity=0.6),
            hovertemplate='Humidity: %{x}%<br>Lap Time: %{y:.3f}s<extra></extra>'
        ), row=2, col=1)
        
        # Wind speed vs lap time
        fig.add_trace(go.Scatter(
            x=clean_data['wind_speed'], 
            y=clean_data['lap_time'],
            mode='markers',
            name='Wind Speed',
            marker=dict(color='red', size=6, opacity=0.6),
            hovertemplate='Wind Speed: %{x} m/s<br>Lap Time: %{y:.3f}s<extra></extra>'
        ), row=2, col=2)
        
        # Update axes labels
        fig.update_xaxes(title_text="Air Temperature (°C)", row=1, col=1)
        fig.update_xaxes(title_text="Track Temperature (°C)", row=1, col=2)
        fig.update_xaxes(title_text="Humidity (%)", row=2, col=1)
        fig.update_xaxes(title_text="Wind Speed (m/s)", row=2, col=2)
        
        fig.update_yaxes(title_text="Lap Time (s)", row=1, col=1)
        fig.update_yaxes(title_text="Lap Time (s)", row=1, col=2)
        fig.update_yaxes(title_text="Lap Time (s)", row=2, col=1)
        fig.update_yaxes(title_text="Lap Time (s)", row=2, col=2)
        
        fig.update_layout(height=600, showlegend=False, title_text="Weather Impact Analysis")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Weather data table
        st.subheader("📋 Detailed Weather Data")
        
        # Show sample of weather data
        display_columns = ['driver', 'lap_number', 'lap_time', 'air_temp', 'track_temp', 'humidity', 'wind_speed']
        available_columns = [col for col in display_columns if col in clean_data.columns]
        
        # Format lap_time for better display
        display_data = clean_data[available_columns].copy()
        if 'lap_time' in display_data.columns:
            display_data['lap_time'] = display_data['lap_time'].round(3)
        
        st.dataframe(display_data.head(20), use_container_width=True)
        
        # Correlation analysis
        st.subheader("🔗 Correlation Analysis")
        
        try:
            # Calculate correlations
            weather_cols = ['air_temp', 'track_temp', 'humidity', 'wind_speed']
            available_weather_cols = [col for col in weather_cols if col in clean_data.columns]
            
            if available_weather_cols and 'lap_time' in clean_data.columns:
                correlations = clean_data[available_weather_cols + ['lap_time']].corr()['lap_time'][:-1]
                
                # Create correlation bar chart
                fig_corr = go.Figure(data=[
                    go.Bar(
                        x=correlations.index,
                        y=correlations.values,
                        marker_color=['blue' if x > 0 else 'red' for x in correlations.values]
                    )
                ])
                
                fig_corr.update_layout(
                    title='Weather Factors Correlation with Lap Time',
                    xaxis_title='Weather Factor',
                    yaxis_title='Correlation Coefficient',
                    height=400
                )
                
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Interpretation
                st.subheader("📖 Interpretation")
                strongest_corr = correlations.abs().idxmax()
                strongest_value = correlations[strongest_corr]
                
                if abs(strongest_value) > 0.3:
                    direction = "positive" if strongest_value > 0 else "negative"
                    st.info(f"💡 **Key Finding**: {strongest_corr.replace('_', ' ').title()} shows the strongest {direction} correlation ({strongest_value:.3f}) with lap times.")
                else:
                    st.info("💡 **Key Finding**: Weather conditions show weak correlation with lap times in this session.")
                    
        except Exception as e:
            st.warning(f"Could not calculate correlations: {e}")
    
    def historical_comparison_page(self):
        """Historical comparison page"""
        st.header("📈 Historical Performance Comparison")
        
        # Season comparison
        st.subheader("🏆 Season Comparison")
        
        try:
            seasons = self.analyzer.get_available_seasons()
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_seasons = st.multiselect(
                    "Select Seasons", 
                    seasons, 
                    default=seasons[-3:] if len(seasons) >= 3 else seasons
                )
            
            with col2:
                comparison_type = st.selectbox(
                    "Comparison Type", 
                    ["Championship Points", "Race Wins", "Pole Positions", "Fastest Laps"]
                )
            
            if selected_seasons and st.button("📊 Generate Historical Comparison"):
                with st.spinner("Generating historical comparison..."):
                    self.display_historical_comparison(selected_seasons, comparison_type)
            
            # Driver comparison across seasons
            st.markdown("---")
            st.subheader("👤 Driver Performance Across Seasons")
            
            col1, col2 = st.columns(2)
            
            with col1:
                driver_name = st.text_input(
                    "Driver Name (e.g., 'hamilton', 'verstappen')",
                    placeholder="Enter driver surname"
                )
            
            with col2:
                analysis_seasons = st.multiselect(
                    "Select Seasons for Driver Analysis", 
                    seasons, 
                    default=seasons[-5:] if len(seasons) >= 5 else seasons
                )
            
            if driver_name and analysis_seasons and st.button("🔍 Analyze Driver Performance"):
                with st.spinner(f"Analyzing {driver_name}'s performance..."):
                    self.display_driver_historical_analysis(driver_name, analysis_seasons)
                    
        except Exception as e:
            st.error(f"Error in historical comparison: {e}")
    
    def display_historical_comparison(self, seasons, comparison_type):
        """Display historical comparison results"""
        st.subheader(f"📊 {comparison_type} Comparison")
        
        comparison_data = []
        
        for season in seasons:
            try:
                if comparison_type == "Championship Points":
                    standings = self.analyzer.get_driver_standings(season)
                    if not standings.empty:
                        total_points = standings['points'].astype(float).sum()
                        comparison_data.append({
                            'Season': season,
                            'Value': total_points,
                            'Metric': 'Total Points'
                        })
                
                elif comparison_type == "Race Wins":
                    results = self.analyzer.get_season_results(season)
                    if not results.empty:
                        wins = len(results[results['position'] == '1'])
                        comparison_data.append({
                            'Season': season,
                            'Value': wins,
                            'Metric': 'Race Wins'
                        })
                
                # Add more comparison types as needed
                
            except Exception as e:
                st.warning(f"Could not load data for season {season}: {e}")
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            
            # Plot comparison
            fig = px.bar(
                df, 
                x='Season', 
                y='Value', 
                title=f'{comparison_type} by Season',
                color='Value',
                color_continuous_scale='viridis'
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display data table
            st.subheader("📋 Detailed Data")
            st.dataframe(df, use_container_width=True)
            
            # Summary statistics
            if len(df) > 1:
                st.subheader("📊 Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📈 Highest", f"{df['Value'].max():.0f}")
                with col2:
                    st.metric("📉 Lowest", f"{df['Value'].min():.0f}")
                with col3:
                    st.metric("📊 Average", f"{df['Value'].mean():.1f}")
                with col4:
                    st.metric("📏 Range", f"{df['Value'].max() - df['Value'].min():.0f}")
        else:
            st.warning("⚠️ No data available for comparison")
            st.info("💡 This might be because the selected seasons don't have complete data or the API is not accessible.")
    
    def display_driver_historical_analysis(self, driver_name, seasons):
        """Display driver historical analysis"""
        st.subheader(f"👤 {driver_name.title()} Performance Analysis")
        
        driver_data = []
        
        for season in seasons:
            try:
                standings = self.analyzer.get_driver_standings(season)
                if not standings.empty:
                    # Find driver in standings (case insensitive partial match)
                    driver_row = standings[standings['Driver'].str.lower().str.contains(driver_name.lower(), na=False)]
                    
                    if not driver_row.empty:
                        driver_info = driver_row.iloc[0]
                        driver_data.append({
                            'Season': season,
                            'Position': int(driver_info['position']),
                            'Points': float(driver_info['points']),
                            'Wins': int(driver_info.get('wins', 0)),
                            'Driver': driver_info['Driver']
                        })
            except Exception as e:
                st.warning(f"Could not load data for {driver_name} in season {season}: {e}")
        
        if driver_data:
            df = pd.DataFrame(driver_data)
            
            # Performance trends
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Championship Position', 'Points per Season', 'Race Wins', 'Performance Trend'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Championship position (inverted y-axis)
            fig.add_trace(go.Scatter(
                x=df['Season'], 
                y=df['Position'], 
                mode='lines+markers', 
                name='Position',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ), row=1, col=1)
            
            # Points
            fig.add_trace(go.Bar(
                x=df['Season'], 
                y=df['Points'], 
                name='Points',
                marker_color='blue'
            ), row=1, col=2)
            
            # Wins
            fig.add_trace(go.Bar(
                x=df['Season'], 
                y=df['Wins'], 
                name='Wins',
                marker_color='gold'
            ), row=2, col=1)
            
            # Points trend line
            fig.add_trace(go.Scatter(
                x=df['Season'], 
                y=df['Points'], 
                mode='lines+markers', 
                name='Points Trend',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ), row=2, col=2)
            
            # Update y-axis for position (lower is better)
            fig.update_yaxes(autorange="reversed", row=1, col=1)
            fig.update_layout(height=600, title_text=f"{driver_name.title()} Performance Analysis", showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            st.subheader("📊 Career Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏆 Best Position", int(df['Position'].min()))
            with col2:
                st.metric("🎯 Total Points", int(df['Points'].sum()))
            with col3:
                st.metric("🏁 Total Wins", int(df['Wins'].sum()))
            with col4:
                st.metric("📊 Avg Position", f"{df['Position'].mean():.1f}")
            
            # Detailed data table
            st.subheader("📋 Detailed Performance Data")
            st.dataframe(df, use_container_width=True)
            
            # Performance insights
            st.subheader("💡 Performance Insights")
            
            if len(df) > 1:
                # Trend analysis
                position_trend = "improving" if df['Position'].iloc[-1] < df['Position'].iloc[0] else "declining"
                points_trend = "increasing" if df['Points'].iloc[-1] > df['Points'].iloc[0] else "decreasing"
                
                st.info(f"📈 **Position Trend**: {position_trend.title()} (from P{df['Position'].iloc[0]} to P{df['Position'].iloc[-1]})")
                st.info(f"🎯 **Points Trend**: {points_trend.title()} (from {df['Points'].iloc[0]} to {df['Points'].iloc[-1]} points)")
                
                # Best and worst seasons
                best_season = df.loc[df['Position'].idxmin()]
                worst_season = df.loc[df['Position'].idxmax()]
                
                st.success(f"🏆 **Best Season**: {best_season['Season']} (P{best_season['Position']}, {best_season['Points']} points)")
                st.warning(f"📉 **Challenging Season**: {worst_season['Season']} (P{worst_season['Position']}, {worst_season['Points']} points)")
        else:
            st.warning(f"⚠️ No data found for driver '{driver_name}'")
            st.info("💡 Try using just the driver's surname (e.g., 'hamilton', 'verstappen', 'leclerc')")

# Main execution
def main():
    """Main function to run the dashboard"""
    try:
        dashboard = F1Dashboard()
        dashboard.run_dashboard()
    except Exception as e:
        st.error(f"🚨 Critical Error: {e}")
        st.error("Please check that all required files are present and try refreshing the page")
        
        # Debug information
        with st.expander("🔧 Debug Information"):
            st.write("**Error Details:**")
            st.code(str(e))
            
            st.write("**Required Files:**")
            st.write("- main.py")
            st.write("- advanced_analyzer.py") 
            st.write("- live_monitor.py")
            st.write("- dashboard.py")
            
            st.write("**Required Packages:**")
            st.write("- streamlit")
            st.write("- fastf1")
            st.write("- pandas")
            st.write("- plotly")
            st.write("- numpy")

if __name__ == "__main__":
    main()
