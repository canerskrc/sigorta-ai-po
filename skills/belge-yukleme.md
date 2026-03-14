# Skill: Belge Yükleme (Files API)

## Amaç
Sigorta belgeleri (poliçe PDF'leri, hasar raporları, ekspertiz raporları, görseller)
Files API ile bir kez yüklenir; aynı dosya birden fazla sorgu ve analizde referans alınır.
Tekrar yükleme maliyetini ve gecikmesini ortadan kaldırır.

## Claude API Yüzeyi
- **Model:** `claude-opus-4-6`
- **Yöntem:** `client.beta.files` + `client.beta.messages.create()`
- **Beta Header:** `betas=["files-api-2025-04-14"]`
- **Desteklenen Formatlar:** PDF, PNG, JPEG, GIF, WebP, TXT, CSV, JSON, XML
- **Limit:** Dosya başına 500 MB | Toplam 100 GB / organizasyon

## Python Şablonu — Temel Kullanım

```python
import anthropic

client = anthropic.Anthropic()

# 1. Dosyayı bir kez yükle
def belge_yukle(dosya_yolu: str, mime_type: str = "application/pdf") -> str:
    """Dosyayı Files API'ye yükler ve file_id döner."""
    with open(dosya_yolu, "rb") as f:
        yuklenen = client.beta.files.upload(
            file=(dosya_yolu.split("/")[-1], f, mime_type),
        )
    print(f"Yüklendi: {yuklenen.id} ({yuklenen.size_bytes} bytes)")
    return yuklenen.id

# 2. Aynı dosyayı birden fazla soruda kullan
def dosyaya_sor(file_id: str, soru: str) -> str:
    yanit = client.beta.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": soru},
                {
                    "type": "document",
                    "source": {"type": "file", "file_id": file_id},
                    "citations": {"enabled": True},  # kaynak referansı
                },
            ],
        }],
        betas=["files-api-2025-04-14"],
    )
    return next(b.text for b in yanit.content if b.type == "text")

# 3. İşim bitince dosyayı sil
def belge_sil(file_id: str):
    client.beta.files.delete(file_id)
    print(f"Silindi: {file_id}")
```

## Sigorta Belge İş Akışı

```python
def ekspertiz_raporu_isle(pdf_yolu: str) -> dict:
    """
    Ekspertiz raporunu yükle, birden fazla açıdan analiz et.
    """
    file_id = belge_yukle(pdf_yolu)

    try:
        sonuclar = {
            "ozet": dosyaya_sor(file_id, "Bu ekspertiz raporunu özetle."),
            "hasar_tutari": dosyaya_sor(
                file_id,
                "Belirlenen hasar tutarı nedir? Sadece rakamı ver."
            ),
            "sorumluluk": dosyaya_sor(
                file_id,
                "Kusur/sorumluluk dağılımı nasıl belirlenmiş?"
            ),
            "itiraz_noktalari": dosyaya_sor(
                file_id,
                "Müşterinin itiraz edebileceği noktalar var mı?"
            ),
        }
    finally:
        belge_sil(file_id)  # her durumda temizle

    return sonuclar
```

## Görsel Analiz (Hasar Fotoğrafı)

```python
def hasar_fotografı_analiz_et(gorsel_yolu: str) -> dict:
    """Hasar fotoğrafını yükleyip analiz eder."""
    with open(gorsel_yolu, "rb") as f:
        gorsel = client.beta.files.upload(
            file=(gorsel_yolu.split("/")[-1], f, "image/jpeg"),
        )

    try:
        yanit = client.beta.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Bu hasar fotoğrafını analiz et: "
                            "1) Hasar türü nedir? "
                            "2) Tahmini onarım kategorisi (Kozmetik/Orta/Ağır)? "
                            "3) Ek ekspertiz gerekiyor mu?"
                        ),
                    },
                    {
                        "type": "image",
                        "source": {"type": "file", "file_id": gorsel.id},
                    },
                ],
            }],
            betas=["files-api-2025-04-14"],
        )
        return {"analiz": next(b.text for b in yanit.content if b.type == "text")}
    finally:
        client.beta.files.delete(gorsel.id)
```

## Dosya Yönetimi

```python
# Tüm yüklü dosyaları listele
def yuklu_dosyalari_listele():
    dosyalar = client.beta.files.list()
    for f in dosyalar.data:
        print(f"{f.id}: {f.filename} ({f.size_bytes} bytes)")

# Metadata getir
def dosya_bilgisi(file_id: str):
    meta = client.beta.files.retrieve_metadata(file_id)
    return {"id": meta.id, "dosya_adi": meta.filename, "mime": meta.mime_type}
```

## Ne Zaman Kullanılır
- Aynı poliçe/rapor için 2+ sorgu yapılacaksa
- Hasar dosyasında çok sayıda belge var (rapor + fotoğraf + tutanak)
- Uzun vadeli referans dokümanlar (genel şartname, mevzuat)
- Müşteri belgelerini analiz pipeline'ına beslemek

## Dikkat Edilecekler
- Dosyalar silinene kadar organizasyon depolama kotasından düşer
- KVKK: kişisel veri içeren belgeler işlem sonrası silinmeli
- Bedrock ve Vertex AI'da Files API desteği yoktur
- `betas` header olmadan beta messages endpoint'i kullanılamaz
