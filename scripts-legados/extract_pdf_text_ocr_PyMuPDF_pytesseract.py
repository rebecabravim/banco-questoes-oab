import argparse
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image


def extrair_texto_com_ocr(
    caminho_pdf: Path,
    pagina_inicial: int,
    pagina_final: int
) -> str:
    textos_paginas = []

    with fitz.open(caminho_pdf) as pdf:
        for numero_pagina in range(pagina_inicial, pagina_final + 1):
            indice_pagina = numero_pagina - 1
            pagina = pdf[indice_pagina]

            pix = pagina.get_pixmap(dpi=300)

            imagem = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            texto = pytesseract.image_to_string(
                imagem,
                lang="por"
            )

            textos_paginas.append(
                f"\n\n===== Página {numero_pagina} =====\n\n"
            )
            textos_paginas.append(texto)

    return "".join(textos_paginas)


def salvar_texto(
    texto: str,
    caminho_pdf: Path,
    pagina_inicial: int,
    pagina_final: int
) -> Path:
    pasta_saida = Path("provas-extraidas")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivo_saida = (
        pasta_saida
        / f"{caminho_pdf.stem}_paginas_{pagina_inicial}_{pagina_final}_ocr.txt"
    )

    arquivo_saida.write_text(texto, encoding="utf-8")

    return arquivo_saida


def main():
    parser = argparse.ArgumentParser(
        description="Extrai texto de um intervalo de páginas de um PDF usando OCR."
    )

    parser.add_argument(
        "caminho_pdf",
        help="Caminho do arquivo PDF."
    )

    parser.add_argument(
        "--pagina-inicial",
        type=int,
        required=True,
        help="Página inicial da extração."
    )

    parser.add_argument(
        "--pagina-final",
        type=int,
        required=True,
        help="Página final da extração."
    )

    argumentos = parser.parse_args()

    caminho_pdf = Path(argumentos.caminho_pdf)

    if not caminho_pdf.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_pdf}"
        )

    if caminho_pdf.suffix.lower() != ".pdf":
        raise ValueError(
            "O arquivo informado precisa ser um PDF."
        )

    texto_extraido = extrair_texto_com_ocr(
        caminho_pdf,
        argumentos.pagina_inicial,
        argumentos.pagina_final
    )

    arquivo_saida = salvar_texto(
        texto_extraido,
        caminho_pdf,
        argumentos.pagina_inicial,
        argumentos.pagina_final
    )

    print("Texto extraído com OCR com sucesso.")
    print(f"Arquivo salvo em: {arquivo_saida}")


if __name__ == "__main__":
    main()