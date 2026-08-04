# TNU — diagnóstico e proposta da Camada D

Data da inspeção: 2026-08-03. Este relatório descreve o estado efetivo do
repositório e uma migração incremental para uma projeção ontológica
explicável e determinística.

## Resumo executivo

O agrupamento inadequado de `água` não é apenas um problema de peso: a
projeção `B` atual não codifica significado lexical. Ela é calculada como:

```
c0 = média(e1, e2, e7)  # IPA/forma + bucket derivado de (idioma, palavra)
c1 = e5                 # etimologia
c2 = e6                 # valência
```

Assim, `c0` é majoritariamente ortográfico/fonético; `c1` usa atualmente
`hash(word)` em `etym.py`, que varia entre processos Python; e `c2` é 0,5
quando NLTK/corpora não estão disponíveis. A solução recomendada é adicionar
uma camada D por **sentido/conceito**, mantida fora do sigma lexical. D deve
ser o principal sinal de tradução, enquanto A/forma continua útil apenas para
desempate e aproximação fonética.

Há ainda uma distinção necessária no corpus: em `agua` aparecem `water`,
`sea`, `river`, `stream` e seus equivalentes. São relacionados, mas não são a
mesma tradução. A chave de anotação deve ser um `sense_id`, por exemplo
`WATER.SUBSTANCE`, `WATER.SEA`, `WATER.RIVER` e `WATER.STREAM`; não apenas o
rótulo amplo `agua`.

## Inventário de código

### Núcleo

| Arquivo | Papel observado |
|---|---|
| `tnu.py` | CLI, vetor alfa, sigma canônico, SQLite, import/export, gauge e `transp`. |
| `tnu_determinism.py` | normalização NFC/casefold, quantização, JSON e BLAKE2b estáveis. |
| `ipa_fixed.py` | IPA fixo para algumas palavras e pseudo-IPA determinístico por regras. |
| `sigma_partial.py` | projeção B de três componentes (`codeO`). |
| `translate_partial.py` | busca por ressonância B, gates e pesos de distância. |

### Utilitários e análise

| Arquivo | Papel observado |
|---|---|
| `metrics_gauge.py` | amplitude intra-conceito, distância entre centros e separabilidade. |
| `plot_gauge.py` | gráficos da régua a partir de `codeO`. |
| `semantic_gap.py` | lacunas entre centros já calculados; depende de pandas. |
| `lookup_partial.py` | índice e busca exata/aproximada por `codeO`. |
| `atualiza.py` | vincula manualmente duas palavras ao mesmo sigma legado. |
| `atualiza_auto.py` | insere grupos fixos e escreve log; é legado/manual. |
| `emotion.py` | valência por SentiWordNet, com fallback neutro. |
| `etym.py` | *placeholder* etimológico; hoje não é determinístico. |

### Testes

`test_determinism.py`, `test_gauge_format.py`, `test_ipa_fixed.py`,
`test_lookup_partial.py`, `test_quality_separability.py`,
`test_sigma_partial.py`, `test_tnu.py`, `test_translate_compat.py` e
`test_translate_partial.py` são testes do projeto. Na inspeção, os 9 testes
passaram. `pytest.ini` exclui os diretórios de ambientes virtuais.

## Fluxo atual e limitações

1. `alfa_vector()` em `tnu.py` produz `[e1..e7]`: soma de codepoints IPA,
   forma das letras, sílabas, constante, etimologia, valência e bucket estável.
2. `sigma_code()` serializa palavra, idioma, IPA e vetor e calcula BLAKE2b;
   esse sigma identifica a forma calculada, não um conceito multilingue.
3. `sigma_partial()` cria B: `c0=mean(e1,e2,e7)`, `c1=e5`, `c2=e6`.
4. `translate_partial()` normaliza por média de idioma e filtra por limiares
   de B; sua pontuação é `d_scalar + w_aux*(|etym_src-etym_tgt| +
   |valence_src-valence_tgt|)`. Não há A, C ou D explícitas nessa métrica.
5. O banco guarda `ipa`, `vec` e `codeO` como JSON em `gama.marks`.

Portanto A existe somente diluída no vetor; B é híbrida de forma/etimologia/
emoção; C não está implementada. A fórmula `α·σ + β·A + γ·B + λ·C + δ·D`
não deve tratar `σ` hexadecimal como distância numérica. Use-o como ID e
calcule distâncias somente entre vetores/projeções.

### Correções técnicas prioritárias

- Substituir `hash(word)` em `etym.py`: o hash interno do Python é
  aleatorizado por processo. Isso já gerou registros diferentes para o mesmo
  lema. Usar uma tabela curada ou `stable_hash`/BLAKE2b caso se mantenha um
  fallback puramente formal.
- Não usar `INSERT OR REPLACE` para mascarar múltiplas versões de um lema.
  O banco tem 314 linhas, mas somente 120 pares distintos `(lang, lemma)`;
  há duplicação por `scode`.
- Separar tradução (`sense_id` igual) de relação semântica (`sea` é
  `related_to` water, não tradução exata de `water`).
