# Relatório de limpeza — TNU

## Causa do erro `No pyvenv.cfg file`

O erro não era emitido por `tnu.py` nem pelos demais scripts. A varredura de
todos os arquivos Python não encontrou nenhuma referência a `pyvenv.cfg`,
`os.path.exists(...pyvenv.cfg)` ou caminho absoluto `C:\Users\jessi\...`.

O executável `de\Scripts\python.exe` existia, mas seu arquivo obrigatório
`de\pyvenv.cfg` não. Havia um `pyvenv.cfg` na raiz cujo campo `command`
declarava ter criado justamente `...\TNU\de`; portanto ele estava no local
errado. Um `pyvenv.cfg` na raiz nunca torna válido o interpretador dentro de
`de`. O ambiente novo e válido é `venv\`, com:

```
venv\pyvenv.cfg
venv\Scripts\python.exe
```

## Ocorrências e ações por arquivo

| Arquivo | Achado | Ação |
|---|---|---|
| `tnu.py` | Não há referências a venv/caminho absoluto. Na linha 327 importava `_distance_triplet`, ausente anteriormente. | Mantido; a função compatível foi acrescentada em `translate_partial.py`. |
| `translate_partial.py` | Linhas 186–187 (antes da limpeza) eram código morto: `if tol is None` após retorno do modo exato. | Removidas. Mantém modo legado e híbrido. |
| `atualiza.py` | Linhas 1–19 usam o sigma legado e inserem pares manualmente. Não é importado por nenhum arquivo ativo. | Mover para `legado/`; não apagar. |
| `atualiza_auto.py` | Linhas 1–40 usam sigma legado, gravam log e não são importadas pelo fluxo ativo. | Mover para `legado/`, junto de `atualiza_auto.log.json`. |
| `emotion.py` | Importação NLTK é opcional e possui fallback neutro. | Manter. |
| `etym.py` | Placeholder agora usa BLAKE2b estável. | Manter; substituir futuramente por dados etimológicos curados. |
| `ipa_fixed.py`, `tnu_determinism.py`, `sigma_partial.py`, `ontology.py`, `import_ontology.py` | Núcleo ativo; sem referência problemática. | Manter. |
| `lookup_partial.py`, `metrics_gauge.py`, `plot_gauge.py`, `semantic_gap.py` | Utilitários ativos. `semantic_gap.py` requer `pandas`; `plot_gauge.py` requer `matplotlib`. | Manter; instalar dependências apenas se esses utilitários forem usados. |
| `test_*.py` | `sys.executable` ocorre em dois testes e é correto: garante que subprocessos usem o mesmo Python do teste. | Manter, sem alteração. |
| `in_backup_gap.csv` | Backup antigo, não usado pelo fluxo principal. | Mover para `legado/`; não apagar. |
| `de/` | Ambiente Python incompleto: tem `Scripts/python.exe`, mas não tem `de/pyvenv.cfg`. | Mover para `legado/de/`. |
| `pyvenv.cfg` na raiz | Configuração de ambiente colocada fora do ambiente virtual. | Mover para `legado/pyvenv.cfg`. |

Não foram encontrados módulos locais importados e inexistentes. Dependências
externas: `pandas` (`semantic_gap.py`), `matplotlib` (`plot_gauge.py`), NLTK
opcional (`emotion.py`) e pytest para testes.

## Script de limpeza

`cleanup_tnu.py` grava `cleanup_log.txt` e é seguro por padrão:

```powershell
python cleanup_tnu.py          # somente simula
python cleanup_tnu.py --apply  # move itens legados para legado/
```

Ele também procura condicionais explícitos que verifiquem `pyvenv.cfg` e
literais absolutos do caminho deste projeto. Na inspeção atual não havia
ocorrências de código para modificar; o script continua disponível para
futuras cópias antigas.

## Ambiente e validação

O ambiente correto foi recriado com `python -m venv venv`. Para uso no
PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install pytest pandas matplotlib
python translate_partial.py --hybrid --query "água" --lang pt --target en
```

Validação com `venv\Scripts\python.exe`:

```
en:water score=0.044433 D=0.000 relation=same
en:sea score=0.236929 D=0.214 relation=related
```

O comando não produziu `No pyvenv.cfg file`.
