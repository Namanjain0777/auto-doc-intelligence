"""Debug launcher - captures all output"""
import sys
import traceback

try:
    from main import app
    print("App loaded successfully!", flush=True)
    print(f"App: {app}", flush=True)
    
    import uvicorn
    print("Starting server on http://0.0.0.0:8000", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
    input("Press Enter to exit...")