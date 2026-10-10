"""Verificações de cálculos e fluxos críticos do protótipo."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from codigo_fonte import (
    ARQUIVO_PADRAO, alertas_priorizados, avaliar, carregar_dados, construir_trie,
    erro_numerico, metricas, separar_ciclos, treinar_modelo,
)
from gerar_dados import COLUNAS, gerar_registros


class TesteSCIC(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registros = carregar_dados(ARQUIVO_PADRAO)
        cls.treino, cls.validacao, cls.teste = separar_ciclos(cls.registros)
        cls.modelo = treinar_modelo(cls.treino)

    def test_base_reproduzivel_e_separacao_temporal(self) -> None:
        self.assertEqual(len(gerar_registros()), 120)
        self.assertEqual(len(self.registros), 120)
        self.assertEqual([len(parte) for parte in (self.treino, self.validacao, self.teste)], [72, 24, 24])
        self.assertLess(max(r.ciclo for r in self.treino), min(r.ciclo for r in self.validacao))
        self.assertLess(max(r.ciclo for r in self.validacao), min(r.ciclo for r in self.teste))
        self.assertEqual(self.registros[0].latencia_observada_ms, gerar_registros()[0]["latencia_observada_ms"])

    def test_metricas_e_erros_com_unidades_coerentes(self) -> None:
        valores = metricas([10, 20, 30], [12, 18, 29])
        self.assertAlmostEqual(valores["MAE"], 5 / 3)
        self.assertAlmostEqual(valores["MSE"], 3)
        self.assertAlmostEqual(valores["RMSE"], 3 ** 0.5)
        self.assertAlmostEqual(valores["R2"], 0.955)
        registro = self.registros[0]
        absoluto, relativo = erro_numerico(registro, registro.latencia_observada_ms + 5)
        self.assertAlmostEqual(absoluto, 5)
        self.assertAlmostEqual(relativo, 500 / registro.latencia_observada_ms)

    def test_modelo_supera_baseline_no_teste(self) -> None:
        media_treino = sum(r.latencia_observada_ms for r in self.treino) / len(self.treino)
        resultado = avaliar(self.teste, self.modelo, media_treino)
        self.assertLess(resultado["modelo"]["MAE"], resultado["baseline"]["MAE"])
        self.assertGreater(resultado["modelo"]["R2"], 0)

    def test_heap_prioriza_e_trie_encontra_prefixo(self) -> None:
        alertas = alertas_priorizados(self.registros, self.modelo)
        self.assertGreaterEqual(len(alertas), 3)
        prioridades = [(p, atraso) for p, atraso, _ in alertas]
        self.assertEqual(prioridades, sorted(prioridades, key=lambda item: (-item[0], -item[1])))
        self.assertEqual(alertas[0][2].codigo_sensor, "MED-2E")
        trie = construir_trie(self.registros)
        encontrados = trie.buscar_prefixo("com")
        self.assertEqual(len(encontrados), 15)
        self.assertTrue(all(r.codigo_sensor == "COM-2A" for r in encontrados))
        self.assertEqual(trie.buscar_prefixo("XXX"), [])
        self.assertEqual(trie.buscar_prefixo(""), [])

    def test_csv_rejeita_duplicata_e_valor_invalido(self) -> None:
        base = gerar_registros()
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "dados.csv"
            for linhas, mensagem in (([base[0], base[0]], "duplicados"),
                                     ([{**base[0], "latencia_observada_ms": 0}], "fora da faixa")):
                with caminho.open("w", encoding="utf-8", newline="") as arquivo:
                    escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
                    escritor.writeheader()
                    escritor.writerows(linhas)
                with self.assertRaisesRegex(ValueError, mensagem):
                    carregar_dados(caminho)


if __name__ == "__main__":
    unittest.main()
