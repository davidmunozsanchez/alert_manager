import os
import pytest
from airflow.models import Variable


class TestGitHubSecrets:
    """
    Tests para verificar que todos los secrets de GitHub están configurados
    y son accesibles desde Airflow y el código.
    """

    # Definir los secrets requeridos
    REQUIRED_SECRETS = {
        "AEMET_API_KEY": {
            "description": "API Key para acceder a AEMET OpenData",
            "required": True,
            "fallback": "env_var",  # Puede venir de variable de entorno
        },
    }

    # Secrets opcionales
    OPTIONAL_SECRETS = {
        "GITHUB_TOKEN": {
            "description": "Token de GitHub para CI/CD",
            "required": False,
        },
        "DB_PASSWORD": {
            "description": "Password de PostgreSQL",
            "required": False,
        },
    }

    @pytest.fixture
    def all_secrets(self):
        """Combina secrets requeridos y opcionales"""
        return {**self.REQUIRED_SECRETS, **self.OPTIONAL_SECRETS}

    def test_required_secrets_configured(self):
        """Verifica que todos los secrets requeridos están configurados"""
        missing_secrets = []

        for secret_name, secret_info in self.REQUIRED_SECRETS.items():
            # Intentar obtener del ambiente
            env_value = os.getenv(secret_name)

            # Intentar obtener de Airflow Variable
            airflow_value = None
            try:
                airflow_value = Variable.get(secret_name, default=None)
            except Exception as e:
                print(f"⚠️  No se pudo acceder a Variable.get('{secret_name}'): {e}")

            # Verificar que al menos una fuente está configurada
            if not env_value and not airflow_value:
                missing_secrets.append(secret_name)
                print(f"❌ Secret requerido no encontrado: {secret_name}")

        assert len(missing_secrets) == 0, (
            f"Secrets requeridos no configurados: {missing_secrets}\n"
            f"Por favor, configúralos en GitHub Secrets o como variables de entorno."
        )

    def test_aemet_api_key_accessible(self):
        """Verifica que AEMET_API_KEY es accesible"""
        secret_name = "AEMET_API_KEY"

        # Intentar desde entorno
        env_value = os.getenv(secret_name)

        # Intentar desde Airflow
        airflow_value = None
        try:
            airflow_value = Variable.get(secret_name, default=None)
        except Exception as e:
            print(f"⚠️  No se pudo acceder a Airflow Variable: {e}")

        # Al menos una debe estar disponible
        assert (
            env_value or airflow_value
        ), f"{secret_name} no está configurado en variables de entorno ni en Airflow Variables"

        print(f"✅ {secret_name} accesible desde: ", end="")
        sources = []
        if env_value:
            sources.append("variable de entorno")
        if airflow_value:
            sources.append("Airflow Variable")
        print(" y ".join(sources))

    def test_aemet_api_key_not_hardcoded(self):
        """Verifica que AEMET_API_KEY no esté hardcoded en el código"""
        # Buscar patrones sospechosos en archivos Python
        import glob
        from pathlib import Path

        suspicious_patterns = [
            "AEMET_API_KEY",
            "eyJhbGciOiJIUzI1NiJ9",  # Patrón JWT común
        ]

        test_folder = Path(__file__).parent.parent
        python_files = [
            f
            for f in glob.glob(str(test_folder / "src" / "**" / "*.py"), recursive=True)
            if "__pycache__" not in f
        ]

        hardcoded_files = []

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # No buscar en comentarios
                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        # Ignorar comentarios
                        if line.strip().startswith("#"):
                            continue

                        # Verificar patrones
                        for pattern in suspicious_patterns:
                            if (
                                pattern in line
                                and "Variable.get" not in line
                                and "os.getenv" not in line
                            ):
                                hardcoded_files.append(
                                    f"{py_file}:{line_num} - {line.strip()[:100]}"
                                )

            except Exception as e:
                print(f"⚠️  Error revisando {py_file}: {e}")

        assert (
            len(hardcoded_files) == 0
        ), f"Se encontraron secrets potencialmente hardcoded:\n" + "\n".join(hardcoded_files)

    def test_secrets_documentation(self):
        """Verifica que los secrets estén documentados"""
        from pathlib import Path

        doc_file = Path(__file__).parent.parent / "GITHUB_SECRETS_SETUP.md"

        assert (
            doc_file.exists()
        ), "Se debe crear GITHUB_SECRETS_SETUP.md con documentación de secrets"

        with open(doc_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verificar que los secrets requeridos están documentados
        for secret_name in self.REQUIRED_SECRETS.keys():
            assert (
                secret_name in content
            ), f"Secret '{secret_name}' no está documentado en GITHUB_SECRETS_SETUP.md"

        print("✅ Todos los secrets están documentados")

    def test_secrets_not_in_git_history(self):
        """
        Verificación suave: Advierte si hay archivos con posibles secrets sin ser ignorados.
        (Este test es más preventivo que restrictivo)
        """
        import glob
        from pathlib import Path

        sensitive_files = [
            ".env",
            ".env.local",
            "load_secrets.sh",
            "load_secrets.ps1",
        ]

        test_folder = Path(__file__).parent.parent

        for pattern in sensitive_files:
            found = list(test_folder.glob(f"**/{pattern}"))

            if found and pattern not in [".gitignore", "load_secrets*"]:
                for file_path in found:
                    gitignore_path = Path(__file__).parent.parent / ".gitignore"

                    if gitignore_path.exists():
                        with open(gitignore_path, "r") as f:
                            gitignore_content = f.read()

                        if pattern not in gitignore_content:
                            print(
                                f"⚠️  {file_path} existe pero no está en .gitignore"
                            )
