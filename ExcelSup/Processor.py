from pathlib import Path
from typing import Optional, List

import pandas as pd


class ExcelProcessor:
    """
    Service do przetwarzania plików Excel (Single Responsibility Principle)
    """

    def __init__(self, file_path: Path, purchase_item_column: str = 'C4'):
        self.file_path = file_path
        self.purchase_item_column = purchase_item_column
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> 'ExcelProcessor':
        """Wczytuje plik Excel"""
        self.df = pd.read_excel(self.file_path)
        return self

    def get_purchase_items(self) -> List[str]:
        """Zwraca unikalne numery Purchase Item"""
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load() first.")

        # Zakładam, że kolumna nazywa się 'Purchase item number'
        col_name = 'Purchase item number'
        if col_name not in self.df.columns:
            raise ValueError(f"Column '{col_name}' not found in Excel")

        items = self.df[col_name].dropna().unique().tolist()
        return [str(item) for item in items]

    def save(self, output_path: Optional[Path] = None):
        """Zapisuje zmieniony DataFrame do pliku"""
        if self.df is None:
            raise ValueError("DataFrame not loaded")

        path = output_path or self.file_path
        self.df.to_excel(path, index=False)