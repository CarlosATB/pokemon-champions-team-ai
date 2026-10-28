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


def url_da_imagem(pokemon_id: str) -> str:
    """Endereço da imagem para usar dentro de HTML (<img src=...>)."""
    return f"{config.SPRITES_URL}/{pokemon_id}.png"


def foto(pokemon_id: str, tamanho: int = 28) -> str:
    """HTML de uma fotinho do Pokémon."""
    return (f'<img class="foto" src="{url_da_imagem(pokemon_id)}" '
            f'width="{tamanho}" height="{tamanho}">')


def grade_de_tipos(celulas: list[dict]) -> str:
    """Grade com os 18 tipos (6 por linha), um número embaixo de cada um e
    uma caixinha que aparece ao passar o mouse.

    celula = {tipo, numero: "+3", cor: "verde" | "vermelho" | "neutro", detalhe: HTML}
    """
    html = []
    for c in celulas:
        html.append(
            f'<div class="celula">'
            f'<span class="tipo largo" style="background:{CORES_DOS_TIPOS[c["tipo"]]}">'
            f'{TIPOS_PT[c["tipo"]]}</span>'
            f'<div class="numero {c["cor"]}">{c["numero"]}</div>'
            f'<div class="detalhe">{c["detalhe"]}</div></div>')
    return f'<div class="grade">{"".join(html)}</div>'


def css_fotos_na_lista(ids_ordenados: list[str]) -> str:
    """Coloca a fotinha do Pokémon ao lado de cada nome na lista de escolha.

    O selectbox do Streamlit não aceita imagens, mas cada opção da lista aberta
    tem data-key = posição dela nas opções (0 = "Escolha um Pokémon"). Então
    uma regra de CSS por Pokémon põe a imagem certa como fundo da opção.
    """
    regras = [f'[role="listbox"][aria-label="Pokémon"] [data-key="{n}"] > div'
              f'{{background-image:url({url_da_imagem(pid)})}}'
              for n, pid in enumerate(ids_ordenados, start=1)]
    return "<style>" + "\n".join(regras) + "</style>"


# CSS colocado uma vez no topo da página (st.markdown com unsafe_allow_html).
# Os cards são st.container(key="card_N"): o Streamlit dá a classe "st-key-card_N".
# Cores: fundo cinza escuro (tema) e detalhes em #3a0445.
CSS = """
<style>
/* Barra de cima no estilo de site: logo à esquerda e abas em maiúsculas */
[data-testid="stHeader"] { background: #18181B; border-bottom: 1px solid #3a0445; }
[data-testid="stHeaderLogo"] { height: 2.3rem; max-width: none; margin-right: 2rem; }
/* Sem o título grande, o conteúdo pode começar mais perto da barra */
.block-container { padding-top: 4rem; }
[data-testid="stTopNavLink"] p {
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.04em;
}
[class*="st-key-card_"] {
    background: #26262B;
    border: 1px solid #3a0445;
    border-radius: 10px;
    padding: 10px 12px;
}
/* Borda em cada seletor do card (golpe, habilidade, item), para ver onde termina */
[class*="st-key-card_"] [data-testid="stSelectbox"] [role="group"] {
    border: 1px solid #5b1f70 !important;
    border-radius: 6px;
}
/* Cartões com borda (st.container(border=True)) no mesmo tom */
[data-testid="stVerticalBlockBorderWrapper"] { border-color: #3a0445 !important; }
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
.tipo.largo { display: block; border-radius: 6px; font-size: 0.85rem; padding: 3px 4px; }
/* Imagens em pixel art: aumentar sem borrar */
[data-testid="stImage"] img, img.foto { image-rendering: pixelated; }
img.foto { vertical-align: middle; }
.vazio { color: #8a7f8f; font-size: 0.85rem; text-align: center; padding: 30px 0; }

/* Fotinha ao lado do nome na lista de Pokémon (ver css_fotos_na_lista) */
[role="listbox"][aria-label="Pokémon"] [role="option"] > div {
    background-repeat: no-repeat;
    background-size: 32px 32px;
    background-position: left center;
    padding-left: 38px;
    image-rendering: pixelated;
}

/* Grade de tipos (cobertura e fraquezas) */
.grade {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 6px 8px;
    background: #26262B;
    border: 1px solid #3a0445;
    border-radius: 10px;
    padding: 12px;
}
@media (max-width: 700px) { .grade { grid-template-columns: repeat(3, 1fr); } }
.celula { position: relative; text-align: center; cursor: default; }
.numero { font-weight: 600; margin-top: 2px; }
.numero.verde { color: #4cd964; }
.numero.vermelho { color: #ff5c5c; }
.numero.neutro { color: #ECE6EF; }
.detalhe {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 100;
    min-width: 280px;
    text-align: left;
    background: #2A2A30;
    border: 1px solid #3a0445;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.85rem;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5);
}
.celula:hover .detalhe { display: block; }
/* As caixinhas das 2 últimas colunas abrem para a esquerda, para não sair da tela */
.celula:nth-child(6n) .detalhe, .celula:nth-child(6n-1) .detalhe { left: auto; right: 0; }
.detalhe table { border: none; margin: 6px 0 0 0; width: 100%; }
.detalhe td { border: none; padding: 2px 4px; }
.detalhe .tipo.pequena { width: auto; min-width: 56px; }
</style>
"""
