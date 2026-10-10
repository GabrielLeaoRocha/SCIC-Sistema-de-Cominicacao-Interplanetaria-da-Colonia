# Roteiro de apresentação — máximo de 5 minutos

Gravar a tela do terminal executando o projeto real. Deixar o relatório aberto como apoio, se desejado, mas mostrar as saídas do Python. Meta: **4min40s** para haver margem de edição.

| Tempo | Fala e demonstração |
| --- | --- |
| 0:00–0:30 | Apresentar o SCIC e a comunicação da Aurora Siger: oito módulos fictícios, análise da latência, apoio à decisão. Dizer que os dados são simulados. |
| 0:30–1:10 | Rodar `python codigo_fonte.py --demo`. Mostrar a leitura do CSV, 120 registros, status e consulta `COM-2A`. Explicar entrada e organização dos dados. |
| 1:10–1:55 | Mostrar indicadores por módulo e potência `P=V×I`. Citar erro absoluto e relativo, com o exemplo de 0,40 ms/0,64% no teste e o caso crítico de 41,40 ms/27,13%. Explicar arredondamento e ponto flutuante. |
| 1:55–2:45 | Explicar a regressão linear simples, recursos utilizados e divisão temporal treino/validação/teste. Mostrar as quatro métricas no teste: MAE 9,05 ms, MSE 188,39 ms², RMSE 13,73 ms e R² 0,843; comparar com MAE 26,61 ms do baseline. Dizer que erros individuais exigem atenção. |
| 2:45–3:25 | Mostrar a fila heap e a ordem MED-2E, ENE-30, COM-2A. Explicar a regra de pontos e a retirada do mais urgente. Mostrar a trie com prefixo `COM` e resultado `COM-2A`. |
| 3:25–4:10 | Explicar sensores/medidores como entrada, terminal como saída, interfaces conceituais, `42₁₀ = 00101010₂ = 2A₁₆` e consumo elétrico aproximado. Relacionar monitoramento, redundância, manutenção preditiva, rede inteligente e microrrede aos alertas observados. |
| 4:10–4:40 | Mostrar análise final. Comentar sustentabilidade, transparência e revisão humana, além do limite da base sintética. Encerrar. |

## Checklist antes de publicar

- O vídeo mostra **o Python em execução**, não apenas slides ou código parado.
- Áudio compreensível, tela legível e duração **menor ou igual a 5:00**.
- Apresenta todos os tópicos técnicos listados acima e a relação com a missão.
- Visibilidade no YouTube: **Não listado**.
- Link testado sem estar conectado à conta que publicou e inserido em `link_video.txt`.
