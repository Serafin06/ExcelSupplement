"""
Excel-SQL Data Enrichment Script
Pobiera dane z tabeli KO na podstawie Purchase Item Number i wzbogaca Excel
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ArticleData:
    """Value Object przechowujący dane artykułu z bazy"""
    art: str
    szerokosc_1: Optional[int]
    grubosc_11: Optional[str]
    grubosc_21: Optional[str]
    grubosc_31: Optional[str]
    receptura_1: Optional[str]
    tech: Optional[float]
    jm2: Optional[str]

    @property
    def warstwy(self) -> List[str]:
        """Ekstrahuje warstwy z receptury"""
        if not self.receptura_1:
            return []
        # Zakładam format typu "PE/PA/PE" lub podobny
        return [w.strip() for w in self.receptura_1.split('/') if w.strip()]

    @property
    def is_trojwarstwowe(self) -> bool:
        """Sprawdza czy materiał jest trójwarstwowy"""
        return self.grubosc_31 is not None and self.grubosc_31 != ''
