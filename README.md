# Projeto Base — CI/CD com GitHub Actions

Este projeto foi preparado para uma atividade prática de construção de uma esteira de CI/CD.

## Estrutura

- `app/pipeline.py`: script Python principal
- `data/sales.csv`: arquivo de entrada
- `tests/test_pipeline.py`: testes automatizados
- `requirements.txt`: dependências do projeto
- `.github/workflows/`: pasta onde o workflow deverá ser criado pelos alunos

## Objetivo do projeto

O script lê um arquivo CSV com vendas, valida os dados e gera um resumo com:

- total de vendas
- média de vendas
- total de pedidos

## Como executar localmente

### 1. Criar ambiente virtual

```bash
python -m venv .venv
```

### 2. Ativar ambiente virtual

No Linux/macOS:

```bash
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Executar o script

```bash
python app/pipeline.py
```

### 5. Executar os testes

```bash
pytest
```

## Chamada de API no CI/CD

O workflow em `.github/workflows/ci.yml` faz uma chamada `POST` ao final da execução, desde que o secret `CI_API_URL` esteja configurado no GitHub.

Secrets esperados:

- `CI_API_URL`: endpoint da API que receberá a notificação
- `CI_API_TOKEN`: token Bearer enviado no header `Authorization`

## Resultado esperado

Após executar o script, será criado o arquivo:

```text
output/summary.csv
```

## Esteira de CI

O workflow `.github/workflows/ci.yml` roda em `push` e `pull_request` na `main`,
e tambem sob demanda via `workflow_dispatch`. O job `validate` executa, nesta ordem:

| Step | Comando |
| --- | --- |
| flake8 - Linting | `python -m flake8 app` |
| mypy - Type checking | `python -m mypy app` |
| bandit - Security checks | `python -m bandit -r app` |
| radon - Complexity report | `python -m radon cc app -a` |
| Pytest - Run tests | `python -m pytest tests -v` |
| Run pipeline | `python app/pipeline.py` |

Ao final, o conteudo de `output/` e publicado como artifact `summary`, e o step
`Notify external API` faz o `POST` para `CI_API_URL`. Esse ultimo step so executa
se o secret existir (`if: success() && env.CI_API_URL != ''`); sem ele, aparece
como *skipped* e nao quebra a esteira.
