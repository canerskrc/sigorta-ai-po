# Skill: Ajan ve Subagent (Agent SDK)

## Amaç
Dosya okuma, web araştırma, shell komutları ve çok adımlı öz-yönlendirmeli görevler
için Claude Agent SDK kullanır. Sigorta mevzuatı araştırma, poliçe dizini tarama
ve kod üretme gibi açık uçlu görevler için idealdir.

## Claude API Yüzeyi
- **SDK:** `claude-agent-sdk` (Python)
- **Yöntem:** `query()` (basit) veya `ClaudeSDKClient` (özel araçlar, hook'lar)
- **Ne Zaman Agent SDK, Ne Zaman Direkt API?**
  - Claude'un kendisi dosya/web/shell erişmesi gerekiyorsa → Agent SDK
  - Sen dosyayı okuyup Claude'a veriyorsan → Direkt API

## Temel Kullanım

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def mevzuat_araştır(konu: str) -> str:
    """Claude'un web araması yaparak SEDDK mevzuatını araştırmasını sağlar."""
    sonuc = ""
    async for mesaj in query(
        prompt=(
            f"SEDDK ve Türk sigorta mevzuatında '{konu}' konusunu araştır. "
            f"Güncel düzenlemeleri, son değişiklikleri ve uyum gerekliliklerini özetle."
        ),
        options=ClaudeAgentOptions(
            allowed_tools=["WebSearch", "WebFetch"],
            model="claude-opus-4-6",
            max_turns=10,
        ),
    ):
        if isinstance(mesaj, ResultMessage):
            sonuc = mesaj.result
    return sonuc

anyio.run(mevzuat_araştır, "zorunlu deprem sigortası DASK")
```

## Çok Adımlı Poliçe Dizini Tarama

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def police_dizini_tara(dizin_yolu: str) -> str:
    """Poliçe klasörünü tarayıp analiz raporu üretir."""
    sonuc = ""
    async for mesaj in query(
        prompt=(
            f"{dizin_yolu} dizinindeki tüm poliçe dosyalarını tara. "
            f"Her poliçe için: ürün türü, prim miktarı, bitiş tarihi ve risk sınıfını listele. "
            f"30 gün içinde biten poliçeleri özellikle vurgula. "
            f"Özet tabloyu markdown formatında sun."
        ),
        options=ClaudeAgentOptions(
            cwd=dizin_yolu,
            allowed_tools=["Read", "Glob", "Grep"],
            model="claude-opus-4-6",
            max_turns=20,
            permission_mode="default",
        ),
    ):
        if isinstance(mesaj, ResultMessage):
            sonuc = mesaj.result
    return sonuc
```

## Subagent ile Paralel Analiz

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition, ResultMessage

async def kapsamli_hasar_analizi(hasar_dosyasi: str) -> str:
    """Ana ajan + uzman subagentlar ile derinlemesine hasar analizi."""
    sonuc = ""
    async for mesaj in query(
        prompt=(
            f"{hasar_dosyasi} dosyasındaki hasarı analiz et. "
            f"Hem hukuki hem teknik değerlendirme için ilgili subagentları kullan."
        ),
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Agent"],
            model="claude-opus-4-6",
            max_turns=15,
            agents={
                "hukuk-uzmani": AgentDefinition(
                    description="Sigorta hukuku ve mevzuat uyum uzmanı.",
                    prompt=(
                        "Türk sigorta hukuku ve SEDDK mevzuatı konusunda uzman bir hukukçusun. "
                        "Hasar belgelerini hukuki açıdan değerlendir."
                    ),
                    tools=["Read", "Grep"],
                ),
                "teknik-eksper": AgentDefinition(
                    description="Araç hasarı teknik değerlendirme uzmanı.",
                    prompt=(
                        "Deneyimli bir araç ekspertisin. "
                        "Hasar tespiti, tamir maliyeti ve toplam hasar değerlendirmesi yaparsın."
                    ),
                    tools=["Read"],
                ),
            },
        ),
    ):
        if isinstance(mesaj, ResultMessage):
            sonuc = mesaj.result
    return sonuc
```

## Hook ile Denetim Kaydı

```python
import anyio
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, ResultMessage

async def denetimli_dosya_guncelle(gorev: str):
    """Tüm dosya değişikliklerini audit.log'a kaydeder."""

    async def dosya_degisikligi_kaydet(girdi, tool_id, context):
        dosya = girdi.get("tool_input", {}).get("file_path", "bilinmiyor")
        with open("./audit.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {dosya}\n")
        return {}

    async for mesaj in query(
        prompt=gorev,
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Write"],
            permission_mode="acceptEdits",
            hooks={
                "PostToolUse": [
                    HookMatcher(
                        matcher="Edit|Write",
                        hooks=[dosya_degisikligi_kaydet],
                    )
                ]
            },
        ),
    ):
        if isinstance(mesaj, ResultMessage):
            print(mesaj.result)
```

## MCP Entegrasyonu

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def notion_ile_calis(gorev: str):
    """Notion MCP sunucusu aracılığıyla Notion'a erişir."""
    async for mesaj in query(
        prompt=gorev,
        options=ClaudeAgentOptions(
            mcp_servers={
                "notion": {
                    "command": "npx",
                    "args": ["-y", "@anthropic-ai/mcp-server-notion"],
                    "env": {"NOTION_API_KEY": os.environ["NOTION_API_KEY"]},
                }
            }
        ),
    ):
        if isinstance(mesaj, ResultMessage):
            print(mesaj.result)
```

## Ne Zaman Kullanılır
- Mevzuat araştırması ve güncel bilgi taraması
- Poliçe dosya klasörlerini otomatik tarama ve raporlama
- Karmaşık hasar dosyası hazırlama (belgeler + analiz + rapor)
- Ajan destekli müşteri mektupları yazma

## Dikkat Edilecekler
- `max_turns` ile sınır koy — kontrolsüz döngü masraf yaratır
- Üretim ortamında `bypassPermissions` kullanma
- Hassas müşteri verisi içeren dizinlerde `permission_mode="default"` zorunlu
- Agent SDK Claude Code CLI gerektirir — `pip install claude-agent-sdk`
