import os
from supabase import create_client
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

class DatabaseConnection:
    """
    Clase que implementa el patrón Singleton para asegurar una única 
    instancia de conexión a la base de datos Supabase.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url: 
                raise ValueError("Error: No se encontraron las credenciales de Supabase en el archivo .env")
            cls._instance = create_client(url, key)
        return cls._instance

# Instancia global de la base de datos para uso en repositorios
db = DatabaseConnection()