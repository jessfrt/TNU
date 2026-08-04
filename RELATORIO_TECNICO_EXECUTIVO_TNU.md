# Relatório Técnico-Executivo — TNU

## 1. Resumo Executivo

O TNU (Tradutor Numérico Universal) é um sistema de processamento de linguagem natural explicável e determinístico, desenvolvido em Python por Jéssica Freitas no contexto de pesquisa em Engenharia de Software. Em vez de depender exclusivamente de modelos estatísticos opacos, o TNU representa palavras por estruturas numéricas e ontológicas, comparando sua proximidade semântica entre idiomas. A Camada D, sua principal evolução, registra sentidos, propriedades e relações conceituais de forma auditável. Assim, o sistema consegue distinguir traduções diretas, como `água → water`, de termos apenas relacionados, como `água → sea`.

## 2. Arquitetura do Sistema

O TNU é organizado em módulos independentes, conectados por arquivos JSON, SQLite e interfaces de linha de comando.

### Núcleo determinístico

`tnu.py` é o núcleo do sistema. Ele normaliza texto, produz uma sequência pseudo-IPA, calcula um vetor numérico e gera um código-σ por hash BLAKE2b. O σ funciona como identificador estrutural determinístico, e não como uma distância numérica direta.

### Projeções linguísticas

- **A — Fonética:** derivada da representação IPA/pseudo-IPA determinística.
- **B — Híbrida:** serializada como `codeO`, combinando sinais estruturais, etimológicos provisórios e de valência.
- **C — Sintática:** prevista na arquitetura; atualmente pode usar a marca `pos` quando houver anotação, mas ainda não possui cobertura ampla.
- **D — Ontológica:** distância entre sentidos e vetores de `ontology_concepts.json`. É a principal fonte de significado lexical explícito.

### Ontologia e banco

`ontology_concepts.json` contém a memória conceitual do TNU. Na revisão industrial atual, ela possui 393 sentidos e 751 léxicos, distribuídos pelos domínios de emoções, natureza, saúde, tecnologia, esportes, arte, ciência e sociedade. `import_ontology.py` transfere esses dados para `gama.db`, criando as tabelas `ontology_sense` e `lexeme_sense`.

### Fluxo de busca

```text
Palavra + idioma de origem
        ↓
Normalização, pseudo-IPA e codeO
        ↓
Identificação de sentidos na Camada D
        ↓
Busca de candidatos no gama.db pelo idioma-alvo
        ↓
Distâncias D, B, A e C → score híbrido → ranking
```

A formulação conceitual é:

```text
Score = α·σ + β·A + γ·B + λ·C + δ·D
```

Na implementação atual, σ é mantido como identificador; a pontuação híbrida usa principalmente D, seguida de B, A e C. Os pesos padrão são D=0,80, B=0,10, A=0,05 e C=0,05. Menor score representa maior proximidade.

### Testes, relatórios e enriquecimento

- `batch_test_tnu.py` executa consultas em lote, compara os modos legado e híbrido e produz Markdown, CSV, JSON e gráficos.
- `wikidata_enrich.py` prepara candidatos multilíngues com QID, rótulos, fonte e confiança.
- `apply_wikidata_candidates.py` aplica somente candidatos aceitos após a revisão humana.
- `TNU-Site/` disponibiliza uma interface Flask para busca, comparação, ontologia e estatísticas.

## 3. Comandos de Uso

### Busca híbrida

```powershell
python translate_partial.py --hybrid --query "água" --lang pt --target en --top-k 5
```

Exemplo de saída:

```text
en:water score=0.044433 D=0.000 relation=same
en:sea score=0.236929 D=0.214 relation=related
```

O modo híbrido prioriza equivalência de sentido na Camada D.

### Busca legada

```powershell
python translate_partial.py --query "água" --lang pt --target en --top-k 5
```

Exemplo de saída:

```text
devotion ↔ water ↔ water
```

Esse modo serve como linha de base histórica. Ele não expõe score ou distância D e pode priorizar similaridade estrutural em vez de significado.

### Testes em lote

```powershell
python batch_test_tnu.py
```

Saída esperada:

```text
Executando 26 testes...
[01/26] Hibrido: água -> water (ok)
Concluido: 123 resultados; 3 graficos; pasta=...\relatorios
```

O comando gera relatórios Markdown, CSV, JSON e gráficos de comparação.

### Importação da ontologia

```powershell
python import_ontology.py --file ontology_concepts.json --db gama.db
```

Saída esperada:

```text
Ontologia industrial-seed-pt-v1 importada em gama.db.
```

### Enriquecimento multilíngue com Wikidata

```powershell
python wikidata_enrich.py --out wikidata_candidates.json
python apply_wikidata_candidates.py --candidates wikidata_candidates.json --apply
```

O primeiro comando gera candidatos rastreáveis; o segundo inclui no JSON apenas os registros aceitos.

### Testes unitários

```powershell
python -m pytest -q
```

Saída esperada:

```text
12 passed
```

### Consulta direta ao banco

```powershell
sqlite3 gama.db
```

Exemplo de consulta SQL:

```sql
SELECT lang, lemma FROM gama WHERE lang = 'en' LIMIT 10;
```

## 4. Áreas de Aplicação e Usos Potenciais

### 4.1 Tradução semântica

