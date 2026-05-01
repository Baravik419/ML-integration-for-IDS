import os
import pdb
import subprocess
import sys
import time
import webbrowser
from getpass import getpass
import signal
from pathlib import Path
from pyfiglet import figlet_format

BASE_DIR = Path(__file__).resolve().parent
ES_PASSWORD = None
SUDO_PASSWORD = None
ML_SERVICE_PATH = str(BASE_DIR / "ml_service.py")
ML_PID_FILE = BASE_DIR / "ml_service.pid"
ML_LOG_FILE = BASE_DIR / "ml_service.log"
SERVICES = ["suricata", "filebeat", "elasticsearch", "evebox"]
STOP_SERVICES = ["evebox", "filebeat", "suricata", "elasticsearch"]
EVEBOX_URL = "https://127.0.0.1:5636"
PYTHON_BIN = sys.executable

# Clears the terminal screen
def clear_screen():
    if os.environ.get("TERM"):
        os.system("clear")

# For running commands
def run_cmd(cmd: list[str], use_sudo: bool = False) -> tuple[int, str]:
    try:
        if use_sudo:
            password = get_sudo_password()
            cmd = ["sudo", "-S"] + cmd
            result = subprocess.run(
                cmd,
                input=password + "\n",
                capture_output=True,
                text=True,
                check=False
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode, output.strip()

    except Exception as error:
        return 1, f"Command failed: {error}"

# Checking service status
def check_service_status(service_name: str) -> str:
    code, output = run_cmd(["systemctl", "is-active", service_name])

    if code == 0:
        return "Active"
    if output:
        return output.capitalize()

# Starting service one by one
def start_service(service_name: str):
    code, output = run_cmd(["systemctl", "start", service_name], use_sudo=True)

    if code != 0:
        print(f"{service_name} start failed: {output}")

    time.sleep(1)
    return f"{service_name}: {check_service_status(service_name)}"

# Stopping service one by one
def stop_service(service_name: str):
    code, output = run_cmd(["systemctl", "stop", service_name], use_sudo=True)

    if code !=0:
        print(f"{service_name} stop failed: {output}")

    time.sleep(1)
    return f"{service_name}: {check_service_status(service_name)}"

# Starting all services
def start_ids_services() -> list[str]:
    results = []

    for service in SERVICES:
        results.append(start_service(service))

    return results

# Stopping all services
def stop_ids_services() -> list[str]:
    results = []

    for service in STOP_SERVICES:
        results.append(stop_service(service))

    return results

# Getting sudo password
def get_sudo_password() -> str:
    global SUDO_PASSWORD

    if SUDO_PASSWORD is None:
        SUDO_PASSWORD = getpass("Enter sudo password: ")

    return SUDO_PASSWORD

# Getting password for the Elasticsearch
def get_es_password() -> str:
    global ES_PASSWORD
    if ES_PASSWORD is None:
        ES_PASSWORD = getpass("Enter Elasticsearch password: ")

    return ES_PASSWORD

# Checking whether the ML service is running
def ml_pid_running() -> bool:
    if not ML_PID_FILE.exists():
        return False

    try:
        pid = int(ML_PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False

# Convert ML service status to string
def ml_status() -> str:
    if ml_pid_running():
        return "Active"
    return "Inactive"

# Services' statuses
def get_services_status() -> list[str]:
    lines = []

    for service in SERVICES:
        lines.append(f"{service:<14}: {check_service_status(service)}")

    lines.append(f"{"ml_model":<14}: {ml_status()}")
    return lines

# Starting ML service
def start_ml_model():
    if ml_pid_running():
        return "ML model: Active"

    ml_path = Path(ML_SERVICE_PATH)
    if not ml_path.exists():
        return f"ML model: Not found: {ml_path}"

    log_handle = open(ML_LOG_FILE, "a", encoding="utf-8")

    env = os.environ.copy()
    env["ES_PASSWORD"] = get_es_password()

    process = subprocess.Popen(
        [PYTHON_BIN, str(ml_path)],
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    ML_PID_FILE.write_text(str(process.pid), encoding="utf-8")
    time.sleep(1)

    if ml_pid_running():
        return "ML model: Active"

    return "ML model: Failed to start"

# Stopping ML service
def stop_ml_model() -> str:
    if not ML_PID_FILE.exists():
        return "ML model: Inactive"

    try:
        pid = int(ML_PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
    except Exception as error:
        return f"ML model: Failed to stop – {error}"
    finally:
        if ML_PID_FILE.exists():
            ML_PID_FILE.unlink(missing_ok=True)
    return "ML model: Inactive"

# Opening EveBox platform in the browser
def open_evebox() -> str:
    try:
        webbrowser.open(EVEBOX_URL)
        return f"EveBox: {EVEBOX_URL}"
    except Exception as error:
        return f"Failed to open EveBox: {error}"

# Menu
def print_menu(message: str = "") -> None:
    clear_screen()
    print("=" * 70)
    print(figlet_format("IoT IDS Prototype", font="small"))
    print("=" * 70)
    print()

    for line in get_services_status():
        print(line)

    print()
    print("1. Start IDS")
    print("2. Start ML model")
    print("3. Open EveBox")
    print("4. Stop ML model")
    print("0. Exit")
    print()

    if message:
        print("-" * 70)
        print(message)
        print("-" * 70)

# Main function
def main() -> None:
    last_message = "Ready."

    while True:
        print_menu(last_message)

        try:
            choice = input("Choose an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if choice == "1":
            results = start_ids_services()
            last_message = "\n".join(results)

        elif choice == "2":
            last_message = start_ml_model()

        elif choice == "3":
            last_message = open_evebox()

        elif choice == "4":
            last_message = stop_ml_model()

        elif choice == "0":
            shutdown_results = []

            shutdown_results.append(stop_ml_model())
            shutdown_results.extend(stop_ids_services())

            print("\n".join(shutdown_results))
            print("Goodbye software engineer!")
            break

        else:
            print("You haven't designed it in your project!")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()