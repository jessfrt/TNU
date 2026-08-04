#!/usr/bin/env python3
"""Limpeza auditável de resquícios legados do projeto TNU.

Por segurança, o modo padrão só mostra o que seria feito e grava o log. Use
``python cleanup_tnu.py --apply`` para editar/mover arquivos de fato. Nenhum
arquivo é apagado: os itens legados vão para ``legado/``.
"""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "cleanup_log.txt"
EXCLUDED_DIRS = {"legado", ".git", ".pytest_cache", "__pycache__", "de", "venv", "Trabalho"}
LEGACY_ITEMS = (
    "de",                    # ambiente virtual sem de/pyvenv.cfg
    "pyvenv.cfg",            # arquivo inválido na raiz do projeto
    "atualiza.py",           # atualizador manual do formato sigma legado
    "atualiza_auto.py",      # atualizador automático do formato sigma legado
    "atualiza_auto.log.json",
    "in_backup_gap.csv",
)

# Bloco ``if ... pyvenv.cfg:`` e seu corpo indentado. A expressão só toca em
# condicionais explícitos; casos incomuns são registrados para revisão humana.
PYVENV_BLOCK = re.compile(r"(?ms)^[ \t]*if[^\n]*pyvenv\.cfg[^\n]*:\s*\n(?:^[ \t]+.*(?:\n|$))*")
PYVENV_LINE = re.compile(r"(?m)^.*(?:os\.path\.exists|Path\([^\n]*\.exists\()[^\n]*pyvenv\.cfg[^\n]*(?:\n|$)")
PROJECT_LITERAL = re.compile(
    r"(['\"])[A-Za-z]:[\\/]+Users[\\/]+jessi[\\/]+Desktop[\\/]+TNU- Registros[\\/]+TNU(?:[\\/]([^'\"]*))?\1"
)


def log(message: str) -> None:
    stamp = datetime.now().isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {message}\n")
    print(message)


def project_python_files() -> list[Path]:
    """Lista somente código do projeto; nunca altera ambientes ou legado."""
    return [
        path for path in ROOT.rglob("*.py")
        if path.name != Path(__file__).name
        and not any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)
    ]


def replace_project_literal(source: str) -> tuple[str, int]:
    """Converte literais absolutos conhecidos em expressões relativas a __file__."""
    count = 0

    def replacement(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        tail = (match.group(2) or "").replace("\\", "/")
        if tail:
            return f"str(PROJECT_ROOT / {tail!r})"
        return "str(PROJECT_ROOT)"

    return PROJECT_LITERAL.sub(replacement, source), count


def ensure_project_root_helper(source: str) -> str:
    """Insere a constante somente quando uma substituição de caminho a exige."""
    if "PROJECT_ROOT = Path(__file__).resolve().parent" in source:
        return source
    prefix = "from pathlib import Path\nPROJECT_ROOT = Path(__file__).resolve().parent\n"
    if source.startswith("#!"):
        first, _, rest = source.partition("\n")
        return first + "\n" + prefix + rest
    return prefix + source


def clean_python_file(path: Path, apply: bool) -> None:
    original = path.read_text(encoding="utf-8")
    changed = original
    changed, blocks = PYVENV_BLOCK.subn("", changed)
    changed, lines = PYVENV_LINE.subn("", changed)
    changed, paths = replace_project_literal(changed)
    if paths:
        changed = ensure_project_root_helper(changed)

    if changed == original:
        log(f"SEM ALTERAÇÃO {path.relative_to(ROOT)}")
        return
    action = "ALTERADO" if apply else "SIMULAÇÃO"
    log(f"{action} {path.relative_to(ROOT)}: blocos_pyvenv={blocks}, linhas_pyvenv={lines}, caminhos={paths}")
    if apply:
        path.write_text(changed, encoding="utf-8", newline="")


def unique_destination(folder: Path, name: str) -> Path:
    destination = folder / name
    index = 1
    while destination.exists():
        destination = folder / f"{Path(name).stem}_{index}{Path(name).suffix}"
        index += 1
    return destination


def move_legacy_items(apply: bool) -> None:
    destination_dir = ROOT / "legado"
    for name in LEGACY_ITEMS:
        source = ROOT / name
        if not source.exists():
            log(f"LEGADO AUSENTE {name}")
            continue
        destination = unique_destination(destination_dir, name)
        action = "MOVIDO" if apply else "SIMULAÇÃO MOVER"
        log(f"{action} {name} -> {destination.relative_to(ROOT)}")
        if apply:
            destination_dir.mkdir(exist_ok=True)
            shutil.move(str(source), str(destination))


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpeza auditável do TNU")
    parser.add_argument("--apply", action="store_true", help="aplica edições e move arquivos para legado/")
    args = parser.parse_args()
    LOG_FILE.write_text("", encoding="utf-8")
    log(f"INÍCIO modo={'APLICAR' if args.apply else 'SIMULAÇÃO'} raiz={ROOT}")
    for path in project_python_files():
        clean_python_file(path, args.apply)
    move_legacy_items(args.apply)
    log("FIM. Crie o novo ambiente com: python -m venv venv")


if __name__ == "__main__":
    main()
