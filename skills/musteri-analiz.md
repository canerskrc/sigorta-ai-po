# Skill: Müşteri Analizi

## Amaç
Sigorta portföyündeki müşterileri segmentlere ayırır, churn (iptal) riski taşıyanları
tespit eder ve çapraz satış / upsell fırsatlarını belirler.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** Structured Output — `client.messages.parse()` + Pydantic
- **Thinking:** `{"type": "adaptive"}` — karmaşık portföy değerlendirme
- **Batch API:** Büyük portföylerde toplu analiz için

## System Prompt
```
Sen sigorta portföy analizi ve müşteri deneyimi uzmanısın.
Verilen müşteri verilerini analiz ederek:
- Segment sınıflandırması (Platinum / Gold / Silver / Bronze)
- Churn risk skoru (0-100)
- Churn başlıca nedenleri
- Çapraz satış önerileri (mevcut ürünlere göre)
- Öncelikli aksiyon önerileri

üretirsin. Analizin ölçülebilir metriklere dayalı ve aksiyona yönelik olmalı.
```

## Yapılandırılmış Çıktı Şeması

```python
from pydantic import BaseModel, Field
from typing import List
import anthropic

client = anthropic.Anthropic()

class MusteriSegmenti(BaseModel):
    segment: str = Field(description="Platinum, Gold, Silver veya Bronze")
    churn_riski: int = Field(ge=0, le=100, description="Churn olasılığı 0-100")
    churn_nedenleri: List[str]
    capraz_satis_onerileri: List[str]
    oncelikli_aksiyonlar: List[str]
    ozet: str

def musteri_analiz_et(musteri_verisi: dict) -> MusteriSegmenti:
    import json
    yanit = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Şu müşteriyi analiz et:\n"
                f"{json.dumps(musteri_verisi, ensure_ascii=False, indent=2)}"
            ),
        }],
        output_format=MusteriSegmenti,
    )
    return yanit.parsed_output
```

## Batch Versiyon — Büyük Portföy

```python
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
import time

def portfoy_toplu_analiz(musteriler: list[dict]) -> dict:
    """Tüm portföyü Batch API ile analiz eder (%50 maliyet avantajı)."""
    istekler = [
        Request(
            custom_id=f"musteri-{m['id']}",
            params=MessageCreateParamsNonStreaming(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Analiz et: {json.dumps(m, ensure_ascii=False)}",
                }],
            ),
        )
        for m in musteriler
    ]

    batch = client.messages.batches.create(requests=istekler)
    print(f"Batch ID: {batch.id}")

    # Tamamlanmasını bekle
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        time.sleep(30)

    # Sonuçları topla
    sonuclar = {}
    for sonuc in client.messages.batches.results(batch.id):
        if sonuc.result.type == "succeeded":
            mesaj = sonuc.result.message
            metin = next(b.text for b in mesaj.content if b.type == "text")
            sonuclar[sonuc.custom_id] = metin
    return sonuclar
```

## Ne Zaman Kullanılır
- Yıllık portföy sağlık taraması
- Yenileme sezonunda öncelikli iletişim listesi oluşturma
- Kampanya hedefleme ve segmentasyon
- Müşteri kayıp analizi raporlaması

## Dikkat Edilecekler
- KVKK kapsamında kişisel veriler anonim/pseudonim işlenmeli
- Churn skoru ayrımcı karar almak için kullanılmamalı
- Batch sonuçları 29 gün sonra silinir — hemen indir ve kaydet
