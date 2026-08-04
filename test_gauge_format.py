import csv
from pathlib import Path
from tnu import cli  # se seu cli roda via if __name__ == "__main__", troque por subprocess
import subprocess, sys

def test_gauge_generates_csv(tmp_path):
    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"

    inp.write_text("concept,lang,word\ncasa,pt,casa\ncasa,fr,maison\n", encoding="utf-8")

    # chama por subprocess para simular CLI real
    cmd = [sys.executable, "tnu.py", "gauge", "--inp", str(inp), "--out", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    assert out.exists()
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows and set(rows[0].keys()) == {"concept","lang","word","codeO"}
