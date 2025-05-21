import json
import argparse
import csv
import os
import statistics
import difflib

from sisimpur.processor import DocumentProcessor


def load_ground_truth(gt_path):
    with open(gt_path, "r", encoding="utf-8") as f:
        return json.load(f).get("questions", [])


def normalize(text):
    return " ".join(text.lower().strip().split())


def compare(gt, pred, threshold=0.7):
    gt_qs = [normalize(q["question"]) for q in gt]
    pred_qs = [normalize(q["question"]) for q in pred]

    matched = set()
    for i, g in enumerate(gt_qs):
        for p in pred_qs:
            if difflib.SequenceMatcher(None, g, p).ratio() >= threshold:
                matched.add(i)
                break

    unmatched_gt = [gt[i]["question"] for i in range(len(gt_qs)) if i not in matched]
    return len(matched) / max(1, len(gt_qs)), unmatched_gt


def main():
    parser = argparse.ArgumentParser(
        description="Run Sisimpur pipeline multiple times and evaluate"
    )
    parser.add_argument(
        "doc_gt_pairs", nargs="+", help="Pairs: document.pdf ground_truth.json"
    )
    parser.add_argument("--runs", "-r", type=int, default=1, help="Number of trials")
    parser.add_argument("--out", "-o", default="harness_results.csv", help="Output CSV")
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.7,
        help="Similarity threshold (0–1) for fuzzy matching",
    )
    args = parser.parse_args()

    dp = DocumentProcessor()
    all_results = []

    for run_idx in range(1, args.runs + 1):
        for pdf_path, gt_path in zip(args.doc_gt_pairs[::2], args.doc_gt_pairs[1::2]):
            name = os.path.basename(pdf_path)
            if not os.path.exists(pdf_path) or not os.path.exists(gt_path):
                print(f"[!] Missing file: {pdf_path} or {gt_path}, skipping.")
                continue

            output = dp.process(pdf_path)
            with open(output, "r", encoding="utf-8") as f:
                pred = json.load(f).get("questions", [])
            gt = load_ground_truth(gt_path)

            # compare
            score, unmatched_gt = compare(gt, pred, threshold=args.threshold)
            all_results.append({"run": run_idx, "doc": name, "accuracy": score})

            print(f"Run {run_idx} — {name}: {score:.2%}")
            if unmatched_gt:
                print("  Unmatched GT questions:")
                for q in unmatched_gt:
                    print("   -", q)
                print()

    with open(args.out, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=["run", "doc", "accuracy"])
        writer.writeheader()
        for row in all_results:
            writer.writerow(
                {
                    "run": row["run"],
                    "doc": row["doc"],
                    "accuracy": f"{row['accuracy']:.4f}",
                }
            )
    print(f"\nSaved detailed results to {args.out}")

    if all_results:
        scores = [r["accuracy"] for r in all_results]
        avg = statistics.mean(scores)
        mn = min(scores)
        mx = max(scores)
        print(f"\nSummary over {len(scores)} runs:")
        print(f"  • Average accuracy: {avg:.2%}")
        print(f"  • Min accuracy:     {mn:.2%}")
        print(f"  • Max accuracy:     {mx:.2%}")
    else:
        print("No runs executed.")


if __name__ == "__main__":
    main()
