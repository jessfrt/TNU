# plot_gauge.py  (somente as 4 primeiras linhas mudam)
import csv, math
from pathlib import Path
import matplotlib.pyplot as plt

EN_DASH = "–"

def parse_code_o(code_o: str):
    code_o = (code_o or "").strip()
    parts = code_o.split(EN_DASH) if EN_DASH in code_o else code_o.split("-")
    vals = []
    for p in parts:
        p = p.strip()
        if not p: continue
        try:
            vals.append(float(p))
        except:
            pass
    while len(vals) < 3:
        vals.append(0.0)
    return vals[:3]

def scalar_from_triplet(vals, mode="first"):
    if not vals: return 0.0
    if mode == "mean":
        return sum(vals)/len(vals)
    if mode == "l2":
        return math.sqrt(sum(v*v for v in vals))
    if mode == "weighted":
        c0, c1, c2 = vals[:3]
        return 0.5*c0 + 0.4*c1 + 0.1*c2
    return vals[0]

def compute_means(rows, key):
    acc = {}
    for r in rows:
        k = r[key].strip()
        v = parse_code_o(r.get("codeO",""))
        if k not in acc:
            acc[k] = {"sum":[0.0,0.0,0.0], "n":0}
        for i in range(3):
            acc[k]["sum"][i] += v[i]
        acc[k]["n"] += 1
    means = {}
    for k, st in acc.items():
        n = max(1, st["n"])
        means[k] = [st["sum"][i]/n for i in range(3)]
    return means

def sub(a,b): return [a[i]-b[i] for i in range(3)]

def plot_gauge(csv_in: str, out_dir: str = "out", mode="first", norm="none"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    rows = []
    with open(csv_in, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    lang_mu = compute_means(rows, "lang") if norm in ("lang","lang+concept") else {}
    concept_mu = compute_means(rows, "concept") if norm in ("concept","lang+concept") else {}

    # agrupa por conceito
    by_concept = {}
    for r in rows:
        c = r["concept"].strip()
        by_concept.setdefault(c, []).append(r)

    for concept, items in by_concept.items():
        points = []
        for r in items:
            trip = parse_code_o(r.get("codeO",""))
            if norm in ("lang","lang+concept"):
                trip = sub(trip, lang_mu.get(r["lang"].strip(), [0.0,0.0,0.0]))
            if norm in ("concept","lang+concept"):
                trip = sub(trip, concept_mu.get(concept, [0.0,0.0,0.0]))
            x = scalar_from_triplet(trip, mode=mode)
            label = f"{r['lang'].strip()}:{r['word'].strip()}"
            points.append((x, label))

        points.sort(key=lambda t: t[0])
        xs = [p[0] for p in points]
        labels = [p[1] for p in points]
        ys = [0]*len(points)

        plt.figure(figsize=(9, 2.2))
        plt.plot(xs, ys, "o", markersize=6)
        for x, y, lbl in zip(xs, ys, labels):
            plt.text(x, y+0.02, lbl, rotation=45, ha="left", va="bottom", fontsize=8)

        plt.yticks([])
        plt.xlabel(f"code-O ({mode})  norm={norm}")
        plt.title(f"Régua semântica — conceito: {concept}")
        plt.grid(axis="x", linestyle=":", linewidth=0.7)

        out_path = Path(out_dir) / f"gauge_{concept}_{mode}_{norm}.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=160)
        plt.close()
        print(f"[ok] gráfico salvo: {out_path}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Plot da régua semântica por conceito")
    ap.add_argument("--inp", required=True, help="CSV de entrada (concept,lang,word,codeO)")
    ap.add_argument("--outdir", default="out", help="Pasta de saída (default: out)")
    ap.add_argument("--mode", choices=["first","mean","l2","weighted"], default="first")
    ap.add_argument("--norm", choices=["none","lang","concept","lang+concept"], default="none")
    args = ap.parse_args()
    plot_gauge(args.inp, args.outdir, mode=args.mode, norm=args.norm)
