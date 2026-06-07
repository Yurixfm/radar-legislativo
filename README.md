# Radar Legislativo

Projeto Python para um desafio de monitoramento legislativo.

A ideia inicial e organizar proposicoes, filtrar por temas de interesse e gerar uma prioridade simples para acompanhamento.

## Requisitos

- Python 3.11+

## Como rodar

```powershell
python -m radar_legislativo.cli
```

Durante o desenvolvimento, rode a partir da raiz usando:

```powershell
$env:PYTHONPATH="src"
python -m radar_legislativo.cli
```

## Testes

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## Estrutura

```text
src/radar_legislativo/
  cli.py       Entrada de linha de comando
  models.py    Modelos principais do dominio
  radar.py     Regras de filtro e priorizacao
tests/
  test_radar.py
```

