"""
Excel-SQL Data Enrichment Script
Pobiera dane z tabeli KO na podstawie Purchase Item Number i wzbogaca Excel
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

from ExcelSup.Mapper import MATERIAL_TYPE_MAPPING


@dataclass
class MaterialLayer:
    """Warstwa materiału z grubością i typem"""
    material: str  # Surowa nazwa z receptury (np. "PE", "PET")
    thickness: Optional[float]  # Grubość w mikrometrach
    material_type: str  # Zmapowany typ (np. "4-LDPE-Low-density polyethylene")

    @property
    def proportion(self) -> Optional[float]:
        """Proporcja warstwy (będzie obliczona względem całości)"""
        return self.thickness


@dataclass
class ArticleData:
    """Value Object przechowujący dane artykułu z bazy"""
    art: str
    szerokosc_1: Optional[int]
    grubosc_11: Optional[float]
    grubosc_21: Optional[float]
    grubosc_31: Optional[float]
    receptura_1: Optional[str]
    tech: Optional[float]
    jm2: Optional[str]

    @property
    def layers(self) -> List[MaterialLayer]:
        """Ekstrahuje warstwy z receptury z grubościami"""
        if not self.receptura_1:
            return []

        # Parsowanie receptury - tylko po '/'
        raw_materials = [m.strip() for m in self.receptura_1.split('/') if m.strip()]

        # EVOH ignorujemy - usuwamy z listy materiałów i grubości
        filtered_materials = []
        filtered_thicknesses = []

        # Zbierz grubości
        all_thicknesses = []
        if self.grubosc_11 is not None:
            all_thicknesses.append(self.grubosc_11)
        if self.grubosc_21 is not None:
            all_thicknesses.append(self.grubosc_21)
        if self.grubosc_31 is not None:
            all_thicknesses.append(self.grubosc_31)

        # Filtruj materiały i grubości (pomijamy EVOH)
        for i, material in enumerate(raw_materials):
            material_upper = material.upper()
            # Pomijamy EVOH i wszystko co zawiera EVOH (np. "PE-EVOH")
            if 'EVOH' not in material_upper:
                filtered_materials.append(material)
                if i < len(all_thicknesses):
                    filtered_thicknesses.append(all_thicknesses[i])

        # Twórz warstwy tylko z nie-EVOH materiałów
        layers = []
        for i, material in enumerate(filtered_materials):
            thickness = filtered_thicknesses[i] if i < len(filtered_thicknesses) else None
            material_upper = material.upper().replace('-EVOH', '').strip()  # Usuń -EVOH jeśli zostało
            material_type = MATERIAL_TYPE_MAPPING.get(
                material_upper,
                '7-Other plastics'
            )

            layers.append(MaterialLayer(
                material=material_upper,
                thickness=thickness,
                material_type=material_type
            ))

        return layers

    @property
    def total_thickness(self) -> float:
        """Całkowita grubość wszystkich warstw"""
        return sum(float(layer.thickness) for layer in self.layers if layer.thickness)

    def get_layer_proportions(self) -> List[Tuple[MaterialLayer, float]]:
        """Zwraca warstwy z proporcjami procentowymi"""
        # total też musi być float
        total = sum(float(layer.thickness) for layer in self.layers if layer.thickness)
        if total == 0:
            return [(layer, 0.0) for layer in self.layers]

        proportions = []
        for layer in self.layers:
            try:
                thickness = float(layer.thickness) if layer.thickness else 0.0
            except (ValueError, TypeError):
                thickness = 0.0
            proportion = (thickness / total * 100) if total > 0 else 0.0
            proportions.append((layer, proportion))
        return proportions


