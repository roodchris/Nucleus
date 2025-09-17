import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

app = create_app()

if __name__ == "__main__":
    # Use more robust defaults and ignore problematic environment variables
    host = "127.0.0.1"  # Always use localhost for development
    port = 5050  # Fixed port for consistency
    debug = True  # Always enable debug for development
    
    print(f"Starting Flask app on {host}:{port}")
    try:
        app.run(debug=debug, host=host, port=port)
    except Exception as e:
        print(f"Error starting app: {e}")
        # Fallback to different port if 5050 is busy
        try:
            port = 5051
            print(f"Trying port {port}...")
            app.run(debug=debug, host=host, port=port)
        except Exception as e2:
            print(f"Failed to start on port {port}: {e2}")
