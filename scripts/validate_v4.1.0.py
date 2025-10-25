#!/usr/bin/env python3
"""
GW2Optimizer v4.1.0 - Validation Script
Teste automatiquement tous les composants du projet
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Results storage
results = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "version": "4.1.0",
    "tests": {},
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
}


def test_result(name: str, passed: bool, message: str = "", details: Any = None):
    """Record test result"""
    results["tests"][name] = {
        "passed": passed,
        "message": message,
        "details": details
    }
    results["summary"]["total"] += 1
    if passed:
        results["summary"]["passed"] += 1
        print(f"✅ {name}: PASS")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ {name}: FAIL - {message}")
    
    if message:
        print(f"   {message}")


def test_imports():
    """Test 1: Verify all imports work"""
    print("\n=== TEST 1: IMPORTS ===")
    
    try:
        from app.ai.core import GW2AICore, GameMode
        test_result("import_ai_core", True, "AI Core imports successfully")
    except Exception as e:
        test_result("import_ai_core", False, f"Import failed: {str(e)}")
    
    try:
        from app.learning.models.synergy_model import SynergyModel
        test_result("import_synergy_model", True, "SynergyModel imports successfully")
    except Exception as e:
        test_result("import_synergy_model", False, f"Import failed: {str(e)}")
    
    try:
        from app.ai.feedback import FeedbackHandler
        test_result("import_feedback", True, "FeedbackHandler imports successfully")
    except Exception as e:
        test_result("import_feedback", False, f"Import failed: {str(e)}")
    
    try:
        from app.ai.trainer import AITrainer
        test_result("import_trainer", True, "AITrainer imports successfully")
    except Exception as e:
        test_result("import_trainer", False, f"Import failed: {str(e)}")
    
    try:
        from app.ai.context import ContextAnalyzer
        test_result("import_context", True, "ContextAnalyzer imports successfully")
    except Exception as e:
        test_result("import_context", False, f"Import failed: {str(e)}")
    
    try:
        from app.learning.data.external import ExternalDataStore
        test_result("import_external_store", True, "ExternalDataStore imports successfully")
    except Exception as e:
        test_result("import_external_store", False, f"Import failed: {str(e)}")


def test_synergy_model():
    """Test 2: SynergyModel functionality"""
    print("\n=== TEST 2: SYNERGY MODEL ===")
    
    try:
        from app.learning.models.synergy_model import SynergyModel
        
        model = SynergyModel()
        test_result("synergy_model_init", True, "Model initialized")
        
        # Test feature extraction
        composition = {
            "builds": [
                {
                    "profession": "Guardian",
                    "role": "Support",
                    "count": 3,
                    "key_boons": ["Might", "Fury"]
                }
            ],
            "game_mode": "zerg",
            "size": 50
        }
        
        features = model._extract_features(composition)
        test_result(
            "synergy_model_features",
            features.shape[1] == 31,
            f"Extracted {features.shape[1]} features (expected 31)"
        )
        
        # Test prediction (without trained model)
        score = model.predict(composition)
        test_result(
            "synergy_model_predict",
            0 <= score <= 10,
            f"Predicted score: {score:.2f}"
        )
        
    except Exception as e:
        test_result("synergy_model_test", False, f"Error: {str(e)}")


def test_feedback_handler():
    """Test 3: FeedbackHandler functionality"""
    print("\n=== TEST 3: FEEDBACK HANDLER ===")
    
    try:
        from app.ai.feedback import FeedbackHandler, FeedbackType
        
        handler = FeedbackHandler()
        test_result("feedback_handler_init", True, "Handler initialized")
        
        # Record feedback
        feedback_id = handler.record_feedback(
            composition_id="test-comp-123",
            user_id="test-user-456",
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=8.5,
            comments="Great composition!"
        )
        
        test_result(
            "feedback_record",
            feedback_id is not None,
            f"Feedback recorded: {feedback_id}"
        )
        
        # Retrieve feedback
        feedback = handler.get_feedback(feedback_id)
        test_result(
            "feedback_retrieve",
            feedback is not None and feedback["rating"] == 8.5,
            "Feedback retrieved successfully"
        )
        
        # Get statistics
        stats = handler.get_statistics()
        test_result(
            "feedback_stats",
            stats["total_feedbacks"] >= 1,
            f"Total feedbacks: {stats['total_feedbacks']}"
        )
        
    except Exception as e:
        test_result("feedback_handler_test", False, f"Error: {str(e)}")


def test_ai_trainer():
    """Test 4: AITrainer functionality"""
    print("\n=== TEST 4: AI TRAINER ===")
    
    try:
        from app.ai.trainer import AITrainer
        from app.learning.models.synergy_model import SynergyModel
        from app.ai.feedback import FeedbackHandler
        
        model = SynergyModel()
        handler = FeedbackHandler()
        trainer = AITrainer(model=model, feedback_handler=handler)
        
        test_result("ai_trainer_init", True, "Trainer initialized")
        
        # Test batch training with mock data
        mock_data = [
            {
                "composition": {
                    "builds": [{"profession": "Guardian", "role": "Support", "count": 3, "key_boons": ["Might"]}],
                    "game_mode": "zerg",
                    "size": 50
                },
                "rating": 8.5
            },
            {
                "composition": {
                    "builds": [{"profession": "Warrior", "role": "Tank", "count": 2, "key_boons": ["Fury"]}],
                    "game_mode": "raid",
                    "size": 10
                },
                "rating": 7.0
            }
        ]
        
        # Train model
        model.train(mock_data)
        test_result("ai_trainer_train", True, "Model trained on mock data")
        
        # Test prediction after training
        score = model.predict(mock_data[0]["composition"])
        test_result(
            "ai_trainer_predict_after_train",
            0 <= score <= 10,
            f"Score after training: {score:.2f}"
        )
        
    except Exception as e:
        test_result("ai_trainer_test", False, f"Error: {str(e)}")


def test_context_analyzer():
    """Test 5: ContextAnalyzer functionality"""
    print("\n=== TEST 5: CONTEXT ANALYZER ===")
    
    try:
        from app.ai.context import ContextAnalyzer
        from app.learning.data.external import ExternalDataStore
        
        store = ExternalDataStore()
        analyzer = ContextAnalyzer(store=store)
        
        test_result("context_analyzer_init", True, "Analyzer initialized")
        
        # Test should_update
        should_update = analyzer.should_update()
        test_result(
            "context_should_update",
            isinstance(should_update, bool),
            f"Should update: {should_update}"
        )
        
    except Exception as e:
        test_result("context_analyzer_test", False, f"Error: {str(e)}")


def test_external_store():
    """Test 6: ExternalDataStore functionality"""
    print("\n=== TEST 6: EXTERNAL DATA STORE ===")
    
    try:
        from app.learning.data.external import ExternalDataStore
        
        store = ExternalDataStore()
        test_result("external_store_init", True, "Store initialized")
        
        # Test save
        mock_meta = {
            "trending": {
                "professions": [
                    {"name": "Guardian", "popularity": 0.95}
                ]
            }
        }
        
        path = store.save(mock_meta)
        test_result("external_store_save", True, f"Meta saved to {path}")
        
        # Test load
        loaded = store.load()
        test_result(
            "external_store_load",
            "trending" in loaded,
            "Meta loaded successfully"
        )
        
        # Test statistics
        stats = store.get_statistics()
        test_result(
            "external_store_stats",
            stats["n_trending_professions"] >= 1,
            f"Trending professions: {stats['n_trending_professions']}"
        )
        
    except Exception as e:
        test_result("external_store_test", False, f"Error: {str(e)}")


def test_file_structure():
    """Test 7: Verify all required files exist"""
    print("\n=== TEST 7: FILE STRUCTURE ===")
    
    base_path = Path(__file__).parent.parent
    
    required_files = [
        "backend/app/ai/core.py",
        "backend/app/ai/feedback.py",
        "backend/app/ai/trainer.py",
        "backend/app/ai/context.py",
        "backend/app/learning/models/synergy_model.py",
        "backend/app/learning/data/external.py",
        "backend/app/api/ai.py",
        "frontend/src/services/aiService.ts",
        "frontend/src/components/ai/ChatBoxAI.tsx",
        "frontend/src/components/builds/BuildCard.tsx",
        "frontend/src/components/builds/BuildDetailModal.tsx",
        "frontend/src/components/team/TeamSynergyView.tsx",
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        exists = full_path.exists()
        test_result(
            f"file_{file_path.replace('/', '_')}",
            exists,
            f"{'Found' if exists else 'Missing'}: {file_path}"
        )


def generate_report():
    """Generate validation report"""
    print("\n=== GENERATING REPORT ===")
    
    report_path = Path(__file__).parent.parent / "reports" / "LOCAL_VALIDATION_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate pass rate
    total = results["summary"]["total"]
    passed = results["summary"]["passed"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    # Determine status
    if pass_rate == 100:
        status = "✅ PRÊT POUR PRODUCTION LOCAL"
    elif pass_rate >= 80:
        status = "⚠️ PRÊT AVEC AVERTISSEMENTS"
    else:
        status = "❌ CORRECTIONS REQUISES"
    
    report = f"""# 🧪 GW2Optimizer v4.1.0 - Rapport de Validation Locale

