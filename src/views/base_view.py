from abc import ABC, abstractmethod
import streamlit as st

class Vista(ABC):
    """
    Clase Base Abstracta para todas las vistas de la aplicación.
    Asegura que cada pantalla implemente su propia lógica de renderizado
    manteniendo una estructura consistente.
    """
    
    @abstractmethod
    def render(self):
        """
        Método obligatorio para renderizar los componentes de Streamlit 
        en la interfaz de usuario.
        """
        pass