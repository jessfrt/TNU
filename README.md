# TNU — Tradutor Numérico Universal

O TNU é um sistema determinístico e explicável de processamento de linguagem natural, desenvolvido em Python por Jéssica Freitas no contexto de pesquisa em Engenharia de Software. Ele converte palavras em estruturas numéricas e ontológicas para comparar sua proximidade semântica entre idiomas.

A proposta central é representar significado de forma auditável: o sistema diferencia traduções diretas, como `água → water`, de termos apenas relacionados, como `água → sea`.

## Arquitetura

| Componente | Função |
|---|---|
| `tnu.py` | Núcleo determinístico, vetor numérico e código-σ por BLAKE2b. |
| `ipa_fixed.py` | Representação fonética pseudo-IPA estável. |
| `sigma_partial.py` | Projeção B, serializada como `codeO`. |
| `translate_partial.py` | Busca legada e busca híbrida. |
| `ontology_concepts.json` | Memória ontológica da Camada D. |
| `import_ontology.py` | Importação da ontologia para `gama.db`. |
| `batch_test_tnu.py` | Testes em lote e geração de relatórios/gráficos. |
| `wikidata_enrich.py` | Candidatos multilíngues auditáveis com QID e confiança. |

O código-σ é um identificador estrutural. A busca híbrida calcula proximidade usando as projeções A, B, C e principalmente D:

```text
Score = α·σ + β·A + γ·B + λ·C + δ·D
```

Na implementação, σ é mantido como identificador; os pesos padrão da busca são D=0,80, B=0,10, A=0,05 e C=0,05. Menor score é melhor.

## Camada D

A Camada D registra sentidos, vetores, tags e relações conceituais. A ontologia industrial atual contém centenas de sentidos distribuídos entre emoções, natureza, saúde, tecnologia, esportes, arte, ciência e sociedade.

Ela permite relações como:

- `same`: mesmo sentido e tradução direta;
- `related`: sentidos semanticamente associados;
- `broader` / `narrower`: hiperônimo e hipônimo;
- `opposite`: antonímia.

## Uso

Crie e ative o ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install pytest pandas matplotlib
```

Busca híbrida:

```powershell
python translate_partial.py --hybrid --query "água" --lang pt --target en --top-k 5
```

Exemplo:

```text
en:water score=0.044433 D=0.000 relation=same
en:sea score=0.236929 D=0.214 relation=related
```

Busca legada para comparação:

```powershell
python translate_partial.py --query "água" --lang pt --target en --top-k 5
```

Importação da ontologia:

```powershell
python import_ontology.py --file ontology_concepts.json --db gama.db
```

Testes unitários e em lote:

```powershell
python -m pytest -q
python batch_test_tnu.py
```

O executor em lote gera Markdown, CSV, JSON e gráficos na pasta `relatorios/`.

## Aplicações

- Tradução semântica assistida e explicável.
- Educação linguística por conceitos, sinônimos e relações semânticas.
- Pré-processamento rastreável em pipelines de PLN.
- Análise de discurso, sentimentos e polaridade ontológica.
- Sistemas de recomendação baseados em afinidade conceitual.
- Pesquisa sobre universais linguísticos e geometria do significado.
- Indexação e codificação semântica experimental; não substitui criptografia convencional.

## Validação

A suíte de testes cobre determinismo, formato de dados, importação, distância ontológica, relações e ranking híbrido. O executor em lote avalia consultas entre português, inglês, espanhol, francês, alemão e italiano.

Os testes operacionais devem ser complementados por um conjunto ouro revisado por humanos e métricas como Recall@1, MRR, precisão por idioma e cobertura lexical.

## Limitações e próximos passos

A expansão industrial foi inicialmente curada em português. O enriquecimento multilíngue usa candidatos do Wikidata, com QID, rótulos e confiança, mas entradas ambíguas devem passar por revisão humana antes de serem incorporadas.

Também são prioridades futuras: ampliar a cobertura da projeção sintática C, refinar a projeção B, sincronizar léxicos aprovados ao banco e ampliar a API/interface web.

Consulte o [relatório técnico-executivo](RELATORIO_TECNICO_EXECUTIVO_TNU.md) para a documentação completa.

---

Relatório gerado pelo TNU - Tradutor Numérico Universal. © 2026 Jéssica Freitas.
