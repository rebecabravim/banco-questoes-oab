CREATE TABLE prova (
    uuid UUID PRIMARY KEY,
    edicao INTEGER NOT NULL,
    ano INTEGER NOT NULL
);

CREATE TABLE questao (
    uuid UUID PRIMARY KEY,
    numero INTEGER NOT NULL,
    enunciado TEXT NOT NULL,
    prova_uuid UUID NOT NULL,
    disciplina_uuid UUID,

    FOREIGN KEY (prova_uuid) REFERENCES prova(uuid)
);

CREATE TABLE alternativa (
    uuid UUID PRIMARY KEY,
    letra CHAR(1) NOT NULL,
    enunciado TEXT NOT NULL,
    resposta_correta BOOLEAN NOT NULL,
    questao_uuid UUID NOT NULL,

    FOREIGN KEY (questao_uuid) REFERENCES questao(uuid)
);

ALTER TABLE alternativa
ADD CONSTRAINT ck_alternativa_letra
CHECK (letra IN ('A', 'B', 'C', 'D'));

ALTER TABLE prova
ALTER COLUMN uuid SET DEFAULT gen_random_uuid();

ALTER TABLE questao
ALTER COLUMN uuid SET DEFAULT gen_random_uuid();

ALTER TABLE alternativa
ALTER COLUMN uuid SET DEFAULT gen_random_uuid();

ALTER TABLE prova
ADD CONSTRAINT uq_prova_edicao_ano
UNIQUE (edicao, ano);

ALTER TABLE questao
ADD CONSTRAINT uq_questao_prova_numero
UNIQUE (prova_uuid, numero);

ALTER TABLE alternativa
ADD CONSTRAINT uq_alternativa_questao_letra
UNIQUE (questao_uuid, letra);

ALTER TABLE questao
DROP CONSTRAINT questao_prova_uuid_fkey;

ALTER TABLE questao
ADD CONSTRAINT questao_prova_uuid_fkey
FOREIGN KEY (prova_uuid)
REFERENCES prova(uuid)
ON DELETE CASCADE;

ALTER TABLE alternativa
DROP CONSTRAINT alternativa_questao_uuid_fkey;

ALTER TABLE alternativa
ADD CONSTRAINT alternativa_questao_uuid_fkey
FOREIGN KEY (questao_uuid)
REFERENCES questao(uuid)
ON DELETE CASCADE;

CREATE TABLE disciplina (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL UNIQUE
);

ALTER TABLE questao
ADD CONSTRAINT questao_disciplina_uuid_fkey
FOREIGN KEY (disciplina_uuid)
REFERENCES disciplina(uuid);