from banco import conectar_banco


def buscar_questoes(ano=None, edicao=None, disciplina=None, numero=None):
    conexao = conectar_banco()

    try:
         with conexao.cursor() as cursor:
            consulta = """
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
                WHERE 1 = 1
            """

            parametros = []

            if ano is not None:
                consulta += " AND p.ano = %s"
                parametros.append(ano)

            if edicao is not None:
                consulta += " AND p.edicao = %s"
                parametros.append(edicao)

            if disciplina is not None:
                consulta += """
                    AND d.codigo = %s
                """
                parametros.append(disciplina)

            if numero is not None:
                consulta += " AND q.numero = %s"
                parametros.append(numero)

            consulta += """
                ORDER BY p.ano, p.edicao, q.numero, a.letra
            """

            cursor.execute(consulta, parametros)

            return cursor.fetchall()

    finally:
        conexao.close()


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

def buscar_anos():
    conexao = conectar_banco()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT ano
                FROM prova
                ORDER BY ano DESC
            """)

            return cursor.fetchall()

    finally:
        conexao.close()

def buscar_edicoes():
    conexao = conectar_banco()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT edicao
                FROM prova
                ORDER BY edicao DESC
            """)

            return cursor.fetchall()

    finally:
        conexao.close()

def buscar_disciplinas():
    conexao = conectar_banco()

    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                SELECT
                    uuid,
                    nome,
                    codigo
                FROM disciplina
                ORDER BY nome
            """)

            return cursor.fetchall()

    finally:
        conexao.close()