
import argparse
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def classificar_questoes(prova, padrao):
    classificacoes = {}

    for faixa in padrao["questoes"]:
        inicio = faixa["inicio"]
        fim = faixa["fim"]
        disciplina_codigo = faixa["disciplina_codigo"]

        for numero in range(inicio, fim + 1):
            if numero in classificacoes:
                raise ValueError(
                    f"Questão {numero} aparece em mais de uma faixa."
                )

            classificacoes[numero] = disciplina_codigo

    numeros_prova = {
        questao["numero"]
        for questao in prova["questoes"]
    }

    numeros_classificados = set(classificacoes)

    faltantes = numeros_prova - numeros_classificados
    extras = numeros_classificados - numeros_prova

    if faltantes:
        raise ValueError(
            f"Questões sem classificação no modelo: {sorted(faltantes)}"
        )

    if extras:
        raise ValueError(
            f"Questões inexistentes na prova: {sorted(extras)}"
        )

    return classificacoes


def persistir_classificacoes(prova, classificacoes):
    edicao = prova["edicao"]
    ano = prova["ano"]

    conexao = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT uuid
                FROM prova
                WHERE edicao = %s AND ano = %s
                """,
                (edicao, ano)
            )

            resultado = cursor.fetchone()

            if not resultado:
                raise ValueError(
                    f"Prova da edição {edicao}, ano {ano}, não encontrada."
                )

            prova_uuid = resultado[0]

            disciplinas = {}

            for disciplina_codigo in set(classificacoes.values()):
                cursor.execute(
                    """
                    SELECT uuid
                    FROM disciplina
                    WHERE codigo = %s
                    """,
                    (disciplina_codigo,)
                )

                resultado = cursor.fetchone()

                if not resultado:
                    raise ValueError(
                        f"Disciplina não encontrada: {disciplina_codigo}"
                    )

                disciplinas[disciplina_codigo] = resultado[0]

            for numero, disciplina_codigo in sorted(classificacoes.items()):
                disciplina_uuid = disciplinas[disciplina_codigo]

                cursor.execute(
                    """
                    UPDATE questao
                    SET disciplina_uuid = %s
                    WHERE prova_uuid = %s AND numero = %s
                    """,
                    (disciplina_uuid, prova_uuid, numero)
                )

                if cursor.rowcount == 0:
                    print(f"Questão {numero}: não encontrada no banco. Possivelmente anulada.")
                    continue

                print(f"Questão {numero}: {disciplina_codigo}")

        conexao.commit()
        print("Classificações persistidas com sucesso.")

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def main():
    parser = argparse.ArgumentParser(
        description="Classifica e persiste as disciplinas das questões da OAB."
    )

    parser.add_argument(
        "--classificacao",
        type=Path,
        required=True,
        help="Caminho do modelo de classificação por faixas."
    )

    parser.add_argument(
        "--prova",
        type=Path,
        required=True,
        help="Caminho do JSON da prova."
    )

    args = parser.parse_args()

    if not args.classificacao.exists():
        raise FileNotFoundError(
            f"Modelo de classificação não encontrado: {args.classificacao}"
        )

    if not args.prova.exists():
        raise FileNotFoundError(
            f"Arquivo da prova não encontrado: {args.prova}"
        )

    padrao = carregar_json(args.classificacao)
    prova = carregar_json(args.prova)

    classificacoes = classificar_questoes(prova, padrao)

    persistir_classificacoes(prova, classificacoes)


if __name__ == "__main__":
    main()
