"""SCIC: análise didática da comunicação da colônia Aurora Siger.

Uso: python codigo_fonte.py [--demo] [--dados caminho/do/arquivo.csv]
Somente a biblioteca padrão do Python é necessária.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ARQUIVO_PADRAO = Path(__file__).resolve().parent / "dados_aurora_siger.csv"
COLUNAS = {
    "ciclo", "modulo", "tipo_modulo", "codigo_sensor", "fila_mensagens",
    "qualidade_sinal_pct", "tensao_v", "corrente_a", "latencia_observada_ms",
    "status_operacional", "mensagem_alerta",
}
MODULOS_ESSENCIAIS = {"COM-2A", "HAB-2B", "MED-2E", "DAD-2F", "ENE-30", "CTR-31"}


@dataclass(frozen=True)
class Registro:
    ciclo: int
    modulo: str
    tipo_modulo: str
    codigo_sensor: str
    fila_mensagens: int
    qualidade_sinal_pct: float
    tensao_v: float
    corrente_a: float
    latencia_observada_ms: float
    status_operacional: str
    mensagem_alerta: str

    @property
    def potencia_w(self) -> float:
        """Potência elétrica aproximada consumida: P = V × I."""
        return self.tensao_v * self.corrente_a

    @property
    def recursos(self) -> tuple[float, float, float]:
        # Apenas grandezas conhecidas antes de observar a latência entram no modelo.
        return (float(self.fila_mensagens), self.qualidade_sinal_pct, self.potencia_w)


def carregar_dados(caminho: Path = ARQUIVO_PADRAO) -> list[Registro]:
    """Lê e valida o CSV antes de qualquer cálculo."""
    if not caminho.is_file():
        raise ValueError(f"Arquivo não encontrado: {caminho}")
    registros: list[Registro] = []
    identificadores: set[tuple[int, str]] = set()
    try:
        with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            if not leitor.fieldnames or not COLUNAS.issubset(leitor.fieldnames):
                ausentes = sorted(COLUNAS - set(leitor.fieldnames or []))
                raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(ausentes)}")
            for linha, bruto in enumerate(leitor, start=2):
                try:
                    if any(bruto[campo] is None or not bruto[campo].strip() for campo in COLUNAS):
                        raise ValueError("campo obrigatório vazio")
                    registro = Registro(
                        ciclo=int(bruto["ciclo"]),
                        modulo=bruto["modulo"].strip(),
                        tipo_modulo=bruto["tipo_modulo"].strip(),
                        codigo_sensor=bruto["codigo_sensor"].strip().upper(),
                        fila_mensagens=int(bruto["fila_mensagens"]),
                        qualidade_sinal_pct=float(bruto["qualidade_sinal_pct"]),
                        tensao_v=float(bruto["tensao_v"]),
                        corrente_a=float(bruto["corrente_a"]),
                        latencia_observada_ms=float(bruto["latencia_observada_ms"]),
                        status_operacional=bruto["status_operacional"].strip().lower(),
                        mensagem_alerta=bruto["mensagem_alerta"].strip(),
                    )
                    numeros = (registro.qualidade_sinal_pct, registro.tensao_v,
                               registro.corrente_a, registro.latencia_observada_ms)
                    if not all(math.isfinite(valor) for valor in numeros):
                        raise ValueError("número não finito")
                    if not (registro.ciclo > 0 and registro.fila_mensagens >= 0
                            and 0 <= registro.qualidade_sinal_pct <= 100
                            and registro.tensao_v > 0 and registro.corrente_a > 0
                            and registro.latencia_observada_ms > 0):
                        raise ValueError("valor numérico fora da faixa")
                    if registro.status_operacional not in {"ativo", "alerta", "manutencao"}:
                        raise ValueError("status operacional inválido")
                    chave = (registro.ciclo, registro.codigo_sensor)
                    if chave in identificadores:
                        raise ValueError("ciclo e código de sensor duplicados")
                    identificadores.add(chave)
                    registros.append(registro)
                except (TypeError, ValueError, AttributeError) as erro:
                    raise ValueError(f"Linha {linha}: {erro}") from erro
    except UnicodeError as erro:
        raise ValueError("O CSV deve estar codificado em UTF-8") from erro
    if not registros:
        raise ValueError("O CSV não contém registros")
    return registros


def separar_ciclos(registros: list[Registro]) -> tuple[list[Registro], list[Registro], list[Registro]]:
    """Treino nos primeiros 60%, validação nos 20% seguintes, teste nos últimos 20%."""
    ciclos = sorted({registro.ciclo for registro in registros})
    if len(ciclos) < 5:
        raise ValueError("São necessários pelo menos 5 ciclos para treino, validação e teste")
    limite_treino = max(1, int(len(ciclos) * 0.6))
    limite_validacao = max(limite_treino + 1, int(len(ciclos) * 0.8))
    conjuntos = (set(ciclos[:limite_treino]), set(ciclos[limite_treino:limite_validacao]),
                set(ciclos[limite_validacao:]))
    partes = tuple([registro for registro in registros if registro.ciclo in grupo]
                  for grupo in conjuntos)
    if any(not parte for parte in partes):
        raise ValueError("Treino, validação e teste precisam conter registros")
    return partes  # type: ignore[return-value]


def resolver_sistema(matriz: list[list[float]], vetor: list[float]) -> list[float]:
    """Eliminação de Gauss com pivoteamento parcial para o ajuste linear."""
    ordem = len(vetor)
    ampliada = [linha[:] + [valor] for linha, valor in zip(matriz, vetor)]
    for coluna in range(ordem):
        pivo = max(range(coluna, ordem), key=lambda i: abs(ampliada[i][coluna]))
        if abs(ampliada[pivo][coluna]) < 1e-10:
            raise ValueError("Dados insuficientes ou recursos linearmente dependentes")
        ampliada[coluna], ampliada[pivo] = ampliada[pivo], ampliada[coluna]
        escala = ampliada[coluna][coluna]
        ampliada[coluna] = [valor / escala for valor in ampliada[coluna]]
        for linha in range(ordem):
            if linha != coluna:
                fator = ampliada[linha][coluna]
                ampliada[linha] = [a - fator * b for a, b in zip(ampliada[linha], ampliada[coluna])]
    return [linha[-1] for linha in ampliada]


@dataclass(frozen=True)
class ModeloLinear:
    medias: tuple[float, float, float]
    escalas: tuple[float, float, float]
    coeficientes: tuple[float, float, float, float]

    def prever(self, registro: Registro) -> float:
        normalizados = [(valor - media) / escala for valor, media, escala
                        in zip(registro.recursos, self.medias, self.escalas)]
        return self.coeficientes[0] + sum(c * x for c, x in zip(self.coeficientes[1:], normalizados))


def treinar_modelo(treino: list[Registro]) -> ModeloLinear:
    """Ajusta regressão linear múltipla por mínimos quadrados no treino apenas."""
    colunas = list(zip(*(registro.recursos for registro in treino)))
    medias = tuple(sum(coluna) / len(coluna) for coluna in colunas)
    escalas = tuple(math.sqrt(sum((x - media) ** 2 for x in coluna) / len(coluna))
                   for coluna, media in zip(colunas, medias))
    if any(escala < 1e-10 for escala in escalas):
        raise ValueError("Um recurso do treino não varia entre os registros")
    x = [[1.0] + [(valor - media) / escala for valor, media, escala
                  in zip(registro.recursos, medias, escalas)] for registro in treino]
    y = [registro.latencia_observada_ms for registro in treino]
    ordem = len(x[0])
    xtx = [[sum(linha[i] * linha[j] for linha in x) for j in range(ordem)]
           for i in range(ordem)]
    xty = [sum(linha[i] * alvo for linha, alvo in zip(x, y)) for i in range(ordem)]
    coeficientes = tuple(resolver_sistema(xtx, xty))
    return ModeloLinear(medias, escalas, coeficientes)  # type: ignore[arg-type]


def metricas(observados: list[float], previstos: list[float]) -> dict[str, float]:
    if len(observados) != len(previstos) or not observados:
        raise ValueError("Métricas exigem vetores não vazios de mesmo tamanho")
    erros = [real - previsto for real, previsto in zip(observados, previstos)]
    mae = sum(abs(erro) for erro in erros) / len(erros)
    mse = sum(erro ** 2 for erro in erros) / len(erros)
    media = sum(observados) / len(observados)
    variacao = sum((valor - media) ** 2 for valor in observados)
    r2 = 1 - sum(erro ** 2 for erro in erros) / variacao if variacao else float("nan")
    return {"MAE": mae, "MSE": mse, "RMSE": math.sqrt(mse), "R2": r2}


def avaliar(parte: list[Registro], modelo: ModeloLinear, media_treino: float) -> dict[str, dict[str, float]]:
    reais = [r.latencia_observada_ms for r in parte]
    return {
        "modelo": metricas(reais, [modelo.prever(r) for r in parte]),
        "baseline": metricas(reais, [media_treino] * len(parte)),
    }


def erro_numerico(registro: Registro, previsao: float) -> tuple[float, float]:
    absoluto = abs(registro.latencia_observada_ms - previsao)
    relativo = absoluto / abs(registro.latencia_observada_ms) * 100 if registro.latencia_observada_ms else float("nan")
    return absoluto, relativo


def pontuar_alerta(registro: Registro, previsao: float) -> tuple[int, float]:
    """Pontuação didática: status, módulo essencial, atraso e sinal degradado."""
    atraso = max(0.0, registro.latencia_observada_ms - previsao)
    pontos = (3 if registro.status_operacional == "alerta" else 0)
    pontos += 3 if registro.codigo_sensor in MODULOS_ESSENCIAIS else 0
    pontos += min(4, int(atraso // 10))
    pontos += 2 if registro.qualidade_sinal_pct < 55 else 0
    return pontos, atraso


def alertas_priorizados(registros: list[Registro], modelo: ModeloLinear, ciclo: int | None = None) -> list[tuple[int, float, Registro]]:
    """Usa min-heap com prioridade negativa; desempate por atraso e código."""
    ciclo = max(r.ciclo for r in registros) if ciclo is None else ciclo
    heap: list[tuple[int, float, int, str, Registro]] = []
    for registro in registros:
        if registro.ciclo != ciclo:
            continue
        pontos, atraso = pontuar_alerta(registro, modelo.prever(registro))
        if registro.status_operacional == "alerta" or atraso >= 18 or registro.qualidade_sinal_pct < 55:
            heapq.heappush(heap, (-pontos, -atraso, registro.ciclo, registro.codigo_sensor, registro))
    return [(-pontos, -atraso, registro) for pontos, atraso, _ciclo, _codigo, registro
            in (heapq.heappop(heap) for _ in range(len(heap)))]


class Trie:
    """Árvore de prefixos de códigos de sensor; terminais guardam registros."""

    def __init__(self) -> None:
        self.raiz: dict = {"filhos": {}, "registros": []}

    def inserir(self, codigo: str, registro: Registro) -> None:
        no = self.raiz
        for caractere in codigo.upper():
            no = no["filhos"].setdefault(caractere, {"filhos": {}, "registros": []})
        no["registros"].append(registro)

    def buscar_prefixo(self, prefixo: str) -> list[Registro]:
        if not prefixo.strip():
            return []
        no = self.raiz
        for caractere in prefixo.strip().upper():
            no = no["filhos"].get(caractere)
            if no is None:
                return []
        encontrados: list[Registro] = []
        pilha = [no]
        while pilha:
            atual = pilha.pop()
            encontrados.extend(atual["registros"])
            pilha.extend(atual["filhos"].values())
        return sorted(encontrados, key=lambda r: (r.codigo_sensor, r.ciclo))


def construir_trie(registros: list[Registro]) -> Trie:
    trie = Trie()
    for registro in registros:
        trie.inserir(registro.codigo_sensor, registro)
    return trie


def imprimir_resumo(registros: list[Registro]) -> None:
    print(f"\nBase: {len(registros)} registros, {len({r.modulo for r in registros})} módulos, "
          f"ciclos {min(r.ciclo for r in registros)}–{max(r.ciclo for r in registros)}.")
    contagens = defaultdict(int)
    for registro in registros:
        contagens[registro.status_operacional] += 1
    print("Status: " + ", ".join(f"{status}={contagens[status]}" for status in ("ativo", "alerta", "manutencao")))
    print("Exemplo: ciclo | módulo | sensor | latência (ms) | potência (W)")
    for registro in registros[:5]:
        print(f"  {registro.ciclo:>2} | {registro.modulo:<16} | {registro.codigo_sensor:<6} | "
              f"{registro.latencia_observada_ms:>8.2f} | {registro.potencia_w:>6.2f}")


def imprimir_consulta(registros: list[Registro], termo: str) -> None:
    termo = termo.strip().casefold()
    if not termo:
        print("Digite um nome de módulo ou código de sensor.")
        return
    encontrados = [r for r in registros if termo in r.modulo.casefold() or termo in r.codigo_sensor.casefold()]
    print(f"\nConsulta: {len(encontrados)} registro(s); mostrando até 10.")
    for r in encontrados[:10]:
        print(f"  ciclo {r.ciclo:>2} | {r.modulo:<16} | {r.codigo_sensor} | "
              f"{r.latencia_observada_ms:>6.2f} ms | {r.status_operacional}")


def imprimir_indicadores(registros: list[Registro], modelo: ModeloLinear) -> None:
    grupos: dict[str, list[Registro]] = defaultdict(list)
    for registro in registros:
        grupos[registro.modulo].append(registro)
    print("\nMódulo             Latência média   Potência média   Alertas")
    for modulo, grupo in sorted(grupos.items()):
        media_lat = sum(r.latencia_observada_ms for r in grupo) / len(grupo)
        media_pot = sum(r.potencia_w for r in grupo) / len(grupo)
        n_alertas = sum(r.status_operacional == "alerta" for r in grupo)
        print(f"{modulo:<18} {media_lat:>8.2f} ms   {media_pot:>8.2f} W      {n_alertas:>2}")
    pior = max(registros, key=lambda r: erro_numerico(r, modelo.prever(r))[0])
    absoluto, relativo = erro_numerico(pior, modelo.prever(pior))
    print(f"Maior erro absoluto: ciclo {pior.ciclo}, {pior.modulo}: "
          f"observado {pior.latencia_observada_ms:.2f} ms; previsto {modelo.prever(pior):.2f} ms; "
          f"erro {absoluto:.2f} ms ({relativo:.2f}%).")


def imprimir_avaliacao(treino: list[Registro], validacao: list[Registro], teste: list[Registro],
                      modelo: ModeloLinear, media_treino: float) -> None:
    print(f"\nDivisão por ciclos: treino {min(r.ciclo for r in treino)}–{max(r.ciclo for r in treino)} "
          f"({len(treino)}); validação {min(r.ciclo for r in validacao)}–{max(r.ciclo for r in validacao)} "
          f"({len(validacao)}); teste {min(r.ciclo for r in teste)}–{max(r.ciclo for r in teste)} ({len(teste)}).")
    print("Conjunto    Método       MAE (ms)   MSE (ms²)  RMSE (ms)       R²")
    for nome, parte in (("Validação", validacao), ("Teste", teste)):
        for metodo, valores in avaliar(parte, modelo, media_treino).items():
            print(f"{nome:<11} {metodo:<10} {valores['MAE']:>8.2f}   {valores['MSE']:>9.2f}  "
                  f"{valores['RMSE']:>9.2f}  {valores['R2']:>7.3f}")
    exemplo = teste[0]
    previsto = modelo.prever(exemplo)
    absoluto, relativo = erro_numerico(exemplo, previsto)
    print(f"Exemplo do teste: {exemplo.codigo_sensor}, ciclo {exemplo.ciclo}: "
          f"observado={exemplo.latencia_observada_ms:.2f} ms, previsto={previsto:.2f} ms, "
          f"erro absoluto={absoluto:.2f} ms, relativo={relativo:.2f}%.")
    print("MAE/RMSE em ms; MSE em ms². RMSE enfatiza grandes desvios. R² não garante segurança operacional.")


def imprimir_alertas(registros: list[Registro], modelo: ModeloLinear) -> None:
    ciclo = max(r.ciclo for r in registros)
    print(f"\nFila de prioridade (heap), ciclo {ciclo}:")
    alertas = alertas_priorizados(registros, modelo, ciclo)
    if not alertas:
        print("  Nenhum alerta pelos limiares ilustrativos.")
    for posicao, (pontos, atraso, r) in enumerate(alertas, start=1):
        print(f"  {posicao}. {r.codigo_sensor} / {r.modulo}: {pontos} pontos, "
              f"atraso +{atraso:.2f} ms, status={r.status_operacional}")
    print("Critério: +3 status alerta, +3 módulo essencial, +0..4 atraso, +2 sinal <55%.")


def imprimir_prefixo(trie: Trie, prefixo: str) -> None:
    encontrados = trie.buscar_prefixo(prefixo)
    codigos = sorted({r.codigo_sensor for r in encontrados})
    print(f"\nPrefixo {prefixo!r}: {len(encontrados)} registro(s), códigos: "
          + (", ".join(codigos) if codigos else "nenhum"))
    for r in encontrados[-5:]:
        print(f"  {r.codigo_sensor} | ciclo {r.ciclo:>2} | {r.modulo}")


def imprimir_analise_final(registros: list[Registro], modelo: ModeloLinear,
                          teste: list[Registro], media_treino: float) -> None:
    resultados = avaliar(teste, modelo, media_treino)
    m, b = resultados["modelo"], resultados["baseline"]
    atual = alertas_priorizados(registros, modelo)
    print("\nANÁLISE FINAL")
    print(f"No teste, MAE do modelo: {m['MAE']:.2f} ms; baseline: {b['MAE']:.2f} ms. "
          f"RMSE do modelo: {m['RMSE']:.2f} ms; R²: {m['R2']:.3f}.")
    print(f"Ciclo mais recente: {len(atual)} alerta(s) para revisão humana. "
          + (f"Primeiro: {atual[0][2].codigo_sensor}." if atual else "Nenhum urgente."))
    print("Os limiares e dados são simulados. Confirmar medições antes de agir; avaliar "
          "redundância de enlace e consumo energético nos módulos essenciais.")


def imprimir_hardware(registros: list[Registro]) -> None:
    exemplo = next((r for r in registros if r.codigo_sensor == "COM-2A"), registros[0])
    print("\nEntrada: sensores e medidores simulados; saída: terminal e relatório.")
    print("Rede, USB ou Wi-Fi seriam interfaces possíveis, aqui apenas conceituais.")
    print("Exemplo de identificador: 42 (decimal) = 00101010 (binário) = 2A (hexadecimal).")
    print(f"{exemplo.codigo_sensor}: {exemplo.tensao_v:.2f} V × {exemplo.corrente_a:.3f} A "
          f"= {exemplo.potencia_w:.2f} W de consumo elétrico aproximado; "
          "isso não é a potência irradiada pela antena.")


def executar_demo(registros: list[Registro], modelo: ModeloLinear, treino: list[Registro],
                  validacao: list[Registro], teste: list[Registro], media_treino: float) -> None:
    print("=== DEMONSTRAÇÃO SCIC / AURORA SIGER ===")
    imprimir_resumo(registros)
    imprimir_consulta(registros, "COM-2A")
    imprimir_indicadores(registros, modelo)
    imprimir_avaliacao(treino, validacao, teste, modelo, media_treino)
    imprimir_alertas(registros, modelo)
    imprimir_prefixo(construir_trie(registros), "COM")
    imprimir_hardware(registros)
    imprimir_analise_final(registros, modelo, teste, media_treino)


def executar_menu(registros: list[Registro], modelo: ModeloLinear, treino: list[Registro],
                  validacao: list[Registro], teste: list[Registro], media_treino: float) -> None:
    trie = construir_trie(registros)
    opcoes = {
        "1": lambda: imprimir_resumo(registros),
        "2": lambda: imprimir_consulta(registros, input("Módulo ou código: ")),
        "3": lambda: imprimir_indicadores(registros, modelo),
        "4": lambda: imprimir_avaliacao(treino, validacao, teste, modelo, media_treino),
        "5": lambda: imprimir_alertas(registros, modelo),
        "6": lambda: imprimir_prefixo(trie, input("Prefixo do código: ")),
        "7": lambda: imprimir_hardware(registros),
        "8": lambda: imprimir_analise_final(registros, modelo, teste, media_treino),
    }

    def mostrar_menu() -> None:
        """Apresenta as opções agrupadas por tarefa em uma moldura simples."""
        largura = 58
        borda = "+" + "-" * (largura + 2) + "+"

        def linha(texto: str = "") -> str:
            return "| " + texto[:largura].ljust(largura) + " |"

        titulo = "SCIC | AURORA SIGER"
        subtitulo = "Sistema de Comunicação Interplanetária da Colônia"
        resumo = (f"Base carregada: {len(registros)} registros | "
                  f"{len({r.modulo for r in registros})} módulos | "
                  f"ciclos {min(r.ciclo for r in registros)}-{max(r.ciclo for r in registros)}")
        linhas = [
            borda,
            linha(titulo.center(largura)),
            linha(subtitulo.center(largura)),
            borda,
            linha(resumo),
            borda,
            linha("DADOS E CONSULTAS"),
            linha("  [1] Visão geral da base"),
            linha("  [2] Consultar módulo ou código de sensor"),
            linha("ANÁLISE"),
            linha("  [3] Indicadores, potência e erros numéricos"),
            linha("  [4] Previsão de latência e métricas"),
            linha("ALERTAS E BUSCA"),
            linha("  [5] Priorizar alertas (heap)"),
            linha("  [6] Buscar código por prefixo (trie)"),
            linha("REFERÊNCIA"),
            linha("  [7] Dispositivos, bases numéricas e eletricidade"),
            linha("  [8] Análise final da operação"),
            borda,
            linha("  [0] Sair"),
            borda,
        ]
        print("\n" + "\n".join(linhas))

    while True:
        mostrar_menu()
        try:
            escolha = input("Escolha uma opção [0-8] e pressione Enter: ").strip()
            if escolha == "0":
                print("Encerrado.")
                return
            acao = opcoes.get(escolha)
            if acao is None:
                print("Opção inválida; escolha um número do menu.")
            else:
                acao()
        except EOFError:
            print("\nEntrada encerrada.")
            return


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Sistema de Comunicação Interplanetária da Colônia")
    parser.add_argument("--demo", action="store_true", help="executa todas as funções sem interação")
    parser.add_argument("--dados", type=Path, default=ARQUIVO_PADRAO, help="caminho do CSV")
    args = parser.parse_args()
    try:
        registros = carregar_dados(args.dados)
        treino, validacao, teste = separar_ciclos(registros)
        modelo = treinar_modelo(treino)
        media_treino = sum(r.latencia_observada_ms for r in treino) / len(treino)
        if args.demo:
            executar_demo(registros, modelo, treino, validacao, teste, media_treino)
        else:
            executar_menu(registros, modelo, treino, validacao, teste, media_treino)
        return 0
    except ValueError as erro:
        print(f"Erro ao iniciar o SCIC: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
