import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(ROOT / ".env")

from includes.fonctions.requetellm import requetGrok405B
from includes.objets.DocumentClasse import Document
from includes.objets.QuestionClasse import Question

DEFAULT_DATASET = ROOT / "src" / "data" / "gold_dataset_llmethique.json"
DEFAULT_OUTPUT_DIR = ROOT / "src" / "data" / "evaluation"


def _response_label(value) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "null"


def parse_llm_json(raw_response: str) -> dict:
    default = {
        "Reponse": None,
        "Justification": "Aucun JSON detecte dans la reponse du modele.",
        "Recommandation": "",
        "Source": "",
    }
    if not raw_response:
        return default

    text = str(raw_response).replace("\ufeff", "").strip()
    text = text.replace("```json", "").replace("```", "")
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return default

    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return default

    if not isinstance(data, dict):
        return default

    data.setdefault("Reponse", None)
    data.setdefault("Justification", "")
    data.setdefault("Recommandation", "")
    data.setdefault("Source", "")
    return data


def build_documents(case_documents: dict[str, str]) -> list[Document]:
    documents = []
    for name, content in case_documents.items():
        doc = Document(name)
        doc.SetChemin([f"{name.lower()}_gold.txt"])
        doc.SetTexte([content])
        documents.append(doc)
    return documents


def run_case(case: dict) -> dict:
    documents = build_documents(case["documents"])
    question = Question(case["question"], documents)
    raw_response = requetGrok405B(question.PromptGen())
    parsed_response = parse_llm_json(raw_response)
    predicted_error = parsed_response.get("Reponse") is False

    return {
        "id": case["id"],
        "theme": case["theme"],
        "question": case["question"],
        "expected_reponse": case["expected"]["reponse"],
        "predicted_reponse": parsed_response.get("Reponse"),
        "expected_error_detected": case["expected"]["error_detected"],
        "predicted_error_detected": predicted_error,
        "source_expected": case["expected"]["source"],
        "source_predicted": parsed_response.get("Source", ""),
        "manual_validation_note": case["expected"]["manual_validation_note"],
        "llm_response": parsed_response,
    }


def compute_metrics(results: list[dict]) -> dict:
    tp = sum(1 for row in results if row["expected_error_detected"] and row["predicted_error_detected"])
    fp = sum(1 for row in results if not row["expected_error_detected"] and row["predicted_error_detected"])
    fn = sum(1 for row in results if row["expected_error_detected"] and not row["predicted_error_detected"])
    tn = sum(1 for row in results if not row["expected_error_detected"] and not row["predicted_error_detected"])

    exact_match = sum(1 for row in results if row["expected_reponse"] == row["predicted_reponse"])
    total = len(results)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    accuracy = (tp + tn) / total if total else 0.0
    exact_match_rate = exact_match / total if total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "dataset_size": total,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision_error_detection": round(precision, 4),
        "recall_error_detection": round(recall, 4),
        "f1_error_detection": round(f1, 4),
        "accuracy_error_detection": round(accuracy, 4),
        "exact_match_rate_reponse": round(exact_match_rate, 4),
    }


def compute_metrics_by_theme(results: list[dict]) -> dict:
    grouped_results: dict[str, list[dict]] = {}
    for row in results:
        grouped_results.setdefault(row["theme"], []).append(row)

    return {
        theme: compute_metrics(theme_results)
        for theme, theme_results in sorted(grouped_results.items())
    }


def collect_response_breakdown(results: list[dict]) -> dict:
    expected_counts = {"true": 0, "false": 0, "null": 0}
    predicted_counts = {"true": 0, "false": 0, "null": 0}

    for row in results:
        expected_counts[_response_label(row["expected_reponse"])] += 1
        predicted_counts[_response_label(row["predicted_reponse"])] += 1

    return {
        "expected_reponse_distribution": expected_counts,
        "predicted_reponse_distribution": predicted_counts,
    }


def collect_mismatch_summary(results: list[dict]) -> dict:
    exact_mismatches = [
        {
            "id": row["id"],
            "theme": row["theme"],
            "expected_reponse": row["expected_reponse"],
            "predicted_reponse": row["predicted_reponse"],
            "expected_error_detected": row["expected_error_detected"],
            "predicted_error_detected": row["predicted_error_detected"],
        }
        for row in results
        if row["expected_reponse"] != row["predicted_reponse"]
    ]

    return {
        "exact_reponse_mismatches": exact_mismatches,
        "predicted_null_when_expected_non_null": [
            row for row in exact_mismatches if row["predicted_reponse"] is None and row["expected_reponse"] is not None
        ],
        "predicted_non_null_when_expected_null": [
            row for row in exact_mismatches if row["predicted_reponse"] is not None and row["expected_reponse"] is None
        ],
        "false_positive_error_cases": [
            {
                "id": row["id"],
                "theme": row["theme"],
                "expected_reponse": row["expected_reponse"],
                "predicted_reponse": row["predicted_reponse"],
            }
            for row in results
            if not row["expected_error_detected"] and row["predicted_error_detected"]
        ],
        "false_negative_error_cases": [
            {
                "id": row["id"],
                "theme": row["theme"],
                "expected_reponse": row["expected_reponse"],
                "predicted_reponse": row["predicted_reponse"],
            }
            for row in results
            if row["expected_error_detected"] and not row["predicted_error_detected"]
        ],
    }


def save_report(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"gold_eval_{timestamp}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Execute le benchmark sur le gold dataset et calcule precision/rappel."
    )
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET),
        help="Chemin du gold dataset JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Dossier de sortie pour le rapport JSON.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)

    with dataset_path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    results = [run_case(case) for case in dataset]
    metrics = compute_metrics(results)
    metrics_by_theme = compute_metrics_by_theme(results)
    response_breakdown = collect_response_breakdown(results)
    mismatch_summary = collect_mismatch_summary(results)

    report = {
        "generated_at": datetime.now().isoformat(),
        "dataset_path": str(dataset_path),
        "metrics": metrics,
        "metrics_by_theme": metrics_by_theme,
        "response_breakdown": response_breakdown,
        "mismatch_summary": mismatch_summary,
        "results": results,
    }
    output_path = save_report(report, output_dir)

    print("Evaluation terminee.")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Rapport ecrit dans: {output_path}")


if __name__ == "__main__":
    main()