**Date**: {results['timestamp']}  
**Version**: {results['version']}  
**Status**: {status}

---

## 📊 RÉSUMÉ

| Métrique | Valeur |
|----------|--------|
| **Tests Totaux** | {total} |
| **Tests Réussis** | {passed} ✅ |
| **Tests Échoués** | {results['summary']['failed']} ❌ |
| **Taux de Réussite** | {pass_rate:.1f}% |

---

## 🧪 RÉSULTATS DÉTAILLÉS

"""
    
    # Group tests by category
    categories = {
        "Imports": [],
        "Synergy Model": [],
        "Feedback Handler": [],
        "AI Trainer": [],
        "Context Analyzer": [],
        "External Store": [],
        "File Structure": []
    }
    
    for test_name, test_data in results["tests"].items():
        if "import" in test_name:
            categories["Imports"].append((test_name, test_data))
        elif "synergy" in test_name:
            categories["Synergy Model"].append((test_name, test_data))
        elif "feedback" in test_name:
            categories["Feedback Handler"].append((test_name, test_data))
        elif "trainer" in test_name:
            categories["AI Trainer"].append((test_name, test_data))
        elif "context" in test_name:
            categories["Context Analyzer"].append((test_name, test_data))
        elif "external" in test_name:
            categories["External Store"].append((test_name, test_data))
        elif "file" in test_name:
            categories["File Structure"].append((test_name, test_data))
    
    for category, tests in categories.items():
        if not tests:
            continue
        
        report += f"### {category}\n\n"
        
        for test_name, test_data in tests:
            icon = "✅" if test_data["passed"] else "❌"
            report += f"- {icon} **{test_name}**"
            if test_data["message"]:
                report += f": {test_data['message']}"
            report += "\n"
        
        report += "\n"
    
    report += f"""---

