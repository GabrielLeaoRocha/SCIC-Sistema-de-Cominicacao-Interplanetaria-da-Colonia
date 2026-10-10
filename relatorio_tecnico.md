# Relatório técnico — SCIC / Aurora Siger

## 1. Contexto e objetivo

O Sistema de Comunicação Interplanetária da Colônia (SCIC) é um protótipo didático para apoiar a operação da *Aurora Siger*. Ele organiza medições simuladas de oito módulos, estima a latência de comunicação, mede a diferença entre previsão e observação, ordena alertas críticos e permite localizar registros pelo prefixo do código de sensor. O sistema **não controla equipamentos** nem substitui decisões humanas.

## 2. Base de dados e hipóteses

O arquivo `dados_aurora_siger.csv` contém **120 registros**: oito módulos em cada um de 15 ciclos. `gerar_dados.py` reproduz a mesma base com semente aleatória fixa `2026`. Foram inseridas flutuações normais e incidentes simulados em ciclos específicos para testar a capacidade de detectar erros grandes e priorizar alertas. Os números e limiares são ilustrativos; não representam medições reais ou limites de segurança de uma missão.

| Campo | Significado |
| --- | --- |
| `ciclo` | Ordem temporal discreta, sem equivalência definida em minutos ou horas. |
| `modulo`, `tipo_modulo`, `codigo_sensor` | Identificação da origem da medição. Um código se repete em ciclos diferentes. |
| `fila_mensagens` | Quantidade simulada de mensagens aguardando transmissão. |
| `qualidade_sinal_pct` | Indicador de qualidade entre 0 e 100%; é uma aproximação didática, não uma medida física padronizada. |
| `tensao_v`, `corrente_a` | Tensão em volts e corrente em amperes para estimar o consumo elétrico. |
| `latencia_observada_ms` | Tempo observado de comunicação, em milissegundos; alvo da previsão. |
| `status_operacional`, `mensagem_alerta` | Estado e mensagem simulados para apresentação e triagem. |

Ao carregar o CSV, o programa verifica colunas, campos vazios, tipos numéricos, faixas válidas, números finitos e duplicatas da combinação `(ciclo, codigo_sensor)`. Há **101 registros ativos, 18 em alerta e 1 em manutenção**. A criação da base foi feita com uma relação controlada entre fila, qualidade do sinal, potência, características do módulo e ruído; incidentes acrescentam atraso. Portanto, o desempenho do modelo se refere **somente a essa distribuição sintética**.

## 3. Indicadores e análise numérica

O indicador elétrico é a potência aproximada consumida pelo transmissor, **P = V × I**, em watts. No primeiro registro do sensor `COM-2A`, `12,24 V × 1,135 A = 13,8924 W`, exibidos como `13,89 W`. Esse valor não é a potência irradiada pela antena. Outros indicadores são a latência média por módulo, a quantidade de registros em alerta e o atraso positivo em relação à previsão.

Exemplos da base completa: o módulo **Laboratório** tem latência média de **93,13 ms** e quatro registros em alerta; **Controle** tem média de **67,60 ms** e nenhum registro em alerta. Esses números descrevem os dados simulados e não uma diferença causal entre módulos.

Para cada registro, o programa calcula:

\[
E_{abs} = |L_{observada} - L_{prevista}| \quad (ms)
\]

\[
E_{rel} = \frac{E_{abs}}{|L_{observada}|} \times 100 \quad (\%)
\]

A latência observada é a referência da comparação. Todos os valores da base são positivos; o código ainda trata denominador zero retornando um valor indefinido (`NaN`). Em um registro do teste, `COM-2A` no ciclo 13, a observação é **62,75 ms**, a previsão é **62,35 ms**, o erro absoluto é **0,40 ms** e o relativo é **0,64%** (valores exibidos com arredondamento). O maior erro absoluto da base ocorre em **Suporte Médico, ciclo 15**: observação **152,60 ms**, previsão **111,20 ms**, diferença **41,40 ms** ou **27,13%**. Esse caso demanda revisão mesmo quando as médias agregadas parecem boas.

Os cálculos usam `float`, sujeito à representação finita em ponto flutuante. O programa arredonda somente para exibir; arredondar a previsão antes de calcular o erro alteraria o resultado. Diferenças centesimais de exibição não devem ser confundidas com falha operacional. Para este exercício, um atraso positivo de **18 ms** frente à previsão já pode entrar na triagem; a equipe da missão teria de definir um limite aceitável a partir de requisitos reais de cada serviço, além de conferir a qualidade do sensor.

