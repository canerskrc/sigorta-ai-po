"""
Sigorta AI Dönüşüm Platformu
Claude API (claude-opus-4-6) kullanan sigortacılık AI ajanı.
"""

import os
import json
import anthropic
from anthropic import beta_tool


# ---------------------------------------------------------------------------
# İstemci başlatma
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """Sen deneyimli bir sigortacılık uzmanısın ve yapay zeka asistanısın.
Türk sigorta sektörü mevzuatına (Sigortacılık Kanunu, SEDDK yönetmelikleri) hakimsin.
Poliçe analizi, risk değerlendirme ve müşteri danışmanlığı konularında uzman desteği sağlarsın.
Yanıtların her zaman net, profesyonel ve aksiyona yönelik olmalıdır."""


# ---------------------------------------------------------------------------
# Tool tanımlamaları
# ---------------------------------------------------------------------------

@beta_tool
def police_veritabani_sorgula(police_no: str) -> str:
    """Poliçe veritabanından poliçe bilgilerini getirir.

    Args:
        police_no: Sorgulanacak poliçe numarası.
    """
    # Gerçek uygulamada bu fonksiyon CRM/veritabanına bağlanır
    mock_data = {
        "POL-2024-001": {
            "musteri": "Ahmet Yılmaz",
            "urun": "Kasko",
            "prim": 8500,
            "baslangic": "2024-01-01",
            "bitis": "2025-01-01",
            "durum": "Aktif",
        }
    }
    result = mock_data.get(police_no, {"hata": "Poliçe bulunamadı"})
    return json.dumps(result, ensure_ascii=False)


@beta_tool
def risk_skoru_hesapla(yas: int, sehir: str, arac_modeli: str, hasar_sayisi: int) -> str:
    """Araç sigortası için müşteri risk skoru hesaplar.

    Args:
        yas: Sürücünün yaşı.
        sehir: İkametgah şehri.
        arac_modeli: Araç markası ve modeli.
        hasar_sayisi: Son 3 yıldaki hasar sayısı.
    """
    # Basit kural tabanlı skor (gerçek uygulamada ML modeli kullanılır)
    skor = 100
    if yas < 25:
        skor -= 20
    if sehir in ["İstanbul", "Ankara", "İzmir"]:
        skor -= 10
    skor -= hasar_sayisi * 15
    skor = max(0, min(100, skor))
    kategori = "Düşük" if skor >= 70 else "Orta" if skor >= 40 else "Yüksek"

    return json.dumps(
        {"risk_skoru": skor, "risk_kategorisi": kategori, "prim_carpani": round(1 + (100 - skor) / 100, 2)},
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Temel fonksiyonlar
# ---------------------------------------------------------------------------

def police_analiz_et(police_metni: str) -> str:
    """Poliçe metnini analiz ederek kritik bilgileri çıkarır (streaming)."""
    print("\n📋 Poliçe analiz ediliyor...\n")

    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Aşağıdaki sigorta poliçesini analiz et. "
                    f"Teminat kapsamı, muafiyetler, önemli kısıtlamalar ve müşterinin "
                    f"dikkat etmesi gereken maddeler hakkında yapılandırılmış bir özet sun:\n\n{police_metni}"
                ),
            }
        ],
    ) as stream:
        tam_yanit = ""
        for metin in stream.text_stream:
            print(metin, end="", flush=True)
            tam_yanit += metin

    print("\n")
    return tam_yanit


def risk_degerlendirmesi_yap(musteri_profili: dict) -> str:
    """Müşteri profiline göre kapsamlı risk değerlendirmesi yapar (tool use + adaptive thinking)."""
    print("\n🔍 Risk değerlendirmesi yapılıyor...\n")

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        tools=[risk_skoru_hesapla, police_veritabani_sorgula],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Şu müşteri için risk değerlendirmesi yap ve prim önerisi sun:\n"
                    f"{json.dumps(musteri_profili, ensure_ascii=False, indent=2)}\n\n"
                    f"Risk skoru hesapla ve kapsamlı bir değerlendirme raporu hazırla."
                ),
            }
        ],
    )

    sonuc = ""
    for mesaj in runner:
        for blok in mesaj.content:
            if blok.type == "text":
                sonuc = blok.text

    print(sonuc)
    return sonuc


