# scripts/test_harness.py
import json, argparse, csv
from sisimpur.processor import DocumentProcessor

def load_ground_truth(gt_path):
    with open(gt_path, 'r', encoding='utf-8') as f:
        return json.load(f)['questions']

def compare(gt, pred):
    # simple precision: fraction of GT questions found exactly in pred
    gt_set = set(q['question'] for q in gt)
    pred_set = set(q['question'] for q in pred)
    true_pos = len(gt_set & pred_set)
    return true_pos / max(1, len(gt_set))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("doc_gt_pairs", nargs="+",
                   help="Pairs: doc1.pdf gt1.json doc2.pdf gt2.json …")
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--out", default="harness_results.csv")
    args = p.parse_args()

    results = []
    dp = DocumentProcessor()
    for i in range(args.runs):
        for doc, gt in zip(args.doc_gt_pairs[::2], args.doc_gt_pairs[1::2]):
            output = dp.process(doc)
            with open(output, 'r', encoding='utf-8') as f:
                pred = json.load(f)['questions']
            gt_questions = load_ground_truth(gt)
            score = compare(gt_questions, pred)
            results.append({'run': i+1, 'doc': doc, 'score': score})

    with open(args.out, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['run','doc','score'])
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved results to {args.out}")