## 4. Previsão e avaliação

O alvo é `latencia_observada_ms`. Os três recursos são `fila_mensagens`, `qualidade_sinal_pct` e `potencia_w` calculada antes da previsão. O programa ajusta uma **regressão linear múltipla** por mínimos quadrados, com padronização das entradas usando apenas a média e o desvio calculados no treino. A solução do pequeno sistema linear usa eliminação de Gauss com pivoteamento parcial, conteúdo compatível com a Fase 6. O código não usa `status_operacional`, mensagens, prioridade ou erros como recurso, pois essas informações podem depender da latência observada e causariam vazamento de dados.

A divisão segue a ordem dos ciclos: **treino 1–9 (72 registros)**, **validação 10–12 (24)** e **teste 13–15 (24)**. O modelo é ajustado só no treino; a validação serve para inspecionar seu comportamento antes do teste; o teste é a avaliação final. Não houve escolha de parâmetros com o teste. O **baseline** prevê em todos os registros a média da latência do treino. Assim, a comparação exige que a regressão ofereça valor além de uma estimativa constante.

| Conjunto | Método | MAE (ms) | MSE (ms²) | RMSE (ms) | R² |
| --- | --- | ---: | ---: | ---: | ---: |
| Validação | Regressão | 6,30 | 95,53 | 9,77 | 0,829 |
| Validação | Baseline | 17,71 | 566,66 | 23,80 | -0,013 |
| Teste | Regressão | **9,05** | **188,39** | **13,73** | **0,843** |
| Teste | Baseline | 26,61 | 1.370,04 | 37,01 | -0,142 |

**MAE** é a média dos erros absolutos, fácil de interpretar em ms. **MSE** eleva os erros ao quadrado e tem unidade ms². **RMSE** é a raiz do MSE, volta a ms e penaliza mais os desvios grandes. **R²** compara o ajuste com a média do conjunto avaliado; pode ser negativo, como no baseline, e não prova causalidade nem confiabilidade em dados reais. No teste, a regressão supera o baseline nas quatro medidas, mas RMSE maior que MAE e o incidente de 41,40 ms mostram que uma previsão média boa não elimina eventos críticos. AIC, BIC, Grid Search e Random Search não foram usados porque há apenas um modelo simples, sem seleção de hiperparâmetros.

## 5. Heap e priorização de alertas

Cada alerta do ciclo mais recente recebe uma pontuação didática:

- `+3` se o status é `alerta`;
- `+3` se o módulo é essencial (Comunicação, Habitação, Suporte Médico, Armazenamento, Energia ou Controle);
- `+0` a `+4` conforme o atraso positivo em blocos de 10 ms;
- `+2` se a qualidade do sinal é inferior a 55%.

Um registro entra na fila quando tem status `alerta`, atraso de pelo menos 18 ms ou sinal abaixo de 55%. O `heapq` da biblioteca padrão é um *min-heap*; o programa usa pontuação e atraso negativos para retirar primeiro o mais urgente. Havendo empate, usa ciclo e código para obter ordem estável. No **ciclo 15**, a ordem calculada é: **MED-2E (10 pontos, +41,40 ms)**, **ENE-30 (9 pontos, +32,98 ms)**, **COM-2A (8 pontos, +22,43 ms)**. Os três requerem verificação humana. O heap garante a raiz mais prioritária, sem ordenar todos os elementos internamente; consultar a raiz custa `O(1)` e inserir/retirar custa `O(log n)`, evitando procurar o máximo em uma lista a cada atendimento. A pontuação é uma regra transparente de triagem, não uma classificação médica ou de segurança validada.

## 6. Trie e consulta por prefixo

Os códigos de sensor são inseridos caractere por caractere em uma *trie*. A busca por `COM` retorna os **15 registros** do código `COM-2A`; `XXX` retorna nenhum. A entrada é normalizada para maiúsculas. Percorrer o prefixo custa `O(L)`, com `L` caracteres, e listar os resultados tem custo adicional proporcional à quantidade encontrada. A trie permite consultas por prefixo sem examinar todos os códigos a cada busca, ao custo de nós extras na memória. A opção de consulta comum do menu também permite buscar um nome ou código por substring, para comparar os dois tipos de consulta.

## 7. Dispositivos, bases numéricas e eletricidade

