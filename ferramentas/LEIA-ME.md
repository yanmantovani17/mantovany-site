# Site novo: do terreno à chave

- `index.html`: página. A abertura toca a sequência `ciclo/1600/001.webp … 096.webp` (computador) e `ciclo/960/` (celular) conforme a rolagem.
- `planta.js`: maquete 3D interativa do apartamento (three.js).
- `ciclo/img/*.webp`: imagens dos 5 serviços (projeto, gestao, obra, vistoria, laudo), tiradas da própria animação.
- `ferramentas/predio.py`: cena do Blender que gerou a primeira animação provisória (`python predio.py <saida> all 100 10`).

## Animação atual (imagens do Higgsfield animadas localmente)
Três imagens-chave geradas no Higgsfield (Nano Banana Pro, 16:9, mesmo prédio, terreno e ângulo):
prédio pronto ao entardecer → edição em obra (estrutura, grua, canteiro) → edição do terreno com o contorno em linhas douradas.
Os vídeos de quadro inicial/final (Kling/Seedance) não foram usados por falta de créditos; a transição é feita por código:

1. `python ferramentas/camadas.py <pasta>` — a pasta precisa ter `pronto.png`, `obra.png`, `linhas.png`.
   Alinha obra e linhas ao prédio pronto e cria `A_*.png` (inclui o terreno sem linhas e o prédio com as luzes apagadas)
   e `M_luzes.png`. Versões já prontas estão em `ferramentas/quadros-chave/` (webp; converta para `A_<nome>.png` se for reusar).
2. `python ferramentas/ciclo.py <pasta> <saida> video` — gera `saida/1600`, `saida/960` (001…096.webp),
   `saida/etapas/*.webp` (para `ciclo/img/`) e `saida/previa.mp4` (16 s, 24 fps).

Linha do tempo (igual aos marcos da rolagem no `index.html`):
0,00 terreno (linhas acendem de baixo para cima) · 0,13 projeto (holograma completo) ·
0,30 estrutura (concreto sobe andar por andar, quadros 30–66, contador de andares) ·
0,68 fechamento (fachada fecha, grua e canteiro somem) · 0,90 entrega (luzes acendem janela por janela).

## Para trocar por vídeos de verdade (Higgsfield, quando houver créditos)
1. Gere os vídeos 3→2 e 2→1 com quadro inicial e final (Kling 3.0: ~14 créditos cada em 8 s, modo pro, sem som).
2. Junte em um só vídeo e extraia 96 quadros igualmente espaçados:
   `ffmpeg -i video.mp4 -vf "fps=96/DURACAO,scale=1600:-2" -q:v 3 ciclo/1600/%03d.webp`
   e o mesmo com `scale=960:-2` para `ciclo/960/`.
3. Mantenha os nomes 001.webp … 096.webp. Se mudar a quantidade, ajuste `TOTAL` no `index.html`
   (e a faixa do contador de andares, `quadro - 30` / `quadro <= 66`).
