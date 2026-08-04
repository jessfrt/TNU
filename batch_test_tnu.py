#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Executor em lote para comparar a busca legada e a busca híbrida do TNU.

Gera CSV, Markdown e gráficos em ``relatorios/``. O modo legado não possui
score/D na sua interface de linha de comando; por isso suas palavras são
registradas separadamente, sem inventar métricas numéricas.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "relatorios"
os.environ.setdefault("MPLCONFIGDIR", str(OUT_DIR / ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TESTS = [
    ("água", "pt", "en", 5, True), ("água", "pt", "en", 5, False), ("water", "en", "pt", 5, True),
    ("sea", "en", "pt", 5, True), ("rio", "pt", "en", 5, True),
    ("comida", "pt", "en", 5, True), ("comida", "pt", "en", 5, False), ("food", "en", "pt", 5, True), ("fruta", "pt", "en", 5, True),
    ("amor", "pt", "en", 5, True), ("amor", "pt", "en", 5, False), ("love", "en", "pt", 5, True), ("paixão", "pt", "en", 5, True),
    ("casa", "pt", "en", 5, True), ("casa", "pt", "en", 5, False), ("home", "en", "pt", 5, True),
    ("vida", "pt", "en", 5, True), ("vida", "pt", "en", 5, False), ("life", "en", "pt", 5, True), ("existência", "pt", "en", 5, True),
    ("luz", "pt", "en", 5, True), ("eau", "fr", "pt", 5, True), ("Wasser", "de", "en", 5, True), ("maison", "fr", "en", 5, True),
    ("carro", "pt", "en", 5, True), ("felicidade", "pt", "en", 5, True),
]

CONCEPTS = {
    "água": "AGUA", "water": "AGUA", "sea": "AGUA", "rio": "AGUA", "eau": "AGUA", "wasser": "AGUA",
    "comida": "COMIDA", "food": "COMIDA", "fruta": "COMIDA", "amor": "AMOR", "love": "AMOR", "paixão": "AMOR",
    "casa": "CASA", "home": "CASA", "maison": "CASA", "vida": "VIDA", "life": "VIDA", "existência": "VIDA",
}
HYBRID_LINE = re.compile(r"(?P<lang>\w+):(?P<word>\S+)\s+score=(?P<score>[\d.]+)\s+D=(?P<d>[\d.]+)\s+relation=(?P<relation>\S+)")


def concept(query: str) -> str:
    return CONCEPTS.get(query.casefold(), "OUTROS")


def parse_hybrid(output: str) -> list[dict]:
    return [{"lang": m["lang"], "word": m["word"], "score": float(m["score"]), "d": float(m["d"]), "relation": m["relation"]}
            for line in output.splitlines() if (m := HYBRID_LINE.search(line))]


def parse_legacy(output: str, target: str) -> list[dict]:
    """O legado devolve `palavra ↔ palavra`; não possui score ou distância D."""
    words = [word.strip() for word in output.replace("\n", " ").split("↔") if word.strip() and word.strip() != "(vazio)"]
    return [{"lang": target, "word": word, "score": None, "d": None, "relation": None} for word in words]


def run_test(query: str, source: str, target: str, top_k: int, hybrid: bool) -> dict:
    command = [sys.executable, "translate_partial.py", "--query", query, "--lang", source, "--target", target, "--top-k", str(top_k)]
    if hybrid:
        command.append("--hybrid")
    # errors=replace evita que a página de código cp1252 do Windows interrompa
    # um lote inteiro quando alguma mensagem externa não estiver em UTF-8.
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (process.stdout or "").strip()
    return {
        "query": query, "lang_from": source, "lang_to": target, "top_k": top_k, "hybrid": hybrid,
        "mode": "Hibrido" if hybrid else "Legado", "concept": concept(query), "success": process.returncode == 0,
        "output": output, "error": (process.stderr or "").strip(), "command": " ".join(command),
        "results": parse_hybrid(output) if hybrid else parse_legacy(output, target),
    }


def flatten(results: list[dict]) -> list[dict]:
    rows = []
    for test in results:
        for position, item in enumerate(test["results"], 1):
            rows.append({"query": test["query"], "lang_from": test["lang_from"], "lang_to": test["lang_to"],
                         "mode": test["mode"], "concept": test["concept"], "position": position, **item})
    return rows


def charts(rows: list[dict]) -> list[Path]:
    OUT_DIR.mkdir(exist_ok=True)
    df = pd.DataFrame(rows)
    hybrid = df[(df["mode"] == "Hibrido") & (df["position"] == 1)].copy()
    legacy = df[(df["mode"] == "Legado") & (df["position"] == 1)].copy()
    files = []
    if not hybrid.empty:
        fig, ax = plt.subplots(figsize=(11, 6))
        colors = hybrid["relation"].map({"same": "#2ca02c", "related": "#f0a53a"}).fillna("#7f7f7f")
        ax.scatter(hybrid["d"], hybrid["score"], c=colors, s=90, edgecolors="#1f2937")
        for _, row in hybrid.iterrows(): ax.annotate(row["query"], (row["d"], row["score"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.set(xlabel="Distancia D", ylabel="Score do primeiro resultado", title="TNU hibrido: Score x distancia ontologica")
        ax.grid(alpha=.25); path = OUT_DIR / "score_vs_distancia_d.png"; fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig); files.append(path)
        summary = hybrid.groupby("concept", as_index=False).agg(score=("score", "mean"), distance_d=("d", "mean"))
        fig, ax = plt.subplots(figsize=(10, 6)); ax.bar(summary["concept"], summary["score"], color="#2155d9")
        ax.set(ylabel="Score medio", title="Primeiro resultado hibrido por conceito"); ax.grid(axis="y", alpha=.25)
        path = OUT_DIR / "distribuicao_conceitos.png"; fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig); files.append(path)
    if not hybrid.empty and not legacy.empty:
        common = sorted(set(hybrid["query"]) & set(legacy["query"]))
        fig, ax = plt.subplots(figsize=(10, 5)); x = range(len(common))
        # O legado não tem score; o gráfico mostra a posição do resultado, não uma métrica inexistente.
        ax.bar([i-.2 for i in x], [1] * len(common), .4, label="Legado: primeira posicao", color="#ff9d37")
        ax.bar([i+.2 for i in x], [1-hybrid[hybrid["query"].eq(q)].iloc[0]["score"] for q in common], .4, label="Hibrido: 1-score", color="#36c8a1")
        ax.set(xticks=list(x), xticklabels=common, ylim=(0, 1.05), title="Comparacao visual: legado x hibrido")
        ax.legend(); path = OUT_DIR / "comparacao_scores.png"; fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig); files.append(path)
    return files


def markdown(results: list[dict], filename: Path, graphics: list[Path]) -> None:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for item in results: groups[(item["query"], item["lang_from"], item["lang_to"])].append(item)
    lines = ["# Relatorio de testes do TNU", "", f"Data: {datetime.now().isoformat(timespec='seconds')}",
             f"Testes: {len(results)}; sucessos: {sum(x['success'] for x in results)}", "", "## Graficos", *[f"![{p.stem}]({p.name})" for p in graphics], "", "## Resultados"]
    for (query, source, target), items in groups.items():
        lines += [f"### {query} ({source} -> {target})", ""]
        for item in items:
            first = item["results"][0] if item["results"] else None
            if first:
                metrics = f"score={first['score']:.4f}; D={first['d']:.3f}; {first['relation']}" if item["hybrid"] else "sem score/D no modo legado"
                lines.append(f"- **{item['mode']}**: `{first['word']}` ({metrics})")
            else: lines.append(f"- **{item['mode']}**: sem resultado")
        lines.append("")
    filename.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    results = []
    print(f"Executando {len(TESTS)} testes...")
    for index, test in enumerate(TESTS, 1):
        result = run_test(*test); results.append(result)
        first = result["results"][0]["word"] if result["results"] else "sem resultado"
        print(f"[{index:02}/{len(TESTS)}] {result['mode']}: {result['query']} -> {first} ({'ok' if result['success'] else 'erro'})")
    rows = flatten(results); stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pd.DataFrame(rows).to_csv(OUT_DIR / f"relatorio_tnu_{stamp}.csv", index=False, encoding="utf-8-sig")
    graphics = charts(rows)
    markdown(results, OUT_DIR / f"relatorio_tnu_{stamp}.md", graphics)
    (OUT_DIR / f"resultados_brutos_{stamp}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Concluido: {len(rows)} resultados; {len(graphics)} graficos; pasta={OUT_DIR}")


if __name__ == "__main__":
    main()