def hasar_asistani(hasar_aciklamasi: str) -> str:
    """Hasar bildirimi sürecinde müşteriyi yönlendirir (adaptive thinking)."""
    print("\n🚨 Hasar asistanı devreye girdi...\n")

    yanit = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Bir müşteri şu hasarı bildirdi:\n\n\"{hasar_aciklamasi}\"\n\n"
                    f"1) Hasarın sigorta kapsamında olup olmadığını değerlendir.\n"
                    f"2) Müşterinin atması gereken adımları listele (belgeler, süreler, iletişim bilgileri).\n"
                    f"3) Süreçte dikkat etmesi gereken kritik noktaları vurgula."
                ),
            }
        ],
    )

    for blok in yanit.content:
        if blok.type == "text":
            print(blok.text)
            return blok.text

    return ""


def sozlesme_ozetle(sozlesme_metni: str) -> str:
    """Uzun sigorta sözleşmesini sade dille özetler (streaming)."""
    print("\n📄 Sözleşme özetleniyor...\n")

    with client.messages.stream(
        model=MODEL,
        max_tokens=1536,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Aşağıdaki sigorta sözleşmesini bir müşterinin anlayabileceği sade Türkçe ile özetle. "
                    f"Başlıklar: Ana Teminatlar, Kapsam Dışı Durumlar, Önemli Yükümlülükler, "
                    f"İptal ve İade Koşulları.\n\n{sozlesme_metni}"
                ),
            }
        ],
    ) as stream:
        ozet = ""
        for metin in stream.text_stream:
            print(metin, end="", flush=True)
            ozet += metin

    print("\n")
    return ozet


# ---------------------------------------------------------------------------
# Ajan sınıfı
# ---------------------------------------------------------------------------

class SigortaAIAgent:
    """Sigortacılık AI dönüşüm ajanı — tüm yetenekleri tek arayüzde toplar."""

    def analyze_police(self, police_metni: str) -> str:
        return police_analiz_et(police_metni)

    def risk_score(self, musteri_profili: dict) -> str:
        return risk_degerlendirmesi_yap(musteri_profili)

    def hasar_asistan(self, aciklama: str) -> str:
        return hasar_asistani(aciklama)

    def summarize_contract(self, sozlesme: str) -> str:
        return sozlesme_ozetle(sozlesme)


# ---------------------------------------------------------------------------
# Demo çalıştırma
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Sigorta AI Dönüşüm Platformu — Demo")
    print("=" * 60)

    # Demo 1: Poliçe analizi
    ornek_police = """
    KASKO SİGORTASI POLİÇESİ
    Poliçe No: POL-2024-001
    Sigortalı: Ahmet Yılmaz | Araç: 2022 Toyota Corolla

    Teminatlar:
    - Çarpma, çarpışma, devrilme, yanma teminatı: 450.000 TL
    - Hırsızlık ve hırsızlığa teşebbüs: 450.000 TL
    - Doğal afetler (deprem hariç): dahil
    - Cam kırılması: 15.000 TL limit

    Muafiyetler:
    - Her hasarda %10 muafiyet (min. 2.500 TL)
    - Deprem ve sel hasarı teminat dışı
    - Alkollü araç kullanımı sonucu oluşan hasarlar kapsam dışıdır
    """
    police_analiz_et(ornek_police)

    # Demo 2: Risk değerlendirmesi
    musteri = {
        "ad_soyad": "Mehmet Kaya",
        "yas": 28,
        "sehir": "İstanbul",
        "arac_modeli": "Honda Civic 2021",
        "ehliyet_yili": 4,
        "hasar_sayisi": 2,
    }
    risk_degerlendirmesi_yap(musteri)

    # Demo 3: Hasar asistanı
    hasar_asistani(
        "Dün gece park halindeyken araçıma çarpmışlar, kapı ve çamurluk ezildi. "
        "Karşı taraf kaçmış, tanık yok. Ne yapmalıyım?"
    )
