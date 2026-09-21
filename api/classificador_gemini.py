import json
import os
import time

from dotenv import load_dotenv
from google import genai


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

    resposta = cliente.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    texto_resposta = resposta.text.strip()

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


def carregar_prova(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_classificacoes(caminho, classificacoes):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            classificacoes,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    caminho_json = "json/prova-oab-45-completa.json"
    caminho_saida = "json/classificacoes-oab-45.json"

    prova = carregar_prova(caminho_json)

    classificacoes = []

    questoes = prova["questoes"]

    for inicio in range(0, len(questoes), TAMANHO_LOTE):
        lote = questoes[inicio:inicio + TAMANHO_LOTE]

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
                "edicao": prova["edicao"],
                "ano": prova["ano"],
                "numero": classificacao["numero"],
                "disciplina_codigo": classificacao["disciplina_codigo"]
            }

            classificacoes.append(classificacao_completa)

            print(
                f"  Questão {classificacao['numero']} "
                f"→ {classificacao['disciplina_codigo']}"
            )

        salvar_classificacoes(
            caminho_saida,
            classificacoes
        )

        print(f"  Lote concluído.\n")

        if inicio + TAMANHO_LOTE < len(questoes):
            time.sleep(5)

    print()
    print(f"Classificação concluída: {caminho_saida}")
