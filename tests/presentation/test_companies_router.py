from domain.value_objects.company_filters import CompanyField
from presentation.backend.routers.company_field_normalizer import normalize_field


def test_normalize_field_accepts_code_aliases():
    assert normalize_field("codigo") == CompanyField.CODE
    assert normalize_field("ticker") == CompanyField.CODE
    assert normalize_field("code") == CompanyField.CODE
    assert normalize_field("CNPJ") == CompanyField.CNPJ


def test_normalize_field_returns_none_for_unknown_fields():
    assert normalize_field(None) is None
    assert normalize_field(" ") is None
    assert normalize_field("unknown") is None
