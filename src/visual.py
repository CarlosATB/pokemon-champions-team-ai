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


def icone(nome: str, classe: str = "") -> str:
    """Ícone da biblioteca Material Symbols (a mesma que o Streamlit usa) para o HTML.
    Nos textos do Streamlit usa-se ":material/nome:"; dentro de HTML, este span."""
    return f'<span class="icone {classe}">{nome}</span>'


# CSS colocado uma vez no topo da página (st.markdown com unsafe_allow_html).
# Os cards são st.container(key="card_N") ou key="vidro_..." (classe "st-key-...").
# Visual: azul-escuro com painéis de "vidro" (fundo translúcido + desfoque).
CSS = """
<style>
:root {
    --vidro: rgba(20, 32, 58, 0.55);
    --vidro-forte: rgba(14, 22, 42, 0.82);
    --borda: rgba(120, 160, 255, 0.14);
    --borda-forte: rgba(120, 160, 255, 0.28);
    --destaque: #5B9BFF;
    --destaque-2: #7C6CFF;
    --texto-apagado: #8A9BB8;
    --verde: #34D399;
    --vermelho: #F87171;
    --amarelo: #FBBF24;
}

/* Fundo azul-escuro com brilhos suaves (fica parado ao rolar) */
.stApp {
    background:
        radial-gradient(1100px 600px at 8% -10%, rgba(59, 130, 246, 0.22), transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(124, 108, 255, 0.16), transparent 60%),
        radial-gradient(900px 700px at 50% 110%, rgba(14, 165, 233, 0.10), transparent 60%),
        linear-gradient(180deg, #070C18 0%, #0A1224 100%);
    background-attachment: fixed;
}

/* Barra de cima: vidro, logo à esquerda, abas em "pílula" */
[data-testid="stHeader"] {
    background: rgba(7, 12, 24, 0.62);
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
    border-bottom: 1px solid var(--borda);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    height: 4rem;
}
[data-testid="stHeader"]::after {
    content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--destaque), var(--destaque-2), transparent);
    opacity: 0.55;
}
[data-testid="stToolbar"] { height: 4rem; padding: 0 1.5rem; }
[data-testid="stHeaderLogo"] { height: 2.4rem; max-width: none; margin-right: 1.75rem; }
[data-testid="stTopNav"] { gap: 4px; }
[data-testid="stTopNavLink"], [data-testid="stTopNavSection"] {
    border-radius: 999px;
    padding: 6px 16px !important;
    transition: background 0.2s, color 0.2s;
}
[data-testid="stTopNavLink"] p, [data-testid="stTopNavSection"] p {
    font-weight: 600;
    font-size: 0.92rem;
    letter-spacing: 0.01em;
    color: #B9C6DE;
}
[data-testid="stTopNavLink"]:hover { background: rgba(91, 155, 255, 0.10); }
[data-testid="stTopNavLink"]:hover p { color: #FFFFFF; }
[data-testid="stTopNavLink"][aria-current="page"] {
    background: linear-gradient(135deg, rgba(91, 155, 255, 0.22), rgba(124, 108, 255, 0.22));
    box-shadow: inset 0 0 0 1px var(--borda-forte);
}
[data-testid="stTopNavLink"][aria-current="page"] p { color: #FFFFFF; }
.block-container { padding-top: 5.5rem; }

h1, h2, h3, h4 { letter-spacing: -0.01em; }
h2 { font-weight: 700 !important; }

/* Painéis de vidro: cards do time e containers com key "vidro_..." */
[class*="st-key-card_"], [class*="st-key-vidro"],
.veredito, .categoria, .ameaca, .grade {
    background: var(--vidro) !important;
    border: 1px solid var(--borda) !important;
    border-radius: 14px;
    backdrop-filter: blur(14px) saturate(140%);
    -webkit-backdrop-filter: blur(14px) saturate(140%);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
[class*="st-key-card_"] { padding: 10px 12px; }
[class*="st-key-vidro"] { padding: 14px 16px; }
[class*="st-key-card_"] [data-testid="stSelectbox"] [role="group"] {
    border: 1px solid var(--borda-forte) !important;
    border-radius: 8px;
}

/* Botões: principal em degradê azul, secundário em vidro */
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #3B82F6, #6366F1) !important;
    border: none !important;
    box-shadow: 0 6px 18px rgba(59, 130, 246, 0.35);
    transition: transform 0.15s, box-shadow 0.15s;
}
[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(59, 130, 246, 0.45);
}
[data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"] {
    background: rgba(20, 32, 58, 0.6) !important;
    border: 1px solid var(--borda-forte) !important;
}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stPopoverButton"]:hover {
    border-color: var(--destaque) !important;
    color: #FFFFFF !important;
}

/* Seletor das visões (Análise da IA / Melhorar o time / Detalhes) */
[data-testid="stButtonGroup"] > div {
    background: var(--vidro-forte);
    border: 1px solid var(--borda);
    border-radius: 999px;
    padding: 4px;
    display: inline-flex;
}
[data-testid="stButtonGroup"] button {
    padding: 8px 22px;
    font-size: 0.98rem;
    border: none !important;
    border-radius: 999px !important;
    background: transparent;
}
[data-testid="stButtonGroup"] button[kind*="Active"] {
    background: linear-gradient(135deg, #3B82F6, #6366F1) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
}

/* Abas */
[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--borda); }
[data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--destaque), var(--destaque-2)); }
[data-testid="stExpander"] details {
    background: var(--vidro);
    border: 1px solid var(--borda) !important;
    border-radius: 12px;
}
[data-testid="stAlertContainer"] { border-radius: 12px; backdrop-filter: blur(10px); }

/* Ícones Material Symbols dentro do HTML (ver icone()) */
.icone {
    font-family: "Material Symbols Rounded";
    font-weight: normal;
    font-style: normal;
    font-size: 1.2em;
    line-height: 1;
    vertical-align: -0.22em;
    letter-spacing: normal;
    text-transform: none;
    white-space: nowrap;
    font-feature-settings: "liga";
    -webkit-font-smoothing: antialiased;
    user-select: none;
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
.tipo.largo { display: block; border-radius: 6px; font-size: 0.85rem; padding: 3px 4px; }
/* Imagens em pixel art: aumentar sem borrar */
[data-testid="stImage"] img, img.foto { image-rendering: pixelated; }
img.foto { vertical-align: middle; }
.vazio { color: var(--texto-apagado); font-size: 0.85rem; text-align: center; padding: 30px 0; }

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
    padding: 12px;
}
@media (max-width: 700px) { .grade { grid-template-columns: repeat(3, 1fr); } }
.celula { position: relative; text-align: center; cursor: default; }
.numero { font-weight: 600; margin-top: 2px; }
.numero.verde { color: var(--verde); }
.numero.vermelho { color: var(--vermelho); }
.numero.neutro { color: #E5ECF8; }
.detalhe {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 100;
    min-width: 280px;
    text-align: left;
    background: #0F1A30;
    border: 1px solid var(--borda-forte);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.85rem;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55);
}
.celula:hover .detalhe { display: block; }
/* As caixinhas das 2 últimas colunas abrem para a esquerda, para não sair da tela */
.celula:nth-child(6n) .detalhe, .celula:nth-child(6n-1) .detalhe { left: auto; right: 0; }
.detalhe table { border: none; margin: 6px 0 0 0; width: 100%; }
.detalhe td { border: none; padding: 2px 4px; }
.detalhe .tipo.pequena { width: auto; min-width: 56px; }

/* Veredito da IA: nota num anel colorido */
.veredito {
    display: flex;
    align-items: center;
    gap: 26px;
    padding: 20px 24px;
    margin-bottom: 16px;
    line-height: 1.7;
}
.anel {
    flex: none;
    width: 116px;
    height: 116px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: conic-gradient(var(--cor) var(--pct), rgba(255, 255, 255, 0.08) 0);
    box-shadow: 0 0 32px color-mix(in srgb, var(--cor) 35%, transparent);
}
.anel > div {
    width: 92px;
    height: 92px;
    border-radius: 50%;
    background: #0D1628;
    display: grid;
    place-content: center;
    text-align: center;
    line-height: 1.1;
}
.anel b { font-size: 1.9rem; }
.anel small { color: var(--texto-apagado); }
.veredito .rotulo {
    color: var(--destaque); font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
}
.veredito .titulo { font-size: 1.55rem; font-weight: 800; }
.apagado { color: var(--texto-apagado); font-size: 0.85rem; }

/* Cards das categorias e das ameaças do meta */
.categorias, .ameacas {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 14px;
    margin-bottom: 16px;
}
.ameacas { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.categoria, .ameaca { padding: 14px 16px; }
.categoria .cabecalho, .ameaca .cabecalho { display: flex; align-items: center; gap: 8px; font-size: 1.05rem; }
.categoria .cabecalho .icone { color: var(--destaque); }
.categoria .ordem {
    width: 24px; height: 24px; border-radius: 50%; flex: none;
    background: linear-gradient(135deg, #3B82F6, #6366F1);
    display: grid; place-items: center; font-size: 0.78rem; font-weight: 700;
}
.categoria .nota { margin-left: auto; font-size: 1.45rem; font-weight: 800; }
.categoria .selo, .ameaca .selo {
    font-size: 0.7rem; padding: 1px 9px; border-radius: 10px;
    background: rgba(255, 255, 255, 0.07); color: #B9C6DE;
}
.ameaca .selo { margin-left: auto; }
.ameaca img.foto { background: rgba(255, 255, 255, 0.04); border-radius: 12px; }
.barra { height: 8px; border-radius: 4px; background: rgba(255, 255, 255, 0.08); margin: 8px 0 6px 0; overflow: hidden; }
.barra > div { height: 100%; border-radius: 4px; }
.motivos { list-style: none; padding: 0; margin: 8px 0 0 0; font-size: 0.88rem; }
.motivos li { margin: 5px 0; padding-left: 22px; text-indent: -22px; }
.motivos li > .icone:first-child { display: inline-block; width: 22px; text-indent: 0; }
.motivos li.verde > .icone:first-child { color: var(--verde); }
.motivos li.vermelho > .icone:first-child { color: var(--vermelho); }
.motivos li.neutro > .icone:first-child { color: var(--texto-apagado); }
</style>
"""
