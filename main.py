import subprocess
import sys

def run_script(script_name):
    try:
        print(f"Starting {script_name}...")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"Finished {script_name} ✅")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_script("graham.py")
    run_script("macd.py")
