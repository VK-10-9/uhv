import subprocess
import sys
import time
import os

def run_with_watchdog():
    cmd = [sys.executable, "-u", "generate_explanations.py"]
    env = os.environ.copy()
    
    print("Starting RAG generator watchdog wrapper...")
    
    while True:
        print("\n[WATCHDOG] Launching generate_explanations.py...")
        # Start subprocess (inherit stdout/stderr to prevent pipe deadlock)
        process = subprocess.Popen(
            cmd,
            env=env
        )
        
        cache_file = "explanations_cache.json"
        last_mtime = os.path.getmtime(cache_file) if os.path.exists(cache_file) else 0
        last_activity = time.time()
        
        # Read output line by line with timeout
        while True:
            time.sleep(5)
            
            # Check if process is still running
            poll = process.poll()
            if poll is not None:
                if poll == 0:
                    print("[WATCHDOG] generate_explanations.py completed successfully!")
                    return True
                else:
                    print(f"[WATCHDOG] generate_explanations.py exited with error code {poll}. Restarting in 5s...")
                    break
            
            # Check cache file updates relative to when we started or last saw an update
            if os.path.exists(cache_file):
                current_mtime = os.path.getmtime(cache_file)
                if current_mtime != last_mtime:
                    # Cache was updated! Reset watchdog timer
                    last_mtime = current_mtime
                    last_activity = time.time()
                    print(f"[WATCHDOG] Cache updated successfully. Watchdog timer reset.")
                else:
                    # No update since start or last reset
                    idle_time = time.time() - last_activity
                    if idle_time > 80:  # 80 seconds timeout
                        print(f"[WATCHDOG] No cache updates for {int(idle_time)}s. Process likely hung. Killing and restarting...")
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        break
            else:
                # If cache file doesn't exist yet, check process running time
                run_time = time.time() - last_activity
                if run_time > 80:
                    print("[WATCHDOG] Process running for 80s without creating cache. Killing and restarting...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break

def main():
    if "GEMINI_API_KEY" not in os.environ:
        print("[ERROR] GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)
    
    # Run the watchdog loop
    run_with_watchdog()

if __name__ == "__main__":
    main()
