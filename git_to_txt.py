# Python package usage
from gitingest import ingest
repo = "https://github.com/faustostangler/FLY"
branch = "2025-11-19-Charts-Rebuild-01"

summary, tree, content = ingest(repo, branch=branch)

# Mapeia o conteúdo para os nomes de arquivo
repo_name_prefix = repo.split('/')[-1].lower()
files_to_save = {
    f"{repo_name_prefix}_summary.txt": summary,
    f"{repo_name_prefix}_tree.txt": tree,
    f"{repo_name_prefix}_content.txt": content
}

# === Salvamento dos Arquivos ===
for filename, data in files_to_save.items():
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(data)
        # print(f"✅ Arquivo salvo com sucesso: {filename}")
    except Exception as e:
        print(f"❌ Falha ao salvar o arquivo {filename}: {e}")

# print("\n--- Preview da Estrutura da Branch ---")
# Exibe a estrutura de arquivos (tree) para confirmação
# print(tree)
