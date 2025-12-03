"""Utility to create VS Code configuration for the virtual environment."""

import json
import os
import platform

def run():
    # Detecta o sistema operacional
    is_windows = platform.system() == "Windows"
    vscode_dir = ".vscode"
    settings_path = os.path.join(vscode_dir, "settings.json")

    # Define o caminho do interpretador conforme o sistema
    if is_windows:
        python_path = "${workspaceFolder}\\.venv\\Scripts\\python.exe"
        os_env = "Windows"
    else:
        python_path = "${workspaceFolder}/.venv-linux/bin/python"
        os_env = "Linux"

    # Garante que o diretório .vscode existe
    os.makedirs(vscode_dir, exist_ok=True)

    # Monta o dicionário de configuração
    settings = {"python.defaultInterpreterPath": python_path}

    # Salva o settings.json
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=4)

    print(f"[✓] Ambiente configurado para: {os_env}")


# import os
# import json
# import platform

# def run():
    # vscode_dir = ".vscode"
    # settings_path = os.path.join(vscode_dir, "settings.json")

    # # Detect OS
    # is_windows = platform.system() == "Windows"

    # # Default fallback
    # fallback_path = (
        # "${workspaceFolder}\\.venv\\Scripts\\python.exe"
        # if is_windows else
        # "/mnt/linux_d/venvs/ai-env/bin/python"
    # )

    # # Try to load existing settings.json
    # default_path = None
    # if os.path.exists(settings_path):
        # try:
            # with open(settings_path, "r") as f:
                # data = json.load(f)
                # default_path = data.get("python.defaultInterpreterPath")
        # except Exception:
            # pass  # ignore malformed file

    # # Use existing interpreter if found, otherwise fallback
    # env_path = default_path or fallback_path

    # # Ensure .vscode exists
    # os.makedirs(vscode_dir, exist_ok=True)

    # # Build final settings
    # settings = {
        # "python.defaultInterpreterPath": env_path,
        # "python.terminal.activateEnvironment": True,
        # "python.terminal.activateEnvInCurrentTerminal": True
    # }

    # # Save file
    # with open(settings_path, "w") as f:
        # json.dump(settings, f, indent=4)

    # print(f"[✓] VSCode configurado para usar: {env_path}")

# run()
