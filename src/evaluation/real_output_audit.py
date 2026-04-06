import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT / "src" / "data" / "jsonProf"
DEFAULT_OUTPUT_DIR = ROOT / "src" / "data" / "evaluation"

VALID_DOC_TOKENS = {
    "F1",
    "FIC",
    "outilsRecrutement",
    "financement",
    "rechercheMilieu",
    "questionnaires",
    "guideEntrevue",
    "guideDiscussions",
    "guideObservation",
    "instrumentsMesure",
    "autorisationDonneesSecondaires",
    "descriptionCollecte",
    "preuveCGRB",
}


def list_candidate_files(input_dir: Path, limit: int) -> list[Path]:
    candidates = [
        path
        for path in input_dir.glob("*.json")
        if not path.name.startswith("thumbs_votes_") and not path.name.startswith("feedback_")
    ]
    return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(value) -> str:
    return str(value or "").strip()


def is_valid_reponse(value) -> bool:
    return value in (True, False, None)


def count_words(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def source_mentions_known_doc(source: str) -> bool:
    lowered = source.lower()
    return any(token.lower() in lowered for token in VALID_DOC_TOKENS)


def evaluate_entry(entry: dict) -> dict:
    response = entry.get("reponse", {}) or {}
    reponse_value = response.get("Reponse")
    justification = normalize_text(response.get("Justification"))
    recommendation = normalize_text(response.get("Recommandation"))
    source = normalize_text(response.get("Source"))

    checks = {
        "reponse_valid": is_valid_reponse(reponse_value),
        "source_present": bool(source),
        "source_mentions_known_doc_type": source_mentions_known_doc(source),
        "justification_present": bool(justification),
        "justification_min_words": count_words(justification) >= 8,
        "recommendation_rule_ok": True,
    }

    if reponse_value is False:
        checks["recommendation_rule_ok"] = count_words(recommendation) >= 15 and recommendation.lower() != "aucune"
    elif reponse_value in (True, None):
        checks["recommendation_rule_ok"] = recommendation == ""

    failed_checks = [name for name, passed in checks.items() if not passed]

    return {
        "question": entry.get("question", ""),
        "reponse": reponse_value,
        "source": source,
        "justification_word_count": count_words(justification),
        "recommendation_word_count": count_words(recommendation),
        "checks": checks,
        "failed_checks": failed_checks,
    }


def summarize_file(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{path} ne contient pas une liste de réponses.")

    entries = [evaluate_entry(entry) for entry in payload]
    counts = Counter()
    for entry in entries:
        for failed_check in entry["failed_checks"]:
            counts[failed_check] += 1

    fully_valid = sum(1 for entry in entries if not entry["failed_checks"])

    return {
        "file": str(path),
        "total_entries": len(entries),
        "fully_valid_entries": fully_valid,
        "entries_with_issues": len(entries) - fully_valid,
        "failed_check_counts": dict(counts),
        "entries": entries,
    }


def build_report(files: list[Path]) -> dict:
    file_reports = [summarize_file(path) for path in files]
    aggregate = Counter()
    total_entries = 0
    fully_valid_entries = 0

    for report in file_reports:
        total_entries += report["total_entries"]
        fully_valid_entries += report["fully_valid_entries"]
        for check_name, count in report["failed_check_counts"].items():
            aggregate[check_name] += count

    return {
        "generated_at": datetime.now().isoformat(),
        "audited_files": [str(path) for path in files],
        "summary": {
            "file_count": len(file_reports),
            "total_entries": total_entries,
            "fully_valid_entries": fully_valid_entries,
            "entries_with_issues": total_entries - fully_valid_entries,
            "failed_check_counts": dict(aggregate),
        },
        "files": file_reports,
    }


def save_report(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"real_output_audit_{timestamp}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Audite un corpus réel de sorties JSON pour vérifier la qualité minimale des champs explicatifs."
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help="Dossier contenant les sorties JSON réelles.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Nombre maximal de fichiers récents à auditer.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Dossier de sortie pour le rapport d'audit.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    files = list_candidate_files(input_dir, args.limit)
    report = build_report(files)
    output_path = save_report(report, output_dir)

    print("Audit termine.")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Rapport ecrit dans: {output_path}")


if __name__ == "__main__":
    main()
