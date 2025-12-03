import os
import sys
import json
import platform

def run():
    vscode_dir = ".vscode"
    settings_path = os.path.join(vscode_dir, "settings.json")

    is_windows = platform.system() == "Windows"

    # Caminho base do código (workspace)
    codebase_path = os.getcwd().lower()

    # Lógica de fallback
    if is_windows:
        fallback_path = "${workspaceFolder}\\.venv\\Scripts\\python.exe"
    else:
        if "fly" in codebase_path:
            fallback_path = "/mnt/linux_d/venvs/fly-env/bin/python"
        else:
            fallback_path = sys.executable

    # Carrega settings existentes se houver
    data = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}

    # NÃO sobrescreve python.defaultInterpreterPath se já existir
    env_path = data.get("python.defaultInterpreterPath", fallback_path)

    # Garante .vscode
    os.makedirs(vscode_dir, exist_ok=True)

    # Atualiza configs
    data["python.defaultInterpreterPath"] = env_path
    data["python.terminal.activateEnvironment"] = True
    data["python.terminal.activateEnvInCurrentTerminal"] = True

    with open(settings_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[✓] VSCode configurado para usar: {env_path}")

run()
