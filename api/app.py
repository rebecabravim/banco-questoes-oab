from flask import Flask, jsonify, request
from consultas import (
    buscar_questoes,
    buscar_questao_por_uuid,
    buscar_anos,
    buscar_edicoes,
    buscar_disciplinas
)

app = Flask(__name__)

app.json.ensure_ascii = False


def montar_questoes(resultado):
    questoes = {}

    for linha in resultado:
        uuid = str(linha[0])

        if uuid not in questoes:
            questoes[uuid] = {
                "uuid": uuid,
                "numero": linha[1],
                "enunciado": linha[2],
                "prova": {
                    "edicao": linha[3],
                    "ano": linha[4]
                },
                "disciplina": None,
                "alternativas": [],
                "resposta_correta": None
            }

            if linha[5] is not None:
                questoes[uuid]["disciplina"] = {
                    "uuid": str(linha[5]),
                    "nome": linha[6]
                }

        alternativa = {
            "letra": linha[7],
            "enunciado": linha[8]
        }

        questoes[uuid]["alternativas"].append(alternativa)

        if linha[9]:
            questoes[uuid]["resposta_correta"] = linha[7]

    return list(questoes.values())


@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "API de questões da OAB funcionando"
    })


@app.route("/questoes-oab/questoes")
def consultar_questoes():

    parametros_validos = {"ano", "edicao", "disciplina-codigo", "numero"}

    parametros_recebidos = set(request.args.keys())

    parametros_invalidos = parametros_recebidos - parametros_validos

    if parametros_invalidos:
        return jsonify({
            "erro": "Parâmetro inválido",
            "parametros": list(parametros_invalidos)
        }), 400

    
    ano = request.args.get("ano", type=int)
    edicao = request.args.get("edicao", type=int)
    disciplina = request.args.get("disciplina-codigo")
    numero = request.args.get("numero", type=int)

    resultado = buscar_questoes(
        ano=ano,
        edicao=edicao,
        disciplina=disciplina,
        numero=numero
    )

    questoes = montar_questoes(resultado)

    return jsonify(questoes)


@app.route("/questoes-oab/questoes/<uuid>")
def consultar_questao(uuid):
    resultado = buscar_questao_por_uuid(uuid)

    if not resultado:
        return jsonify({
            "erro": "Questão não encontrada"
        }), 404

    questoes = montar_questoes(resultado)

    return jsonify(questoes[0])

@app.route("/questoes-oab/anos")
def consultar_anos():
    resultado = buscar_anos()

    anos = [linha[0] for linha in resultado]

    return jsonify(anos)


@app.route("/questoes-oab/edicoes")
def consultar_edicoes():
    resultado = buscar_edicoes()

    edicoes = [linha[0] for linha in resultado]

    return jsonify(edicoes)


@app.route("/questoes-oab/disciplinas")
def consultar_disciplinas():
    resultado = buscar_disciplinas()

    disciplinas = []

    for linha in resultado:
        disciplinas.append({
            "uuid": str(linha[0]),
            "nome": linha[1],
            "codigo": linha[2]
        })

    return jsonify(disciplinas)


if __name__ == "__main__":
    app.run(debug=True)