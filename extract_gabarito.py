import argparse
import csv
import re
from pathlib import Path

import fitz  # PyMuPDF

PROVA_TIPO = 1
TOTAL_QUESTOES = 80


# def extrair_texto_do_pdf(caminho_pdf: Path) -> str:
#     text_pages = []

#     with fitz.open(pdf_path) as pdf:
#         for page_number, page in enumerate(pdf, start=1):
#             text = page.get_text("text", sort=True)

#             text_pages.append(f"\n\n===== Página {page_number} =====\n\n")
#             text_pages.append(text)

#     return "".join(text_pages)

def extrair_texto_do_pdf(caminho_pdf: Path) -> str:
    textos_paginas = []

    with fitz.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf, start=1):
            texto = pagina.get_text("text", sort=True)
            # textos_paginas.append(f"\n\n===== Página {num_pagina} =====\n\n")
            textos_paginas.append(texto)

    return "".join(textos_paginas)


def obter_bloco_tipo_1(texto: str) -> str:
    texto_maiusculo = texto.upper()

    marcador_inicio = re.search(
        r"(?:PROVA\s+)?TIPO\s+1",
        texto_maiusculo
    )

    if not marcador_inicio:
        raise ValueError(
            "Não foi possível localizar o bloco do Tipo 1."
        )

    inicio = marcador_inicio.start()

    marcador_fim = re.search(
        r"(?:PROVA\s+)?TIPO\s+2",
        texto_maiusculo[inicio:]
    )

    if not marcador_fim:
        return texto[inicio:]

    fim = inicio + marcador_fim.start()

    return texto[inicio:fim]


def extrair_gabarito_tipo_1(texto: str) -> dict[int, str]:
    gabarito = {}

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    for indice in range(len(linhas) - 1):
        linha_numeros = linhas[indice]
        linha_respostas = linhas[indice + 1]

        numeros = re.findall(r"\b\d{1,2}\b", linha_numeros)
        respostas = re.findall(r"\b[A-D]\b|\*", linha_respostas.upper())

        if len(numeros) >= 10 and len(respostas) >= len(numeros):
            for numero, resposta in zip(numeros, respostas):
                numero = int(numero)

                if 1 <= numero <= TOTAL_QUESTOES:
                    gabarito[numero] = resposta

    return gabarito


def salvar_csv(gabarito: dict[int, str], caminho_pdf: Path) -> Path:
    pasta_saida = Path("gabaritos-extraidos")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivo_saida = pasta_saida / f"{caminho_pdf.stem}_tipo_1.csv"

    with arquivo_saida.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(["questao", "alternativa_correta"])

        for numero in sorted(gabarito):
            escritor.writerow([numero, gabarito[numero]])

    return arquivo_saida


def main():
    parser = argparse.ArgumentParser(
        description="Extrai o gabarito Tipo 1 da OAB."
    )

    parser.add_argument(
        "caminho_pdf",
        help="Caminho do arquivo PDF do gabarito."
    )

    args = parser.parse_args()

    caminho_pdf = Path(args.caminho_pdf)

    if not caminho_pdf.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_pdf}")

    if caminho_pdf.suffix.lower() != ".pdf":
        raise ValueError("O arquivo informado precisa ser um PDF.")

    texto = extrair_texto_do_pdf(caminho_pdf)
    texto_tipo_1 = obter_bloco_tipo_1(texto)
    gabarito = extrair_gabarito_tipo_1(texto_tipo_1)
    arquivo_saida = salvar_csv(gabarito, caminho_pdf)

    print("Gabarito Tipo 1 extraído com sucesso.")
    print(f"Total de respostas extraídas: {len(gabarito)}")
    print(f"Arquivo salvo em: {arquivo_saida}")


if __name__ == "__main__":
    main()