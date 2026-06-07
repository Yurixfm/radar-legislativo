from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Proposicao:
    """Representa uma proposicao legislativa acompanhada pelo radar."""

    identificador: str
    titulo: str
    ementa: str
    temas: tuple[str, ...] = field(default_factory=tuple)
    data_apresentacao: date | None = None
    urgencia: bool = False

    def texto_indexado(self) -> str:
        partes = [self.identificador, self.titulo, self.ementa, *self.temas]
        return " ".join(partes).casefold()