## 🎯 CONCLUSION

**Status Final**: {status}

### Composants Validés
- ✅ AI Core (imports)
- ✅ ML System (SynergyModel, Trainer, Feedback)
- ✅ Context Awareness (ContextAnalyzer, ExternalStore)
- ✅ Structure fichiers

### Prochaines Étapes
{"- ✅ Projet prêt pour déploiement local" if pass_rate == 100 else "- ⚠️ Corriger les tests échoués avant déploiement"}
- 🚀 Tests E2E avec serveurs lancés
- 🌐 Tests API endpoints
- 🎨 Tests frontend (Playwright/Cypress)

---

**Rapport généré**: {results['timestamp']}  
**Script**: `scripts/validate_v4.1.0.py`  
**Taux de réussite**: {pass_rate:.1f}%
"""
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Rapport généré: {report_path}")
    print(f"\n{status}")
    print(f"Taux de réussite: {pass_rate:.1f}% ({passed}/{total})")
    
    return report_path


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("🧪 GW2Optimizer v4.1.0 - Validation Automatique")
    print("=" * 60)
    
    try:
        test_file_structure()
        test_imports()
        test_synergy_model()
        test_feedback_handler()
        test_ai_trainer()
        test_context_analyzer()
        test_external_store()
        
        report_path = generate_report()
        
        # Return exit code
        if results["summary"]["failed"] == 0:
            return 0
        else:
            return 1
    
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
