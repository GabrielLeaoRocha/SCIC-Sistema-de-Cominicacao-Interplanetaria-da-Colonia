"""Gera a base simulada e reproduzível do SCIC (Aurora Siger)."""

from __future__ import annotations

import csv
import random
from pathlib import Path


DESTINO = Path(__file__).resolve().parent / "dados_aurora_siger.csv"
SEMENTE = 2026
MODULOS = [
    ("Comunicação", "comunicacao", "COM-2A", True, 5),
    ("Habitação", "habitacao", "HAB-2B", True, 9),
    ("Agricultura", "agricultura", "AGR-2C", False, 11),
    ("Laboratório", "laboratorio", "LAB-2D", False, 14),
    ("Suporte Médico", "medico", "MED-2E", True, 10),
    ("Armazenamento", "dados", "DAD-2F", True, 7),
    ("Energia", "energia", "ENE-30", True, 8),
    ("Controle", "controle", "CTR-31", True, 6),
]
COLUNAS = [
    "ciclo", "modulo", "tipo_modulo", "codigo_sensor", "fila_mensagens",
    "qualidade_sinal_pct", "tensao_v", "corrente_a",
    "latencia_observada_ms", "status_operacional", "mensagem_alerta",
]


def gerar_registros() -> list[dict[str, object]]:
    """Cria 15 ciclos × 8 módulos com ruído e falhas pontuais intencionais."""
    sorteio = random.Random(SEMENTE)
    registros: list[dict[str, object]] = []
    incidentes = {(4, "COM-2A"), (8, "MED-2E"), (11, "ENE-30"),
                 (14, "HAB-2B"), (15, "COM-2A"), (15, "MED-2E"),
                 (15, "ENE-30")}

    for ciclo in range(1, 16):
        for indice, (modulo, tipo, codigo, _essencial, deslocamento) in enumerate(MODULOS):
            fila = 8 + ((ciclo * 7 + indice * 11) % 28) + sorteio.randint(0, 12)
            qualidade = 61 + ((ciclo * 13 + indice * 9) % 34) + sorteio.uniform(-3, 3)
            tensao = 11.6 + sorteio.uniform(-0.5, 0.7)
            corrente = 1.1 + indice * 0.09 + sorteio.uniform(-0.12, 0.12)
            atraso_incidente = 0

            if (ciclo, codigo) in incidentes:
                qualidade -= 19
                fila += 17
                atraso_incidente = 37

            qualidade = round(max(35, min(99, qualidade)), 2)
            tensao = round(tensao, 2)
            corrente = round(corrente, 3)
            potencia = tensao * corrente
            latencia = (
                93 + 1.85 * fila - 0.82 * qualidade - 0.58 * potencia
                + deslocamento + sorteio.gauss(0, 4.5) + atraso_incidente
            )
            latencia = round(max(1, latencia), 2)
            if atraso_incidente or latencia >= 105 or qualidade < 55:
                status = "alerta"
                mensagem = "Latência ou sinal fora da faixa ilustrativa"
            elif ciclo == 12 and codigo == "LAB-2D":
                status = "manutencao"
                mensagem = "Verificação preventiva programada"
            else:
                status = "ativo"
                mensagem = "Operação dentro da faixa ilustrativa"

            registros.append({
                "ciclo": ciclo,
                "modulo": modulo,
                "tipo_modulo": tipo,
                "codigo_sensor": codigo,
                "fila_mensagens": fila,
                "qualidade_sinal_pct": qualidade,
                "tensao_v": tensao,
                "corrente_a": corrente,
                "latencia_observada_ms": latencia,
                "status_operacional": status,
                "mensagem_alerta": mensagem,
            })
    return registros


def main() -> None:
    with DESTINO.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(gerar_registros())
    print(f"Base gerada: {DESTINO} (120 registros, semente {SEMENTE})")


if __name__ == "__main__":
    main()
