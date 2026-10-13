"""Estado local e editável de uma atividade no TEApoia."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Atividade:
    nome: str = ""
    classe: str = ""
    materia: str = ""
    imagem: Path | None = None
    texto_ocr: str = ""
    texto: str = ""
    instrucao: str = ""
    disciplina: str = ""
    serie: str = ""
    tema: str = ""

    def limpar(self) -> None:
        self.nome = self.classe = self.materia = ""
        self.imagem = None
        self.texto_ocr = ""
        self.texto = ""
        self.instrucao = ""
        self.disciplina = self.serie = self.tema = ""
