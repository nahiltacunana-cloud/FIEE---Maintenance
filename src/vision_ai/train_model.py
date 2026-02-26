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

class ModeloEntrenador:
    """Clase especializada en el Fine-Tuning de modelos ViT para diagnóstico."""

    def __init__(self, modelo_base="google/vit-base-patch16-224"):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_path = os.path.join(self.base_dir, "dataset", "train")
        self.output_path = os.path.join(self.base_dir, "modelo")
        
        # Componentes de Hugging Face
        self.modelo_nombre = modelo_base
        self.processor = AutoImageProcessor.from_pretrained(self.modelo_nombre)
        self.model = None

    def _preparar_imagenes(self, examples):
        """Método privado para procesar tensores de imagen."""
        imagenes_rgb = [img.convert("RGB") for img in examples["image"]]
        inputs = self.processor(imagenes_rgb, return_tensors="pt")
        inputs["labels"] = examples["label"]
        return inputs

    def ejecutar_entrenamiento(self, epochs=5):
        """Orquesta todo el proceso de carga, mapeo y entrenamiento."""
        print("--- Iniciando proceso de entrenamiento POO ---")
        
        # 1. Carga de datos
        raw_dataset = load_dataset("imagefolder", data_dir=self.dataset_path, split="train")
        
        # 2. Procesamiento
        dataset_procesado = raw_dataset.map(
            self._preparar_imagenes, 
            batched=True, 
            remove_columns=raw_dataset.column_names
        )

        # 3. Configuración de etiquetas (Metadata)
        labels = raw_dataset.features["label"].names
        label2id = {label: i for i, label in enumerate(labels)}
        id2label = {i: label for i, label in enumerate(labels)}

        # 4. Inicialización del Modelo
        self.model = AutoModelForImageClassification.from_pretrained(
            self.modelo_nombre,
            num_labels=len(labels),
            label2id=label2id,
            id2label=id2label,
            ignore_mismatched_sizes=True
        )

        # 5. Configuración de Hiperparámetros
        args = TrainingArguments(
            output_dir=self.output_path,
            per_device_train_batch_size=4,
            num_train_epochs=epochs,
            logging_steps=10,
            save_strategy="epoch",
            remove_unused_columns=False,
            report_to="none"
        )

        # 6. Entrenamiento
        trainer = Trainer(
            model=self.model,
            args=args,
            train_dataset=dataset_procesado,
            data_collator=DefaultDataCollator()
        )

        trainer.train()

        # 7. Persistencia
        trainer.save_model(self.output_path)
        self.processor.save_pretrained(self.output_path)
        print(f"--- Entrenamiento finalizado. Modelo guardado en {self.output_path} ---")

if __name__ == "__main__":
    entrenador = ModeloEntrenador()
    entrenador.ejecutar_entrenamiento()