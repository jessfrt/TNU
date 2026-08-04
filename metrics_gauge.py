import csv, json, math
from pathlib import Path

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

def scalar(vals, mode="first"):
    if not vals: return 0.0
    if mode == "mean":
        return sum(vals)/len(vals)
    if mode == "l2":
        return math.sqrt(sum(v*v for v in vals))
    if mode == "weighted":
        c0, c1, c2 = vals[:3]
        return 0.5*c0 + 0.4*c1 + 0.1*c2  # pesos mais semânticos
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

def compute_metrics(csv_in: str, out_dir: str = "out", mode="first", norm="none"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(csv_in, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    lang_mu = compute_means(rows, "lang") if norm in ("lang","lang+concept") else {}
    concept_mu = compute_means(rows, "concept") if norm in ("concept","lang+concept") else {}

    # agrupa por conceito e extrai escalares
    series = {}
    for r in rows:
        c = r["concept"].strip()
        trip = parse_code_o(r.get("codeO",""))
        if norm in ("lang","lang+concept"):
            trip = sub(trip, lang_mu.get(r["lang"].strip(), [0.0,0.0,0.0]))
        if norm in ("concept","lang+concept"):
            trip = sub(trip, concept_mu.get(c, [0.0,0.0,0.0]))
        v = scalar(trip, mode=mode)
        series.setdefault(c, []).append(v)

    # métricas por conceito
    per_concept = {}
    for c, xs in series.items():
        xs = sorted(xs)
        amp = (max(xs) - min(xs)) if xs else 0.0
        center = sum(xs)/len(xs) if xs else 0.0
        per_concept[c] = {"amplitude_intra": amp, "center": center, "n": len(xs)}

    # distâncias inter
    centers = [(c, m["center"]) for c, m in per_concept.items()]
    inter = []
    for i in range(len(centers)):
        for j in range(i+1, len(centers)):
            c1, v1 = centers[i]
            c2, v2 = centers[j]
            inter.append({"pair": f"{c1}↔{c2}", "dist": abs(v1 - v2)})

    mean_intra = sum(m["amplitude_intra"] for m in per_concept.values())/max(1, len(per_concept))
    mean_inter = sum(x["dist"] for x in inter)/max(1, len(inter))
    separability = (mean_inter / mean_intra) if mean_intra > 0 else float("inf")

    # salvar CSV/JSON com sufixo do modo/norm
    suf = f"{mode}_{norm}"
    metrics_csv = Path(out_dir) / f"gauge_metrics_{suf}.csv"
    with metrics_csv.open("w", newline="", encoding="utf-8") as g:
        g.write("concept,center,amplitude_intra,n\n")
        for c, m in per_concept.items():
            g.write(f"{c},{m['center']:.6f},{m['amplitude_intra']:.6f},{m['n']}\n")
        g.write("\nconcept_pair,dist\n")
        for x in inter:
            g.write(f"{x['pair']},{x['dist']:.6f}\n")
        g.write("\nsummary,mean_intra,mean_inter,separability\n")
        g.write(f"all,{mean_intra:.6f},{mean_inter:.6f},{separability:.6f}\n")

    metrics_json = Path(out_dir) / f"gauge_metrics_{suf}.json"
    metrics_json.write_text(
        json.dumps({
            "per_concept": per_concept,
            "inter_pairs": inter,
            "summary": {
                "mean_intra": mean_intra,
                "mean_inter": mean_inter,
                "separability": separability
            },
            "mode": mode,
            "norm": norm
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[ok] métricas salvas:\n- {metrics_csv}\n- {metrics_json}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Métricas da régua semântica")
    ap.add_argument("--inp", required=True, help="CSV de entrada (concept,lang,word,codeO)")
    ap.add_argument("--outdir", default="out", help="Pasta de saída (default: out)")
    ap.add_argument("--mode", choices=["first","mean","l2","weighted"], default="first")
    ap.add_argument("--norm", choices=["none","lang","concept","lang+concept"], default="none")
    args = ap.parse_args()
    compute_metrics(args.inp, args.outdir, mode=args.mode, norm=args.norm)

