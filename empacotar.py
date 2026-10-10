"""Cria o pacote final somente após o link do vídeo estar preenchido."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile


RAIZ = Path(__file__).resolve().parent
ARQUIVOS = [
    "codigo_fonte.py", "dados_aurora_siger.csv", "relatorio_tecnico.md",
    "README.md", "link_video.txt", "gerar_dados.py",
]
DESTINO = RAIZ.parent / "SCIC_Aurora_Siger.zip"


def link_valido(texto: str) -> bool:
    if len(texto.splitlines()) != 1:
        return False
    url = urlparse(texto.strip())
    host = (url.hostname or "").lower()
    if url.scheme != "https" or host not in {"youtube.com", "www.youtube.com", "youtu.be"}:
        return False
    return bool(url.path.strip("/"))


def main() -> int:
    faltantes = [nome for nome in ARQUIVOS if not (RAIZ / nome).is_file()]
    if faltantes:
        print("Arquivos ausentes: " + ", ".join(faltantes))
        return 1
    link = (RAIZ / "link_video.txt").read_text(encoding="utf-8").strip()
    if not link_valido(link):
        print("Preencha link_video.txt com uma URL HTTPS válida do vídeo no YouTube antes de empacotar.")
        return 1
    with ZipFile(DESTINO, "w", compression=ZIP_DEFLATED) as pacote:
        for nome in ARQUIVOS:
            pacote.write(RAIZ / nome, arcname=nome)
    print(f"Pacote criado: {DESTINO}")
    print("Confira manualmente se o vídeo tem até 5 minutos e está como Não listado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
