import json
import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def carregar_classificacoes(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def persistir_classificacoes(caminho):
    classificacoes = carregar_classificacoes(caminho)

    conexao = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    try:
        with conexao.cursor() as cursor:

            for classificacao in classificacoes:
                edicao = classificacao["edicao"]
                ano = classificacao["ano"]
                numero = classificacao["numero"]
                disciplina_codigo = classificacao["disciplina_codigo"]

                cursor.execute(
                    """
                    SELECT uuid
                    FROM prova
                    WHERE edicao = %s
                      AND ano = %s
                    """,
                    (edicao, ano)
                )

                prova = cursor.fetchone()

                if not prova:
                    raise ValueError(
                        f"Prova não encontrada: edição {edicao}, ano {ano}"
                    )

                prova_uuid = prova[0]

                cursor.execute(
                    """
                    SELECT uuid
                    FROM disciplina
                    WHERE codigo = %s
                    """,
                    (disciplina_codigo,)
                )

                disciplina = cursor.fetchone()

                if not disciplina:
                    raise ValueError(
                        f"Disciplina não encontrada: {disciplina_codigo}"
                    )

                disciplina_uuid = disciplina[0]

                cursor.execute(
                    """
                    UPDATE questao
                    SET disciplina_uuid = %s
                    WHERE prova_uuid = %s
                      AND numero = %s
                    """,
                    (
                        disciplina_uuid,
                        prova_uuid,
                        numero
                    )
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Questão não encontrada: "
                        f"edição {edicao}, ano {ano}, questão {numero}"
                    )

                print(
                    f"Questão {numero} → {disciplina_codigo}"
                )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


if __name__ == "__main__":
    caminho_json = "json/classificacoes-oab-45.json"

    persistir_classificacoes(caminho_json)

    print()
    print("Classificações persistidas com sucesso.")