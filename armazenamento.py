"""Histórico local em JSON, sem banco de dados ou servidor."""

import json
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class ExercicioSalvo:
    nome: str
    classe: str
    materia: str
    texto: str
    texto_ocr: str
    adaptado: str
    preferencias: list[str]
    instrucao: str
    imagem: str = ""
    tipo: str = "adaptado"
    identificador: str = field(default_factory=lambda: str(uuid.uuid4()))
    atualizado_em: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y %H:%M"))


class BibliotecaLocal:
    """Repositório simples, substituível por banco de dados no futuro."""

    def __init__(self, pasta: Path | None = None) -> None:
        self.pasta = pasta or Path(__file__).parent / "dados"
        self.arquivo = self.pasta / "exercicios.json"
        self.imagens = self.pasta / "imagens"

    def listar(self) -> list[ExercicioSalvo]:
        if not self.arquivo.exists():
            return []
        try:
            registros = json.loads(self.arquivo.read_text(encoding="utf-8"))
            if not isinstance(registros, list):
                return []

            itens = []
            for registro in registros:
                if not isinstance(registro, dict):
                    return []
                # Registros gravados antes da classificação são adaptações.
                dados = dict(registro)
                if dados.get("tipo") not in {"criado", "adaptado"}:
                    dados["tipo"] = "adaptado"
                itens.append(ExercicioSalvo(**dados))
            return itens
        except (json.JSONDecodeError, OSError, TypeError):
            return []

    def buscar(self, identificador: str) -> ExercicioSalvo | None:
        return next((item for item in self.listar() if item.identificador == identificador), None)

    def salvar(self, item: ExercicioSalvo, imagem_origem: Path | None = None) -> ExercicioSalvo:
        self.pasta.mkdir(parents=True, exist_ok=True)
        if imagem_origem and imagem_origem.is_file():
            self.imagens.mkdir(exist_ok=True)
            destino = self.imagens / f"{item.identificador}{imagem_origem.suffix.lower()}"
            shutil.copy2(imagem_origem, destino)
            item.imagem = str(destino)
        itens = [existente for existente in self.listar() if existente.identificador != item.identificador]
        itens.insert(0, item)
        self.arquivo.write_text(json.dumps([asdict(x) for x in itens], ensure_ascii=False, indent=2), encoding="utf-8")
        return item

    def excluir(self, identificador: str) -> bool:
        """Remove somente o exercício identificado e sua cópia local de imagem, se houver."""
        itens = self.listar()
        alvo = next((item for item in itens if item.identificador == identificador), None)
        if alvo is None:
            return False

        restantes = [item for item in itens if item.identificador != identificador]
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.arquivo.write_text(
            json.dumps([asdict(item) for item in restantes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if alvo.imagem:
            try:
                caminho_imagem = Path(alvo.imagem).resolve()
                if caminho_imagem.parent == self.imagens.resolve() and caminho_imagem.is_file():
                    caminho_imagem.unlink()
            except OSError:
                pass
        return True
