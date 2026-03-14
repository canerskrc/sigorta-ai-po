# Skill: Prompt Önbellekleme (Prompt Caching)

## Amaç
Büyük ve tekrar eden bağlamları (sigorta mevzuatı, şirket standartları, geniş poliçe veritabanı)
önbelleğe alarak API maliyetini %90'a kadar düşürür ve yanıt süresini kısaltır.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** `cache_control` parametresi — otomatik veya manuel
- **TTL:** Varsayılan 5 dakika | `"ttl": "1h"` ile 1 saate uzatılabilir
- **Maliyet:** Cache oluşturma 1.25x normal fiyat; sonraki kullanımlar 0.1x (%90 indirim)

## Ne Zaman Cache'le?

| Durum | Cache Değeri |
|---|---|
| Aynı sorgu birden fazla kullanıcı için | Çok yüksek |
| Büyük mevzuat/standart system prompt | Yüksek |
| Konuşma geçmişi 10K+ token | Orta |
| Her sorgu için farklı içerik | Düşük |

## Otomatik Cache (Önerilen)

```python
import anthropic

client = anthropic.Anthropic()

# En son cache'lenebilir bloğu otomatik cache'ler — manuel annotasyon gerekmez
def sorgu_gonder(kullanici_sorusu: str, buyuk_baglam: str) -> str:
    yanit = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        cache_control={"type": "ephemeral"},  # son büyük bloğu cache'le
        system=buyuk_baglam,                   # örn: 200KB mevzuat metni
        messages=[{"role": "user", "content": kullanici_sorusu}],
    )
    return next(b.text for b in yanit.content if b.type == "text")
```

## Manuel Cache — Çok Bölümlü System Prompt

```python
SEDDK_MEVZUATI = "...200KB SEDDK düzenleme metni..."
SIRKET_STANDARTLARI = "...50KB şirket poliçe standartları..."

def cache_kullanarak_sorgula(soru: str) -> str:
    yanit = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SEDDK_MEVZUATI,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},  # 1 saat cache
            },
            {
                "type": "text",
                "text": SIRKET_STANDARTLARI,
                "cache_control": {"type": "ephemeral"},  # 5 dakika cache
            },
            {
                "type": "text",
                "text": "Sen sigorta uzmanısın. Yukarıdaki mevzuat ve standartlara dayanarak yanıt ver.",
                # son metin cache'lenmez — her sorgu için değişebilir
            },
        ],
        messages=[{"role": "user", "content": soru}],
    )
    return next(b.text for b in yanit.content if b.type == "text")
```

## Çok Turlu Konuşmada Cache

```python
def cok_turlu_konusma(oturum_belgesi: str) -> None:
    """
    Büyük sigorta dosyasını bir kez yükle, tüm konuşmada cache'le.
    Müşteri temsilcisi defalarca soru sorabilir.
    """
    mesajlar = []

    while True:
        soru = input("Temsilci sorusu ('çıkış' ile bitir): ")
        if soru.lower() == "çıkış":
            break

        mesajlar.append({"role": "user", "content": soru})

        yanit = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": oturum_belgesi,           # her turda cache'den gelir
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }],
            messages=mesajlar,
        )

        asistan_metni = next(b.text for b in yanit.content if b.type == "text")
        mesajlar.append({"role": "assistant", "content": asistan_metni})

        # Cache kullanım istatistiklerini göster
        kullanim = yanit.usage
        print(f"\nYanıt: {asistan_metni}")
        print(
            f"[Token: giriş={kullanim.input_tokens}, "
            f"cache_okuma={getattr(kullanim, 'cache_read_input_tokens', 0)}, "
            f"çıkış={kullanim.output_tokens}]\n"
        )
```

## Batch API + Cache Kombinasyonu

```python
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

BUYUK_SISTEM = [{"type": "text", "text": SEDDK_MEVZUATI, "cache_control": {"type": "ephemeral"}}]

istekler = [
    Request(
        custom_id=f"sorgu-{i}",
        params=MessageCreateParamsNonStreaming(
            model="claude-opus-4-6",
            max_tokens=512,
            system=BUYUK_SISTEM,      # tüm batch'te aynı system → cache'den okunur
            messages=[{"role": "user", "content": sorgu}],
        ),
    )
    for i, sorgu in enumerate(sorgular)
]
```

## Cache İstatistiklerini İzle

```python
yanit = client.messages.create(...)
k = yanit.usage

toplam_maliyet = (
    k.input_tokens * 5.00 / 1_000_000           # normal giriş
    + getattr(k, "cache_creation_input_tokens", 0) * 6.25 / 1_000_000  # cache oluşturma
    + getattr(k, "cache_read_input_tokens", 0) * 0.50 / 1_000_000       # cache okuma
    + k.output_tokens * 25.00 / 1_000_000       # çıkış
)
print(f"İstek maliyeti: ${toplam_maliyet:.6f}")
```

## Ne Zaman Kullanılır
- Tüm isteklerde aynı büyük mevzuat/standart metni kullanılıyorsa
- Müşteri temsilcisi aynı dosya üzerinde çok soru soruyorsa
- Batch analizde ortak sistem bağlamı varsa
- Response süresini kritik kullanıcı akışlarında kısaltmak gerekiyorsa

## Dikkat Edilecekler
- Cache TTL dolduğunda otomatik yeniden oluşturulur — maliyet 1 kez daha alınır
- Tool tanımları ve görsel içerikler de cache'lenebilir
- Cache `cache_read_input_tokens` > 0 ise aktif çalışıyor demektir
- İlk istek her zaman tam fiyat (`cache_creation`) öder
