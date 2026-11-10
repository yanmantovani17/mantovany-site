# Site novo: do terreno à chave

- `index.html`: página. A abertura toca a sequência `ciclo/1600/001.webp … 096.webp` (computador) e `ciclo/960/` (celular) conforme a rolagem.
- `planta.js`: maquete 3D interativa do apartamento (three.js).
- `ciclo/img/*.webp`: imagens dos 5 serviços (projeto, gestao, obra, vistoria, laudo).
- `ferramentas/predio.py`: cena do Blender que gerou a animação provisória (`python predio.py <saida> all 100 10`).

## Para trocar pela animação realista (Higgsfield)
1. Gere os vídeos (terreno com projeto → estrutura → prédio pronto), 16:9.
2. Junte em um só vídeo e extraia 96 quadros igualmente espaçados:
   `ffmpeg -i video.mp4 -vf "fps=96/DURACAO,scale=1600:-2" -q:v 3 ciclo/1600/%03d.webp`
   e o mesmo com `scale=960:-2` para `ciclo/960/`.
3. Mantenha os nomes 001.webp … 096.webp. Se mudar a quantidade, ajuste `TOTAL` no `index.html`.
4. A linha do tempo e os textos mudam nos pontos 0,13 (projeto), 0,30 (estrutura), 0,68 (fechamento) e 0,90 (entrega) da rolagem.
