# TNU-Site

Interface web do Tradutor Numérico Universal. Este diretório usa os módulos e
o `gama.db` do diretório-pai; não cria cópias dos dados.

## Executar

```powershell
cd TNU-Site
..\venv\Scripts\python.exe -m pip install -r requirements.txt
..\venv\Scripts\python.exe app.py
```

Abra `http://127.0.0.1:5000`.

## API REST

| Endpoint | Método | Função |
|---|---|---|
| `/api/search` | POST | Busca híbrida (`query`, `lang_from`, `lang_to`, `top_k`). |
| `/api/search_legacy` | POST | Busca legada sem D. |
| `/api/ontology` | GET | Sentidos, vetores e relações. |
| `/api/ontology/import` | POST | Importa o JSON no SQLite. |
| `/api/stats` | GET | Métricas do corpus. |
| `/api/ruler?concept=agua` | GET | Pontos da régua semântica. |
| `/api/export` | POST | Exporta CSV, JSON ou Markdown. |
| `/api/tutorial/status` | GET | Estado do onboarding. |
| `/api/tutorial/complete` | POST | Persiste o onboarding. |

O PDF é gerado no navegador por jsPDF. Bootstrap, Chart.js, AOS e Font Awesome
são carregados por CDN.
