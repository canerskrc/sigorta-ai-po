# Skill: Hasar Asistanı

## Amaç
Hasar bildirimi yapan müşteriyi adım adım yönlendirir: hasarın kapsam dahilinde
olup olmadığını değerlendirir, gerekli belgeler ve süreler hakkında bilgi verir,
kritik hataları önler.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** Tek API çağrısı (`.create()`) veya streaming (uzun açıklamalar için)
- **Thinking:** `{"type": "adaptive"}` — hasar türüne göre değişen kapsam yorumu
- **Tool Use:** Poliçe sorgulama tool'u ile anlık kapsam doğrulama

## System Prompt
```
Sen deneyimli bir Türk sigorta hasar eksperi ve müşteri danışmanısın.
Hasar bildirimi yapan müşteriye şu konularda rehberlik edersin:
1. Hasarın sigorta kapsamında olup olmadığını değerlendir
2. Gerekli belgelerin eksiksiz listesini ver (fotoğraf, tutanak, rapor vb.)
3. Yasal süreleri ve son tarihleri hatırlat
4. Sık yapılan hataları önlemek için uyarılar ver
5. Sonraki adımı net biçimde belirt

Yanıtların empati içermeli, teknik jargondan kaçınmalı ve aksiyona yönelik olmalı.
```

## Python Şablonu

```python
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

@beta_tool
def police_kapsam_sorgula(police_no: str, hasar_turu: str) -> str:
    """Belirtilen poliçenin hasar türünü kapsayıp kapsamadığını kontrol eder.

    Args:
        police_no: Müşterinin poliçe numarası.
        hasar_turu: Hasar türü (örn: 'çarpma', 'hırsızlık', 'yangın').
    """
    # Poliçe veritabanı sorgusu
    return json.dumps({
        "kapsam_var": True,
        "muafiyet": 2500,
        "azami_teminat": 450000,
    })

def hasar_asistani_calistir(police_no: str, hasar_aciklamasi: str) -> str:
    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=3000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        tools=[police_kapsam_sorgula],
        messages=[{
            "role": "user",
            "content": (
                f"Poliçe No: {police_no}\n\n"
                f"Müşteri hasar bildirimi:\n{hasar_aciklamasi}\n\n"
                f"Bu hasarı değerlendir ve müşteriyi yönlendir."
            ),
        }],
    )
    for mesaj in runner:
        for blok in mesaj.content:
            if blok.type == "text":
                return blok.text
    return ""
```

## Çok Turlu Konuşma Versiyonu

```python
class HasarAsistani:
    """Müşteriyle çok turlu hasar danışmanlığı oturumu."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.mesajlar = []

    def konuş(self, kullanici_mesaji: str) -> str:
        self.mesajlar.append({"role": "user", "content": kullanici_mesaji})
        yanit = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=self.mesajlar,
        )
        asistan_metni = next(
            b.text for b in yanit.content if b.type == "text"
        )
        self.mesajlar.append({"role": "assistant", "content": asistan_metni})
        return asistan_metni
```

## Ne Zaman Kullanılır
- Web/mobil uygulamada self-servis hasar bildirimi
- Çağrı merkezi destek aracı
- WhatsApp/chatbot hasar hattı
- İlk 24 saat kritik hasar yönlendirmesi

## Dikkat Edilecekler
- Hukuki bağlayıcılığı olmayan bilgi verildiği kullanıcıya belirtilmeli
- Büyük hasarlarda (ölüm, ağır yaralanma) insan ekspere yönlendirme zorunlu
- Kullanıcı sesi/görüntü içeriyorsa Files API ile yükleyip analiz et
- Çok turlu konuşmalar uzarsa Compaction (`compact-2026-01-12`) etkinleştir
