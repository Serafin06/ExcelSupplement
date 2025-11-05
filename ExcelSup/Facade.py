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

    def __init__(self, engine: Engine):
        self.repository = SQLAlchemyRepository(engine)
        self.enricher = DataEnricher(self.repository)

    def process_file(self, input_path: str, output_path: Optional[str] = None):
        """
        Główna metoda do przetwarzania pliku Excel
        """
        try:
            # Wczytaj Excel
            processor = ExcelProcessor(Path(input_path))
            processor.load()

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

            print(f"✓ Przetworzono pomyślnie: {input_path}")
            if output_path:
                print(f"✓ Zapisano do: {output_path}")

        finally:
            self.repository.close()
