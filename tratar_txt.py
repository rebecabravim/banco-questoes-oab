
import argparse
import re
from pathlib import Path


PASTA_SAIDA = Path("provas-tratadas")

PADRAO_ALTERNATIVA_SEM_PARENTESES = r'(?m)^([A-E])\)'
PADRAO_ALTERNATIVA_COLADA = r'(?m)^(\([A-E]\))([A-Za-zÀ-ÿ])'

PADRAO_ALTERNATIVA_J = r'(?m)^\(([A-E])\s*J(?=[A-Za-zÀ-ÿ])'
PADRAO_ALTERNATIVA_J_COM_ESPACO = r'(?m)^\(([A-E])\s*J\)\s*'


def identificar_questao(texto, posicao):
    """
    Identifica a questão à qual pertence uma alteração,
    considerando o último número isolado antes do trecho.
    """

    texto_anterior = texto[:posicao]

    ocorrencias = list(
        re.finditer(r'(?m)^(\d{1,2})\s*$', texto_anterior)
    )

    if ocorrencias:
        return int(ocorrencias[-1].group(1))

    return "Não identificada"


def registrar_alteracoes(texto, padrao, substituicao, descricao, alteracoes):
    """
    Executa uma substituição e registra cada alteração realizada.
    """

    def substituir(ocorrencia):
        antes = ocorrencia.group(0)

        if callable(substituicao):
            depois = substituicao(ocorrencia)
        else:
            depois = ocorrencia.expand(substituicao)

        alteracoes.append({
            "questao": identificar_questao(texto, ocorrencia.start()),
            "correcao": descricao,
            "antes": antes,
            "depois": depois
        })

        return depois

    return re.sub(padrao, substituir, texto)


def normalizar_alternativas(texto, alteracoes):
    """
    Converte marcadores como:

    A)
    B)
    C)
    D)

    para:

    (A)
    (B)
    (C)
    (D)
    """

    return registrar_alteracoes(
        texto,
        PADRAO_ALTERNATIVA_SEM_PARENTESES,
        r'(\1)',
        "Normalização do marcador de alternativa",
        alteracoes
    )


def corrigir_espacamento_alternativas(texto, alteracoes):
    """
    Corrige alternativas coladas ao início do texto.

    Exemplo:

    (A)A publicidade

    para:

    (A) A publicidade
    """

    return registrar_alteracoes(
        texto,
        PADRAO_ALTERNATIVA_COLADA,
        r'\1 \2',
        "Correção de espaçamento da alternativa",
        alteracoes
    )


def corrigir_alternativas_com_j(texto, alteracoes):
    """
    Corrige casos em que o OCR reconheceu o fechamento
    da alternativa como a letra J.

    Exemplos:

    (DJO     -> (D) O
    (AJÉ     -> (A) É
    (BJn     -> (B) n
    (B JO    -> (B) O
    (D JO    -> (D) O
    """

    texto = registrar_alteracoes(
        texto,
        PADRAO_ALTERNATIVA_J_COM_ESPACO,
        lambda m: f"({m.group(1)}) ",
        "Correção de fechamento reconhecido como J",
        alteracoes
    )

    texto = registrar_alteracoes(
        texto,
        PADRAO_ALTERNATIVA_J,
        lambda m: f"({m.group(1)}) ",
        "Correção de fechamento reconhecido como J",
        alteracoes
    )

    return texto


def corrigir_erro_771(texto, alteracoes):
    """
    Corrige o erro específico de OCR em que 77 é reconhecido como 771.
    """

    return registrar_alteracoes(
        texto,
        r'(?m)^771$',
        '77',
        "Correção do número da questão reconhecido como 771",
        alteracoes
    )


def tratar_texto(texto):
    """
    Realiza correções estruturais e registra as alterações.
    """

    alteracoes = []

    texto = corrigir_alternativas_com_j(texto, alteracoes)
    texto = normalizar_alternativas(texto, alteracoes)
    texto = corrigir_erro_771(texto, alteracoes)
    texto = corrigir_espacamento_alternativas(texto, alteracoes)

    return texto, alteracoes


def salvar_log(alteracoes, caminho_saida):
    """
    Salva o relatório das alterações realizadas.
    """

    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as arquivo:

        arquivo.write("RELATÓRIO DE ALTERAÇÕES DO TRATAMENTO OCR\n")
        arquivo.write("=" * 60 + "\n\n")

        if not alteracoes:
            arquivo.write("Nenhuma alteração foi realizada.\n")
            return

        arquivo.write(f"Total de alterações: {len(alteracoes)}\n\n")

        for alteracao in alteracoes:

            arquivo.write(f"QUESTÃO {alteracao['questao']}\n")
            arquivo.write(f"Correção: {alteracao['correcao']}\n")
            arquivo.write(f"Antes: {alteracao['antes']!r}\n")
            arquivo.write(f"Depois: {alteracao['depois']!r}\n")
            arquivo.write("-" * 60 + "\n")


def tratar_arquivo(caminho_entrada):
    caminho_entrada = Path(caminho_entrada)

    texto = caminho_entrada.read_text(encoding="utf-8")

    texto_tratado, alteracoes = tratar_texto(texto)

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    caminho_saida = PASTA_SAIDA / caminho_entrada.name

    caminho_saida.write_text(
        texto_tratado,
        encoding="utf-8"
    )

    caminho_log =   PASTA_SAIDA / "logs" / f"{caminho_entrada.stem}.log.txt"

    salvar_log(alteracoes, caminho_log)

    return caminho_saida, caminho_log, alteracoes


def main():
    parser = argparse.ArgumentParser(
        description="Realiza o tratamento do texto extraído por OCR."
    )

    parser.add_argument(
        "entrada",
        help="Caminho do arquivo TXT gerado pelo OCR."
    )

    argumentos = parser.parse_args()

    caminho_saida, caminho_log, alteracoes = tratar_arquivo(
        argumentos.entrada
    )

    print(f"Arquivo tratado com sucesso: {caminho_saida}")
    print(f"Alterações realizadas: {len(alteracoes)}")
    print(f"Relatório de alterações: {caminho_log}")


if __name__ == "__main__":
    main()
