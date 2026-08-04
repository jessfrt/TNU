# Camada D — Ontologia do TNU

## Propósito

A Camada D introduz significado lexical explícito, independente da grafia e
da pronúncia. O `codeO` legado (B) continua disponível, mas mistura forma,
etimologia provisória e valência; por isso ele não é usado isoladamente para
afirmar que duas palavras são traduções.

A busca híbrida calcula:

```
score = D*0.80 + B*0.10 + A*0.05 + C*0.05
```

Menor score é melhor. `sigma` continua sendo identificador determinístico, e
não uma distância numérica. D é a distância Jaccard ponderada entre vetores
ontológicos; A é Levenshtein normalizado na pseudo-IPA; B é L1 normalizada no
`codeO`; C é zero até haver anotações `pos` em `marks`.

## Fonte de dados

`ontology_concepts.json` é a fonte de verdade, versionada no repositório.

```json
"WATER.SUBSTANCE": {
  "vector": {"physical": 1, "liquid": 1, "natural": 1},
  "tags": ["substance", "liquid"],
  "relations": {"broader": ["SUBSTANCE"], "related": ["WATER.SEA"]}
}
```

- `vector`: dimensões numéricas não negativas; ausências valem zero.
- `tags`: rótulos para leitura humana.
- `relations.broader`: conceito mais amplo; `related`: associação não
  equivalente.
- `lexemes`: chave canônica `idioma:lema` e lista de `sense_id`. A lista
  permite polissemia (`de:leben`, por exemplo, tem dois sentidos no piloto).
- `feature_weights`: peso de cada dimensão na Jaccard. Dimensões inexistentes
  recebem peso 1.

Para incluir um termo, primeiro crie ou reutilize um `sense_id`, depois inclua
os seis campos e relacione os lemas. Não use um único sentido amplo para
palavras como `água`, `mar` e `rio`: elas são relacionadas, mas não são
traduções exatas.

## Importação SQLite

```powershell
python import_ontology.py --file ontology_concepts.json --db gama.db
```

O importador cria `ontology_sense`, `lexeme_sense` e `ontology_metadata`, e
adiciona `gama.ontology_version` quando a tabela `gama` já existe. O modo
legado não depende dessas tabelas.

## Busca

```powershell
python translate_partial.py --hybrid --query "água" --lang pt --target en --top-k 5
python translate_partial.py --query "água" --lang pt --target en
```

O primeiro usa D e mostra score, distância D e relação. O segundo mantém a
função legada `translate_partial()` para comparação.

Em Python, a função recebe uma conexão explicitamente para facilitar testes e
evitar estado global:

```python
from ontology import load_ontology
from translate_partial import hybrid_search

rows = hybrid_search(conn, "pt", "água", "en", None,
                     load_ontology("ontology_concepts.json"), top_k=5)
```

Passe, por exemplo, `{"D": 0.9, "B": 0.05, "A": 0.05, "C": 0.0}` no lugar
de `None` para substituir pesos. D ausente recebe penalidade 1.0 para não ser
tratado como igualdade.

## Próximos passos

1. Curar 20–30 sentidos com pares ouro positivos e negativos.
2. Importar a ontologia e comparar resultados híbridos/legados.
3. Medir Recall@1, MRR e separabilidade por `sense_id`.
4. Expandir candidatos com WordNet/Wikidata, registrando fonte e revisão.
5. Adicionar classe gramatical a `marks.pos` para tornar C informativa.
6. Ajustar pesos somente no conjunto de validação.
7. Migrar o banco legado com backup e deduplicação auditável.
