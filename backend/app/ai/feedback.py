"""
Feedback Handler v4.1.0 - User Feedback Processing

Gère la collecte et le traitement des feedbacks utilisateurs.
Transforme les interactions en données d'entraînement pour le ML.

Feedback Types:
    - Explicit: User rating (1-10)
    - Implicit: Build clicked, composition selected
    - Negative: Build rejected, composition dismissed

Storage:
    - JSON files in /data/feedback/
    - Aggregated for training
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from app.core.logging import logger
from app.core.config import settings


class FeedbackType(str, Enum):
    """Types de feedback"""

    EXPLICIT_RATING = "explicit_rating"  # User rated composition
    BUILD_CLICKED = "build_clicked"  # User clicked on build detail
    COMPOSITION_SELECTED = "composition_selected"  # User selected composition
    BUILD_REJECTED = "build_rejected"  # User removed a build
    COMPOSITION_DISMISSED = "composition_dismissed"  # User closed without action


class FeedbackHandler:
    """
    Gestionnaire de feedbacks utilisateurs.

    Responsibilities:
        - Collect user interactions
        - Normalize feedback to training data
        - Store feedback persistently
        - Aggregate for ML training

    Example:
        ```python
        handler = FeedbackHandler()

        # Explicit rating
        handler.record_feedback(
            composition_id="uuid-123",
            user_id="user-456",
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=8.5,
            comments="Great composition!"
        )

        # Get training data
        training_data = handler.get_training_data(min_rating=6.0)
        ```
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialise le handler.

        Args:
            storage_dir: Dossier de stockage des feedbacks
        """
        self.storage_dir = storage_dir or str(Path(settings.LEARNING_DATA_DIR) / "feedback")

        # Créer dossier si nécessaire
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)

        logger.info("FeedbackHandler initialized", extra={"storage_dir": self.storage_dir})

    def record_feedback(
        self,
        composition_id: str,
        user_id: str,
        feedback_type: FeedbackType,
        rating: Optional[float] = None,
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Enregistre un feedback utilisateur.

        Args:
            composition_id: ID de la composition
            user_id: ID de l'utilisateur
            feedback_type: Type de feedback
            rating: Note (1-10) pour explicit rating
            comments: Commentaires optionnels
            metadata: Métadonnées additionnelles

        Returns:
            Feedback ID
        """
        feedback_id = str(uuid.uuid4())

        feedback = {
            "id": feedback_id,
            "composition_id": composition_id,
            "user_id": user_id,
            "type": feedback_type.value,
            "rating": rating,
            "comments": comments,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Sauvegarder
        feedback_path = Path(self.storage_dir) / f"{feedback_id}.json"
        with open(feedback_path, "w") as f:
            json.dump(feedback, f, indent=2)

        logger.info(
            "Feedback recorded", extra={"feedback_id": feedback_id, "type": feedback_type.value, "rating": rating}
        )

        return feedback_id

    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un feedback par ID.

        Args:
            feedback_id: ID du feedback

        Returns:
            Feedback data ou None
        """
        feedback_path = Path(self.storage_dir) / f"{feedback_id}.json"

        if not feedback_path.exists():
            return None

        with open(feedback_path, "r") as f:
            return json.load(f)

    def get_all_feedbacks(
        self,
        user_id: Optional[str] = None,
        composition_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        min_rating: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère tous les feedbacks avec filtres optionnels.

        Args:
            user_id: Filtrer par utilisateur
            composition_id: Filtrer par composition
            feedback_type: Filtrer par type
            min_rating: Note minimale

        Returns:
            Liste de feedbacks
        """
        feedbacks = []

        for feedback_file in Path(self.storage_dir).glob("*.json"):
            with open(feedback_file, "r") as f:
                feedback = json.load(f)

            # Filtres
            if user_id and feedback.get("user_id") != user_id:
                continue

            if composition_id and feedback.get("composition_id") != composition_id:
                continue

            if feedback_type and feedback.get("type") != feedback_type.value:
                continue

            if min_rating and (feedback.get("rating") or 0) < min_rating:
                continue

            feedbacks.append(feedback)

        return feedbacks

    def normalize_to_rating(self, feedback: Dict[str, Any]) -> float:
        """
        Normalise un feedback en rating (0-10).

        Args:
            feedback: Feedback data

        Returns:
            Normalized rating
        """
        feedback_type = feedback.get("type")

        # Explicit rating
        if feedback_type == FeedbackType.EXPLICIT_RATING.value:
            return feedback.get("rating", 5.0)

        # Implicit positive
        if feedback_type == FeedbackType.BUILD_CLICKED.value:
            return 7.0  # Clicked = interested

        if feedback_type == FeedbackType.COMPOSITION_SELECTED.value:
            return 9.0  # Selected = very satisfied

        # Implicit negative
        if feedback_type == FeedbackType.BUILD_REJECTED.value:
            return 3.0  # Rejected = not good

        if feedback_type == FeedbackType.COMPOSITION_DISMISSED.value:
            return 4.0  # Dismissed = not interested

        # Default
        return 5.0

    def get_training_data(self, min_rating: float = 5.0, max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère les données d'entraînement.

        Args:
            min_rating: Note minimale pour inclure
            max_samples: Nombre max d'échantillons

        Returns:
            Training data [{"composition": {...}, "rating": 8.5}, ...]
        """
        # Charger compositions générées
        compositions_dir = Path(settings.LEARNING_DATA_DIR) / "generated"
        compositions_dir.mkdir(parents=True, exist_ok=True)

        # Charger feedbacks
        feedbacks = self.get_all_feedbacks()

        # Mapper composition_id → rating
        composition_ratings: Dict[str, List[float]] = {}

        for feedback in feedbacks:
            comp_id = feedback.get("composition_id")
            rating = self.normalize_to_rating(feedback)

            if comp_id not in composition_ratings:
                composition_ratings[comp_id] = []

            composition_ratings[comp_id].append(rating)

        # Créer training data
        training_data = []

        for comp_file in compositions_dir.glob("*.json"):
            with open(comp_file, "r") as f:
                composition = json.load(f)

            comp_id = composition.get("id")

            # Calculer rating moyen
            if comp_id in composition_ratings:
                ratings = composition_ratings[comp_id]
                avg_rating = sum(ratings) / len(ratings)
            else:
                # Pas de feedback = rating par défaut
                avg_rating = 5.0

            # Filtrer par min_rating
            if avg_rating < min_rating:
                continue

            training_data.append(
                {
                    "composition": composition,
                    "rating": avg_rating,
                    "n_feedbacks": len(composition_ratings.get(comp_id, [])),
                }
            )

        # Limiter nombre d'échantillons
        if max_samples and len(training_data) > max_samples:
            # Trier par rating décroissant
            training_data.sort(key=lambda x: x["rating"], reverse=True)
            training_data = training_data[:max_samples]

        logger.info("Training data prepared", extra={"n_samples": len(training_data), "min_rating": min_rating})

        return training_data

    def save_composition(self, composition: Dict[str, Any]) -> str:
        """
        Sauvegarde une composition générée.

        Args:
            composition: Composition data

        Returns:
            Composition ID
        """
        compositions_dir = Path(settings.LEARNING_DATA_DIR) / "generated"
        compositions_dir.mkdir(parents=True, exist_ok=True)

        comp_id = composition.get("id", str(uuid.uuid4()))
        composition["id"] = comp_id

        comp_path = compositions_dir / f"{comp_id}.json"
        with open(comp_path, "w") as f:
            json.dump(composition, f, indent=2)

        logger.info("Composition saved", extra={"composition_id": comp_id})

        return comp_id

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les feedbacks.

        Returns:
            Statistics dict
        """
        feedbacks = self.get_all_feedbacks()

        if not feedbacks:
            return {"total_feedbacks": 0, "avg_rating": 0.0, "by_type": {}}

        # Compter par type
        by_type = {}
        ratings = []

        for feedback in feedbacks:
            fb_type = feedback.get("type")
            by_type[fb_type] = by_type.get(fb_type, 0) + 1

            rating = self.normalize_to_rating(feedback)
            ratings.append(rating)

        return {
            "total_feedbacks": len(feedbacks),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "by_type": by_type,
            "min_rating": min(ratings) if ratings else 0.0,
            "max_rating": max(ratings) if ratings else 0.0,
        }


# Singleton instance
_feedback_handler: Optional[FeedbackHandler] = None


def get_feedback_handler() -> FeedbackHandler:
    """
    Récupère ou crée l'instance singleton du handler.

    Returns:
        FeedbackHandler instance
    """
    global _feedback_handler

    if _feedback_handler is None:
        _feedback_handler = FeedbackHandler()

    return _feedback_handler
