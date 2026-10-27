"""
Visual do site: cores dos tipos, etiquetas coloridas e o CSS dos cards.

Só aparência; nenhuma regra de IA mora aqui.
"""

from src import config
from src.tipos import TIPOS_PT

# Cor oficial de cada tipo (a mesma que os jogos e os sites de Pokémon usam).
CORES_DOS_TIPOS = {
    "Normal": "#A8A77A", "Fire": "#EE8130", "Water": "#6390F0", "Electric": "#F7D02C",
    "Grass": "#7AC74C", "Ice": "#96D9D6", "Fighting": "#C22E28", "Poison": "#A33EA1",
    "Ground": "#E2BF65", "Flying": "#A98FF3", "Psychic": "#F95587", "Bug": "#A6B91A",
    "Rock": "#B6A136", "Ghost": "#735797", "Dragon": "#6F35FC", "Dark": "#705746",
    "Steel": "#B7B7CE", "Fairy": "#D685AD",
}

CATEGORIAS = {"Physical": "Físico", "Special": "Especial", "Status": "Status"}


def etiqueta_tipo(tipo: str, pequena: bool = False) -> str:
    """HTML de uma etiqueta colorida com o nome do tipo em português."""
    classe = "tipo pequena" if pequena else "tipo"
    return (f'<span class="{classe}" style="background:{CORES_DOS_TIPOS[tipo]}">'
            f"{TIPOS_PT[tipo]}</span>")


def etiquetas(tipos: list[str]) -> str:
    return " ".join(etiqueta_tipo(t) for t in tipos)


def imagem(pokemon_id: str) -> str | None:
    """Caminho da imagem do Pokémon (None se não houver)."""
    caminho = config.SPRITES_DIR / f"{pokemon_id}.png"
    return str(caminho) if caminho.exists() else None


# CSS colocado uma vez no topo da página (st.markdown com unsafe_allow_html).
# Os cards são st.container(key="card_N"): o Streamlit dá a classe "st-key-card_N".
CSS = """
<style>
[class*="st-key-card_"] {
    background: #2c2c31;
    border: 1px solid #3c3c44;
    border-radius: 10px;
    padding: 10px 12px;
}
.tipo {
    display: inline-block;
    min-width: 64px;
    padding: 2px 8px;
    margin: 2px 0;
    border-radius: 12px;
    color: white;
    font-size: 0.78rem;
    font-weight: 600;
    text-align: center;
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.6);
}
.tipo.pequena { min-width: 0; width: 100%; font-size: 0.7rem; padding: 2px 4px; }
/* Imagens em pixel art: aumentar sem borrar */
[data-testid="stImage"] img { image-rendering: pixelated; }
.vazio { color: #8a8a93; font-size: 0.85rem; text-align: center; padding: 30px 0; }
</style>
"""
