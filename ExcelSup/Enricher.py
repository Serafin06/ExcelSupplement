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
        Wzbogaca DataFrame o dane z bazy i mapuje materiały
        """
        # Pobierz unikalne numery artykułów
        unique_items = df[purchase_item_col].dropna().unique().tolist()
        unique_items = [str(item) for item in unique_items]

        # Pobierz dane z bazy
        article_data = self.repository.get_article_data(unique_items)

        # Przygotuj kolumny dla danych bazowych
        df['SZEROKOSC_1'] = None
        df['GRUBOSC_11'] = None
        df['GRUBOSC_21'] = None
        df['GRUBOSC_31'] = None
        df['RECEPTURA_1'] = None
        df['TECH'] = None
        df['JM2'] = None
        df['TOTAL_THICKNESS'] = None
        df['SALES_DATES'] = None

        # Kolumny dla Material Type 1 (Kolumny I, J, K)
        df['Material_type_1'] = None
        df['Material_1_proportion_%'] = None
        df['Material_1_contact'] = None

        # Kolumny dla Material Type 2 (Kolumny M, N, O)
        df['Material_type_2'] = None
        df['Material_2_proportion_%'] = None
        df['Material_2_contact'] = None

        # Kolumny dla Material Type 3 (Kolumny Q, R, S)
        df['Material_type_3'] = None
        df['Material_3_proportion_%'] = None
        df['Material_3_contact'] = None

        # Wypełnij dane
        for idx, row in df.iterrows():
            purchase_item = str(row[purchase_item_col])
            if pd.isna(purchase_item):
                continue

            if purchase_item in article_data:
                data = article_data[purchase_item]

                # Dane bazowe
                df.at[idx, 'SZEROKOSC_1'] = data.szerokosc_1
                df.at[idx, 'GRUBOSC_11'] = data.grubosc_11
                df.at[idx, 'GRUBOSC_21'] = data.grubosc_21
                df.at[idx, 'GRUBOSC_31'] = data.grubosc_31
                df.at[idx, 'RECEPTURA_1'] = data.receptura_1
                df.at[idx, 'TECH'] = data.tech
                df.at[idx, 'JM2'] = data.jm2
                df.at[idx, 'TOTAL_THICKNESS'] = data.total_thickness

                # Warstwy z proporcjami
                layer_proportions = data.get_layer_proportions()

                # Material Type 1
                if len(layer_proportions) >= 1:
                    layer, proportion = layer_proportions[0]
                    df.at[idx, 'Material_type_1'] = layer.material_type
                    df.at[idx, 'Material_1_proportion_%'] = round(proportion, 2)
                    df.at[idx, 'Material_1_contact'] = 'YES'  # Domyślnie YES, można zmienić

                # Material Type 2
                if len(layer_proportions) >= 2:
                    layer, proportion = layer_proportions[1]
                    df.at[idx, 'Material_type_2'] = layer.material_type
                    df.at[idx, 'Material_2_proportion_%'] = round(proportion, 2)
                    df.at[idx, 'Material_2_contact'] = 'NO'  # Warstwa środkowa zwykle NO

                # Material Type 3
                if len(layer_proportions) >= 3:
                    layer, proportion = layer_proportions[2]
                    df.at[idx, 'Material_type_3'] = layer.material_type
                    df.at[idx, 'Material_3_proportion_%'] = round(proportion, 2)
                    df.at[idx, 'Material_3_contact'] = 'YES'  # Zewnętrzna warstwa YES

        return df