"""Main entry point for the Study Assistant"""
import subprocess
import sys
import os
import argparse

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run AI Study Assistant')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8501, help='Port number (default: 8501)')
    args = parser.parse_args()
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("Streamlit not found. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run streamlit app with custom address using python -m streamlit
    # Add --server.fileWatcherType none to avoid path watcher errors
    cmd = [
        sys.executable, "-m", "streamlit", "run", "ui/app.py",
        "--server.address", args.host,
        "--server.port", str(args.port),
        "--server.fileWatcherType", "none"  # Disable file watcher to avoid errors
    ]
    print(f"Starting server on http://{args.host}:{args.port}")
    print(f"If host is 0.0.0.0, access via: http://localhost:{args.port}")
    subprocess.run(cmd)