- Não incluir D no payload de `sigma_code` na primeira fase. Alterar D não
  deve invalidar identificadores lexicais já persistidos.

## Dados inspecionados

| Fonte | Estrutura e conteúdo |
|---|---|
| `in.clean.csv` | 120 linhas; `concept,lang,word`; cinco grupos: agua, amor, casa, comida, vida. |
| `in_backup_gap.csv` | 125 linhas; mesma base mais cinco linhas-comentário lidas como CSV. |
| `in.csv` | 144 linhas; seis grupos reais: abrigo (18) e os cinco anteriores (24 cada), mais seis linhas-comentário. O CLI as ignora. |
| `out.csv` | 120 linhas; `concept,lang,word,codeO`. |
| `out/gauge-verificado.csv` | 138 linhas; mesma estrutura, incluindo abrigo. |
| `out/gauge_metrics*.csv/json` | métricas agregadas: `concept,center,amplitude_intra,n`; JSON com `per_concept`, `inter_pairs`, `summary`, `mode` e, em versões novas, `norm`. |
| `atualiza_auto.log.json` | uma entrada: `data,nucleo,sigma,palavras`. |
| `gama.db` | tabela única `gama(scode, lang, lemma, freq, conf, marks)`; PK `(scode,lang,lemma)`. 314 linhas; `marks` contém `ipa`, `vec`, `codeO`. |

Idiomas: `pt`, `en`, `fr`, `es`, `de`, `it`. Os conceitos reais atualmente
presentes são `abrigo`, `agua`, `amor`, `casa`, `comida`, `vida`.

Vocabulário por grupo está explicitamente nos CSVs acima. Para referência:

- `agua`: água/water/eau/agua/Wasser/acqua, e também água potável, waters,
  eaux, aguas, acque, riacho/river/ruisseau/arroyo/Bach/Fluss/ruscello e
  mar/sea/mer/Meer/mare.
- `amor`: amor/love/amour/amor/Liebe/amore e afeto/affection/affection/
  afección/Zuneigung/affetto; paixão/passion/passion/pasión/Leidenschaft/
  passione; carinho/devotion/attachement/cariño/Hingabe/tenerezza.
- `casa`: casa/house/maison/casa/Haus/casa e lar/home/foyer/hogar/Zuhause;
  domicílio/residence/domicile/domicilio/Wohnung/dimora; moradia/dwelling/
  logement/vivienda/Heim/abitazione-alloggio.
- `comida`: comida/food/nourriture/comida/Essen/cibo e alimento/foodstuff/
  aliment/alimento/Nahrung/alimento; refeição/meal/repas/comida principal/
  Mahlzeit/pasto; nutriente/nutrient/nutriment/nutriente/Nährstoff/nutriente.
- `vida`: vida/life/vie/vida/Leben/vita e existência/existence/existence/
  existencia/Existenz/esistenza; viver/living-vivre/vivir/leben/vivere;
  biografia/biography/biographie/biografía/Biografie/biografia.
- `abrigo`: abrigo/shelter/abri/abrigo/schutz/rifugio; refugio/refuge/refuge/
  refugio/unterkunft/riparo; protecao/protection/protection/proteccion/asyl/
  protezione.

Esses grupos combinam sinônimos, hipônimos, hiperônimos e associados. O novo
modelo precisa manter esses tipos de relação em vez de forçar igualdade.

## Arquitetura proposta: D por sentido

### Arquivo-fonte versionado

Criar `ontology_concepts.json` (curadoria humana, UTF-8, ordenação estável):

```json
{
  "schema_version": 1,
  "senses": {
    "WATER.SUBSTANCE": {
      "vector": {"entity": 1, "physical": 1, "liquid": 1,
                 "natural": 1, "animate": 0, "mass": 1},
      "tags": ["substance", "liquid", "natural"],
      "relations": {"broader": ["SUBSTANCE"], "related": ["WATER.SEA"]}
    },
    "WATER.SEA": {
      "vector": {"entity": 1, "physical": 1, "geographic": 1,
                 "water_body": 1, "liquid": 1, "natural": 1},
      "tags": ["geographic_feature", "water_body", "salt_water"],
      "relations": {"broader": ["WATER.BODY"], "related": ["WATER.SUBSTANCE"]}
    }
  },
  "lexemes": {
    "pt:água": ["WATER.SUBSTANCE"],
    "en:water": ["WATER.SUBSTANCE"],
    "fr:eau": ["WATER.SUBSTANCE"],
    "es:agua": ["WATER.SUBSTANCE"],
    "de:Wasser": ["WATER.SUBSTANCE"],
    "it:acqua": ["WATER.SUBSTANCE"],
    "en:sea": ["WATER.SEA"]
  }
}
```

É preferível a colunas fixas no CSV, pois novos atributos não exigem migração.
O JSON é a fonte de verdade revisável; o SQLite recebe uma cópia indexada:

