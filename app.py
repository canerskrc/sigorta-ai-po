import os
import re
import json
import asyncio
from pathlib import Path
from typing import AsyncIterator

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Sigorta AI Skills")

SKILLS_DIR = Path(__file__).parent / "skills"

SKILL_FILES = {
    "sprint-planlama": "sprint-planlama.md",
    "toplanti-ozetle": "toplanti-ozetle.md",
    "gorev-parcala": "gorev-parcala.md",
    "haftalik-rapor": "haftalik-rapor.md",
}


def _system_prompt_oku(skill_key: str) -> str:
    dosya = SKILL_FILES.get(skill_key)
    if not dosya:
        raise HTTPException(status_code=404, detail=f"Skill bulunamadı: {skill_key}")
    yol = SKILLS_DIR / dosya
    if not yol.exists():
        raise HTTPException(status_code=404, detail=f"Skill dosyası bulunamadı: {dosya}")
    icerik = yol.read_text(encoding="utf-8")
    eslesme = re.search(r"##\s*System Prompt\s*\n(.*?)(?=\n##\s|\Z)", icerik, re.DOTALL)
    if not eslesme:
        return icerik.strip()
    return eslesme.group(1).strip()


def _notion_kaydet(skill_key: str, girdi: str, cikti: str) -> str | None:
    token = os.environ.get("NOTION_API_KEY")
    db_id = os.environ.get("NOTION_SKILLS_DATABASE_ID") or os.environ.get("NOTION_DATABASE_ID")
    if not token or not db_id:
        return None
    try:
        from notion_client import Client
        from notion_client.errors import APIResponseError

        notion = Client(auth=token)
        baslik = girdi[:80].replace("\n", " ").strip()
        if not baslik:
            baslik = skill_key
        sayfa = notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Başlık": {"title": [{"text": {"content": baslik}}]},
                "Skill": {"rich_text": [{"text": {"content": skill_key}}]},
                "Girdi": {"rich_text": [{"text": {"content": girdi[:2000]}}]},
                "Çıktı": {"rich_text": [{"text": {"content": cikti[:2000]}}]},
            },
        )
        return sayfa["id"]
    except Exception:
        return None


class SkillIstegi(BaseModel):
    girdi: str


async def _stream_yaz(skill_key: str, girdi: str) -> AsyncIterator[str]:
    system_prompt = _system_prompt_oku(skill_key)
    aclient = anthropic.AsyncAnthropic()
    tampon = []

    try:
        async with aclient.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": girdi}],
        ) as stream:
            async for metin in stream.text_stream:
                tampon.append(metin)
                satir = json.dumps({"t": "chunk", "v": metin}, ensure_ascii=False)
                yield satir + "\n"

        tam_cikti = "".join(tampon)
        notion_id = await asyncio.to_thread(_notion_kaydet, skill_key, girdi, tam_cikti)
        bitis = json.dumps({"t": "done", "notion_id": notion_id}, ensure_ascii=False)
        yield bitis + "\n"

    except anthropic.APIError as e:
        hata = json.dumps({"t": "error", "v": str(e)}, ensure_ascii=False)
        yield hata + "\n"


@app.get("/")
async def anasayfa():
    html_dosyasi = Path(__file__).parent / "index.html"
    if not html_dosyasi.exists():
        raise HTTPException(status_code=404, detail="index.html bulunamadı")
    return FileResponse(html_dosyasi, media_type="text/html")


@app.post("/api/run/{skill_key}")
async def skill_calistir(skill_key: str, istek: SkillIstegi):
    if skill_key not in SKILL_FILES:
        raise HTTPException(status_code=404, detail=f"Geçersiz skill: {skill_key}")
    if not istek.girdi.strip():
        raise HTTPException(status_code=422, detail="Girdi boş olamaz")

    return StreamingResponse(
        _stream_yaz(skill_key, istek.girdi),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
