from agentshield.services.bootstrap_service import bootstrap
from agentshield.storage.events_repo import count_events


def main() -> None:
    result = bootstrap()

    print("AgentShield bootstrap succeeded.")
    print(f"App: {result['app_name']} v{result['version']}")
    print(f"Mode: {result['mode']}")
    print(f"Policy mode: {result['policy_mode']}")
    print(f"Proxy target: {result['proxy']}")
    print(f"UI target: {result['ui']}")
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Stored events: {count_events()}")


if __name__ == "__main__":
    main()
