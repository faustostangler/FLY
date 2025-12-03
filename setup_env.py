import os
import json
import platform

def run():
    vscode_dir = ".vscode"
    settings_path = os.path.join(vscode_dir, "settings.json")

    # Detect OS
    is_windows = platform.system() == "Windows"

    # Default fallback
    fallback_path = (
        "${workspaceFolder}\\.venv\\Scripts\\python.exe"
        if is_windows else
        "/mnt/linux_d/venvs/ai-env/bin/python"
    )

    # Try to load existing settings.json
    default_path = None
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                data = json.load(f)
                default_path = data.get("python.defaultInterpreterPath")
        except Exception:
            pass  # ignore malformed file

    # Use existing interpreter if found, otherwise fallback
    env_path = default_path or fallback_path

    # Ensure .vscode exists
    os.makedirs(vscode_dir, exist_ok=True)

    # Build final settings
    settings = {
        "python.defaultInterpreterPath": env_path,
        "python.terminal.activateEnvironment": True,
        "python.terminal.activateEnvInCurrentTerminal": True
    }

    # Save file
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=4)

    print(f"[✓] VSCode configurado para usar: {env_path}")

run()
