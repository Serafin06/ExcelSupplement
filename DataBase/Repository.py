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
    def get_sales_dates(self, art_numbers: List[str]) -> Dict[str, List[str]]:
        """Pobiera daty sprzedaży dla artykułów"""
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
        """Pobiera dane artykułów z tabeli ZO - najpierw Q4'24-Q3'25, potem wcześniejsze"""
        if not art_numbers:
            return {}

        conditions = []
        params = {
            'date_start': '2024-10-01',
            'date_end': '2025-09-30'
        }

        for i, art in enumerate(art_numbers):
            param_exact = f'art_exact_{i}'
            param_like = f'art_like_{i}'

            conditions.append(f"(ART = :{param_exact} OR ART LIKE :{param_like})")
            params[param_exact] = art
            params[param_like] = f'%{art}%'

        where_clause = ' OR '.join(conditions)

        # Krok 1: Szukaj w Q4'24-Q3'25
        query_in_period = text(f"""
            WITH RankedArticles AS (
                SELECT 
                    ART,
                    SZEROKOSC_1,
                    GRUBOSC_11,
                    GRUBOSC_21,
                    GRUBOSC_31,
                    RECEPTURA_1,
                    TECH,
                    JM2,
                    DATA_SPRZ,
                    ROW_NUMBER() OVER (PARTITION BY ART ORDER BY DATA_SPRZ DESC) as rn
                FROM ZO
                WHERE ({where_clause})
                  AND DATA_SPRZ >= :date_start 
                  AND DATA_SPRZ <= :date_end
            )
            SELECT 
                ART, SZEROKOSC_1, GRUBOSC_11, GRUBOSC_21, GRUBOSC_31,
                RECEPTURA_1, TECH, JM2, DATA_SPRZ
            FROM RankedArticles
            WHERE rn = 1
        """)

        result = {}
        found_arts = set()

        with self.engine.connect() as conn:
            # Pobierz z okresu Q4'24-Q3'25
            rows = conn.execute(query_in_period, params).fetchall()

            for row in rows:
                db_art = row[0]
                matched_original = None

                for original_art in art_numbers:
                    if original_art in db_art or db_art == original_art:
                        matched_original = original_art
                        break

                if matched_original:
                    found_arts.add(matched_original)
                    result[matched_original] = ArticleData(
                        art=db_art,
                        szerokosc_1=row[1],
                        grubosc_11=row[2],
                        grubosc_21=row[3],
                        grubosc_31=row[4],
                        receptura_1=row[5],
                        tech=row[6],
                        jm2=row[7]
                    )

            # Krok 2: Dla nieznalezionych, szukaj przed okresem
            missing_arts = [art for art in art_numbers if art not in found_arts]

            if missing_arts:
                conditions_missing = []
                params_missing = {}

                for i, art in enumerate(missing_arts):
                    param_exact = f'miss_exact_{i}'
                    param_like = f'miss_like_{i}'

                    conditions_missing.append(f"(ART = :{param_exact} OR ART LIKE :{param_like})")
                    params_missing[param_exact] = art
                    params_missing[param_like] = f'%{art}%'

                where_clause_missing = ' OR '.join(conditions_missing)
                params_missing['date_start'] = '2024-10-01'

                query_before_period = text(f"""
                    WITH RankedArticles AS (
                        SELECT 
                            ART,
                            SZEROKOSC_1,
                            GRUBOSC_11,
                            GRUBOSC_21,
                            GRUBOSC_31,
                            RECEPTURA_1,
                            TECH,
                            JM2,
                            DATA_SPRZ,
                            ROW_NUMBER() OVER (PARTITION BY ART ORDER BY DATA_SPRZ DESC) as rn
                        FROM ZO
                        WHERE ({where_clause_missing})
                          AND DATA_SPRZ < :date_start
                    )
                    SELECT 
                        ART, SZEROKOSC_1, GRUBOSC_11, GRUBOSC_21, GRUBOSC_31,
                        RECEPTURA_1, TECH, JM2, DATA_SPRZ
                    FROM RankedArticles
                    WHERE rn = 1
                """)

                rows_before = conn.execute(query_before_period, params_missing).fetchall()

                for row in rows_before:
                    db_art = row[0]
                    matched_original = None

                    for original_art in missing_arts:
                        if original_art in db_art or db_art == original_art:
                            matched_original = original_art
                            break

                    if matched_original:
                        result[matched_original] = ArticleData(
                            art=db_art,
                            szerokosc_1=row[1],
                            grubosc_11=row[2],
                            grubosc_21=row[3],
                            grubosc_31=row[4],
                            receptura_1=row[5],
                            tech=row[6],
                            jm2=row[7]
                        )

        return result

    def get_sales_dates(self, art_numbers: List[str]) -> Dict[str, List[str]]:
        """Pobiera daty sprzedaży - pokazuje czy w okresie Q4'24-Q3'25 czy wcześniej"""
        if not art_numbers:
            return {}

        conditions = []
        params = {
            'date_start': '2024-10-01',
            'date_end': '2025-09-30'
        }

        for i, art in enumerate(art_numbers):
            param_exact = f'art_exact_{i}'
            param_like = f'art_like_{i}'

            conditions.append(f"(ART = :{param_exact} OR ART LIKE :{param_like})")
            params[param_exact] = art
            params[param_like] = f'%{art}%'

        where_clause = ' OR '.join(conditions)

        query = text(f"""
            SELECT 
                ART,
                DATA_SPRZ,
                CASE 
                    WHEN DATA_SPRZ >= :date_start AND DATA_SPRZ <= :date_end THEN 'IN_PERIOD'
                    ELSE 'BEFORE_PERIOD'
                END as PERIOD_FLAG
            FROM ZO
            WHERE ({where_clause}) AND DATA_SPRZ IS NOT NULL
            ORDER BY ART, DATA_SPRZ DESC
        """)

        result = {}
        with self.engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()

            for row in rows:
                db_art = row[0]
                sale_date = row[1].strftime('%Y-%m-%d') if row[1] else ''
                period_flag = row[2]

                matched_original = None
                for original_art in art_numbers:
                    if original_art in db_art or db_art == original_art:
                        matched_original = original_art
                        break

                if matched_original:
                    if matched_original not in result:
                        result[matched_original] = []
                    # Ograniczamy do max 5 dat
                    if len(result[matched_original]) < 1:
                        result[matched_original].append(f"{sale_date} ({period_flag})")

        return result

    def close(self):
        """Zamyka połączenie z bazą"""
        self.engine.dispose()
