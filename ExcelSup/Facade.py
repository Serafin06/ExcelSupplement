from pathlib import Path
from typing import Optional

from sqlalchemy import Engine

from DataBase.Repository import SQLAlchemyRepository
from ExcelSup.Enricher import DataEnricher
from ExcelSup.Processor import ExcelProcessor


class ExcelEnrichmentFacade:
    """
    Facade Pattern - upraszcza interfejs dla klienta
    """

    def __init__(self, engine: Engine, date_start: str = '2024-10-01', date_end: str = '2025-09-30'):
        self.repository = SQLAlchemyRepository(engine, date_start, date_end)
        self.enricher = DataEnricher(self.repository)
        self.date_start = date_start
        self.date_end = date_end

    def process_file(self, input_path: str, output_path: Optional[str] = None):
        """
        Główna metoda do przetwarzania pliku Excel
        """
        try:
            # Wczytaj Excel
            processor = ExcelProcessor(Path(input_path))
            processor.load()

            print(f"📁 Wczytano plik: {input_path}")
            print(f"📊 Znaleziono {len(processor.df)} wierszy")

            # Wzbogać dane
            enriched_df = self.enricher.enrich_dataframe(
                processor.df,
                purchase_item_col='Purchase item number'
            )

            # Zaktualizuj DataFrame w procesorze
            processor.df = enriched_df

            # Zapisz wynik
            output = Path(output_path) if output_path else None
            processor.save(output)

            print(f"✅ Przetworzono pomyślnie!")
            print(f"💾 Zapisano do: {output_path or input_path}")

            # Statystyki
            materials_found = enriched_df['Material_type_1'].notna().sum()
            print(f"📦 Znaleziono dane dla {materials_found} artykułów")

        finally:
            self.repository.close()