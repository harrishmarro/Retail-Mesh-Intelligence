"""Canonical project locations shared by entry points and layers."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW_DATA = ROOT / 'data/raw'
PREPROCESSED_DATA = ROOT / 'data/preprocessed'
DEFAULT_DB = PREPROCESSED_DATA / 'retail_mesh.db'
PREPARED_CSV = PREPROCESSED_DATA / 'RetailMesh_Reviewed_CSV_Data.zip'
SQL = ROOT / 'src/dal/models/relational/sql'
SEMANTIC = ROOT / 'src/dal/models/semantic'
