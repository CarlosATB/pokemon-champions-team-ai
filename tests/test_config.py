"""Testes básicos da configuração."""

from src import config


def test_formato_e_de_duplas_do_champions():
    assert config.FORMAT_ID.startswith("gen9championsvgc")


def test_url_do_smogon_esta_montada_corretamente():
    url = config.smogon_chaos_url(month="2026-09", format_id="gen9championsvgc2026regmc", rating=1500)
    assert url == "https://www.smogon.com/stats/2026-09/chaos/gen9championsvgc2026regmc-1500.json"


def test_regras_do_formato():
    assert config.TEAM_SIZE == 6
    assert config.PICK_SIZE == 4
    assert config.LEVEL == 50
    assert config.MAX_MEGA_PER_BATTLE == 1
    assert config.HAS_TERA is False


def test_pastas_de_dados_existem():
    assert config.RAW_DATA_DIR.is_dir()
    assert config.PROCESSED_DATA_DIR.is_dir()
