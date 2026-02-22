import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url: raise ValueError("Falta .env")
            cls._instance = create_client(url, key)
            print("✅ Conexión Singleton establecida") # Esto te avisará que funcionó
        return cls._instance

# ESTA LÍNEA ES CLAVE: Crea el objeto "db" que usará todo el equipo
db = DatabaseConnection()