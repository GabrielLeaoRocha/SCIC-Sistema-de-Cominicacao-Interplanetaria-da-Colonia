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

O menu mostra a quantidade de registros, módulos e ciclos já carregados e agrupa as opções por tarefa:

- **Dados e consultas:** `[1]` visão geral da base; `[2]` consulta por módulo ou código de sensor.
- **Análise:** `[3]` indicadores e erros numéricos; `[4]` previsão e métricas.
- **Alertas e busca:** `[5]` prioridade com heap; `[6]` busca de prefixo com trie.
- **Referência:** `[7]` dispositivos, bases numéricas e eletricidade; `[8]` análise final.
- `[0]` encerra o programa.

Digite o número indicado entre colchetes e pressione Enter. Para a consulta comum, informe parte do nome do módulo ou código; para a trie, informe um prefixo como `COM`.

Exemplo de uso: opção `6`, prefixo `COM` → 15 registros do código `COM-2A`; opção `5` → no ciclo 15, `MED-2E`, `ENE-30` e `COM-2A` nessa ordem. Os valores são didáticos e não representam uma rede real.

## Método resumido

O modelo prevê latência (ms) usando fila de mensagens, qualidade do sinal e potência elétrica `V × I`. Treino: ciclos 1–9; validação: 10–12; teste: 13–15. O baseline é a média da latência do treino. A base e os resultados são explicados em [relatorio_tecnico.md](relatorio_tecnico.md). Para fins de avaliação, o arquivo principal solicitado é **`codigo_fonte.py`**.

## Preparar a entrega

O vídeo de apresentação está disponível no YouTube: <https://youtu.be/e76cJT13JUg>.

1. Execute `python empacotar.py`. O script cria `SCIC_Aurora_Siger.zip` na pasta acima do projeto.
2. Confira o conteúdo extraído do pacote.
3. Envie o `.zip` e informe o link do vídeo na plataforma da atividade.

O pacote final inclui os cinco arquivos obrigatórios com os nomes exatos, além do gerador da base. A publicação do vídeo e o envio devem ser realizados pela equipe.
