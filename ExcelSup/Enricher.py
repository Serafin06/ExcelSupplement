import pandas as pd

from DataBase.Repository import DatabaseRepository


class DataEnricher:
    """
    Service odpowiedzialny za wzbogacanie danych (Single Responsibility Principle)
    """

    def __init__(self, repository: DatabaseRepository):
        self.repository = repository

    def enrich_dataframe(self, df: pd.DataFrame,
                         purchase_item_col: str = 'Purchase item number') -> pd.DataFrame:
        """
        Wzbogaca DataFrame o dane z bazy
        """
        # Pobierz unikalne numery artykułów
        unique_items = df[purchase_item_col].dropna().unique().tolist()
        unique_items = [str(item) for item in unique_items]

        # Pobierz dane z bazy
        article_data = self.repository.get_article_data(unique_items)

        # Przygotuj nowe kolumny
        df['SZEROKOSC_1'] = None
        df['GRUBOSC_11'] = None
        df['GRUBOSC_21'] = None
        df['GRUBOSC_31'] = None
        df['RECEPTURA_1'] = None
        df['TECH'] = None
        df['JM2'] = None

        # Dynamiczne kolumny dla warstw (maksymalnie 3)
        df['WARSTWA_1'] = None
        df['WARSTWA_2'] = None
        df['WARSTWA_3'] = None

        # Wypełnij dane
        for idx, row in df.iterrows():
            purchase_item = str(row[purchase_item_col])
            if purchase_item in article_data:
                data = article_data[purchase_item]

                df.at[idx, 'SZEROKOSC_1'] = data.szerokosc_1
                df.at[idx, 'GRUBOSC_11'] = data.grubosc_11
                df.at[idx, 'GRUBOSC_21'] = data.grubosc_21
                df.at[idx, 'GRUBOSC_31'] = data.grubosc_31
                df.at[idx, 'RECEPTURA_1'] = data.receptura_1
                df.at[idx, 'TECH'] = data.tech
                df.at[idx, 'JM2'] = data.jm2

                # Wypełnij warstwy
                warstwy = data.warstwy
                for i, warstwa in enumerate(warstwy[:3], 1):
                    df.at[idx, f'WARSTWA_{i}'] = warstwa

        return df