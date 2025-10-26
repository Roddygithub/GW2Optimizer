"""
AI Trainer v4.1.0 - ML Training Engine

Module principal d'entraînement du modèle de synergie.
Gère les cycles d'entraînement, validation, et checkpoints.

Features:
    - Batch training
    - Online learning (incremental)
    - Cross-validation
    - Checkpoint management
    - Performance metrics
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from app.core.logging import logger
from app.core.config import settings
from app.learning.models.synergy_model import SynergyModel, get_synergy_model
from app.ai.feedback import FeedbackHandler, get_feedback_handler


class AITrainer:
    """
    Entraîneur IA pour le modèle de synergie.

    Responsibilities:
        - Load training data from feedback
        - Train SynergyModel
        - Validate performance
        - Save checkpoints
        - Track metrics

    Example:
        ```python
        trainer = AITrainer()

        # Batch training
        metrics = trainer.train_batch(min_rating=6.0)
        print(f"Score improvement: {metrics['score_improvement']}")

        # Online learning
        trainer.train_online(feedback={
            "composition": {...},
            "rating": 8.5
        })

        # Save checkpoint
        trainer.save_checkpoint()
        ```
    """

    def __init__(self, model: Optional[SynergyModel] = None, feedback_handler: Optional[FeedbackHandler] = None):
        """
        Initialise le trainer.

        Args:
            model: SynergyModel instance (optionnel)
            feedback_handler: FeedbackHandler instance (optionnel)
        """
        self.model = model or get_synergy_model()
        self.feedback_handler = feedback_handler or get_feedback_handler()

        # Checkpoints directory
        self.checkpoints_dir = Path(settings.LEARNING_DATA_DIR) / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        # Metrics history
        self.metrics_history: List[Dict[str, Any]] = []

        logger.info("AITrainer initialized")

    def train_batch(
        self, min_rating: float = 5.0, max_samples: Optional[int] = None, save_checkpoint: bool = True
    ) -> Dict[str, Any]:
        """
        Entraîne le modèle sur un batch de données.

        Args:
            min_rating: Note minimale pour inclure
            max_samples: Nombre max d'échantillons
            save_checkpoint: Sauvegarder checkpoint après training

        Returns:
            Training metrics
        """
        logger.info("Starting batch training", extra={"min_rating": min_rating, "max_samples": max_samples})

        start_time = datetime.utcnow()

        # Charger training data
        training_data = self.feedback_handler.get_training_data(min_rating=min_rating, max_samples=max_samples)

        if not training_data:
            logger.warning("No training data available")
            return {"status": "no_data", "n_samples": 0}

        # Score avant entraînement
        score_before = self._evaluate_model(training_data)

        # Entraîner
        self.model.train(training_data)

        # Score après entraînement
        score_after = self._evaluate_model(training_data)

        # Calculer métriques
        duration = (datetime.utcnow() - start_time).total_seconds()

        metrics = {
            "status": "success",
            "n_samples": len(training_data),
            "score_before": score_before,
            "score_after": score_after,
            "score_improvement": score_after - score_before,
            "improvement_pct": ((score_after - score_before) / score_before * 100) if score_before > 0 else 0,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Sauvegarder métriques
        self.metrics_history.append(metrics)

        # Sauvegarder checkpoint
        if save_checkpoint:
            self.save_checkpoint(metrics)

        logger.info(
            "Batch training complete",
            extra={
                "n_samples": len(training_data),
                "improvement": f"{metrics['improvement_pct']:.2f}%",
                "duration": f"{duration:.2f}s",
            },
        )

        return metrics

    def train_online(self, feedback: Dict[str, Any], save_checkpoint: bool = False) -> Dict[str, Any]:
        """
        Entraînement online (incrémental) sur un feedback.

        Args:
            feedback: Feedback avec composition et rating
            save_checkpoint: Sauvegarder checkpoint après update

        Returns:
            Update metrics
        """
        logger.info("Online learning update")

        # Update model
        self.model.update(feedback)

        # Métriques
        metrics = {
            "status": "updated",
            "n_updates": self.model.metadata.get("n_updates", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Sauvegarder checkpoint (optionnel)
        if save_checkpoint:
            self.save_checkpoint(metrics)

        return metrics

    def validate(
        self, validation_data: Optional[List[Dict[str, Any]]] = None, test_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Valide le modèle sur un test set.

        Args:
            validation_data: Données de validation (optionnel)
            test_split: Proportion de test (si pas de validation_data)

        Returns:
            Validation metrics
        """
        # Si pas de validation data, split training data
        if validation_data is None:
            all_data = self.feedback_handler.get_training_data(min_rating=0.0)

            if not all_data:
                return {"status": "no_data"}

            # Split
            n_test = int(len(all_data) * test_split)
            np.random.shuffle(all_data)
            validation_data = all_data[:n_test]

        if not validation_data:
            return {"status": "no_data"}

        # Évaluer
        score = self._evaluate_model(validation_data)

        # Calculer erreurs
        errors = []
        for sample in validation_data:
            predicted = self.model.predict(sample["composition"])
            actual = sample["rating"]
            errors.append(abs(predicted - actual))

        metrics = {
            "status": "success",
            "n_samples": len(validation_data),
            "r2_score": score,
            "mae": np.mean(errors),
            "rmse": np.sqrt(np.mean([e**2 for e in errors])),
            "max_error": max(errors),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info("Validation complete", extra={"r2_score": f"{score:.3f}", "mae": f"{metrics['mae']:.3f}"})

        return metrics

    def save_checkpoint(self, metrics: Optional[Dict[str, Any]] = None) -> str:
        """
        Sauvegarde un checkpoint du modèle.

        Args:
            metrics: Métriques à sauvegarder avec le checkpoint

        Returns:
            Checkpoint path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"checkpoint_{timestamp}"
        checkpoint_dir = self.checkpoints_dir / checkpoint_name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarder modèle
        model_path = str(checkpoint_dir / "model.pkl")
        self.model.save(model_path)

        # Sauvegarder métriques
        if metrics:
            metrics_path = checkpoint_dir / "metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)

        # Sauvegarder historique
        history_path = checkpoint_dir / "history.json"
        with open(history_path, "w") as f:
            json.dump(self.metrics_history, f, indent=2)

        logger.info("Checkpoint saved", extra={"checkpoint": checkpoint_name})

        return str(checkpoint_dir)

    def load_checkpoint(self, checkpoint_name: str) -> bool:
        """
        Charge un checkpoint.

        Args:
            checkpoint_name: Nom du checkpoint

        Returns:
            True si succès, False sinon
        """
        checkpoint_dir = self.checkpoints_dir / checkpoint_name

        if not checkpoint_dir.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_name}")
            return False

        # Charger modèle
        model_path = str(checkpoint_dir / "model.pkl")
        success = self.model.load(model_path)

        if not success:
            return False

        # Charger historique
        history_path = checkpoint_dir / "history.json"
        if history_path.exists():
            with open(history_path, "r") as f:
                self.metrics_history = json.load(f)

        logger.info("Checkpoint loaded", extra={"checkpoint": checkpoint_name})

        return True

    def get_latest_checkpoint(self) -> Optional[str]:
        """
        Récupère le nom du dernier checkpoint.

        Returns:
            Checkpoint name ou None
        """
        checkpoints = sorted(self.checkpoints_dir.glob("checkpoint_*"))

        if not checkpoints:
            return None

        return checkpoints[-1].name

    def _evaluate_model(self, data: List[Dict[str, Any]]) -> float:
        """
        Évalue le modèle sur des données (R² score).

        Args:
            data: Training/validation data

        Returns:
            R² score
        """
        if not data:
            return 0.0

        predictions = []
        actuals = []

        for sample in data:
            pred = self.model.predict(sample["composition"])
            actual = sample["rating"]

            predictions.append(pred)
            actuals.append(actual)

        # R² score
        predictions = np.array(predictions)
        actuals = np.array(actuals)

        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)

        if ss_tot == 0:
            return 0.0

        r2 = 1 - (ss_res / ss_tot)

        return float(r2)

    def get_training_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé de l'entraînement.

        Returns:
            Summary dict
        """
        if not self.metrics_history:
            return {"status": "no_training", "n_trainings": 0}

        latest = self.metrics_history[-1]

        # Calculer amélioration totale
        if len(self.metrics_history) > 1:
            first_score = self.metrics_history[0].get("score_after", 0)
            latest_score = latest.get("score_after", 0)
            total_improvement = latest_score - first_score
        else:
            total_improvement = 0

        return {
            "status": "trained",
            "n_trainings": len(self.metrics_history),
            "latest_training": latest,
            "total_improvement": total_improvement,
            "model_metadata": self.model.metadata,
        }


# Singleton instance
_ai_trainer: Optional[AITrainer] = None


def get_ai_trainer() -> AITrainer:
    """
    Récupère ou crée l'instance singleton du trainer.

    Returns:
        AITrainer instance
    """
    global _ai_trainer

    if _ai_trainer is None:
        _ai_trainer = AITrainer()

    return _ai_trainer
