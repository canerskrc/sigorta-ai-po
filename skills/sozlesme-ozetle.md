# Skill: Sözleşme Özetleme

## Amaç
Uzun ve karmaşık sigorta sözleşmelerini, genel şartnameleri veya ek zeyilnameleri
müşterinin anlayabileceği sade Türkçe ile özetler. Hukuki risk içeren maddeleri vurgular.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** Streaming — sözleşmeler genellikle 10-100 sayfa
- **Thinking:** `{"type": "adaptive"}` — hukuki dil çözümlemesi için
- **Files API:** PDF yükleme ile tekrar kullanımlı doküman referansı
- **Prompt Caching:** Genel sigorta şartları tekrar eden sorularda cache'lenmeli

## System Prompt
```
Sen Türk sigorta hukuku konusunda uzman, müşteri odaklı bir hukuk danışmanısın.
Sözleşme metinlerini analiz ederek müşteriye şu başlıklar altında net özet sunarsın:

🛡️ Ana Teminatlar — Ne kapsıyor?
🚫 Kapsam Dışı — Ne kapsamıyor?
⚠️ Önemli Yükümlülükler — Müşteri ne yapmalı?
📅 Kritik Tarihler ve Süreler — Ne zaman yapılmalı?
💰 İptal ve İade Koşulları — Vazgeçme hakkı nedir?
🔴 Dikkat! — Hukuki risk içeren maddeler

Her başlığı madde madde ve kısa cümlelerle yaz. Hukuki jargonu sade Türkçe'ye çevir.
```

## Python Şablonu — Streaming

```python
import anthropic

client = anthropic.Anthropic()

def sozlesme_ozetle(sozlesme_metni: str) -> str:
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        cache_control={"type": "ephemeral"},  # tekrar sorgular için cache
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Şu sigorta sözleşmesini özetle:\n\n{sozlesme_metni}",
        }],
    ) as stream:
        ozet = ""
        for metin in stream.text_stream:
            print(metin, end="", flush=True)
            ozet += metin
    return ozet
```

## Files API Versiyonu — PDF Yükleme

```python
import anthropic

client = anthropic.Anthropic()

def sozlesme_pdf_ozetle(pdf_yolu: str) -> str:
    """PDF sözleşmeyi Files API ile yükleyip özetler."""
    # 1. PDF'i bir kez yükle
    with open(pdf_yolu, "rb") as f:
        yuklenen = client.beta.files.upload(
            file=(pdf_yolu.split("/")[-1], f, "application/pdf"),
        )

    # 2. Birden fazla soru sorabilirsin — yeniden yükleme gerekmez
    sorular = [
        "Bu sözleşmeyi tüm başlıklar altında özetle.",
        "Kapsam dışı maddeleri listele.",
        "Müşterinin imzalamadan önce bilmesi gereken en önemli 3 madde nedir?",
    ]

    sonuclar = {}
    for soru in sorular:
        yanit = client.beta.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": soru},
                    {
                        "type": "document",
                        "source": {"type": "file", "file_id": yuklenen.id},
                    },
                ],
            }],
            betas=["files-api-2025-04-14"],
        )
        sonuclar[soru] = next(b.text for b in yanit.content if b.type == "text")

    # 3. Temizle
    client.beta.files.delete(yuklenen.id)
    return sonuclar
```

## Ne Zaman Kullanılır
- Poliçe satın alma öncesi müşteri bilgilendirmesi
- Yenileme döneminde değişen maddeleri vurgulama
- Müşteri şikayetlerinde ilgili maddeyi hızlı bulma
- Satış temsilcisi için ürün bilgisi özeti

## Dikkat Edilecekler
- Özet hukuki tavsiye niteliği taşımaz — sorumluluk reddi beyanı ekle
- Çok uzun sözleşmelerde (>200K token) bölümlere böl veya 1M context beta kullan
- Kritik madde tespitinde insan hukuk danışmanı onayı alınmalı
