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
