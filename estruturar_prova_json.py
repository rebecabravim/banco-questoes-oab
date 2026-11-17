import argparse
import re
import json
import sys
from pathlib import Path

PASTA_SAIDA = Path("json")

def ler_arquivo(caminho_arquivo):
    caminho = Path(caminho_arquivo)

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def normalizar_texto(texto):
    """
    Normaliza o texto utilizado durante a identificação
    das questões, preservando as quebras de linha necessárias
    para identificar os números das questões.
    """

    # Remove espaços no início e no fim das linhas
    linhas = [linha.strip() for linha in texto.splitlines()]

    # Remove linhas vazias
    linhas = [linha for linha in linhas if linha]

    # Junta o conteúdo novamente preservando as linhas
    texto = "\n".join(linhas)

    return texto


def limpar_texto_para_banco(texto):
    """
    Prepara o texto final para ser armazenado no banco de dados.

    Substitui quebras de linha e múltiplos espaços por um único espaço.
    """

    # Qualquer sequência de espaços, tabs ou quebras de linha
    # é transformada em um único espaço
    texto = re.sub(r"\s+", " ", texto)

    # Remove espaços no início e no fim
    return texto.strip()


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


def estruturar_questoes(questoes_brutas):
    questoes = []
    erros = []

    for questao_bruta in questoes_brutas:
        numero = questao_bruta["numero"]
        texto = questao_bruta["texto"]

        try:
            enunciado, alternativas = extrair_alternativas(texto)

            # Limpa o enunciado para o formato final do banco
            enunciado = limpar_texto_para_banco(enunciado)

            # Limpa cada alternativa para o formato final do banco
            for alternativa in alternativas:
                alternativa["enunciado"] = limpar_texto_para_banco(
                    alternativa["enunciado"]
                )

            questao = {
                "numero": numero,
                "enunciado": enunciado,
                "alternativas": alternativas
            }

            questoes.append(questao)

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

        for alternativa in questao["alternativas"]:

            if not alternativa["enunciado"]:
                raise ValueError(
                    f"Questão {questao['numero']} possui "
                    f"a alternativa {alternativa['letra']} vazia."
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

def estruturar_prova(caminho_entrada, edicao, ano):
    texto = ler_arquivo(caminho_entrada)

    # Normalização necessária para identificar
    # corretamente as questões
    texto = normalizar_texto(texto)

    questoes_brutas = identificar_questoes(texto)

    questoes, erros = estruturar_questoes(questoes_brutas)

    caminho_saida = (
        PASTA_SAIDA / f"prova-oab-estrutura-{edicao}.json"
    )

    if erros:
        caminho_erros = (
            PASTA_SAIDA / "logs" /
            f"prova-oab-estrutura-{edicao}.erros.txt"
        )

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

    parser = argparse.ArgumentParser(
        description="Estrutura o texto tratado da prova em formato JSON."
    )

    parser.add_argument(
        "caminho_entrada",
        help="Caminho do arquivo TXT tratado."
    )

    parser.add_argument(
        "--edicao",
        type=int,
        required=True,
        help="Número da edição da prova."
    )

    parser.add_argument(
        "--ano",
        type=int,
        required=True,
        help="Ano da edição da prova."
    )

    argumentos = parser.parse_args()

    try:

        sucesso = estruturar_prova(
            argumentos.caminho_entrada,
            argumentos.edicao,
            argumentos.ano
        )

        if not sucesso:
            sys.exit(1)

    except ValueError as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)