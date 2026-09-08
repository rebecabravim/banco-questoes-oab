import argparse
import csv
import json
import sys
from pathlib import Path

import psycopg


def ler_json(caminho_arquivo):
    caminho = Path(caminho_arquivo)

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def ler_gabarito(caminho_arquivo):
    caminho = Path(caminho_arquivo)

    gabarito = {}

    with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")

        for linha in leitor:
            numero = int(linha["questao"])
            alternativa = linha["alternativa_correta"].strip().upper()

            gabarito[numero] = alternativa

    return gabarito


def validar_dados(dados, gabarito):
    erros = []

    questoes = dados.get("questoes", [])

    if not questoes:
        erros.append("O JSON não possui questões.")

    numeros_questoes = {
        questao["numero"]
        for questao in questoes
    }

    numeros_gabarito = set(gabarito.keys())

    questoes_sem_gabarito = numeros_questoes - numeros_gabarito
    gabaritos_sem_questao = numeros_gabarito - numeros_questoes

    if questoes_sem_gabarito:
        erros.append(
            f"Questões sem gabarito: "
            f"{sorted(questoes_sem_gabarito)}"
        )

    if gabaritos_sem_questao:
        erros.append(
            f"Gabaritos sem questão correspondente: "
            f"{sorted(gabaritos_sem_questao)}"
        )

    numeros_validos = {"A", "B", "C", "D"}

    for numero, alternativa in gabarito.items():
        if alternativa not in numeros_validos:
            erros.append(
                f"Gabarito inválido na questão {numero}: "
                f"{alternativa}"
            )

    for questao in questoes:
        numero = questao["numero"]
        alternativas = questao.get("alternativas", [])

        letras = [
            alternativa["letra"]
            for alternativa in alternativas
        ]

        if letras != ["A", "B", "C", "D"]:
            erros.append(
                f"Questão {numero}: alternativas inválidas "
                f"ou em ordem incorreta: {letras}"
            )

    return erros


def inserir_prova(cursor, edicao, ano):
    cursor.execute(
        """
        INSERT INTO prova (edicao, ano)
        VALUES (%s, %s)
        RETURNING uuid
        """,
        (edicao, ano)
    )

    return cursor.fetchone()[0]


def inserir_questao(cursor, questao, prova_uuid):
    cursor.execute(
        """
        INSERT INTO questao (
            numero,
            enunciado,
            prova_uuid
        )
        VALUES (%s, %s, %s)
        RETURNING uuid
        """,
        (
            questao["numero"],
            questao["enunciado"],
            prova_uuid
        )
    )

    return cursor.fetchone()[0]


def inserir_alternativa(
    cursor,
    alternativa,
    questao_uuid,
    resposta_correta
):
    cursor.execute(
        """
        INSERT INTO alternativa (
            letra,
            enunciado,
            resposta_correta,
            questao_uuid
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            alternativa["letra"],
            alternativa["enunciado"],
            resposta_correta,
            questao_uuid
        )
    )


def popular_banco(dados, gabarito, conexao):
    with conexao.cursor() as cursor:

        edicao = dados["edicao"]
        ano = dados["ano"]

        prova_uuid = inserir_prova(
            cursor,
            edicao,
            ano
        )

        quantidade_questoes = 0
        quantidade_alternativas = 0

        for questao in dados["questoes"]:

            numero = questao["numero"]

            questao_uuid = inserir_questao(
                cursor,
                questao,
                prova_uuid
            )

            alternativa_correta = gabarito[numero]

            for alternativa in questao["alternativas"]:

                resposta_correta = (
                    alternativa["letra"]
                    == alternativa_correta
                )

                inserir_alternativa(
                    cursor,
                    alternativa,
                    questao_uuid,
                    resposta_correta
                )

                quantidade_alternativas += 1

            quantidade_questoes += 1

    return (
        prova_uuid,
        quantidade_questoes,
        quantidade_alternativas
    )


def main():
    parser = argparse.ArgumentParser(
        description="Popula o banco PostgreSQL com uma prova da OAB."
    )

    parser.add_argument(
        "json",
        help="Arquivo JSON da prova"
    )

    parser.add_argument(
        "gabarito",
        help="Arquivo CSV do gabarito"
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Host do PostgreSQL"
    )

    parser.add_argument(
        "--port",
        default=5432,
        type=int,
        help="Porta do PostgreSQL"
    )

    parser.add_argument(
        "--database",
        required=True,
        help="Nome do banco de dados"
    )

    parser.add_argument(
        "--user",
        required=True,
        help="Usuário do PostgreSQL"
    )

    parser.add_argument(
        "--password",
        required=True,
        help="Senha do PostgreSQL"
    )

    argumentos = parser.parse_args()

    try:
        dados = ler_json(argumentos.json)
        gabarito = ler_gabarito(argumentos.gabarito)

        erros = validar_dados(dados, gabarito)

        if erros:
            print("ERROS DE VALIDAÇÃO:")

            for erro in erros:
                print(f"- {erro}")

            sys.exit(1)

        conexao = psycopg.connect(
            host=argumentos.host,
            port=argumentos.port,
            dbname=argumentos.database,
            user=argumentos.user,
            password=argumentos.password
        )

        try:
            (
                prova_uuid,
                quantidade_questoes,
                quantidade_alternativas
            ) = popular_banco(
                dados,
                gabarito,
                conexao
            )

            conexao.commit()

            print("Importação realizada com sucesso.")
            print(f"Prova: {dados['edicao']}ª edição")
            print(f"Ano: {dados['ano']}")
            print(f"UUID da prova: {prova_uuid}")
            print(f"Questões inseridas: {quantidade_questoes}")
            print(
                f"Alternativas inseridas: "
                f"{quantidade_alternativas}"
            )

        except Exception:
            conexao.rollback()
            raise

        finally:
            conexao.close()

    except Exception as erro:
        print(f"ERRO: {erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()