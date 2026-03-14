# Skill: Yapısal Çıktı (Structured Output)

## Amaç
Claude'un yanıtını garantili JSON şemasına bağlar. Hasar sınıflandırma,
varlık çıkarma, risk skoru, poliçe verileri gibi downstream sistemlere
beslenecek her çıktıda kullanılır.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** `client.messages.parse()` + Pydantic (önerilen) veya `output_config` raw şema
- **Strict Tool Use:** `"strict": True` ile tool input şeması da garantilenir
- **Uyumsuz:** Citations ile birlikte kullanılamaz (400 hatası)

## Pydantic ile Yapısal Çıktı (Önerilen)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
import anthropic

client = anthropic.Anthropic()

class HasarBildirimi(BaseModel):
    hasar_turu: str = Field(description="kaza, hırsızlık, yangın, doğal_afet vb.")
    tahmini_tutar: Optional[float] = Field(default=None, description="TL cinsinden tahmini hasar")
    kapsam_dahil: bool = Field(description="Poliçe kapsamında mı?")
    acil_mudahale_gerekli: bool
    gerekli_belgeler: List[str]
    oncelik: str = Field(description="dusuk, orta, yuksek, acil")
    ozet: str

def hasar_siniflandir(hasar_aciklamasi: str, police_bilgisi: str) -> HasarBildirimi:
    yanit = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system="Sen sigorta hasar sınıflandırma uzmanısın.",
        messages=[{
            "role": "user",
            "content": (
                f"Poliçe: {police_bilgisi}\n\n"
                f"Hasar bildirimi: {hasar_aciklamasi}\n\n"
                f"Bu hasarı sınıflandır ve gerekli bilgileri çıkar."
            ),
        }],
        output_format=HasarBildirimi,
    )
    return yanit.parsed_output  # doğrulanmış HasarBildirimi nesnesi
```

## Poliçe Veri Çıkarma

```python
from pydantic import BaseModel
from datetime import date
from typing import List

class PoliceVerisi(BaseModel):
    police_no: str
    sigorta_turu: str
    baslangic_tarihi: date
    bitis_tarihi: date
    yillik_prim: float
    teminat_limiti: float
    muafiyet_tutari: float
    ek_teminatlar: List[str]
    ozel_sartlar: List[str]

def policeyi_ayristir(police_metni: str) -> PoliceVerisi:
    yanit = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"Bu poliçeden tüm verileri çıkar:\n\n{police_metni}",
        }],
        output_format=PoliceVerisi,
    )
    return yanit.parsed_output
```

## Raw JSON Şema Versiyonu

```python
yanit = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hasar değerlendir: ..."}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "hasar_turu": {"type": "string"},
                    "kapsam_dahil": {"type": "boolean"},
                    "tahmini_tutar": {"type": "number"},
                    "oncelik": {
                        "type": "string",
                        "enum": ["dusuk", "orta", "yuksek", "acil"],
                    },
                },
                "required": ["hasar_turu", "kapsam_dahil", "oncelik"],
                "additionalProperties": False,
            },
        }
    },
)

import json
metin = next(b.text for b in yanit.content if b.type == "text")
veri = json.loads(metin)
```

## Strict Tool Use

```python
# Tool input'unun da şemaya uyması garantilenirse
yanit = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Yeni poliçe oluştur..."}],
    tools=[{
        "name": "police_olustur",
        "description": "Yeni bir sigorta poliçesi oluşturur",
        "strict": True,              # tool input garantili şema
        "input_schema": {
            "type": "object",
            "properties": {
                "sigorta_turu": {
                    "type": "string",
                    "enum": ["kasko", "trafik", "konut", "saglik", "hayat"],
                },
                "yillik_prim": {"type": "number"},
                "teminat_limiti": {"type": "number"},
            },
            "required": ["sigorta_turu", "yillik_prim", "teminat_limiti"],
            "additionalProperties": False,
        },
    }],
)
```

## Hata Yönetimi

```python
def guvenli_parse(metni: str, model: type) -> Optional[BaseModel]:
    """
    Yapısal çıktı başarısız olursa None döner, uygulama çökmez.
    stop_reason == "refusal" durumunu da ele alır.
    """
    yanit = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": metni}],
        output_format=model,
    )

    if yanit.stop_reason == "refusal":
        print("Claude bu içeriği işlemeyi reddetti.")
        return None
    if yanit.stop_reason == "max_tokens":
        print("max_tokens aşıldı — çıktı eksik olabilir.")

    return yanit.parsed_output
```

## Desteklenen Pydantic Anotasyonlar

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class OncelikSeviyesi(str, Enum):
    DUSUK = "dusuk"
    ORTA = "orta"
    YUKSEK = "yuksek"
    ACIL = "acil"

class HasarRaporu(BaseModel):
    oncelik: OncelikSeviyesi               # enum otomatik desteklenir
    teminatlar: List[str]                  # list desteklenir
    tutar: Optional[float] = None          # optional desteklenir
    aciklama: str = Field(min_length=10)   # min_length SDK tarafında kontrol edilir
```

## Ne Zaman Kullanılır
- API / veritabanına yazılacak her AI çıktısında
- Hasar triaj sistemi — önceliklendirme pipeline'ı
- Poliçe verilerini CRM'e aktarma
- Raporlama sistemlerine beslenecek yapılandırılmış veriler

## Desteklenmeyenler
- Recursive şemalar
- `minimum` / `maximum` sayısal kısıtlar (SDK client-side kontrol eder)
- `minLength` / `maxLength` string kısıtlar (SDK client-side kontrol eder)
- Citations ile birlikte kullanım (400 hatası)
