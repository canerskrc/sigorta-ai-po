"""Pydantic şemaları — request / response validation."""

from datetime import date
from pydantic import BaseModel, Field, field_validator


def _tc_algoritma_dogrula(tc: str) -> bool:
    """
    T.C. Kimlik No algoritma doğrulaması.
    - 11 rakam, ilk rakam 0 olamaz
    - 10. rakam: (tek pozisyonlar toplamı * 7 - çift pozisyonlar toplamı) % 10
    - 11. rakam: ilk 10 rakamın toplamı % 10
    """
    if len(tc) != 11 or not tc.isdigit() or tc[0] == "0":
        return False
    digits = [int(c) for c in tc]
    tek_toplam = sum(digits[i] for i in range(0, 9, 2))   # 1,3,5,7,9. rakamlar (0-index)
    cift_toplam = sum(digits[i] for i in range(1, 8, 2))  # 2,4,6,8. rakamlar
    if (tek_toplam * 7 - cift_toplam) % 10 != digits[9]:
        return False
    return sum(digits[:10]) % 10 == digits[10]


class HasarIhbarIstek(BaseModel):
    """POST /hasar/ihbar istek gövdesi."""

    tc_kimlik: str = Field(
        ...,
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$",
        description="T.C. Kimlik Numarası (11 hane)",
        examples=["12345678901"],
    )
    hasar_tarihi: date = Field(
        ...,
        description="Hasarın gerçekleştiği tarih (geçmişte olmalıdır)",
        examples=["2024-03-10"],
    )
    aciklama: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Hasar açıklaması",
        examples=["Park halindeyken araçıma çarptılar, sol kapı hasar gördü."],
    )

    @field_validator("tc_kimlik")
    @classmethod
    def tc_gecerli_olmali(cls, v: str) -> str:
        if not _tc_algoritma_dogrula(v):
            raise ValueError("Geçersiz T.C. Kimlik Numarası")
        return v

    @field_validator("hasar_tarihi")
    @classmethod
    def tarih_gecmiste_olmali(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("Hasar tarihi bugün veya gelecekte olamaz")
        return v


class HasarIhbarYanit(BaseModel):
    """POST /hasar/ihbar başarılı yanıtı."""

    id: int
    tc_kimlik: str
    hasar_tarihi: date
    aciklama: str
    notion_page_id: str | None
    mesaj: str = "Hasar ihbarınız başarıyla alındı."

    model_config = {"from_attributes": True}
