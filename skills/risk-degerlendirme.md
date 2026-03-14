# Skill: Risk Değerlendirme

## Amaç
Müşteri profili, araç/mülk verileri ve geçmiş hasar kayıtlarına dayanarak
sigorta risk skoru hesaplar, prim çarpanı önerir ve risk gerekçesini açıklar.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** Tool Runner (`@beta_tool` + `tool_runner`) — CRM ve istatistik araçları
- **Thinking:** `{"type": "adaptive"}` — çok değişkenli risk analizi için
- **Effort:** `output_config: {"effort": "max"}` — yüksek değerli poliçelerde

## System Prompt
```
Sen aktüeryal analiz ve sigorta risk değerlendirme uzmanısın.
Verilen müşteri ve nesne bilgilerini kullanarak:
- Sayısal risk skoru (0-100, düşük = iyi)
- Risk kategorisi (Düşük / Orta / Yüksek / Çok Yüksek)
- Prim çarpanı önerisi (1.0x – 3.0x)
- Risk faktörlerinin gerekçeli açıklaması
hesaplarsın. Kararlarında aktüeryal prensiplere ve SEDDK mevzuatına uyarsın.
```

## Araçlar (Tools)

```python
from anthropic import beta_tool

@beta_tool
def musteri_gecmis_sorgula(tc_kimlik: str) -> str:
    """Müşterinin geçmiş hasar ve poliçe geçmişini getirir.

    Args:
        tc_kimlik: Müşterinin T.C. Kimlik Numarası.
    """
    # CRM / veritabanı sorgusu
    return json.dumps({"hasar_sayisi": 2, "odenen_toplam": 45000})

@beta_tool
def arac_deger_sorgula(plaka: str) -> str:
    """Araç güncel piyasa değerini ve hasar geçmişini sorgular.

    Args:
        plaka: Araç plaka numarası.
    """
    # Ekspertiz/sigorta değer servisi entegrasyonu
    return json.dumps({"piyasa_degeri": 850000, "kaza_gecmisi": False})
```

## Python Şablonu

```python
import anthropic
from anthropic import beta_tool
import json

client = anthropic.Anthropic()

def risk_degerlendirmesi_yap(musteri_profili: dict) -> str:
    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_config={"effort": "max"},
        system=SYSTEM_PROMPT,
        tools=[musteri_gecmis_sorgula, arac_deger_sorgula],
        messages=[{
            "role": "user",
            "content": (
                f"Şu müşteri için kapsamlı risk değerlendirmesi yap:\n"
                f"{json.dumps(musteri_profili, ensure_ascii=False, indent=2)}"
            ),
        }],
    )
    sonuc = ""
    for mesaj in runner:
        for blok in mesaj.content:
            if blok.type == "text":
                sonuc = blok.text
    return sonuc
```

## Yapılandırılmış Çıktı Versiyonu

```python
from pydantic import BaseModel, Field
from typing import List

class RiskDegerlendirme(BaseModel):
    risk_skoru: int = Field(ge=0, le=100)
    risk_kategorisi: str
    prim_carpani: float = Field(ge=1.0, le=3.0)
    risk_faktorleri: List[str]
    oneri: str
```

## Ne Zaman Kullanılır
- Yeni poliçe tekliflerinde otomatik ön değerlendirme
- Portföy yenileme döneminde risk revizyonu
- Hasar yoğunluğu yüksek müşteri segmentasyonu
- Sigorta acentesi karar destek sistemi

## Dikkat Edilecekler
- Risk skoru nihai karar değil — insan aktüer onayı gerekebilir
- SEDDK mevzuatı uyumu için risk kategorileri konfigüre edilebilir olmalı
- Yanlış pozitif riski yüksek segmentlerde ek doğrulama adımı ekle