O TNU pode apoiar tradutores ao mostrar não apenas uma palavra candidata, mas também sua distância ontológica e sua relação com o termo original. Por exemplo, para `água`, o sistema prioriza `water` e deixa `sea` como termo relacionado, evitando uma substituição semântica indevida.

### 4.2 Educação linguística

Em cursos de idiomas, a régua semântica pode ajudar estudantes a compreender diferenças entre tradução direta, sinônimo, hiperônimo e termo associado. Uma atividade pode comparar `house`, `home`, `dwelling` e `residence` e discutir seus sentidos.

### 4.3 Processamento de linguagem natural explicável

O modelo pode ser usado como etapa de normalização ou enriquecimento em pipelines de PLN que exigem rastreabilidade. Diferentemente de um embedding não interpretável, cada score pode ser decomposto por dimensão e relação ontológica.

### 4.4 Criptografia semântica

Como pesquisa exploratória, o código-σ e os vetores conceituais podem apoiar mecanismos de codificação ou indexação de conteúdo por significado. Não substituem criptografia convencional, mas podem ser investigados para recuperação semântica e assinaturas conceituais.

### 4.5 Análise de discurso e sentimentos

Os sentidos de emoção e os atributos valorativos da ontologia permitem classificar termos por polaridade, intensidade e domínio. Um corpus pode ser analisado para identificar concentração de palavras associadas a medo, alegria, conflito ou cooperação.

### 4.6 Sistemas de recomendação

Produtos, documentos ou conteúdos podem ser relacionados por afinidade ontológica. Por exemplo, materiais didáticos sobre `biologia`, `saúde` e `ecossistema` podem ser sugeridos a partir de proximidade conceitual, com justificativas legíveis.

### 4.7 Pesquisa acadêmica

O TNU oferece uma base experimental para estudos sobre universais linguísticos, representação simbólica de significado, geometria conceitual e avaliação de modelos explicáveis. A ontologia versionada permite repetir experimentos e comparar revisões.

## 5. Métricas e Validação

### Testes automatizados

A suíte unitária atual concluiu com `12 passed`. Ela verifica determinismo, formato do gauge, importação da ontologia, distância D, relações e ranking híbrido básico.

O executor em lote realizou 26 de 26 comandos com retorno bem-sucedido. Essa métrica demonstra estabilidade operacional do fluxo, mas não deve ser interpretada como 100% de precisão linguística: a qualidade semântica deve ser medida por pares ouro revisados por humanos, como Recall@1, MRR e precisão por idioma.

### Comparação legado versus híbrido

Os relatórios mostram a contribuição da Camada D em pares essenciais:

| Consulta | Legado | Híbrido |
|---|---|---|
| `água` pt→en | pode priorizar forma estrutural | `water`, D=0, `same` |
| `amor` pt→en | resultado estruturalmente próximo | `love`, D=0, `same` |
| `casa` pt→en | resultado estruturalmente próximo | `house`, D=0, `same` |
| `luz` pt→en | sem ontologia anterior | `light`, D=0, `same` |
| `carro` pt→en | sem ontologia anterior | `car`, D=0, `same` |

O caso `comida → foodstuff` possui D=0 e representa alimento em sentido geral. A escolha entre `food` e `foodstuff` pode ser refinada por preferência lexical, frequência e anotações de registro de uso.

## 6. Limitações e Melhorias Futuras

### Cobertura multilíngue

Grande parte da expansão industrial foi adicionada inicialmente em português. A tradução automática em massa não deve ser aceita sem desambiguação por sentido. O fluxo Wikidata já registra QID, rótulos e confiança, mas a disponibilidade da API e a revisão humana ainda são necessárias antes de incorporar candidatos ao JSON principal.

### Dados e cobertura lexical

Um sentido somente pode aparecer em uma busca se suas palavras também estiverem disponíveis no banco `gama.db`. A próxima etapa deve sincronizar léxicos ontológicos aprovados com candidatos do banco, preservando procedência e histórico de importação.

### Avaliação científica

É recomendável criar um conjunto ouro multilíngue, com traduções exatas, relações e pares negativos. Métricas como Recall@1, MRR, precisão por domínio, taxa de cobertura e tempo de resposta devem complementar a execução em lote.

### Interface web e API REST

O projeto já possui uma aplicação Flask inicial. Evoluções recomendadas incluem autenticação, edição ontológica com revisão, fila de importação, cache de consultas, documentação OpenAPI e painéis de qualidade por idioma e domínio.

### Camadas B e C

A projeção B ainda contém sinais provisórios, e C precisa de cobertura de classes gramaticais. A curadoria dessas camadas reduzirá empates e melhorará o ranking entre candidatos que já possuem D=0.

## 7. Conclusão

O TNU demonstra que uma abordagem simbólica, determinística e auditável pode apoiar a comparação semântica entre idiomas. Sua contribuição central é combinar sinais estruturais com uma ontologia versionada, permitindo explicar por que uma tradução foi escolhida. A Camada D corrigiu limitações importantes do modo legado e tornou o sistema uma plataforma promissora para tradução semântica, educação, PLN explicável e pesquisa acadêmica. O avanço para cobertura multilíngue curada e avaliação por pares ouro é o passo decisivo para consolidar o TNU como ferramenta de pesquisa e aplicação.

---

Relatório gerado pelo TNU - Tradutor Numérico Universal. © 2026 Jéssica Freitas.
