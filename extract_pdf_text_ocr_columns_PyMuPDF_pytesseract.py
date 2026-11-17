import argparse
from pathlib import Path

import pymupdf  # PyMuPDF
import pytesseract
from PIL import Image

# Script final com extração OCR por colunas, removendo cabeçalho e rodapé, 
# salvando o resultado em um arquivo de texto.

PASTA_SAIDA = Path("provas-extraidas")

def extrair_texto_com_ocr_por_colunas(
    caminho_pdf: Path,
    pagina_inicial: int,
    pagina_final: int
) -> str:
    textos_paginas = []

    with pymupdf.open(caminho_pdf) as pdf:
        for numero_pagina in range(pagina_inicial, pagina_final + 1):
            indice_pagina = numero_pagina - 1
            pagina = pdf[indice_pagina]

            pix = pagina.get_pixmap(dpi=300)

            imagem = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            largura, altura = imagem.size

            # Remove cabeçalho/rodapé e divide a página em duas colunas
            topo = int(altura * 0.07)
            base = int(altura * 0.94)
            meio = largura // 2

            coluna_esquerda = imagem.crop(
                (0, topo, meio, base)
            )

            coluna_direita = imagem.crop(
                (meio, topo, largura, base)
            )

            configuracao = "--psm 6"

            texto_esquerda = pytesseract.image_to_string(
                coluna_esquerda,
                lang="por",
                config=configuracao
            )

            texto_direita = pytesseract.image_to_string(
                coluna_direita,
                lang="por",
                config=configuracao
            )

            # textos_paginas.append(
            #     f"\n\n===== Página {numero_pagina} =====\n\n"
            # )
            textos_paginas.append(texto_esquerda.strip())
            textos_paginas.append("\n\n")
            textos_paginas.append(texto_direita.strip())

    return "".join(textos_paginas)


def salvar_texto(
    texto: str,
    caminho_pdf: Path,
    pagina_inicial: int,
    pagina_final: int
) -> Path:
    pasta_saida = PASTA_SAIDA
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivo_saida = (
        pasta_saida
        / f"OK_{caminho_pdf.stem}_paginas_{pagina_inicial}_{pagina_final}_ocr_columns.txt"
    )

    arquivo_saida.write_text(texto, encoding="utf-8")

    return arquivo_saida


def main():
    parser = argparse.ArgumentParser(
        description="Extrai texto de um intervalo de páginas de um PDF usando OCR por colunas."
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

    with pymupdf.open(caminho_pdf) as pdf:
        total_paginas = len(pdf)

    if argumentos.pagina_inicial < 1:
        raise ValueError(
            "A página inicial deve ser maior ou igual a 1."
        )

    if argumentos.pagina_final < 1:
        raise ValueError(
            "A página final deve ser maior ou igual a 1."
        )

    if argumentos.pagina_inicial > argumentos.pagina_final:
        raise ValueError(
            "A página inicial não pode ser maior que a página final."
        )

    if argumentos.pagina_final > total_paginas:
        raise ValueError(
            f"A página final informada ({argumentos.pagina_final}) "
            f"não existe. O arquivo possui {total_paginas} páginas."
        )

    texto_extraido = extrair_texto_com_ocr_por_colunas(
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

    print("Texto extraído com OCR por colunas com sucesso.")
    print(f"Arquivo salvo em: {arquivo_saida}")


if __name__ == "__main__":
    main()