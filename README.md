# Sigorta AI Dönüşüm Platformu (sigorta-ai-po)

> Sigortacılık sektörüne yönelik yapay zeka destekli analiz, risk değerlendirme ve müşteri deneyimi dönüşüm araçları.

---

## Proje Hakkında

`sigorta-ai-po`, Claude API kullanarak sigortacılık süreçlerini otomatize eden ve akıllandıran bir Python platformudur. Poliçe analizi, hasar tespiti, risk skorlaması ve müşteri iletişimi gibi kritik operasyonları yapay zeka ile destekler.

### Temel Yetenekler

| Alan | Açıklama |
|------|----------|
| Poliçe Analizi | Poliçe belgelerini otomatik okuma ve kritik maddeleri çıkarma |
| Risk Değerlendirme | Müşteri profili ve geçmiş verilere göre risk skoru hesaplama |
| Hasar Asistanı | Hasar bildirimi süreçlerinde AI destekli müşteri yönlendirme |
| Sözleşme Özeti | Uzun sigorta sözleşmelerini sade dille özetleme |
| Müşteri Analizi | Portföy segmentasyonu ve churn riski tespiti |

---

## Proje Yapısı

```
sigorta-ai-po/
├── .claude/
│   └── commands/          # Özel Claude Code komutları
├── docs/                  # Teknik ve iş dokümantasyonu
├── prompts/               # Sigortacılık domain prompt şablonları
├── skills/                # Yeniden kullanılabilir AI skill modülleri
├── main.py                # Ana uygulama giriş noktası
├── requirements.txt       # Python bağımlılıkları
└── README.md
```

---

## Kurulum

### Gereksinimler

- Python 3.10+
- Anthropic API anahtarı

### Adımlar

```bash
# 1. Depoyu klonlayın
git clone https://github.com/your-org/sigorta-ai-po.git
cd sigorta-ai-po

# 2. Sanal ortam oluşturun
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. API anahtarını ayarlayın
export ANTHROPIC_API_KEY="your-api-key-here"
```

---

## Hızlı Başlangıç

```python
from main import SigortaAIAgent

agent = SigortaAIAgent()

# Poliçe analizi
sonuc = agent.analyze_police(police_metni)
print(sonuc)

# Risk değerlendirme
skor = agent.risk_score(musteri_profili)
print(skor)
```

---

## Kullanılan Teknolojiler

- **[Anthropic Claude API](https://docs.anthropic.com)** — `claude-opus-4-6` modeli
- **Claude Agent SDK** — Çok adımlı ajan iş akışları
- **Adaptive Thinking** — Karmaşık risk analizleri için genişletilmiş akıl yürütme
- **Streaming** — Uzun doküman analizlerinde gerçek zamanlı çıktı
- **Tool Use** — Dış sistemlerle entegrasyon (CRM, poliçe veritabanı)

---

## Güvenlik ve Uyumluluk

- API anahtarları yalnızca ortam değişkenleri aracılığıyla yönetilir; kod içinde saklanmaz
- Müşteri verileri işlem süresince şifrelenir
- KVKK ve GDPR uyumlu veri işleme prensipleri benimsenir
- Tüm AI çıktıları insan denetiminden geçirilmesi önerilir

---

## Katkı Rehberi

1. `feature/your-feature` dalı açın
2. Değişikliklerinizi yapın ve test edin
3. Pull Request gönderin

---

## Lisans

MIT License — Ayrıntılar için `LICENSE` dosyasına bakın.
