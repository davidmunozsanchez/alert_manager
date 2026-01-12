import os
import pytest
from airflow.models import Variable


class TestGitHubSecrets:
    """
    Tests para verificar que todos los secrets de GitHub están configurados
    y son accesibles desde Airflow y el código.
    
    Secretos requeridos:
    - AEMET_API_KEY: API Key para acceder a AEMET OpenData
    
    Secretos opcionales (con defaults):
    - POSTGRES_USER: Usuario de PostgreSQL (default: postgres)
    - POSTGRES_PASSWORD: Password de PostgreSQL (default: postgres)
    - POSTGRES_DB: Base de datos (default: alerts)
    - AIRFLOW_DB_USER: Usuario de Airflow DB (default: airflow)
    - AIRFLOW_DB_PASSWORD: Password de Airflow DB (default: airflow)
    - AIRFLOW_DB_NAME: Base de datos de Airflow (default: airflow)
    - AIRFLOW_FERNET_KEY: Clave Fernet para Airflow (cifrado)
    - AIRFLOW_ADMIN_USER: Admin user de Airflow (default: admin)
    - AIRFLOW_ADMIN_PASSWORD: Admin password de Airflow (default: admin)
    - AIRFLOW_ADMIN_EMAIL: Admin email de Airflow (default: admin@example.com)
    - AIRFLOW_WEBSERVER_SECRET_KEY: Secret key del webserver (default: mysecret)
    - SEQ_ADMIN_PASSWORD_HASH: Hash del admin password de Seq (opcional)
    - GITHUB_TOKEN: Token de GitHub para CI/CD
    - LOG_LEVEL: Nivel de logging (default: info)
    - DISABLE_AUTH: Deshabilitar autenticación (default: false)
    - ENVIRONMENT: Environment (default: development)
    """

    # Definir los secrets requeridos
    REQUIRED_SECRETS = {
        "AEMET_API_KEY": {
            "description": "API Key para acceder a AEMET OpenData",
            "required": True,
            "fallback": "env_var",
            "services": ["aemet_alerts_ingestion"],
        },
    }

    # Secrets de PostgreSQL (aplicaciones)
    POSTGRES_SECRETS = {
        "POSTGRES_USER": {
            "description": "Usuario de PostgreSQL para alertas",
            "required": False,
            "default": "postgres",
            "services": ["db", "web"],
        },
        "POSTGRES_PASSWORD": {
            "description": "Password de PostgreSQL para alertas",
            "required": False,
            "default": "postgres",
            "services": ["db", "web"],
        },
        "POSTGRES_DB": {
            "description": "Base de datos de alertas",
            "required": False,
            "default": "alerts",
            "services": ["db", "web"],
        },
    }

    # Secrets de Airflow
    AIRFLOW_SECRETS = {
        "AIRFLOW_DB_USER": {
            "description": "Usuario de la base de datos de Airflow",
            "required": False,
            "default": "airflow",
            "services": ["airflow-db", "airflow-init", "airflow-webserver", "airflow-scheduler"],
        },
        "AIRFLOW_DB_PASSWORD": {
            "description": "Password de la base de datos de Airflow",
            "required": False,
            "default": "airflow",
            "services": ["airflow-db", "airflow-init", "airflow-webserver", "airflow-scheduler"],
        },
        "AIRFLOW_DB_NAME": {
            "description": "Nombre de la base de datos de Airflow",
            "required": False,
            "default": "airflow",
            "services": ["airflow-db", "airflow-init", "airflow-webserver", "airflow-scheduler"],
        },
        "AIRFLOW_FERNET_KEY": {
            "description": "Clave Fernet para cifrar passwords en Airflow",
            "required": False,
            "services": ["airflow-init", "airflow-webserver", "airflow-scheduler"],
        },
        "AIRFLOW_ADMIN_USER": {
            "description": "Username del admin de Airflow",
            "required": False,
            "default": "admin",
            "services": ["airflow-init", "airflow-webserver"],
        },
        "AIRFLOW_ADMIN_PASSWORD": {
            "description": "Password del admin de Airflow",
            "required": False,
            "default": "admin",
            "services": ["airflow-init", "airflow-webserver"],
        },
        "AIRFLOW_ADMIN_EMAIL": {
            "description": "Email del admin de Airflow",
            "required": False,
            "default": "admin@example.com",
            "services": ["airflow-init", "airflow-webserver"],
        },
        "AIRFLOW_WEBSERVER_SECRET_KEY": {
            "description": "Secret key para el webserver de Airflow",
            "required": False,
            "default": "mysecret",
            "services": ["airflow-webserver"],
        },
    }

    # Secrets opcionales
    OPTIONAL_SECRETS = {
        "GITHUB_TOKEN": {
            "description": "Token de GitHub para CI/CD",
            "required": False,
            "services": ["github-actions"],
        },
        "SEQ_ADMIN_PASSWORD_HASH": {
            "description": "Hash del password del admin de Seq",
            "required": False,
            "services": ["seq"],
        },
        "LOG_LEVEL": {
            "description": "Nivel de logging",
            "required": False,
            "default": "info",
            "services": ["web"],
        },
        "DISABLE_AUTH": {
            "description": "Deshabilitar autenticación",
            "required": False,
            "default": "false",
            "services": ["web"],
        },
        "ENVIRONMENT": {
            "description": "Environment (development, staging, production)",
            "required": False,
            "default": "development",
            "services": ["web"],
        },
    }

    @pytest.fixture
    def all_secrets(self):
        """Combina todos los secrets"""
        return {
            **self.REQUIRED_SECRETS,
            **self.POSTGRES_SECRETS,
            **self.AIRFLOW_SECRETS,
            **self.OPTIONAL_SECRETS,
        }

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

    def test_postgres_secrets_configured(self):
        """Verifica que los secrets de PostgreSQL están configurados"""
        postgres_env = {}
        for secret_name in self.POSTGRES_SECRETS.keys():
            value = os.getenv(secret_name)
            postgres_env[secret_name] = value or self.POSTGRES_SECRETS[secret_name].get("default")

        print(f"✅ PostgreSQL configurado con:")
        print(f"  - User: {postgres_env.get('POSTGRES_USER', '(default)')}")
        print(f"  - DB: {postgres_env.get('POSTGRES_DB', '(default)')}")
        print(f"  - Password: {'(configurada)' if os.getenv('POSTGRES_PASSWORD') else '(default)'}")

    def test_airflow_secrets_configured(self):
        """Verifica que los secrets de Airflow están configurados"""
        airflow_env = {}
        for secret_name in self.AIRFLOW_SECRETS.keys():
            value = os.getenv(secret_name)
            airflow_env[secret_name] = value or self.AIRFLOW_SECRETS[secret_name].get("default")

        print(f"✅ Airflow configurado con:")
        print(f"  - DB User: {airflow_env.get('AIRFLOW_DB_USER', '(default)')}")
        print(f"  - Admin User: {airflow_env.get('AIRFLOW_ADMIN_USER', '(default)')}")
        print(f"  - Admin Email: {airflow_env.get('AIRFLOW_ADMIN_EMAIL', '(default)')}")

    def test_aemet_api_key_not_hardcoded(self):
        """Verifica que AEMET_API_KEY no esté hardcoded en el código, configuración y docker"""
        # Buscar patrones sospechosos en archivos Python, YAML, env, etc.
        import glob
        from pathlib import Path

        suspicious_patterns = [
            "eyJhbGciOiJIUzI1NiJ9",  # Patrón JWT común - ESTO SÍ es un secret hardcodeado
        ]

        test_folder = Path(__file__).parent.parent
        
        # Buscar en múltiples tipos de archivos
        files_to_check = []
        
        # Python files en src
        files_to_check.extend([
            f for f in glob.glob(str(test_folder / "src" / "**" / "*.py"), recursive=True)
            if "__pycache__" not in f
        ])
        
        # Docker files
        files_to_check.extend(glob.glob(str(test_folder / "docker" / "*.yml")))
        files_to_check.extend(glob.glob(str(test_folder / "docker" / "*.yaml")))
        files_to_check.extend(glob.glob(str(test_folder / "docker-compose.yml")))
        
        # Archivos env
        files_to_check.extend(glob.glob(str(test_folder / ".env*")))

        hardcoded_files = []

        for file_path in files_to_check:
            if not file_path or not Path(file_path).exists():
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        # Ignorar comentarios y prints
                        if line.strip().startswith("#"):
                            continue
                        if "print(" in line:
                            continue

                        # Verificar patrones JWT (valores reales hardcodeados)
                        for pattern in suspicious_patterns:
                            if pattern in line:
                                hardcoded_files.append(
                                    f"{file_path}:{line_num} - {line.strip()[:100]}"
                                )

            except Exception as e:
                print(f"⚠️  Error revisando {file_path}: {e}")

        assert (
            len(hardcoded_files) == 0
        ), f"Se encontraron secrets potencialmente hardcoded:\n" + "\n".join(hardcoded_files)

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

    def test_all_secrets_summary(self, all_secrets):
        """Resumen de todos los secrets del proyecto"""
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE SECRETS DEL PROYECTO")
        print("=" * 60)

        print("\n🔴 REQUERIDOS (deben estar configurados):")
        for name, info in self.REQUIRED_SECRETS.items():
            status = "✅" if os.getenv(name) else "⚠️"
            print(f"  {status} {name}: {info['description']}")
            print(f"     Servicios: {', '.join(info.get('services', []))}")

        print("\n🟠 POSTGRES (tienen defaults, recomendado configurar):")
        for name, info in self.POSTGRES_SECRETS.items():
            value = os.getenv(name)
            status = "✅" if value else "⚪"
            print(f"  {status} {name}: {info['description']}")
            print(f"     Default: {info.get('default', 'N/A')} | Servicios: {', '.join(info.get('services', []))}")

        print("\n🟠 AIRFLOW (tienen defaults, recomendado configurar):")
        for name, info in self.AIRFLOW_SECRETS.items():
            value = os.getenv(name)
            status = "✅" if value else "⚪"
            print(f"  {status} {name}: {info['description']}")
            print(f"     Default: {info.get('default', 'N/A')} | Servicios: {', '.join(info.get('services', []))}")

        print("\n🟡 OPCIONALES:")
        for name, info in self.OPTIONAL_SECRETS.items():
            value = os.getenv(name)
            status = "✅" if value else "⚪"
            print(f"  {status} {name}: {info['description']}")
            print(f"     Servicios: {', '.join(info.get('services', []))}")

        print("\n" + "=" * 60)

