import IoT_IDS_prototype

def test_clear_screen_calls_clear_when_term_exists(monkeypatch):
    called_commands = []

    monkeypatch.setenv("TERM", "xterm")

    def fake_system(command):
        called_commands.append(command)

    monkeypatch.setattr(IoT_IDS_prototype.os, "system", fake_system)

    IoT_IDS_prototype.clear_screen()

    assert called_commands == ["clear"]

def test_run_cmd_without_sudo_returns_code_and_output(monkeypatch):
    class FakeCompletedProcess:
        returncode = 0
        stdout = "hello\n"
        stderr = ""

    def fake_subprocess_run(cmd, capture_output, text, check):
        assert cmd == ["echo", "hello"]
        assert capture_output is True
        assert text is True
        assert check is False
        return FakeCompletedProcess()

    monkeypatch.setattr(IoT_IDS_prototype.subprocess, "run", fake_subprocess_run)

    code, output = IoT_IDS_prototype.run_cmd(["echo", "hello"])

    assert code == 0
    assert output == "hello"

def test_check_service_status_returns_active_when_service_is_active(monkeypatch):
    def fake_run_cmd(cmd):
        assert cmd == ["systemctl", "is-active", "suricata"]
        return 0, "active"

    monkeypatch.setattr(IoT_IDS_prototype, "run_cmd", fake_run_cmd)

    result = IoT_IDS_prototype.check_service_status("suricata")

    assert result == "Active"

