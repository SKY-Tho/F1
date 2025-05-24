#!/usr/bin/env python3
"""
F1 Performance Analyzer Dashboard Runner
Run this script to start the Streamlit dashboard
"""

import sys
import os
import subprocess

def main():
    """Main function to run the dashboard"""
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Run Streamlit dashboard
        dashboard_path = os.path.join(current_dir, "dashboard.py")
        
        print("🏎️  Starting F1 Performance Analyzer Dashboard...")
        print("📊 Dashboard will open in your default web browser")
        print("🔗 URL: http://localhost:8501")
        print("⏹️  Press Ctrl+C to stop the dashboard")
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", dashboard_path,
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("💡 Make sure you have installed all required packages:")
        print("   pip install streamlit fastf1 pandas plotly matplotlib seaborn scipy")

if __name__ == "__main__":
    main()
