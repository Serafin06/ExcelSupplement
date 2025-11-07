from abc import abstractmethod, ABC
from datetime import date
from typing import List, Dict

from sqlalchemy import Engine, text

from DataBase.Data import ArticleData


class DatabaseRepository(ABC):
    """Interfejs do komunikacji z bazą danych (Dependency Inversion Principle)"""

    @abstractmethod
    def get_article_data(self, art_numbers: List[str]) -> Dict[str, ArticleData]:
        """Pobiera dane artykułów z bazy na podstawie numerów ART"""
        pass

    @abstractmethod
    def close(self):
        """Zamyka połączenie z bazą"""
        pass


class SQLAlchemyRepository(DatabaseRepository):
    """Konkretna implementacja repozytorium dla SQL Server z SQLAlchemy"""

    def __init__(self, engine: Engine):
        self.engine = engine

    def get_article_data(self, art_numbers: List[str]) -> Dict[str, ArticleData]:
        """Pobiera dane artykułów z tabeli KO - uniwersalne dopasowanie i ograniczenie datowe"""
        if not art_numbers:
            return {}

        # Warunki LIKE dla każdego indeksu
        conditions = " OR ".join([f"ART LIKE :art_{i}" for i in range(len(art_numbers))])

        query = text(f"""
            SELECT 
                ART,
                SZEROKOSC_1,
                GRUBOSC_11,
                GRUBOSC_21,
                GRUBOSC_31,
                RECEPTURA_1,
                TECH,
                JM2,
                TERMIN_ZAK
            FROM ZO
            WHERE ({conditions})
              AND TERMIN_ZAK >= :start_date
              AND TERMIN_ZAK <= :end_date
        """)

        # Parametry dla LIKE
        params = {f'art_{i}': f'{art}%' for i, art in enumerate(art_numbers)}
        # Parametry dla dat
        params['start_date'] = date(2024, 9, 28)
        params['end_date'] = date(2025, 9, 30)

        result = {}
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                result[row[0]] = ArticleData(
                    art=row[0],
                    szerokosc_1=row[1],
                    grubosc_11=row[2],
                    grubosc_21=row[3],
                    grubosc_31=row[4],
                    receptura_1=row[5],
                    tech=row[6],
                    jm2=row[7]
                )

        return result

    def close(self):
        """Zamyka połączenie z bazą"""
        self.engine.dispose()