from pathlib import Path
import subprocess
import time


def main() -> None:
    print("Generating host activity for AgentShield collectors...")

    test_file = Path.home() / "AgentShield" / "host_test_file.txt"
    test_file.write_text("hello from host telemetry test\n", encoding="utf-8")
    time.sleep(1)
    _ = test_file.read_text(encoding="utf-8")
    time.sleep(1)
    test_file.write_text("second write\n", encoding="utf-8")
    time.sleep(1)

    subprocess.run(["bash", "-lc", "echo telemetry-network-test >/dev/tcp/example.com/80"], check=False)
    time.sleep(2)

    subprocess.run(["bash", "-lc", "curl -I https://example.com"], check=False)
    time.sleep(2)

    print("Host activity generation complete.")
