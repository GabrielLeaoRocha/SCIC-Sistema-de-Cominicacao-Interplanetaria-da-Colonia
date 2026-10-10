# SCIC — Sistema de Comunicação Interplanetária da Colônia

Protótipo da Fase 6 para a colônia fictícia **Aurora Siger**. O sistema lê dados simulados de módulos, calcula indicadores e erros numéricos, estima latência com regressão linear, compara a previsão com um baseline, prioriza alertas usando heap e busca códigos de sensor por prefixo usando trie.

## Requisitos para executar

- Python **3.10 ou superior**.
- Nenhuma biblioteca externa, rede, API ou equipamento físico. O projeto usa apenas a biblioteca padrão do Python.
- Terminal capaz de mostrar UTF-8. No Windows PowerShell, se os acentos aparecerem incorretos, execute `$env:PYTHONIOENCODING='utf-8'` antes do programa.

## Arquivos

| Arquivo | Finalidade |
| --- | --- |
| `codigo_fonte.py` | Programa principal e menu. |
| `dados_aurora_siger.csv` | 120 medições simuladas, oito módulos e 15 ciclos. |
| `gerar_dados.py` | Recria o CSV com semente fixa 2026. |
| `relatorio_tecnico.md` | Métodos, resultados e reflexão exigidos na atividade. |
| `link_video.txt` | Link da apresentação; deve ser preenchido após publicar o vídeo. |
| `roteiro_video.md` | Guia de gravação em menos de cinco minutos. |
| `empacotar.py` | Gera o `.zip` final após verificar o link do vídeo. |
| `tests/test_scic.py` | Verificações automatizadas; incluídas no repositório. |

## Executar

Na pasta do projeto:

```powershell
python codigo_fonte.py
```

Para uma demonstração contínua das funcionalidades, útil na gravação:

```powershell
python codigo_fonte.py --demo
```

Para ler outro CSV com o mesmo esquema:

```powershell
python codigo_fonte.py --dados caminho\para\dados.csv
```

Para reproduzir a base e executar os testes:

```powershell
python gerar_dados.py
python -m unittest discover -s tests -v
```

O programa resolve caminhos relativos ao seu próprio arquivo, então também funciona após extrair o `.zip` em outra pasta. Não é necessário instalar `pandas` ou `scikit-learn`: a regressão, as métricas, o heap e a trie estão implementados em Python padrão.

## Menu

1. Carregar e resumir a base.
2. Consultar registros por nome de módulo ou código.
3. Mostrar indicadores, potência elétrica e exemplos de erros.
4. Executar previsão e comparar MAE, MSE, RMSE e R² com o baseline.
5. Mostrar alertas do ciclo mais recente na ordem retirada do heap.
6. Buscar código de sensor por prefixo na trie.
7. Relacionar o protótipo a entrada/saída, bases numéricas e eletricidade.
8. Exibir a análise final.
0. Sair.

Exemplo de uso: opção `6`, prefixo `COM` → 15 registros do código `COM-2A`; opção `5` → no ciclo 15, `MED-2E`, `ENE-30` e `COM-2A` nessa ordem. Os valores são didáticos e não representam uma rede real.

## Método resumido

O modelo prevê latência (ms) usando fila de mensagens, qualidade do sinal e potência elétrica `V × I`. Treino: ciclos 1–9; validação: 10–12; teste: 13–15. O baseline é a média da latência do treino. A base e os resultados são explicados em [relatorio_tecnico.md](relatorio_tecnico.md). Para fins de avaliação, o arquivo principal solicitado é **`codigo_fonte.py`**.

## Preparar a entrega

1. Grave a demonstração real do programa em vídeo de **até 5 minutos**. Consulte [roteiro_video.md](roteiro_video.md).
2. Publique no YouTube como **Não listado** e confira o link em uma janela sem login.
3. Substitua o texto provisório de `link_video.txt` pela URL do vídeo, em uma linha.
4. Execute `python empacotar.py`. O script rejeita o texto provisório e cria `SCIC_Aurora_Siger.zip` na pasta acima do projeto.
5. Confira o conteúdo extraído do pacote e envie o `.zip` e o link pela plataforma da atividade.

O pacote final inclui os cinco arquivos obrigatórios com os nomes exatos, além do gerador da base. A publicação do vídeo e o envio devem ser realizados pela equipe.
