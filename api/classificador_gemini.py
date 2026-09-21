import json
import os

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


load_dotenv()

chave_api = os.getenv("GEMINI_API_KEY")

if not chave_api:
    raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env")

cliente = genai.Client(api_key=chave_api)


def classificar_questao(enunciado, alternativas):
    disciplinas = "\n".join(
        f"- {disciplina}"
        for disciplina in DISCIPLINAS
    )

    texto_alternativas = "\n".join(
        f"{alternativa['letra']}) {alternativa['enunciado']}"
        for alternativa in alternativas
    )

    prompt = f"""
Você é um classificador de questões da primeira fase do Exame da OAB.

Classifique a questão em exatamente uma das disciplinas abaixo:

{disciplinas}

Regras:
- Escolha exatamente uma disciplina.
- Não crie uma nova disciplina.
- Retorne somente o código da disciplina.
- Considere o conteúdo jurídico principal da questão.
- Não classifique com base apenas em palavras isoladas.
- O código retornado deve ser exatamente igual a um dos códigos fornecidos.

Enunciado:
{enunciado}

Alternativas:
{texto_alternativas}
"""

    resposta = cliente.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    disciplina = resposta.text.strip()

    if disciplina not in DISCIPLINAS:
        raise ValueError(
            f"Gemini retornou uma disciplina inválida: {disciplina}"
        )

    return disciplina


def carregar_prova(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


if __name__ == "__main__":
    caminho_json = "json/prova-oab-45-completa.json"
    caminho_saida = "json/classificacoes-oab-45.json"

    prova = carregar_prova(caminho_json)

    classificacoes = []

    for questao in prova["questoes"]:
        print(f"Classificando questão {questao['numero']}...")

        disciplina = classificar_questao(
            questao["enunciado"],
            questao["alternativas"]
        )

        classificacoes.append({
            "edicao": prova["edicao"],
            "ano": prova["ano"],
            "numero": questao["numero"],
            "disciplina_codigo": disciplina
        })

        print(f"  → {disciplina}")

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(
            classificacoes,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(f"Classificação concluída: {caminho_saida}")