import argparse
import re
from pathlib import Path


PADRAO_ALTERNATIVA_SEM_PARENTESES = r'(?m)^([A-E])\)'
PADRAO_ALTERNATIVA_COLADA = r'(?m)^(\([A-E]\))([A-Za-zÀ-ÿ])'

PADRAO_ALTERNATIVA_J = r'(?m)^\(([A-E])\s*J\s*'
PADRAO_ALTERNATIVA_J_COM_ESPACO = r'(?m)^\(([A-E])\s*\)J\s*'
# PADRAO_ALTERNATIVA_SEM_FECHAMENTO = r'(?m)^\(([A-E])([A-Za-zÀ-ÿ])'
# 


def normalizar_alternativas(texto):
    """
    Converte marcadores como:

    A)
    B)
    C)
    D)

    para:

    (A)
    (B)
    (C)
    (D)
    """

    return re.sub(
        PADRAO_ALTERNATIVA_SEM_PARENTESES,
        r'(\1)',
        texto
    )



def corrigir_espacamento_alternativas(texto):
    """
    Corrige alternativas coladas ao início do texto.

    Exemplo:

    (A)A publicidade

    para:

    (A) A publicidade
    """

    return re.sub(
        PADRAO_ALTERNATIVA_COLADA,
        r'\1 \2',
        texto
    )


def corrigir_alternativas_com_j(texto):
    """
    Corrige casos em que o OCR reconheceu o fechamento
    da alternativa como a letra J.

    Exemplos:

    (DJO     -> (D) O
    (AJÉ     -> (A) É
    (BJn     -> (B) n
    (B JO    -> (B) O
    (D JO    -> (D) O
    """

    texto = re.sub(
        PADRAO_ALTERNATIVA_J_COM_ESPACO,
        r'(\1) ',
        texto
    )

    texto = re.sub(
        PADRAO_ALTERNATIVA_J,
        r'(\1) ',
        texto
    )

    return texto


# def corrigir_alternativa_j_com_espaco(texto):
#     return re.sub(
#         PADRAO_ALTERNATIVA_J_COM_ESPACO,
#         r'(\1) ',
#         texto
#     )


# def corrigir_fechamento_ausente(texto):
#     return re.sub(
#         PADRAO_ALTERNATIVA_SEM_FECHAMENTO,
#         r'(\1) \2',
#         texto
#     )

def corrigir_erro_771(texto):
    """
    Corrige o erro específico de OCR em que 77 é reconhecido como 771.
    """

    return re.sub(
        r'(?m)^771$',
        '77',
        texto
    )


def tratar_texto(texto):
    """
    Realiza apenas correções estruturais seguras.

    Correções lexicais de palavras reconhecidas incorretamente
    pelo OCR serão tratadas posteriormente por dicionário.
    """

    # texto = corrigir_alternativa_j_com_espaco(texto)
    texto = corrigir_alternativas_com_j(texto)
    texto = normalizar_alternativas(texto)
    # texto = corrigir_fechamento_ausente(texto)
    texto = corrigir_erro_771(texto)
    texto = corrigir_espacamento_alternativas(texto)

    return texto


def tratar_arquivo(caminho_entrada, caminho_saida):
    texto = Path(caminho_entrada).read_text(encoding="utf-8")

    texto_tratado = tratar_texto(texto)

    Path(caminho_saida).write_text(
        texto_tratado,
        encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Realiza o tratamento do texto extraído por OCR."
    )

    parser.add_argument(
        "entrada",
        help="Caminho do arquivo TXT gerado pelo OCR."
    )

    parser.add_argument(
        "saida",
        help="Caminho do arquivo TXT tratado."
    )

    argumentos = parser.parse_args()

    tratar_arquivo(
        argumentos.entrada,
        argumentos.saida
    )

    print(
        f"Arquivo tratado com sucesso: {argumentos.saida}"
    )


if __name__ == "__main__":
    main()