def test_start_service_starts_service_and_returns_status(monkeypatch):
    sleep_calls = []

    def fake_run_cmd(cmd, use_sudo=False):
        assert cmd == ["systemctl", "start", "suricata"]
        assert use_sudo is True
        return 0, ""

    def fake_check_service_status(service_name):
        assert service_name == "suricata"
        return "Active"

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(IoT_IDS_prototype, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(IoT_IDS_prototype, "check_service_status", fake_check_service_status)
    monkeypatch.setattr(IoT_IDS_prototype.time, "sleep", fake_sleep)

    result = IoT_IDS_prototype.start_service("suricata")

    assert result == "suricata: Active"
    assert sleep_calls == [1]

def test_stop_service_stops_service_and_returns_status(monkeypatch):
    sleep_calls = []

    def fake_run_cmd(cmd, use_sudo=False):
        assert cmd == ["systemctl", "stop", "suricata"]
        assert use_sudo is True
        return 0, ""

    def fake_check_service_status(service_name):
        assert service_name == "suricata"
        return "Inactive"

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(IoT_IDS_prototype, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(IoT_IDS_prototype, "check_service_status", fake_check_service_status)
    monkeypatch.setattr(IoT_IDS_prototype.time, "sleep", fake_sleep)

    result = IoT_IDS_prototype.stop_service("suricata")

    assert result == "suricata: Inactive"
    assert sleep_calls == [1]

def test_start_ids_services_starts_all_services(monkeypatch):
    started_services = []

    def fake_start_service(service_name):
        started_services.append(service_name)
        return f"{service_name}: Active"

    monkeypatch.setattr(IoT_IDS_prototype, "start_service", fake_start_service)

    result = IoT_IDS_prototype.start_ids_services()

    assert started_services == IoT_IDS_prototype.SERVICES
    assert result == [
        "suricata: Active",
        "filebeat: Active",
        "elasticsearch: Active",
        "evebox: Active"
    ]

def test_stop_ids_services_stops_all_services(monkeypatch):
    stopped_services = []

    def fake_stop_service(service_name):
        stopped_services.append(service_name)
        return f"{service_name}: Inactive"

    monkeypatch.setattr(IoT_IDS_prototype, "stop_service", fake_stop_service)

    result = IoT_IDS_prototype.stop_ids_services()

    assert stopped_services == IoT_IDS_prototype.STOP_SERVICES
    assert result == [
        "evebox: Inactive",
        "filebeat: Inactive",
        "suricata: Inactive",
        "elasticsearch: Inactive"
    ]

def test_get_sudo_password_reads_password_once(monkeypatch):
    IoT_IDS_prototype.SUDO_PASSWORD = None

    getpass_calls = []

    def fake_getpass(prompt):
        getpass_calls.append(prompt)
        return "fake_sudo_password"

    monkeypatch.setattr(IoT_IDS_prototype, "getpass", fake_getpass)

    result = IoT_IDS_prototype.get_sudo_password()

    assert result == "fake_sudo_password"
    assert IoT_IDS_prototype.SUDO_PASSWORD == "fake_sudo_password"
    assert getpass_calls == ["Enter sudo password: "]

def test_get_es_password_reads_password_once(monkeypatch):
    IoT_IDS_prototype.ES_PASSWORD = None

    getpass_calls = []

    def fake_getpass(prompt):
        getpass_calls.append(prompt)
        return "fake_es_password"

    monkeypatch.setattr(IoT_IDS_prototype, "getpass", fake_getpass)

    result = IoT_IDS_prototype.get_es_password()

    assert result == "fake_es_password"
    assert IoT_IDS_prototype.ES_PASSWORD == "fake_es_password"
    assert getpass_calls == ["Enter Elasticsearch password: "]

def test_ml_pid_running_returns_true_when_pid_exists(monkeypatch, tmp_path):
    fake_pid_file = tmp_path / "ml_service.pid"
    fake_pid_file.write_text("12345", encoding="utf-8")

    monkeypatch.setattr(IoT_IDS_prototype, "ML_PID_FILE", fake_pid_file)

    def fake_kill(pid, signal_number):
        assert pid == 12345
        assert signal_number == 0

    monkeypatch.setattr(IoT_IDS_prototype.os, "kill", fake_kill)

    result = IoT_IDS_prototype.ml_pid_running()

    assert result is True

def test_ml_status_returns_active_when_pid_is_running(monkeypatch):
    monkeypatch.setattr(IoT_IDS_prototype, "ml_pid_running", lambda: True)

    result = IoT_IDS_prototype.ml_status()

    assert result == "Active"

def test_get_services_status_returns_all_services_and_ml_status(monkeypatch):
    def fake_check_service_status(service_name):
        return "Active"

    monkeypatch.setattr(IoT_IDS_prototype, "check_service_status", fake_check_service_status)
    monkeypatch.setattr(IoT_IDS_prototype, "ml_status", lambda: "Inactive")

    result = IoT_IDS_prototype.get_services_status()

    assert result == [
        "suricata      : Active",
        "filebeat      : Active",
        "elasticsearch : Active",
        "evebox        : Active",
        "ml_model      : Inactive"
    ]

def test_start_ml_model_starts_process_when_not_running(monkeypatch, tmp_path):
    fake_pid_file = tmp_path / "ml_service.pid"
    fake_log_file = tmp_path / "ml_service.log"
    fake_ml_service = tmp_path / "ml_service.py"
    fake_ml_service.write_text("print('fake ml service')", encoding="utf-8")

    monkeypatch.setattr(IoT_IDS_prototype, "ML_PID_FILE", fake_pid_file)
    monkeypatch.setattr(IoT_IDS_prototype, "ML_LOG_FILE", fake_log_file)
    monkeypatch.setattr(IoT_IDS_prototype, "ML_SERVICE_PATH", str(fake_ml_service))
    monkeypatch.setattr(IoT_IDS_prototype, "PYTHON_BIN", "python")
    monkeypatch.setattr(IoT_IDS_prototype, "ml_pid_running", lambda: False)
    monkeypatch.setattr(IoT_IDS_prototype, "get_es_password", lambda: "fake_es_password")
    monkeypatch.setattr(IoT_IDS_prototype.time, "sleep", lambda seconds: None)

    class FakeProcess:
        pid = 12345

    def fake_popen(cmd, env, stdout, stderr, stdin, start_new_session):
        assert cmd == ["python", str(fake_ml_service)]
        assert env["ES_PASSWORD"] == "fake_es_password"
        return FakeProcess()

    monkeypatch.setattr(IoT_IDS_prototype.subprocess, "Popen", fake_popen)

    running_checks = [False, True]

    def fake_ml_pid_running():
        return running_checks.pop(0)

    monkeypatch.setattr(IoT_IDS_prototype, "ml_pid_running", fake_ml_pid_running)

    result = IoT_IDS_prototype.start_ml_model()

    assert result == "ML model: Active"
    assert fake_pid_file.read_text(encoding="utf-8") == "12345"

def test_stop_ml_model_stops_running_process(monkeypatch, tmp_path):
    fake_pid_file = tmp_path / "ml_service.pid"
    fake_pid_file.write_text("12345", encoding="utf-8")

    monkeypatch.setattr(IoT_IDS_prototype, "ML_PID_FILE", fake_pid_file)

    killed_pids = []

    def fake_kill(pid, signal_number):
        killed_pids.append((pid, signal_number))

    monkeypatch.setattr(IoT_IDS_prototype.os, "kill", fake_kill)
    monkeypatch.setattr(IoT_IDS_prototype.time, "sleep", lambda seconds: None)

    result = IoT_IDS_prototype.stop_ml_model()

    assert result == "ML model: Inactive"
    assert killed_pids == [(12345, IoT_IDS_prototype.signal.SIGTERM)]
    assert not fake_pid_file.exists()

def test_open_evebox_opens_browser_and_returns_url(monkeypatch):
    opened_urls = []

    def fake_open(url):
        opened_urls.append(url)

    monkeypatch.setattr(IoT_IDS_prototype.webbrowser, "open", fake_open)

    result = IoT_IDS_prototype.open_evebox()

    assert opened_urls == [IoT_IDS_prototype.EVEBOX_URL]
    assert result == f"EveBox: {IoT_IDS_prototype.EVEBOX_URL}"

def test_print_menu_calls_dependencies_and_prints(monkeypatch):
    printed_lines = []

    def fake_print(*args, **kwargs):
        printed_lines.append(" ".join(str(a) for a in args))

    monkeypatch.setattr(IoT_IDS_prototype, "clear_screen", lambda: None)
    monkeypatch.setattr(IoT_IDS_prototype, "get_services_status", lambda: ["svc1: Active", "svc2: Inactive"])
    monkeypatch.setattr(IoT_IDS_prototype, "figlet_format", lambda text, font: "BANNER")
    monkeypatch.setattr("builtins.print", fake_print)

    IoT_IDS_prototype.print_menu("Test message")

    assert any("IoT IDS Prototype" in line or "BANNER" in line for line in printed_lines)
    assert any("svc1: Active" in line for line in printed_lines)
    assert any("svc2: Inactive" in line for line in printed_lines)
    assert any("1. Start IDS" in line for line in printed_lines)
    assert any("Test message" in line for line in printed_lines)

def test_main_exit_option_stops_services_and_exits(monkeypatch):
    inputs = ["0"]

    def fake_input(prompt):
        return inputs.pop(0)

    printed_lines = []

    def fake_print(*args, **kwargs):
        printed_lines.append(" ".join(str(a) for a in args))

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", fake_print)
    monkeypatch.setattr(IoT_IDS_prototype, "print_menu", lambda msg: None)
    monkeypatch.setattr(IoT_IDS_prototype, "stop_ml_model", lambda: "ML model: Inactive")
    monkeypatch.setattr(IoT_IDS_prototype, "stop_ids_services", lambda: ["svc stopped"])

    IoT_IDS_prototype.main()

    assert any("ML model: Inactive" in line for line in printed_lines)
    assert any("svc stopped" in line for line in printed_lines)
    assert any("Goodbye software engineer!" in line for line in printed_lines)
