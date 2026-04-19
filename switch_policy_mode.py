from pathlib import Path
import sys
import yaml


SETTINGS_PATH = Path("configs/settings.yaml")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"observe", "enforce"}:
        print("Usage: python switch_policy_mode.py [observe|enforce]")
        raise SystemExit(1)

    mode = sys.argv[1]

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["policy"]["mode"] = mode

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    print(f"Policy mode switched to: {mode}")


if __name__ == "__main__":
    main()
