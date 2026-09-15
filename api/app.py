from flask import Flask, jsonify
from consultas import buscar_questao_por_uuid


app = Flask(__name__)


@app.route("/questoes-oab/questoes/<uuid>")
def consultar_questao(uuid):
    resultado = buscar_questao_por_uuid(uuid)

    if not resultado:
        return jsonify({
            "erro": "Questão não encontrada"
        }), 404

    primeira_linha = resultado[0]

    questao = {
        "uuid": str(primeira_linha[0]),
        "numero": primeira_linha[1],
        "enunciado": primeira_linha[2],
        "prova": {
            "edicao": primeira_linha[3],
            "ano": primeira_linha[4]
        },
        "disciplina": None,
        "alternativas": [],
        "resposta_correta": None
    }

    if primeira_linha[5] is not None:
        questao["disciplina"] = {
            "uuid": str(primeira_linha[5]),
            "nome": primeira_linha[6]
        }

    for linha in resultado:
        alternativa = {
            "letra": linha[7],
            "enunciado": linha[8]
        }

        questao["alternativas"].append(alternativa)

        if linha[9]:
            questao["resposta_correta"] = linha[7]

    return jsonify(questao)


if __name__ == "__main__":
    app.run(debug=True)