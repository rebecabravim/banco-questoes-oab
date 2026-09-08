import re
import json
import sys
from pathlib import Path


def ler_arquivo(caminho_arquivo):
    caminho = Path(caminho_arquivo)

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def normalizar_texto(texto):
    # Remove espaços no início e no fim das linhas
    linhas = [linha.strip() for linha in texto.splitlines()]

    # Remove linhas vazias
    linhas = [linha for linha in linhas if linha]

    # Junta o conteúdo novamente
    texto = "\n".join(linhas)

    return texto


def identificar_questoes(texto):
    """
    Identifica os blocos de questões.

    Uma questão começa quando encontramos um número isolado
    em uma linha.
    """

    padrao = re.compile(r"(?m)^(\d{1,2})\s*$")

    ocorrencias = list(padrao.finditer(texto))

    questoes = []

    for indice, ocorrencia in enumerate(ocorrencias):
        numero = int(ocorrencia.group(1))

        inicio = ocorrencia.end()

        if indice + 1 < len(ocorrencias):
            fim = ocorrencias[indice + 1].start()
        else:
            fim = len(texto)

        conteudo = texto[inicio:fim].strip()

        questoes.append({
            "numero": numero,
            "texto": conteudo
        })

    return questoes


def extrair_alternativas(texto):
    """
    Separa o enunciado e as quatro alternativas.
    """

    padrao = re.compile(r"\(([ABCD])\)")

    ocorrencias = list(padrao.finditer(texto))

    if len(ocorrencias) != 4:
        raise ValueError(
            f"Esperadas 4 alternativas, mas foram encontradas "
            f"{len(ocorrencias)}."
        )

    letras_esperadas = ["A", "B", "C", "D"]
    letras_encontradas = [ocorrencia.group(1) for ocorrencia in ocorrencias]

    if letras_encontradas != letras_esperadas:
        raise ValueError(
            f"Ordem das alternativas inválida: {letras_encontradas}"
        )

    enunciado = texto[:ocorrencias[0].start()].strip()

    alternativas = []

    for indice, ocorrencia in enumerate(ocorrencias):
        inicio = ocorrencia.end()

        if indice + 1 < len(ocorrencias):
            fim = ocorrencias[indice + 1].start()
        else:
            fim = len(texto)

        conteudo = texto[inicio:fim].strip()

        alternativas.append({
            "letra": ocorrencia.group(1),
            "enunciado": conteudo
        })

    return enunciado, alternativas


# novo
# def encontrar_alternativas(texto):
#     """
#     Procura o início das quatro alternativas.

#     A identificação considera a sequência:

#     (A) ... (B) ... (C) ... (D)

#     Dessa forma, ocorrências como:

#     O(A) advogado(a)
#     (CPI)
#     (CTN)
#     (ADCT)

#     não são consideradas alternativas.
#     """

#     padrao = re.compile(r"\(([ABCD])\)")

#     ocorrencias = list(padrao.finditer(texto))

#     letras_esperadas = ["A", "B", "C", "D"]

#     for indice in range(len(ocorrencias) - 3):

#         candidatas = ocorrencias[indice:indice + 4]

#         letras = [
#             ocorrencia.group(1)
#             for ocorrencia in candidatas
#         ]

#         if letras == letras_esperadas:
#             return candidatas

#     return None

# novo
# def encontrar_alternativas_corrompidas(texto):
#     """
#     Procura uma sequência A-B-C-D considerando alguns
#     erros conhecidos do OCR.

#     Exemplos de erros tratados:

#     (DA
#     (AJA
#     (BBA
#     (BJn
#     (B JO
#     (D JO
#     (B )JA
#     """

#     padroes = [
#         re.compile(r"\(([ABCD])\)"),
#         re.compile(r"\(([ABCD])\s*J\s*"),
#         re.compile(r"\(([ABCD])\s*\)J\s*"),
#         re.compile(r"\(([ABCD])(?=[A-Za-zÀ-ÿ])"),
#     ]

#     ocorrencias = []

#     for padrao in padroes:
#         for ocorrencia in padrao.finditer(texto):
#             ocorrencias.append({
#                 "inicio": ocorrencia.start(),
#                 "fim": ocorrencia.end(),
#                 "letra": ocorrencia.group(1)
#             })

#     ocorrencias.sort(key=lambda ocorrencia: ocorrencia["inicio"])

#     letras_esperadas = ["A", "B", "C", "D"]

#     for indice in range(len(ocorrencias) - 3):

#         candidatas = ocorrencias[indice:indice + 4]

#         letras = [
#             ocorrencia["letra"]
#             for ocorrencia in candidatas
#         ]

#         if letras == letras_esperadas:

#             return candidatas

#     return None


# def extrair_alternativas(texto):
#     """
#     Separa o enunciado e as quatro alternativas.

#     Primeiro procura uma sequência normal A-B-C-D.
#     Caso não encontre, procura a mesma sequência
#     considerando alguns erros conhecidos do OCR.
#     """

#     ocorrencias = encontrar_alternativas(texto)

