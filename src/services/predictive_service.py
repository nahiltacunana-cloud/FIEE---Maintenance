import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class PredictiveService:
    def generar_prediccion(self, equipo):
        # 1. Calculamos los días que han pasado desde la compra
        try:
            fecha_compra = datetime.strptime(equipo.fecha_compra, "%Y-%m-%d")
        except ValueError:
            fecha_compra = datetime.now() - timedelta(days=365) # Valor por defecto si falla
            
        hoy = datetime.now()
        dias_uso = (hoy - fecha_compra).days
        
        if dias_uso <= 0:
            dias_uso = 1 # Para evitar errores matemáticos

        desgaste_actual = equipo.calcular_obsolescencia()

        # 2. Simulamos la data histórica (Día 0 = 0% desgaste, Hoy = Desgaste actual)
        X = np.array([[0], [dias_uso // 2], [dias_uso]])
        y = np.array([0, desgaste_actual / 2.1, desgaste_actual])

        # 3. Entrenamos el modelo de IA (Regresión Lineal)
        modelo = LinearRegression()
        modelo.fit(X, y)

        # 4. Predecimos cuándo el desgaste llegará a 1.0 (100% = Falla total)
        m = modelo.coef_[0]
        b = modelo.intercept_
        
        if m <= 0:
            dias_para_falla = 3650 # Si no hay desgaste, asumimos 10 años
        else:
            dias_para_falla = (1.0 - b) / m

        fecha_falla = fecha_compra + timedelta(days=int(dias_para_falla))

        # 5. Generamos el Gráfico Visual
        fig, ax = plt.subplots(figsize=(6, 4))
        
        x_pred = np.array([[0], [dias_uso], [dias_para_falla]])
        y_pred = modelo.predict(x_pred)

        # Dibujamos las líneas
        ax.plot(x_pred, y_pred, color='red', linestyle='--', label='Tendencia IA')
        ax.scatter([dias_uso], [desgaste_actual], color='blue', zorder=5, label='Hoy')
        
        ax.set_title(f"Predicción de Falla: {equipo.modelo}")
        ax.set_xlabel("Días de Uso")
        ax.set_ylabel("Nivel de Desgaste (0 a 1)")
        ax.set_ylim(0, 1.1)
        ax.axhline(y=1.0, color='black', linestyle=':', label='Falla Crítica')
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fecha_falla.strftime("%Y-%m-%d"), fig