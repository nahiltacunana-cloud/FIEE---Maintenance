# FIEE-Maintenance: Sistema Inteligente de Gestión y Mantenimiento Predictivo

![Status](https://img.shields.io/badge/Status-Desarrollo-green)
![Tech](https://img.shields.io/badge/Framework-Streamlit-FF4B4B)
![AI](https://img.shields.io/badge/IA-Vision_Transformer-blue)
![Database](https://img.shields.io/badge/Cloud-Supabase-3ECF8E)

Plataforma tecnológica integral orientada a la **Industria 4.0** para la gestión, diagnóstico visual y mantenimiento predictivo de equipos de laboratorio críticos en la **Facultad de Ingeniería Eléctrica y Electrónica (FIEE)**.

## Objetivo del Proyecto
Desarrollar una solución basada en **Programación Orientada a Objetos (POO)** e Inteligencia Artificial que permita modelar y predecir el ciclo de vida de los activos físicos. El sistema genera evidencia técnica automatizada (diagnóstico visual y cálculos de degradación) para justificar y optimizar la gestión de recursos y la renovación tecnológica de la facultad.

---

## Pilares Tecnológicos

### 1. Visión por Computador (IA)
Integración con un modelo de **Deep Learning** basado en la arquitectura *Vision Transformer* (ViT), alojado en [Hugging Face](https://huggingface.co/NahilSisai/vit-mantenimiento-fiee).
* **Función:** Diagnóstico visual automatizado para identificar estados de desgaste en osciloscopios, multímetros y motores.

### 2. Mantenimiento Predictivo & Big Data
Implementación de algoritmos matemáticos para el cálculo del **Tiempo Útil Restante (RUL)**.
* **Modelos:** Aplicación de degradación lineal y exponencial para proyectar fallos antes de que ocurran.
* **Visualización:** Dashboards interactivos en Streamlit para la toma de decisiones basada en datos.

### 3. Ciberseguridad & Cloud
Infraestructura segura mediante [Supabase](https://supabase.com/).
* **Autenticación:** Control de Acceso Basado en Roles (RBAC) para separar privilegios entre Docentes y Estudiantes.
* **Seguridad:** Gestión de sesiones mediante tokens (JWT) y flujo de credenciales protegidas.

---

## Arquitectura del Sistema (UML)
El software sigue un patrón de diseño desacoplado (MVC) asegurando escalabilidad y mantenimiento limpio.

* **Capa de Vistas:** Herencia de clases para interfaces de Dashboard e Inspección.
* **Capa de Modelo:** Representación de activos físicos (Motores, Osciloscopios) mediante POO.
* **Capa de Servicios:** Conectores para la IA de Hugging Face y la base de datos de Supabase.

---

## Antecedentes y Referencias
Este proyecto se fundamenta en las siguientes investigaciones y desarrollos open-source:
* [Python Electronics Inventory](https://github.com/Jacob-Pitsenberger/Python-Electronics-Inventory-Management-System-Object-Oriented-Programming-Project): Base para la arquitectura POO.
* [Predictive Maintenance ML](https://github.com/RushikeshKothawade07/predictive-maintenance-ML): Lógica de mantenimiento predictivo.
* [Ralph Asset Management](https://github.com/allegro/ralph): Gestión institucional de activos.

---
## Instalación y Uso

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/nahiltacunana-cloud/FIEE---Maintenance.git](https://github.com/nahiltacunana-cloud/FIEE---Maintenance.git)
   cd FIEE---Maintenance
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
3. **Configurar Secretos:**
   Crea un archivo .streamlit/secrets.toml con tus credenciales:
   ```bash
   SUPABASE_URL = "tu_url_aqui"
   SUPABASE_KEY = "tu_key_aqui"
4. **Ejecutar aplicación:**
   ```bash
   streamlit run app.py
---
## Autoras

* **Nahil Sisai Tacunana Alvarado**
* **Nicole Grezy Gutierrez Ramos**
* *Estudiantes de la Facultad de Ingeniería Eléctrica y Electrónica (FIEE)*