No cenário, sensores de enlace e medidores de tensão/corrente forneceriam os dados de **entrada**. Terminal e relatório seriam **saídas** para operadores. Rede cabeada, USB e Wi-Fi são exemplos conceituais de interface; nenhuma conexão física é implementada. O identificador `COM-2A` contém o valor hexadecimal `2A`, equivalente a **42 em decimal** e **00101010 em binário**. Trata-se de um código de identificação, não de uma leitura de tensão ou de um endereço real. A equação `P = V × I` liga as grandezas elétricas à operação de comunicação; a lei de Ohm (`V = R × I`) poderia estimar resistência equivalente de um circuito simples, mas não é necessária para prever a latência desta base.

## 8. Gerenciamento inteligente da comunicação

No protótipo, a coleta simulada representa sensores e medidores inteligentes. O histórico por ciclos permite perceber aumentos de latência e comparar com uma previsão. A **automação** calcula indicadores e organiza a fila para que a equipe veja primeiro os casos mais críticos, como Suporte Médico no ciclo 15. Uma central real precisaria monitoramento contínuo, registro confiável e confirmação do estado do sensor antes de agir.

Um **enlace redundante** poderia sustentar a comunicação quando o principal falha; o SCIC indica onde verificar a necessidade, sem controlar a comutação. O armazenamento do histórico e a tendência de atrasos ajudariam a planejar **manutenção preditiva**, mas esta base curta não demonstra que uma falha futura possa ser prevista com confiabilidade. Uma **rede inteligente de comunicação** coordenaria medições, análise e decisões. A **microrrede elétrica** da colônia, por sua vez, poderia considerar o consumo aproximado dos transmissores para manter módulos essenciais energizados. Essa relação entre energia e comunicação é conceitual: não há SCADA, IoT, telemetria real ou microrrede implementada.

## 9. Impacto social, cultural e sustentável

O uso eficiente da comunicação pode reduzir retransmissões desnecessárias e consumo de energia, apoiando a **sustentabilidade**. A potência estimada ajuda a pensar nesse custo, mas o SCIC ainda não mede energia acumulada nem prova economia. A regra de prioridade deve ser pública e revisável para evitar desperdício e para que a comunidade compreenda por que um módulo foi atendido primeiro.

Conhecimentos de povos indígenas sobre cuidado com território, ciclos e uso responsável de recursos podem inspirar uma governança mais atenta aos limites ambientais. É preciso reconhecer a diversidade e o protagonismo desses povos, sem tratar saberes distintos como uma solução técnica única ou apropriar conceitos sem contexto. A diversidade cultural, incluindo perspectivas afro-brasileiras e indígenas, também importa na linguagem e nas decisões do sistema: mensagens claras e respeitosas, acesso compreensível e revisão de regras ajudam a evitar exclusão e vieses.

A priorização automática é **apoio**, não ordem definitiva. Pessoas responsáveis devem validar medições, contexto e consequências antes de interromper serviços, especialmente os essenciais. Registrar a pontuação, a causa do alerta e a decisão humana favorece transparência e prestação de contas. Como a base é artificial, nenhuma conclusão sobre pessoas ou comunidades deve ser inferida dos seus números.

## 10. Limitações e melhorias possíveis

Os dados são sintéticos, os ciclos não têm duração física, os incidentes foram programados e as faixas de alerta não foram calibradas. O modelo linear pode falhar com mudanças de ambiente, atrasos não lineares, sensores defeituosos ou novos módulos. A amostra pequena e a repetição de módulos ao longo dos ciclos também limitam generalização; o teste temporal reduz vazamento do futuro, mas não simula uma missão real. O consumo elétrico `V × I` não mede eficiência de transmissão. A trie usa memória adicional e o heap só fornece a próxima prioridade, não uma explicação automática da causa física.

Como evolução, seria possível ampliar ciclos simulados, registrar origem e confiabilidade das medições, recalibrar limiares por tipo de módulo, comparar períodos adicionais e avaliar a estabilidade do modelo. Uma integração real exigiria validação de engenharia, segurança, governança de dados e supervisão humana. Nenhum desses itens é necessário para este protótipo da Fase 6.

## 11. Como reproduzir

Na pasta extraída, execute `python codigo_fonte.py --demo` para ver o fluxo completo ou `python codigo_fonte.py` para usar o menu. Para regenerar a base exatamente, execute `python gerar_dados.py` antes do programa. Os resultados numéricos acima correspondem à base incluída nesta entrega. As verificações automatizadas podem ser executadas com `python -m unittest discover -s tests -v` quando a pasta `tests` estiver presente no repositório.
