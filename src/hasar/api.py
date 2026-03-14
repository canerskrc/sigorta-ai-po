"""
Hasar İhbar API
===============
Endpoint: POST /hasar/ihbar

Akış:
  1. İstek body'si Pydantic ile validate edilir (TC 11 hane, tarih geçmişte).
  2. Kayıt SQLAlchemy aracılığıyla veritabanına yazılır.
  3. Notion'a asenkron olarak iletilir; Notion ID DB kaydına geri yazılır.
  4. Başarı yanıtı döner.
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import HasarIhbar
from .notion import hasar_notion_yaz
from .schemas import HasarIhbarIstek, HasarIhbarYanit

logger = logging.getLogger(__name__)

# Uygulama başlangıcında tabloları oluştur
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/hasar", tags=["Hasar"])


@router.post(
    "/ihbar",
    response_model=HasarIhbarYanit,
    status_code=status.HTTP_201_CREATED,
    summary="Hasar İhbarı Oluştur",
    description=(
        "Yeni bir hasar ihbarı kaydeder. "
        "TC kimlik numarası algoritma ile doğrulanır; "
        "hasar tarihi bugün veya geçmiş bir tarih olmalıdır."
    ),
)
def hasar_ihbar_olustur(
    istek: HasarIhbarIstek,
    db: Session = Depends(get_db),
) -> HasarIhbarYanit:
    """Hasar ihbarını veritabanına kaydeder ve Notion'a iletir."""

    # 1. Veritabanına yaz
    kayit = HasarIhbar(
        tc_kimlik=istek.tc_kimlik,
        hasar_tarihi=istek.hasar_tarihi,
        aciklama=istek.aciklama,
    )
    db.add(kayit)
    db.commit()
    db.refresh(kayit)
    logger.info("Hasar ihbarı kaydedildi — id=%d tc=%s", kayit.id, kayit.tc_kimlik)

    # 2. Notion'a yaz (hata, ana akışı bloke etmez)
    notion_id = hasar_notion_yaz(
        tc_kimlik=kayit.tc_kimlik,
        hasar_tarihi=kayit.hasar_tarihi,
        aciklama=kayit.aciklama,
        ihbar_id=kayit.id,
    )
    if notion_id:
        kayit.notion_page_id = notion_id
        db.commit()
        db.refresh(kayit)

    return HasarIhbarYanit.model_validate(kayit)


@router.get(
    "/ihbar/{ihbar_id}",
    response_model=HasarIhbarYanit,
    summary="Hasar İhbarı Getir",
    description="Belirtilen ID'ye sahip hasar ihbarını döner.",
)
def hasar_ihbar_getir(
    ihbar_id: int,
    db: Session = Depends(get_db),
) -> HasarIhbarYanit:
    """ID'ye göre tek bir hasar ihbarını getirir."""

    kayit = db.get(HasarIhbar, ihbar_id)
    if kayit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"İhbar bulunamadı — id={ihbar_id}",
        )
    return HasarIhbarYanit.model_validate(kayit)
