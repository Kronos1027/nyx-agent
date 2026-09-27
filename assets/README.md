# assets/ — sprites do Nyx (Fase 2)

Este diretório receberá os sprites em pixel art do Nyx, **gerados por script**
(`tools/sprite_gen.py`, Fase 2) e versionados como saída, conforme o prompt mestre
(seção 3.2).

## Especificação visual (seção 2 do prompt mestre)

- Estilo: pixel art kuudere cyberpunk
- Cabelo lavanda/berinjela escuro, franja pontiaguda
- Olhos verdes sonolentos/semicerrados (assinatura visual)
- Viseira metálica inclinada com detalhe amarelo-tech
- Jaleco branco/cinza com manchas verde-musgo, camisa escura por baixo
- Blush dithered nas bochechas
- Escala base 32–48px, renderizada em 160–180px (nearest-neighbor, sem anti-aliasing)

## Codificação funcional de cor (segurança visível)

| Cor da viseira/olhos | Significado |
|---|---|
| Verde | modo assistido (padrão) |
| Âmbar/laranja | modo autônomo ativo |
| Vermelho piscando | erro / ação falhou |
| Olhos fechados, postura baixa | mic desligado / modo sono |

## Estados obrigatórios (7)

`idle`, `talk`, `think`, `surprised`, `listening`, `error`, `sleep`

**Status atual: NÃO IMPLEMENTADO (Fase 2).** Nenhum sprite existe ainda —
nada foi gerado, nada aqui é definitivo.
