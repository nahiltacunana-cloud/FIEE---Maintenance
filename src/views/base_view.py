from abc import ABC, abstractmethod
import streamlit as st

class Vista(ABC):
    """
    Clase Abstracta (Abstracción). 
    Define el contrato que todas las pantallas deben cumplir.
    """
    
    @abstractmethod
    def render(self):
        """Método abstracto que las hijas deben obligatoriamente implementar."""
        pass