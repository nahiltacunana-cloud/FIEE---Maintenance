import os
import torch
from datasets import load_dataset
from transformers import (
    AutoImageProcessor, 
    AutoModelForImageClassification, 
    TrainingArguments, 
    Trainer,
    DefaultDataCollator
)

# 1. Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(BASE_DIR, "dataset", "train")
model_output_path = os.path.join(BASE_DIR, "modelo")

# 2. Cargar dataset desde cero
dataset = load_dataset("imagefolder", data_dir=dataset_path, split="train")

# 3. Processor
modelo_base = "google/vit-base-patch16-224"
processor = AutoImageProcessor.from_pretrained(modelo_base)

# 4. Función de procesamiento
def preparacion_imagenes(examples):
    # Asegurar RGB y procesar
    imagenes_rgb = [img.convert("RGB") for img in examples["image"]]
    inputs = processor(imagenes_rgb, return_tensors="pt")
    # Aseguramos que la etiqueta se llame 'labels' (con 's' final), es como lo pide el Trainer
    inputs["labels"] = examples["label"]
    return inputs

# 5. Mapeo y creación del dataset final
dataset_procesado = dataset.map(
    preparacion_imagenes, 
    batched=True, 
    remove_columns=dataset.column_names, 
    load_from_cache_file=False 
)

# 6. Mapeo de etiquetas
labels = dataset.features["label"].names
num_labels = len(labels)
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for i, label in enumerate(labels)}

# 7. Cargar modelo
model = AutoModelForImageClassification.from_pretrained(
    modelo_base,
    num_labels=num_labels,
    label2id=label2id,
    id2label=id2label,
    ignore_mismatched_sizes=True
)

# 8. Configuración de entrenamiento
training_args = TrainingArguments(
    output_dir=model_output_path,
    per_device_train_batch_size=4,
    num_train_epochs=5,
    logging_steps=10,
    save_strategy="epoch",
    remove_unused_columns=False, 
    push_to_hub=False,
    report_to="none"
)

# 9. Trainer (usando la variable correcta: dataset_procesado)
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset_procesado,
    data_collator=DefaultDataCollator()
)

# 10. Ejecución
print(f"Iniciando entrenamiento para {num_labels} clases...")
trainer.train()

# Guardar
trainer.save_model(model_output_path)
processor.save_pretrained(model_output_path)
print(f"\n¡Éxito! Modelo guardado en: {model_output_path}")