from __future__ import annotations

import time

from agentshield.collectors.file_collector import FileCollector
from agentshield.collectors.network_collector import NetworkCollector
from agentshield.collectors.process_collector import ProcessCollector
from agentshield.storage.db import init_db


def main() -> None:
    print("Starting AgentShield host telemetry collectors...")
    init_db()

    process_collector = ProcessCollector()
    network_collector = NetworkCollector()
    file_collector = FileCollector()

    file_collector.start()

    try:
        while True:
            new_processes = process_collector.poll()
            new_connections = network_collector.poll()

            if new_processes or new_connections:
                print(
                    f"[telemetry] new_processes={new_processes} "
                    f"new_connections={new_connections}"
                )

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nStopping host telemetry collectors...")
        file_collector.stop()


if __name__ == "__main__":
    main()
