import os
import subprocess
from dotenv import load_dotenv

# Carrega a variável OLLAMA_API_KEY do arquivo .env
load_dotenv()


def iniciar():
    print("--- INICIALIZADOR OLLAMA (AIDER) ---")

    # Nome da variável que o Aider e o .env utilizam
    CHAVE_ENV = "OLLAMA_API_KEY"
    MODELO_PADRAO = "ollama_chat/gpt-oss:120b-cloud"

    # Verifica se a chave existe no .env
    chave_final = os.getenv(CHAVE_ENV)

    if not chave_final:
        print(f"Erro: A variável {CHAVE_ENV} não foi encontrada no arquivo .env")
        print("Certifique-se de que o arquivo .env existe e contém a chave.")
        return

    # Escolha do modelo
    modelo_custom = input(f"Modelo padrão: '{MODELO_PADRAO}'.\n[Enter] p/ confirmar ou digite o nome: ")
    nome_modelo = modelo_custom.strip() if modelo_custom.strip() else MODELO_PADRAO

    # Limpeza de arquivos de configuração que podem gerar conflitos
    if os.path.exists(".aider.model.settings.yml"):
        os.remove(".aider.model.settings.yml")

    # Prepara o ambiente para o subprocesso
    env_aider = os.environ.copy()
    env_aider[CHAVE_ENV] = chave_final

    try:
        print(f"\n[OK] Chave carregada com sucesso.")
        print(f"[OK] Iniciando Aider com o modelo '{nome_modelo}'...")

        # Executa o Aider
        subprocess.run(
            ["aider", "--model", nome_modelo, "--watch-files", "--architect"],
            env=env_aider,
            check=True
        )
    except FileNotFoundError:
        print("Erro: O comando 'aider' não foi encontrado. Verifique a instalação.")
    except subprocess.CalledProcessError as e:
        print(f"Aider encerrado. Código de saída: {e.returncode}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    iniciar()