import subprocess
import sys
import time

scripts = [
    "verify_waf.py",
    "verify_totp.py",
    "verify_reputation.py",
    "verify_rbac.py",
    "verify_alerts.py",
    "verify_analytics.py",
    "verify_csp.py",
    "verify_tasks.py",
    "verify_profile.py",
    # "verify_dashboard_ui.py", # Skip UI verification as it might require browser interaction or complex setup
]

def run_script(script_name):
    print(f"\n{'='*20} Running {script_name} {'='*20}")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=60 # 1 minute timeout per script
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {script_name} failed with exit code {result.returncode}")
            print(result.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"ERROR: {script_name} timed out")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run {script_name}: {e}")
        return False

def verify_all():
    print("Starting Full System Verification...")
    start_time = time.time()
    
    results = {}
    for script in scripts:
        success = run_script(script)
        results[script] = "PASS" if success else "FAIL"
        
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    all_passed = True
    for script, status in results.items():
        print(f"{script:<25} : {status}")
        if status == "FAIL":
            all_passed = False
            
    duration = time.time() - start_time
    print(f"\nTotal Duration: {duration:.2f} seconds")
    
    if all_passed:
        print("\nALL SYSTEMS GO! 🚀")
        sys.exit(0)
    else:
        print("\nSOME CHECKS FAILED! ⚠️")
        sys.exit(1)

if __name__ == "__main__":
    verify_all()
