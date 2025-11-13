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

    def __init__(self, engine: Engine, date_start: str = '2024-10-01', date_end: str = '2025-09-30'):
        self.engine = engine
        self.date_start = date_start
        self.date_end = date_end

    def get_article_data(self, art_numbers: List[str]) -> Dict[str, ArticleData]:
        """Pobiera dane artykułów z tabeli ZO:
        - sumuje TECH (ilości) w okresie Q4'24-Q3'25
        - jeśli nie znaleziono, zapisuje tylko datę ostatniej sprzedaży spoza okresu
        """
        if not art_numbers:
            return {}

        conditions = []
        params = {
            'date_start': self.date_start,
            'date_end': self.date_end
        }

        for i, art in enumerate(art_numbers):
            param_exact = f'art_exact_{i}'
            param_like = f'art_like_{i}'
            conditions.append(f"(ART = :{param_exact} OR ART LIKE :{param_like})")
            params[param_exact] = art
            params[param_like] = f'%{art}%'

        where_clause = ' OR '.join(conditions)

        # --- 1️⃣ Szukaj w Q4'24-Q3'25, sumuj TECH ---
        query_in_period = text(f"""
            WITH ArticleSummary AS (
                SELECT 
                    ART,
                    MAX(SZEROKOSC_1) AS SZEROKOSC_1,
                    MAX(GRUBOSC_11) AS GRUBOSC_11,
                    MAX(GRUBOSC_21) AS GRUBOSC_21,
                    MAX(GRUBOSC_31) AS GRUBOSC_31,
                    MAX(RECEPTURA_1) AS RECEPTURA_1,
                    SUM(TECH) AS SUM_TECH,               -- 🔹 sumowanie ilości
                    MAX(JM2) AS JM2,
                    MAX(DATA_SPRZ) AS LAST_DATE           -- 🔹 ostatnia sprzedaż w okresie
                FROM ZO
                WHERE ({where_clause})
                  AND DATA_SPRZ >= :date_start 
                  AND DATA_SPRZ <= :date_end
                GROUP BY ART
            )
            SELECT 
                ART, SZEROKOSC_1, GRUBOSC_11, GRUBOSC_21, GRUBOSC_31,
                RECEPTURA_1, SUM_TECH, JM2, LAST_DATE
            FROM ArticleSummary
        """)

        result = {}
        found_arts = set()

        with self.engine.connect() as conn:
            rows = conn.execute(query_in_period, params).fetchall()

            for row in rows:
                db_art = row[0]
                matched_original = next((a for a in art_numbers if a in db_art or a == db_art), None)

                if matched_original:
                    found_arts.add(matched_original)
                    result[matched_original] = ArticleData(
                        art=db_art,
                        szerokosc_1=row[1],
                        grubosc_11=row[2],
                        grubosc_21=row[3],
                        grubosc_31=row[4],
                        receptura_1=row[5],
                        tech=row[6],  # teraz to suma TECH
                        jm2=row[7],
                        termin_zak=row[8]  # ostatnia sprzedaż z okresu
                    )

            # --- 2️⃣ Szukaj poza okresem – tylko ostatnia data ---
            missing_arts = [art for art in art_numbers if art not in found_arts]

            if missing_arts:
                conditions_missing = []
                params_missing = {'date_start': '2024-10-01'}

                for i, art in enumerate(missing_arts):
                    param_exact = f'miss_exact_{i}'
                    param_like = f'miss_like_{i}'
                    conditions_missing.append(f"(ART = :{param_exact} OR ART LIKE :{param_like})")
                    params_missing[param_exact] = art
                    params_missing[param_like] = f'%{art}%'

                where_clause_missing = ' OR '.join(conditions_missing)

                query_before_period = text(f"""
                    SELECT 
                        ART,
                        MAX(DATA_SPRZ) AS LAST_DATE
                    FROM ZO
                    WHERE ({where_clause_missing})
                      AND DATA_SPRZ < :date_start
                    GROUP BY ART
                """)

                rows_before = conn.execute(query_before_period, params_missing).fetchall()

                for row in rows_before:
                    db_art = row[0]
                    matched_original = next((a for a in missing_arts if a in db_art or a == db_art), None)

                    if matched_original:
                        result[matched_original] = ArticleData(
                            art=db_art,
                            szerokosc_1=None,
                            grubosc_11=None,
                            grubosc_21=None,
                            grubosc_31=None,
                            receptura_1=None,
                            tech=None,
                            jm2=None,
                            termin_zak=row[1]
                        )

        return result

    def close(self):
        """Zamyka połączenie z bazą"""
        self.engine.dispose()
