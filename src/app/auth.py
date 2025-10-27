# from fastapi import Header, HTTPException, Depends
# from typing import Optional
# # import firebase_admin
# # from firebase_admin import credentials, auth as firebase_auth
# import logging
# import os

# # Configurar logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Inicializar Firebase solo una vez, de forma segura
# def initialize_firebase():
#     try:
#         # Verificar si ya está inicializado
#         firebase_admin.get_app()
#         logger.info("Firebase ya está inicializado")
#     except ValueError:
#         # Si no está inicializado, inicializarlo
#         # Obtener la ruta del archivo de credenciales
#         firebase_cred_path = os.getenv(
#             'FIREBASE_CREDENTIALS_PATH',
#             '/app/src/alertmanager-fcb15-firebase-adminsdk-fbsvc-3f66ef9c9c.json'
#         )

#         # Verificar que el archivo existe
#         if not os.path.exists(firebase_cred_path):
#             logger.error(f"Archivo de credenciales no encontrado: {firebase_cred_path}")
#             raise FileNotFoundError(f"Firebase credentials not found at {firebase_cred_path}")

#         logger.info(f"Cargando credenciales desde: {firebase_cred_path}")
#         cred = credentials.Certificate(firebase_cred_path)
#         firebase_admin.initialize_app(cred)
#         logger.info("Firebase inicializado correctamente")

# # Llamar la inicialización al importar el módulo
# initialize_firebase()

# def verify_access_token(authorization: Optional[str] = Header(None)):
#     """
#     Verifica el token de Firebase de forma más robusta
#     """
#     # Validar formato del header
#     if not authorization:
#         logger.warning("Header de autorización faltante")
#         raise HTTPException(
#             status_code=401,
#             detail="Token de autorización requerido"
#         )

#     if not authorization.startswith("Bearer "):
#         logger.warning(f"Formato de token inválido: {authorization[:20]}...")
#         raise HTTPException(
#             status_code=401,
#             detail="Formato de token inválido. Use 'Bearer <token>'"
#         )

#     # Extraer token
#     token = authorization.split(" ")[1]

#     if not token or len(token.strip()) == 0:
#         logger.warning("Token vacío recibido")
#         raise HTTPException(
#             status_code=401,
#             detail="Token vacío"
#         )

#     logger.info(f"Verificando token: {token[:20]}...")

#     try:
#         # Verificar token con opciones adicionales
#         decoded_token = firebase_auth.verify_id_token(
#             token,
#             check_revoked=True,  # Verificar si el token ha sido revocado

#         )

#         logger.info(f"Token verificado exitosamente para usuario: {decoded_token.get('uid', 'unknown')}")
#         return decoded_token

#     except firebase_auth.ExpiredIdTokenError:
#         logger.error("Token expirado")
#         raise HTTPException(
#             status_code=401,
#             detail="Token expirado. Por favor, inicie sesión nuevamente"
#         )
#     except firebase_auth.RevokedIdTokenError:
#         logger.error("Token revocado")
#         raise HTTPException(
#             status_code=401,
#             detail="Token revocado. Por favor, inicie sesión nuevamente"
#         )
#     except firebase_auth.InvalidIdTokenError as e:
#         logger.error(f"Token inválido: {str(e)}")
#         raise HTTPException(
#             status_code=401,
#             detail="Token inválido"
#         )
#     except Exception as e:
#         logger.error(f"Error inesperado verificando token: {str(e)}")
#         raise HTTPException(
#             status_code=401,
#             detail="Error de autenticación"
#         )

# # verify_access_token()
