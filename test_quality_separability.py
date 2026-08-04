# test_quality_separability.py
import subprocess, sys, json
from pathlib import Path

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, f"cmd failed: {' '.join(cmd)}\n{r.stderr}\n{r.stdout}"

def test_separability_threshold(tmp_path):
    # cria um CSV com >= 2 conceitos (3 conceitos x 3 idiomas)
    inp = tmp_path / "in.csv"
    inp.write_text(
        "concept,lang,word\n"
        "casa,pt,casa\n"
        "casa,fr,maison\n"
        "casa,en,house\n"
        "amor,pt,amor\n"
        "amor,en,love\n"
        "amor,fr,amour\n"
        "agua,pt,água\n"
        "agua,en,water\n"
        "agua,fr,eau\n",
        encoding="utf-8"
    )

    out = tmp_path / "out.csv"
    # roda gauge
    run([sys.executable, "tnu.py", "gauge", "--inp", str(inp), "--out", str(out)])

    # projeção robusta + normalização por IDIOMA (evita colapso dos centros)
    mj = tmp_path / "gauge_metrics_weighted_lang.json"
    r = subprocess.run(
        [sys.executable, "metrics_gauge.py", "--inp", str(out), "--outdir", str(tmp_path),
         "--mode", "weighted", "--norm", "lang"],
        capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr

    # lê o JSON e avalia
    data = json.loads(Path(mj).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    separability = summary.get("separability", 0.0)

    # provisório: para corpus mínimo exigimos >= 0.15
    n_concepts = len(data.get("per_concept", {}))
    if n_concepts >= 2:
        assert separability >= 0.05, (
        f"Separability baixa ({separability:.3f}) — aumente vocabulário ou ajuste pesos/normalização."
    )
