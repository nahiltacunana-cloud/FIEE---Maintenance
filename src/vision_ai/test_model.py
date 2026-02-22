import os
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

# 1. Configurar la ruta donde se guardó el modelo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "modelo")

# 2. Cargar el procesador y el modelo entrenado
print("Cargando modelo...")
processor = AutoImageProcessor.from_pretrained(model_path, use_fast=False) # Agregué use_fast=False para quitar la advertencia amarilla
model = AutoModelForImageClassification.from_pretrained(model_path)

# 3. Pon aquí la ruta de la imagen que quieres probar
ruta_imagen = r"C:\Users\Ernesto\Downloads\EJEMPLO.jpg"

try:
    # 4. Abrir la imagen
    imagen = Image.open(ruta_imagen).convert("RGB")
    print("Imagen cargada correctamente. Analizando...\n")

    # 5. Procesar la imagen
    inputs = processor(images=imagen, return_tensors="pt")

    # 6. Hacer la predicción
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        
        # Calcular los porcentajes para TODAS las clases
        probabilidades = F.softmax(logits, dim=-1)[0]
        
        # Obtener las 3 predicciones más altas (Top 3)
        top_prob, top_indices = torch.topk(probabilidades, min(3, len(probabilidades)))

    # 7. Mostrar el resultado principal y el análisis de error
    clase_ganadora = model.config.id2label[top_indices[0].item()]
    confianza_ganadora = top_prob[0].item() * 100
    margen_error = 100 - confianza_ganadora

    print("="*50)
    print(f"🤖 PREDICCIÓN PRINCIPAL: {clase_ganadora}")
    print(f"📊 CONFIANZA:            {confianza_ganadora:.2f}%")
    print(f"⚠️ MARGEN DE DUDA:       {margen_error:.2f}%")
    print("="*50)
    
    print("\n🔍 ANÁLISIS DETALLADO (Top 3 de probabilidades):")
    for i in range(len(top_indices)):
        clase = model.config.id2label[top_indices[i].item()]
        prob = top_prob[i].item() * 100
        print(f"  {i+1}. {clase}: {prob:.2f}%")
    print("\n")

except FileNotFoundError:
    print(f"❌ Error: No se encontró ninguna imagen en la ruta: {ruta_imagen}")