
import argparse
import json
import os
import time

from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import errors


DISCIPLINAS = [
    "direito-administrativo",
    "direito-ambiental",
    "direito-civil",
    "direito-constitucional",
    "direito-crianca-adolescente",
    "direito-consumidor",
    "direito-trabalho",
    "direito-empresarial",
    "direito-internacional",
    "direito-tributario",
    "direito-penal",
    "direitos-humanos",
    "etica",
    "filosofia-direito",
    "processo-civil",
    "processo-trabalho",
    "processo-penal",
    "direito-financeiro",
    "direito-eleitoral",
    "direito-previdenciario",
]


TAMANHO_LOTE = 10
TENTATIVAS = 3
ESPERA_ERRO = 15


load_dotenv()

chave_api = os.getenv("GEMINI_API_KEY")

if not chave_api:
    raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env")

cliente = genai.Client(api_key=chave_api)


def classificar_lote(questoes):
    disciplinas = "\n".join(
        f"- {disciplina}"
        for disciplina in DISCIPLINAS
    )

    texto_questoes = ""

    for questao in questoes:
        texto_alternativas = "\n".join(
            f"{alternativa['letra']}) {alternativa['enunciado']}"
            for alternativa in questao["alternativas"]
        )

        texto_questoes += f"""
        QUESTÃO {questao['numero']}

        Enunciado:
        {questao['enunciado']}

        Alternativas:
        {texto_alternativas}

        """

    prompt = f"""
    Você é um classificador de questões da primeira fase do Exame da OAB.

    Classifique cada questão em exatamente uma das disciplinas abaixo:

    {disciplinas}

    Regras:
    - Cada questão deve receber exatamente uma disciplina.
    - Não crie novas disciplinas.
    - Considere o conteúdo jurídico principal da questão.
    - Não classifique com base apenas em palavras isoladas.
    - O código retornado deve ser exatamente igual a um dos códigos fornecidos.
    - Não resolva as questões.
    - Não forneça explicações.
    - Retorne somente um JSON válido.
    - O JSON deve ser uma lista.
    - Para cada questão, informe o número e o código da disciplina.
    - Não omita nenhuma questão.

    Formato obrigatório:

    [
        {{
            "numero": 1,
            "disciplina_codigo": "etica"
        }}
    ]

    Questões para classificar:

    {texto_questoes}
    """

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = cliente.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

            texto_resposta = resposta.text.strip()

            if texto_resposta.startswith("```"):
                texto_resposta = texto_resposta.split("\n", 1)[1]

            if texto_resposta.endswith("```"):
                texto_resposta = texto_resposta[:-3]

            texto_resposta = texto_resposta.strip()                     

            try:
                classificacoes = json.loads(texto_resposta)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Gemini não retornou um JSON válido:\n{texto_resposta}"
                )

            if not isinstance(classificacoes, list):
                raise ValueError(
                    "Gemini não retornou uma lista de classificações."
                )

            numeros_esperados = {
                questao["numero"]
                for questao in questoes
            }

            numeros_recebidos = {
                classificacao.get("numero")
                for classificacao in classificacoes
            }

            if numeros_esperados != numeros_recebidos:
                raise ValueError(
                    f"Questões retornadas não correspondem ao lote.\n"
                    f"Esperadas: {sorted(numeros_esperados)}\n"
                    f"Recebidas: {sorted(numeros_recebidos)}"
                )

            for classificacao in classificacoes:
                disciplina = classificacao.get("disciplina_codigo")

                if disciplina not in DISCIPLINAS:
                    raise ValueError(
                        f"Gemini retornou uma disciplina inválida: {disciplina}"
                    )

            return classificacoes

        except errors.ServerError as erro:
            print(
                f"  Erro de servidor na tentativa "
                f"{tentativa}/{TENTATIVAS}: {erro}"
            )

            if tentativa < TENTATIVAS:
                print(
                    f"  Aguardando {ESPERA_ERRO} segundos "
                    f"antes de tentar novamente..."
                )
                time.sleep(ESPERA_ERRO)
            else:
                raise

        except errors.APIError as erro:
            print(f"  Erro da API: {erro}")
            raise


def carregar_prova(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar_classificacoes(caminho, prova):
    if not os.path.exists(caminho):
        return {
            "edicao": prova["edicao"],
            "ano": prova["ano"],
            "questoes": []
        }

    with open(caminho, "r", encoding="utf-8") as arquivo:
        classificacoes = json.load(arquivo)

    if (
        classificacoes["edicao"] != prova["edicao"]
        or classificacoes["ano"] != prova["ano"]
    ):
        raise ValueError(
            "O arquivo de classificações não corresponde à prova informada."
        )

    return classificacoes


def salvar_classificacoes(caminho, classificacoes):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            classificacoes,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Classifica questões da OAB utilizando o Gemini."
    )

    parser.add_argument(
        "arquivo",
        help="Caminho do arquivo JSON da prova."
    )

    argumentos = parser.parse_args()

    caminho_json = Path(argumentos.arquivo)

    if not caminho_json.exists():
        raise FileNotFoundError(
            f"Arquivo da prova não encontrado: {caminho_json}"
        )

    prova = carregar_prova(caminho_json)

    pasta_saida = Path("json/classificacoes")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    caminho_saida = (
        pasta_saida /
        f"classificacoes-oab-{prova['edicao']}.json"
    )

    classificacoes = carregar_classificacoes(
        caminho_saida,
        prova
    )

    numeros_classificados = {
        classificacao["numero"]
        for classificacao in classificacoes["questoes"]
    }

    if numeros_classificados:
        print(
            f"{len(numeros_classificados)} questões "
            f"já classificadas."
        )
    else:
        print("Nenhuma questão classificada anteriormente.")

    questoes_pendentes = [
        questao
        for questao in prova["questoes"]
        if questao["numero"] not in numeros_classificados
    ]

    print(
        f"{len(questoes_pendentes)} questões "
        f"ainda precisam ser classificadas."
    )

    for inicio in range(0, len(questoes_pendentes), TAMANHO_LOTE):
        lote = questoes_pendentes[inicio:inicio + TAMANHO_LOTE]

        numeros = [
            questao["numero"]
            for questao in lote
        ]

        print(
            f"Classificando questões "
            f"{numeros[0]} até {numeros[-1]}..."
        )

        classificacoes_lote = classificar_lote(lote)

        for classificacao in classificacoes_lote:
            classificacao_completa = {
                "numero": classificacao["numero"],
                "disciplina_codigo": classificacao["disciplina_codigo"]
            }

            classificacoes["questoes"].append(
                classificacao_completa
            )

            print(
                f"  Questão {classificacao['numero']} "
                f"→ {classificacao['disciplina_codigo']}"
            )

        classificacoes["questoes"].sort(
            key=lambda questao: questao["numero"]
        )

        salvar_classificacoes(
            caminho_saida,
            classificacoes
        )

        print("  Lote concluído.\n")

        if inicio + TAMANHO_LOTE < len(questoes_pendentes):
            time.sleep(5)

    print()
    print(f"Classificação concluída: {caminho_saida}")
