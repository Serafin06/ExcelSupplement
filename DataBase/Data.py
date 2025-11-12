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
    # termin_zak: Optional[str]

    @property
    def layers(self) -> List[MaterialLayer]:
        """Ekstrahuje warstwy z receptury z grubościami, rozdzielając EVOH"""
        if not self.receptura_1:
            return []

        # Parsowanie receptury - po '/'
        raw_materials = [m.strip() for m in self.receptura_1.split('/') if m.strip()]

        # Zbierz grubości
        all_thicknesses = []
        for g in [self.grubosc_11, self.grubosc_21, self.grubosc_31]:
            if g is not None:
                all_thicknesses.append(g)

        layers = []
        for i, material in enumerate(raw_materials):
            thickness = all_thicknesses[i] if i < len(all_thicknesses) else None
            material_upper = material.upper().strip()

            # Jeśli warstwa zawiera EVOH np. "PE-EVOH"
            if '-EVOH' in material_upper:
                # Rozdziel na część przed EVOH
                base_material = material_upper.replace('-EVOH', '').strip()
                material_type = MATERIAL_TYPE_MAPPING.get(base_material, '7-Other plastics')
                layers.append(MaterialLayer(
                    material=base_material,
                    thickness=thickness,
                    material_type=material_type
                ))
            # EVOH ignorujemy, więc nie dodajemy jako osobna warstwa
            else:
                material_type = MATERIAL_TYPE_MAPPING.get(material_upper, '7-Other plastics')
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


