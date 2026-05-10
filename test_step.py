"""Step by step test"""
import sys
print("STEP 1: Starting", flush=True)

try:
    print("STEP 2: Importing api...", flush=True)
    from api import document_router
    print("STEP 3: API imported", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("STEP 4: Done", flush=True)