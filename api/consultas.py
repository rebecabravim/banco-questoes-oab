from banco import conectar_banco


def buscar_questao_por_uuid(uuid):
    conexao = conectar_banco()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                SELECT
                    q.uuid,
                    q.numero,
                    q.enunciado,
                    p.edicao,
                    p.ano,
                    d.uuid,
                    d.nome,
                    a.letra,
                    a.enunciado,
                    a.resposta_correta
                FROM questao q
                INNER JOIN prova p
                    ON p.uuid = q.prova_uuid
                LEFT JOIN disciplina d
                    ON d.uuid = q.disciplina_uuid
                INNER JOIN alternativa a
                    ON a.questao_uuid = q.uuid
                WHERE q.uuid = %s
                ORDER BY a.letra
            """, (uuid,))

            return cursor.fetchall()

    finally:
        conexao.close()