```sql
CREATE TABLE ontology_sense (
  sense_id TEXT PRIMARY KEY,
  vector_json TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  relations_json TEXT NOT NULL,
  source TEXT NOT NULL,
  revision TEXT NOT NULL
);
CREATE TABLE lexeme_sense (
  lang TEXT NOT NULL,
  lemma TEXT NOT NULL,
  sense_id TEXT NOT NULL REFERENCES ontology_sense(sense_id),
  confidence REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY (lang, lemma, sense_id)
);
```

`lexeme_sense` admite polissemia. A escolha de sentido na versão inicial é
determinística: maior `confidence`, depois `sense_id` em ordem lexicográfica;
futuras versões podem receber contexto.

### Vetor e distância D

Use dimensões binárias/versionadas, com pesos humanos explícitos. Exemplo de
famílias: tipo ontológico (peso 4), subclasse (3), estado/matéria (2),
função/uso (2), propriedades sensoriais (1), valência (1), domínio (0,5).

Para vetores esparsos binários, a distância Jaccard ponderada é interpretável:

```
d_D(x,y) = 1 - sum(w_i * min(x_i,y_i)) / sum(w_i * max(x_i,y_i))
```

O `sense_id` igual retorna distância 0; sem anotação retorna `None`, não 0.
Na busca, a falta de D deve receber uma pequena penalidade controlada, para
que termos anotados não sejam comparados como semanticamente idênticos.

Uma métrica inicial apropriada é:

```
score = 0.80*d_D + 0.10*d_B + 0.05*d_A + 0.05*d_C + missing_D_penalty
```

`d_sigma` não entra como número: sigma é ID. Durante o piloto, B pode ser o
codeO atual, A uma distância sobre IPA, C uma distância de classe gramatical
(inicialmente 0 ou 1). Os pesos devem ficar em `tnu_config.json`, não no
código. Para tradução exata, priorize `sense_id` igual; para sugestões,
ordene pelo score e exponha também a relação ontológica.

## Integração incremental

1. **Prova de conceito.** Criar o JSON com 20–30 sentidos, não apenas 20–30
   palavras: água-substância, mar, rio, riacho; amor/afeição/paixão; casa,
   lar, residência; alimento/refeição/nutriente; vida/biografia; abrigo/
   refúgio/proteção. Mapear os seis idiomas já presentes.
2. **Módulo isolado.** Criar `ontology.py` com `load_ontology()`,
   `senses_for()`, `ontology_distance()` e `relation()`. Sem tocar no sigma.
3. **Banco e importação.** Criar as duas tabelas e um comando CLI
   `ontology-import --file ontology_concepts.json`. Guardar `sense_ids` em
   `marks` apenas como cache, não como fonte de verdade.
4. **Busca.** Acrescentar `translate_ontology()` ou a opção
   `tnu.py transp --metric hybrid --weights ...`; manter o modo legado para
   comparação reprodutível.
5. **Validação.** Criar pares ouro de tradução e pares negativos (water–sea,
   water–house). Medir Recall@1/MRR para tradução e separabilidade por
   `sense_id`; a atual amplitude por `concept` não basta.
6. **Escala.** Importar candidatos de WordNet/Wikidata/ConceptNet em arquivo
   separado, registrar `source`/`revision` e aceitar somente mapeamentos
   revisados. Para multilinguismo, Wikidata é candidato a identificador-pivô;
   a taxonomia e pesos finais devem continuar curados e versionados localmente.
7. **Otimização.** Ajustar pesos contra o conjunto ouro, reservando pares de
   validação por conceito; não ajustar contra o próprio corpus de treinamento.

## Pseudocódigo do módulo inicial

```python
def ontology_distance(lang_a, word_a, lang_b, word_b, ontology):
    senses_a = ontology.lexemes.get(f"{lang_a}:{canonical_text(word_a)}", [])
    senses_b = ontology.lexemes.get(f"{lang_b}:{canonical_text(word_b)}", [])
    if not senses_a or not senses_b:
        return None
    return min(weighted_jaccard(ontology.senses[a].vector,
                                ontology.senses[b].vector)
               for a in senses_a for b in senses_b)

def hybrid_score(a, b, weights):
    d_d = ontology_distance(*a, *b, ONTOLOGY)
    return (weights["D"] * (d_d if d_d is not None else 1.0) +
            weights["B"] * code_o_distance(*a, *b) +
            weights["A"] * ipa_distance(*a, *b) +
            weights["C"] * pos_distance(*a, *b))
```

## Manutenção e reprodutibilidade

- Documentar cada dimensão, valores válidos e peso em
  `ontology_schema.md`; não alterar o significado de uma dimensão existente.
- Toda anotação deve ter `source`, `revision`, autor/revisor e teste de
  validação de esquema. Chaves JSON e listas devem ser serializadas de forma
  ordenada.
- Criar testes: igualdade multilingue (`água`/`water`/`eau`), separação
  (`water`/`sea`), polissemia e caso sem anotação.
- Versionar o arquivo ontológico junto com o código; exportar a versão usada
  em cada experimento e registrar pesos, dataset e resultados.
- Remover ou migrar os registros duplicados de `gama` somente após um backup
  e um script de migração auditável. Não apagar diretamente o banco atual.
