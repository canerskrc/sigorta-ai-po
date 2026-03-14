# Skill: Toplu İşleme (Batch API)

## Amaç
Gecikme kritik olmayan işlemlerde — portföy taraması, poliçe toplu analizi,
hasar ön değerlendirme — Claude'un Batch API'sini kullanarak %50 maliyet avantajı sağlar.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6` (veya yoğun portföylerde `claude-haiku-4-5`)
- **Yöntem:** `client.messages.batches` — asenkron, max 24 saat
- **Kapasite:** Batch başına 100.000 istek veya 256 MB
- **Sonuç Süresi:** Çoğunlukla 1 saat içinde tamamlanır

## Ne Zaman Batch, Ne Zaman Direkt API?

| Durum | Yöntem |
|---|---|
| Müşteri gerçek zamanlı cevap bekliyor | Direkt API |
| Gece tarama / haftalık rapor | Batch API |
| Binlerce poliçeyi analiz et | Batch API |
| Tek hasar bildirimi | Direkt API |
| Yıllık portföy segmentasyonu | Batch API |

## Python Şablonu

```python
import anthropic
import time
import json
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

client = anthropic.Anthropic()

def toplu_police_analizi(policeler: list[dict]) -> dict[str, str]:
    """
    Poliçe listesini Batch API ile analiz eder.
    Returns: {police_no: analiz_sonucu}
    """

    # 1. Batch oluştur
    istekler = [
        Request(
            custom_id=f"police-{p['police_no']}",
            params=MessageCreateParamsNonStreaming(
                model="claude-opus-4-6",
                max_tokens=1024,
                system="Sen sigorta analiz uzmanısın. Kısa ve net yanıtlar ver.",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Poliçe {p['police_no']} analizi:\n"
                        f"Ürün: {p['urun']}, Prim: {p['prim']} TL, "
                        f"Müşteri segmenti: {p.get('segment', 'bilinmiyor')}\n"
                        f"Risk faktörlerini ve yenileme önerisini belirt."
                    ),
                }],
            ),
        )
        for p in policeler
    ]

    batch = client.messages.batches.create(requests=istekler)
    print(f"Batch başlatıldı: {batch.id} — {len(istekler)} istek")

    # 2. Tamamlanmasını bekle (polling)
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        sayilar = batch.request_counts
        print(
            f"Durum: {batch.processing_status} | "
            f"İşleniyor: {sayilar.processing} | "
            f"Tamamlandı: {sayilar.succeeded} | "
            f"Hatalı: {sayilar.errored}"
        )
        if batch.processing_status == "ended":
            break
        time.sleep(60)

    # 3. Sonuçları topla
    sonuclar = {}
    hatalar = []

    for sonuc in client.messages.batches.results(batch.id):
        match sonuc.result.type:
            case "succeeded":
                mesaj = sonuc.result.message
                metin = next(
                    (b.text for b in mesaj.content if b.type == "text"), ""
                )
                sonuclar[sonuc.custom_id] = metin
            case "errored":
                hata_turu = sonuc.result.error.type
                hatalar.append({
                    "id": sonuc.custom_id,
                    "hata": hata_turu,
                    "yeniden_dene": hata_turu != "invalid_request",
                })
            case "expired":
                hatalar.append({"id": sonuc.custom_id, "hata": "expired"})

    print(f"Tamamlandı: {len(sonuclar)} başarılı, {len(hatalar)} hatalı")
    if hatalar:
        print("Hatalar:", json.dumps(hatalar, ensure_ascii=False, indent=2))

    return sonuclar


def hatali_istekleri_yeniden_gonder(hatalar: list[dict], tum_istekler: list[dict]):
    """Yeniden denenebilir (non-invalid_request) hataları tekrar işler."""
    yeniden_denenecek_idler = {
        h["id"] for h in hatalar if h.get("yeniden_dene")
    }
    yeniden_gonder = [
        i for i in tum_istekler
        if f"police-{i['police_no']}" in yeniden_denenecek_idler
    ]
    if yeniden_gonder:
        return toplu_police_analizi(yeniden_gonder)
    return {}
```

## Prompt Caching ile Batch

```python
# Büyük sistem prompt'u tüm batch isteklerinde cache'le
BUYUK_SISTEM_PROMPTU = "...şirket standartları ve mevzuat (50KB)..."

istekler = [
    Request(
        custom_id=f"police-{i}",
        params=MessageCreateParamsNonStreaming(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": BUYUK_SISTEM_PROMPTU,
                "cache_control": {"type": "ephemeral"},  # tüm batch'te paylaşılır
            }],
            messages=[{"role": "user", "content": police_sorusu}],
        ),
    )
    for i, police_sorusu in enumerate(sorular)
]
```

## Ne Zaman Kullanılır
- Haftalık otomatik portföy taraması (cron job)
- Ay sonu hasar istatistik raporları
- Toplu poliçe metin sınıflandırması
- A/B test: farklı prompt versiyonlarını büyük veri setinde karşılaştırma

## Dikkat Edilecekler
- Sonuçlar 29 gün sonra silinir — `results()` çağrısından sonra hemen kaydet
- `invalid_request` hataları yeniden deneme yapma — isteği düzelt
- Batch iptal için `client.messages.batches.cancel(batch_id)` kullan
- Büyük batch'lerde rate limit değil, yalnızca boyut limiti (100K istek / 256 MB) var