#     if ocorrencias is None:
#         ocorrencias = encontrar_alternativas_corrompidas(texto)

#     if ocorrencias is None:
#         raise ValueError(
#             "Não foi possível identificar um bloco de "
#             "quatro alternativas na sequência A, B, C, D."
#         )

#     inicio_alternativas = ocorrencias[0]["inicio"]

#     enunciado = texto[:inicio_alternativas].strip()

#     alternativas = []

#     for indice, ocorrencia in enumerate(ocorrencias):

#         inicio = ocorrencia["fim"]

#         if indice + 1 < len(ocorrencias):
#             fim = ocorrencias[indice + 1]["inicio"]
#         else:
#             fim = len(texto)

#         conteudo = texto[inicio:fim].strip()

#         alternativas.append({
#             "letra": ocorrencia["letra"],
#             "enunciado": conteudo
#         })

#     return enunciado, alternativas
    

def estruturar_questoes(questoes_brutas):
    questoes = []
    erros = []

    for questao_bruta in questoes_brutas:
        numero = questao_bruta["numero"]
        texto = questao_bruta["texto"]

        try:
            enunciado, alternativas = extrair_alternativas(texto)

            questao = {
                "numero": numero,
                "enunciado": enunciado,
                "alternativas": alternativas
            }

            questoes.append(questao)

    #     except ValueError as erro:
    #         raise ValueError(
    #             f"Erro na questão {numero}: {erro}"
    #         ) from erro

    # return questoes

        except ValueError as erro:
                erros.append({
                    "numero": numero,
                    "erro": str(erro),
                    "texto": texto
                })
    
    return questoes, erros


def validar_questoes(questoes):
    numeros = [questao["numero"] for questao in questoes]

    if not numeros:
        raise ValueError("Nenhuma questão foi encontrada.")

    numeros_esperados = list(range(1, len(numeros) + 1))

    if numeros != numeros_esperados:
        raise ValueError(
            f"Sequência de questões inválida. "
            f"Encontrado: {numeros}"
        )

    for questao in questoes:
        if not questao["enunciado"]:
            raise ValueError(
                f"Questão {questao['numero']} possui enunciado vazio."
            )

        if len(questao["alternativas"]) != 4:
            raise ValueError(
                f"Questão {questao['numero']} não possui 4 alternativas."
            )


def salvar_json(dados, caminho_saida):
    caminho = Path(caminho_saida)

    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

#novo
def salvar_erros(erros, caminho_saida):
    caminho = Path(caminho_saida)

    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as arquivo:

        arquivo.write(
            "ERROS ENCONTRADOS NA ESTRUTURAÇÃO DA PROVA\n"
        )
        arquivo.write("=" * 60 + "\n\n")

        for erro in erros:
            arquivo.write(
                f"QUESTÃO {erro['numero']}\n"
            )

            arquivo.write(
                f"Erro: {erro['erro']}\n\n"
            )

            arquivo.write(
                "Texto da questão:\n"
            )

            arquivo.write(
                erro["texto"]
            )

            arquivo.write("\n\n")
            arquivo.write("-" * 60 + "\n\n")

def estruturar_prova(caminho_entrada, caminho_saida, edicao, ano):
    texto = ler_arquivo(caminho_entrada)

    texto = normalizar_texto(texto)

    questoes_brutas = identificar_questoes(texto)

    questoes, erros = estruturar_questoes(questoes_brutas)

    # novo
    if erros:
        caminho_erros = Path(caminho_saida).with_suffix(".erros.txt")

        salvar_erros(erros, caminho_erros)

        print(f"Arquivo: {caminho_entrada}")
        print(f"Questões encontradas: {len(questoes_brutas)}")
        print(f"Questões estruturadas: {len(questoes)}")
        print(f"Erros encontrados: {len(erros)}")
        print()
        print("QUESTÕES COM ERRO:")

        for erro in erros:
            print(
                f"- Questão {erro['numero']}: "
                f"{erro['erro']}"
            )

        print()
        print(f"Relatório de erros: {caminho_erros}")
        print()
        print(
            "Corrija os erros no arquivo TXT e execute "
            "o script novamente."
        )

        return False

    validar_questoes(questoes)

    dados = {
        "edicao": edicao,
        "ano": ano,
        "questoes": questoes
    }

    salvar_json(dados, caminho_saida)

    print(f"Arquivo: {caminho_entrada}")
    print(f"Questões encontradas: {len(questoes)}")
    print(f"JSON gerado: {caminho_saida}")


if __name__ == "__main__":

    if len(sys.argv) != 5:
        print(
            "Uso: python estruturar_prova.py "
            "<txt> <json> <edicao> <ano>"
        )
        sys.exit(1)

    caminho_entrada = sys.argv[1]
    caminho_saida = sys.argv[2]
    edicao = int(sys.argv[3])
    ano = int(sys.argv[4])

    try:
        estruturar_prova(
            caminho_entrada,
            caminho_saida,
            edicao,
            ano
        )

    except ValueError as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)