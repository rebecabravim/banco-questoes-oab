from flask import Flask, jsonify
from consultas import buscar_questoes, buscar_questao_por_uuid

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
    resultado = buscar_questoes()

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


if __name__ == "__main__":
    app.run(debug=True)