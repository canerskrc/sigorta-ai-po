# CLAUDE.md — Sigorta AI Dönüşüm Platformu

Bu dosya Claude Code'un bu projede nasıl davranacağını tanımlar.

---

## Model ve API Varsayılanları

- **Varsayılan model:** `claude-opus-4-6` — kullanıcı açıkça başka bir model belirtmedikçe değiştirme.
- **Düşünme modu:** Karmaşık her görevde `thinking: {"type": "adaptive"}` kullan. `budget_tokens` kullanma — Opus 4.6'da deprecated.
- **Effort:** Derin analizlerde `output_config: {"effort": "max"}`, rutin görevlerde `"high"` (varsayılan).
- **Streaming:** Uzun belge analizi, poliçe özeti, sözleşme inceleme gibi yüksek token'lı her çıktıda `.stream()` + `.get_final_message()` kullan. Timeout riskini ortadan kaldırır.
- **Tool Runner:** Birden fazla tool çağrısı olan akışlarda `client.beta.messages.tool_runner()` + `@beta_tool` decorator kullan. Manuel döngü yalnızca insan onayı gereken operasyonlarda.
- **Structured Output:** Hasar sınıflandırma, varlık çıkarma, risk skoru gibi sabit şema gerektiren çıktılarda `client.messages.parse()` + Pydantic model kullan.
- **Prompt Caching:** Büyük sigorta mevzuatı / şirket poliçe dokümanları system prompt'a giriyorsa `cache_control: {"type": "ephemeral"}` ekle.
- **Batch API:** Portföy taraması, toplu poliçe analizi gibi gecikme kritik olmayan işlemlerde `client.messages.batches` kullan (%50 maliyet avantajı).

---

## Proje Mimarisi

```
sigorta-ai-po/
├── src/
│   └── hasar/
│       ├── api.py        # FastAPI router — POST/GET /hasar/ihbar
│       ├── database.py   # SQLAlchemy engine + get_db
│       ├── models.py     # ORM modelleri
│       ├── schemas.py    # Pydantic v2 şemaları + TC doğrulama
│       └── notion.py     # Notion entegrasyonu (graceful degradation)
├── skills/               # Yeniden kullanılabilir AI skill tanımları (.md)
├── prompts/              # Domain-specific prompt şablonları
├── docs/                 # Teknik ve iş dokümantasyonu
├── tests/
│   └── hasar/
│       └── test_api.py   # 32 test, coverage %95+
├── main.py               # Demo — SigortaAIAgent sınıfı
├── CLAUDE.md             # Bu dosya
├── pytest.ini
└── requirements.txt
```

---

## Ortam Değişkenleri

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `ANTHROPIC_API_KEY` | Evet | Claude API anahtarı |
| `NOTION_API_KEY` | Hayır | Notion entegrasyonu için PAT |
| `NOTION_DATABASE_ID` | Hayır | Hasar ihbarlarının yazılacağı Notion DB ID'si |
| `DATABASE_URL` | Hayır | SQLAlchemy bağlantı URL'i (varsayılan: `sqlite:///./hasar.db`) |

---

## Geliştirme Kuralları

### Commit Mesajları
Tüm commit mesajları **Türkçe** olmalı. Format:
```
<tip>: <kısa açıklama>

<isteğe bağlı detay>
```
Tipler: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Örnekler:
- `feat: poliçe analiz endpoint'i eklendi`
- `fix: TC doğrulama algoritması düzeltildi`
- `test: Notion hata senaryosu testi eklendi`

### Test Coverage
- **Minimum %80** — `pytest.ini` ile zorunlu kılınmıştır.
- Her yeni özellik için önce test yaz (TDD).
- Dış servisler (Notion, harici API) her zaman mock'lanmalı.
- `sqlite:///file:testdb?mode=memory&cache=shared&uri=true` — testlerde in-memory paylaşımlı DB kullan.

### Kod Stili
- Python 3.10+ syntax (match/case, `X | Y` union tipler)
- Pydantic v2 — `model_validate()`, `@field_validator`
- SQLAlchemy 2.0 — `Mapped[]` tip annotasyonları
- Env değişkenlerini modül seviyesinde değil fonksiyon içinde oku (mock testleri için)
- Dış servis hataları ana akışı bloke etmemeli (graceful degradation)

### Güvenlik
- API anahtarları asla kod içinde — yalnızca `os.environ.get()`
- Kullanıcı girdileri Pydantic ile validate edilmeli
- TC Kimlik: 11 hane regex + algoritma doğrulama
- Dosya indirmelerinde `os.path.basename()` ile path traversal önlemi

---

## Komutlar

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Testleri çalıştır (coverage dahil)
pytest

# API sunucusunu başlat
uvicorn src.hasar.api:router --reload --port 8000

# Demo çalıştır
python main.py
```

---

## Skills Dizini

`skills/` klasöründeki her `.md` dosyası bir AI skill tanımıdır.
Her skill şu bölümleri içerir: Amaç, Claude API Yüzeyi, System Prompt, Python Şablonu, Ne Zaman Kullanılır.

| Skill Dosyası | Kapsam |
|---|---|
| `police-analiz.md` | Poliçe belgesi okuma ve kritik madde çıkarma |
| `risk-degerlendirme.md` | Müşteri profili + araç verisiyle risk skoru |
| `hasar-asistan.md` | Hasar bildirimi yönlendirme ve adım planı |
| `sozlesme-ozetle.md` | Uzun sözleşmeleri sade Türkçe ile özetleme |
| `musteri-analiz.md` | Portföy segmentasyonu ve churn riski |
| `toplu-isleme.md` | Batch API ile yüzlerce poliçe paralel analizi |
| `belge-yukleme.md` | Files API ile tekrar kullanımlı PDF yükleme |
| `ajan-subagent.md` | Agent SDK ile çok adımlı araştırma akışları |
| `prompt-onbellekleme.md` | Büyük mevzuat dokümanlarını cache'leme |
| `yapisal-cikti.md` | Pydantic + JSON Schema ile garantili çıktı |
