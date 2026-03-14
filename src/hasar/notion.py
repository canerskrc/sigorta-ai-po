"""Notion entegrasyonu — başarılı hasar ihbarlarını veritabanına yazar."""

import logging
import os
from datetime import date

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)

def _get_client() -> Client:
    return Client(auth=os.environ.get("NOTION_API_KEY", ""))


def hasar_notion_yaz(
    tc_kimlik: str,
    hasar_tarihi: date,
    aciklama: str,
    ihbar_id: int,
) -> str | None:
    """
    Hasar ihbarını Notion veritabanına ekler.

    Notion veritabanında şu sütunlar beklenir:
      - TC Kimlik  (title)
      - Hasar Tarihi (date)
      - Açıklama   (rich_text)
      - İhbar ID   (number)

    Başarılı olursa oluşturulan sayfanın ID'sini döner; hata durumunda None.
    """
    if not os.environ.get("NOTION_API_KEY") or not os.environ.get("NOTION_DATABASE_ID"):
        logger.warning("Notion kimlik bilgileri eksik — kayıt atlandı.")
        return None

    try:
        client = _get_client()
        yanit = client.pages.create(
            parent={"database_id": os.environ.get("NOTION_DATABASE_ID", "")},
            properties={
                "TC Kimlik": {
                    "title": [{"text": {"content": tc_kimlik}}]
                },
                "Hasar Tarihi": {
                    "date": {"start": hasar_tarihi.isoformat()}
                },
                "Açıklama": {
                    "rich_text": [{"text": {"content": aciklama[:2000]}}]
                },
                "İhbar ID": {
                    "number": ihbar_id
                },
            },
        )
        page_id: str = yanit["id"]
        logger.info("Notion sayfası oluşturuldu: %s", page_id)
        return page_id

    except APIResponseError as exc:
        logger.error("Notion API hatası: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("Notion yazma hatası: %s", exc)
        return None
