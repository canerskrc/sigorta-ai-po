"""
Hasar İhbar API testleri.
Çalıştırmak için: pytest --cov=src/hasar --cov-report=term-missing
Hedef coverage: ≥ %80
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.hasar.api import router
from src.hasar.database import Base, get_db
from src.hasar.schemas import _tc_algoritma_dogrula


# ---------------------------------------------------------------------------
# Test DB kurulumu — in-memory SQLite
# ---------------------------------------------------------------------------

# Paylaşımlı in-memory SQLite: tüm bağlantılar aynı DB'yi görür
TEST_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ---------------------------------------------------------------------------
# Yardımcı sabitler
# ---------------------------------------------------------------------------

GECERLI_TC = "17754314574"          # Algoritmayı geçen gerçek format TC
GECMIS_TARIH = (date.today() - timedelta(days=5)).isoformat()
BUGUN = date.today().isoformat()
GELECEK = (date.today() + timedelta(days=1)).isoformat()
ACIKLAMA = "Park halindeyken araçıma çarptılar, sol kapı hasar gördü."


# ---------------------------------------------------------------------------
# TC algoritma birimi testleri
# ---------------------------------------------------------------------------

class TestTcAlgoritmaDogrula:
    def test_gecerli_tc(self):
        assert _tc_algoritma_dogrula(GECERLI_TC) is True

    def test_11_haneden_kisa(self):
        assert _tc_algoritma_dogrula("1234567890") is False

    def test_11_haneden_uzun(self):
        assert _tc_algoritma_dogrula("123456789012") is False

    def test_rakam_olmayan_karakter(self):
        assert _tc_algoritma_dogrula("1234567890X") is False

    def test_ilk_rakam_sifir(self):
        assert _tc_algoritma_dogrula("01234567890") is False

    def test_yanlis_10_rakam(self):
        # Son iki rakamı bozan TC
        yanlis = GECERLI_TC[:9] + "99"
        assert _tc_algoritma_dogrula(yanlis) is False

    def test_yanlis_11_rakam(self):
        yanlis = GECERLI_TC[:10] + str((int(GECERLI_TC[10]) + 1) % 10)
        assert _tc_algoritma_dogrula(yanlis) is False


# ---------------------------------------------------------------------------
# POST /hasar/ihbar — başarılı senaryolar
# ---------------------------------------------------------------------------

class TestHasarIhbarOlustur:
    def _ihbar_gonder(self, tc=GECERLI_TC, tarih=GECMIS_TARIH, aciklama=ACIKLAMA):
        return client.post(
            "/hasar/ihbar",
            json={"tc_kimlik": tc, "hasar_tarihi": tarih, "aciklama": aciklama},
        )

    @patch("src.hasar.api.hasar_notion_yaz", return_value="notion-page-abc")
    def test_basarili_ihbar_201_doner(self, mock_notion):
        yanit = self._ihbar_gonder()
        assert yanit.status_code == 201

    @patch("src.hasar.api.hasar_notion_yaz", return_value="notion-page-abc")
    def test_basarili_ihbar_notion_id_iceriyor(self, mock_notion):
        yanit = self._ihbar_gonder()
        veri = yanit.json()
        assert veri["notion_page_id"] == "notion-page-abc"

    @patch("src.hasar.api.hasar_notion_yaz", return_value="notion-page-abc")
    def test_basarili_ihbar_yanit_alanlari_dolu(self, mock_notion):
        yanit = self._ihbar_gonder()
        veri = yanit.json()
        assert "id" in veri
        assert veri["tc_kimlik"] == GECERLI_TC
        assert veri["hasar_tarihi"] == GECMIS_TARIH
        assert "mesaj" in veri

    @patch("src.hasar.api.hasar_notion_yaz", return_value=None)
    def test_notion_hata_verirse_kayit_yine_olusur(self, mock_notion):
        """Notion başarısız olsa bile ihbar DB'ye yazılmalı."""
        yanit = self._ihbar_gonder()
        assert yanit.status_code == 201
        assert yanit.json()["notion_page_id"] is None

    @patch("src.hasar.api.hasar_notion_yaz", return_value="notion-page-abc")
    def test_notion_cagirildi(self, mock_notion):
        self._ihbar_gonder()
        mock_notion.assert_called_once()

    @patch("src.hasar.api.hasar_notion_yaz", return_value=None)
    def test_dun_tarihi_gecerli(self, _):
        dun = (date.today() - timedelta(days=1)).isoformat()
        yanit = self._ihbar_gonder(tarih=dun)
        assert yanit.status_code == 201

    @patch("src.hasar.api.hasar_notion_yaz", return_value=None)
    def test_uzun_gecmis_tarih_gecerli(self, _):
        uzak_gecmis = "2000-01-01"
        yanit = self._ihbar_gonder(tarih=uzak_gecmis)
        assert yanit.status_code == 201


# ---------------------------------------------------------------------------
# POST /hasar/ihbar — hatalı senaryolar (422)
# ---------------------------------------------------------------------------

