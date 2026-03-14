# Skill: Poliçe Analizi

## Amaç
Sigorta poliçesi belgelerini okuyarak teminat kapsamı, muafiyetler, kısıtlamalar ve
müşterinin dikkat etmesi gereken kritik maddeleri yapılandırılmış biçimde çıkarır.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** Streaming (`.stream()` + `.get_final_message()`) — poliçeler uzun olabilir
- **Thinking:** `{"type": "adaptive"}` — karmaşık hukuki dil yorumu için
- **Prompt Caching:** Şirket poliçe standartları system prompt'ta cache'lenebilir

## System Prompt
```
Sen deneyimli bir Türk sigorta hukuku uzmanısın. Poliçe metinlerini analiz ederek
müşterilerin anlayabileceği sade Türkçe ile şu başlıklar altında özet çıkarırsın:
1. Ana Teminatlar ve Limitler
2. Kapsam Dışı Durumlar (Muafiyetler)
3. Müşterinin Yükümlülükleri
4. Hasar Durumunda Yapılacaklar
5. Önemli Tarihler ve Süreler
Her maddeyi net, kısa ve aksiyona yönelik yaz.
```

## Python Şablonu

```python
import anthropic

client = anthropic.Anthropic()

def police_analiz_et(police_metni: str) -> str:
    """Poliçe metnini analiz ederek kritik bilgileri çıkarır."""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,  # yukarıdaki system prompt
        messages=[{
            "role": "user",
            "content": (
                f"Aşağıdaki sigorta poliçesini analiz et ve "
                f"yapılandırılmış özet çıkar:\n\n{police_metni}"
            ),
        }],
    ) as stream:
        sonuc = ""
        for metin in stream.text_stream:
            print(metin, end="", flush=True)
            sonuc += metin
    return sonuc
```

## Yapılandırılmış Çıktı Versiyonu (Pydantic)

```python
from pydantic import BaseModel
from typing import List

class PoliceAnalizi(BaseModel):
    ana_teminatlar: List[str]
    kapsam_disi: List[str]
    musteri_yukumlulukleri: List[str]
    hasar_adimlari: List[str]
    onemli_tarihler: List[str]

response = client.messages.parse(
    model="claude-opus-4-6",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": f"Analiz et:\n\n{police_metni}"}],
    output_format=PoliceAnalizi,
)
analiz: PoliceAnalizi = response.parsed_output
```

## Ne Zaman Kullanılır
- Yeni poliçe satın alan müşteriye hızlı özet sunmak
- Poliçe yenileme sürecinde değişiklikleri tespit etmek
- Müşteri şikayetlerinde teminat kapsamını doğrulamak
- Satış ekibine ürün bilgisi desteği sağlamak

## Dikkat Edilecekler
- Poliçe metni 100K token'ı geçiyorsa `betas=["context-1m-2025-08-07"]` ekle
- Hukuki ifadeler için AI çıktısı insan uzmanı tarafından doğrulanmalı
- Müşteriye sunulan özet yasal tavsiye niteliği taşımaz