class TestHasarIhbarValidasyon:
    def _ihbar_gonder(self, payload: dict):
        return client.post("/hasar/ihbar", json=payload)

    def test_tc_10_hane_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": "1234567890", "hasar_tarihi": GECMIS_TARIH, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_tc_12_hane_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": "123456789012", "hasar_tarihi": GECMIS_TARIH, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_tc_harf_iceriyor_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": "1234567890X", "hasar_tarihi": GECMIS_TARIH, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_gecersiz_tc_algoritmasi_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": "11111111111", "hasar_tarihi": GECMIS_TARIH, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_bugun_tarihi_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": GECERLI_TC, "hasar_tarihi": BUGUN, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_gelecek_tarihi_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": GECERLI_TC, "hasar_tarihi": GELECEK, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_kisa_aciklama_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": GECERLI_TC, "hasar_tarihi": GECMIS_TARIH, "aciklama": "kısa"}
        )
        assert yanit.status_code == 422

    def test_eksik_alan_tc_422(self):
        yanit = self._ihbar_gonder(
            {"hasar_tarihi": GECMIS_TARIH, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_eksik_alan_tarih_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": GECERLI_TC, "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422

    def test_eksik_alan_aciklama_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": GECERLI_TC, "hasar_tarihi": GECMIS_TARIH}
        )
        assert yanit.status_code == 422

    def test_gecersiz_tarih_formati_422(self):
        yanit = self._ihbar_gonder(
            {"tc_kimlik": GECERLI_TC, "hasar_tarihi": "10-03-2024", "aciklama": ACIKLAMA}
        )
        assert yanit.status_code == 422


# ---------------------------------------------------------------------------
# GET /hasar/ihbar/{id}
# ---------------------------------------------------------------------------

class TestHasarIhbarGetir:
    @patch("src.hasar.api.hasar_notion_yaz", return_value="notion-xyz")
    def test_mevcut_ihbar_getirilir(self, _):
        olustur = client.post(
            "/hasar/ihbar",
            json={"tc_kimlik": GECERLI_TC, "hasar_tarihi": GECMIS_TARIH, "aciklama": ACIKLAMA},
        )
        ihbar_id = olustur.json()["id"]
        yanit = client.get(f"/hasar/ihbar/{ihbar_id}")
        assert yanit.status_code == 200
        assert yanit.json()["id"] == ihbar_id

    def test_olmayan_ihbar_404(self):
        yanit = client.get("/hasar/ihbar/999999")
        assert yanit.status_code == 404

    def test_404_hata_mesaji_iceriyor(self):
        yanit = client.get("/hasar/ihbar/999999")
        assert "bulunamadı" in yanit.json()["detail"].lower() or "999999" in yanit.json()["detail"]


# ---------------------------------------------------------------------------
# Notion modülü birimi testleri
# ---------------------------------------------------------------------------

class TestNotionYaz:
    def test_notion_bilgileri_eksikse_none_doner(self):
        from src.hasar.notion import hasar_notion_yaz
        with patch.dict("os.environ", {"NOTION_API_KEY": "", "NOTION_DATABASE_ID": ""}):
            # Modülü yeniden yükleyip çağırmak yerine, doğrudan env boşken çağırıyoruz
            # notion.py her çağrıda env'i okur (token/db id'yi _get_client içinde)
            sonuc = hasar_notion_yaz("12345678901", date(2024, 1, 1), "test", 1)
            # Env boşken None dönmeli
            assert sonuc is None

    def test_notion_api_hatasinda_none_doner(self):
        from src.hasar.notion import hasar_notion_yaz
        from notion_client.errors import APIResponseError

        with (
            patch.dict("os.environ", {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "db-id"}),
            patch("src.hasar.notion._get_client") as mock_client_factory,
        ):
            mock_client = MagicMock()
            # notion-client v3'te APIResponseError doğrudan raise edilebilir
            import httpx
            mock_client.pages.create.side_effect = APIResponseError(
                code="validation_error",
                status=400,
                message="hata",
                headers=httpx.Headers({}),
                raw_body_text="Bad Request",
            )
            mock_client_factory.return_value = mock_client
            sonuc = hasar_notion_yaz(GECERLI_TC, date(2024, 1, 1), "açıklama", 42)
            assert sonuc is None

    def test_notion_beklenmedik_hata_none_doner(self):
        from src.hasar.notion import hasar_notion_yaz

        with (
            patch.dict("os.environ", {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "db-id"}),
            patch("src.hasar.notion._get_client") as mock_client_factory,
        ):
            mock_client = MagicMock()
            mock_client.pages.create.side_effect = RuntimeError("beklenmedik hata")
            mock_client_factory.return_value = mock_client
            sonuc = hasar_notion_yaz(GECERLI_TC, date(2024, 1, 1), "açıklama", 42)
            assert sonuc is None

    def test_notion_basarili_page_id_doner(self):
        from src.hasar.notion import hasar_notion_yaz

        with (
            patch.dict("os.environ", {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "db-id"}),
            patch("src.hasar.notion._get_client") as mock_client_factory,
        ):
            mock_client = MagicMock()
            mock_client.pages.create.return_value = {"id": "page-abc-123"}
            mock_client_factory.return_value = mock_client
            sonuc = hasar_notion_yaz(GECERLI_TC, date(2024, 1, 1), "açıklama", 42)
            assert sonuc == "page-abc-123"
