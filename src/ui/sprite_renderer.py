"""Nyx — ui/sprite_renderer.py (Fase 2: Gerador e Renderizador de Pixel Art)

Especificação visual (assets/README.md & seção 2 do prompt mestre):
- Estilo: pixel art kuudere cyberpunk
- Cabelo lavanda/berinjela escuro, franja pontiaguda
- Olhos verdes sonolentos/semicerrados (assinatura visual)
- Viseira metálica inclinada com detalhe amarelo-tech e cor funcional de segurança:
  * Verde (#10B981): modo assistido
  * Âmbar (#F59E0B): modo autônomo
  * Vermelho (#EF4444): erro
  * Dim/Cinza (#475569): sleep
- Jaleco branco/cinza com detalhes verde-musgo, camisa escura
- 7 estados emocionais: idle, talk, think, surprised, listening, error, sleep
- Grid base 36x36 renderizado em 144x144 ou 180x180 via nearest-neighbor.
"""

from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap

# Dimensões do sprite
GRID_W = 36
GRID_H = 36
DEFAULT_SCALE = 5  # 36 * 5 = 180px

# Paleta Cyberpunk
C_TRANSPARENT = QColor(0, 0, 0, 0)
C_SKIN = QColor("#F3E8E2")
C_SKIN_SHADOW = QColor("#E2D0C8")
C_BLUSH = QColor("#F4B4AC")
C_HAIR_DARK = QColor("#2D1B36")
C_HAIR_MID = QColor("#4A2E5B")
C_HAIR_LIGHT = QColor("#6B4882")
C_COAT = QColor("#E2E8F0")
C_COAT_SHADOW = QColor("#94A3B8")
C_COAT_MOSS = QColor("#4D7C0F")
C_SHIRT = QColor("#1E1B2E")
C_TECH_YELLOW = QColor("#FACC15")
C_EYE_GREEN = QColor("#10B981")
C_EYE_DARK = QColor("#064E3B")
C_PUPIL_WHITE = QColor("#FFFFFF")
C_OUTLINE = QColor("#1A1423")


class SpriteRenderer:
    """Gera pixmaps pixel art de alta fidelidade para Nyx."""

    def __init__(self, scale: int = DEFAULT_SCALE) -> None:
        self.scale = scale
        self._cache: dict[tuple[str, str], QPixmap] = {}

    def get_pixmap(self, emotion: str = "idle", mode: str = "assistida", frame: int = 0) -> QPixmap:
        """Obtém ou gera o QPixmap para a emoção, modo e frame atual."""
        key = (emotion, mode, frame % 2)
        if key in self._cache:
            return self._cache[key]

        img = self._generate_image(emotion, mode, frame)
        pix = QPixmap.fromImage(img)
        scaled_pix = pix.scaled(
            GRID_W * self.scale,
            GRID_H * self.scale,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,  # Nearest-neighbor perfeito
        )
        self._cache[key] = scaled_pix
        return scaled_pix

    render = get_pixmap

    def _get_visor_color(self, mode: str, emotion: str) -> QColor:
        if emotion == "error":
            return QColor("#EF4444")
        if emotion == "sleep":
            return QColor("#64748B")
        if mode == "autonoma":
            return QColor("#F59E0B")
        return QColor("#10B981")  # Verde assistida

    def _generate_image(self, emotion: str, mode: str, frame: int) -> QImage:
        img = QImage(GRID_W, GRID_H, QImage.Format.Format_ARGB32)
        img.fill(C_TRANSPARENT)
        p = QPainter(img)

        # 1. Jaleco e ombros (Linhas 24-35)
        self._draw_body(p, emotion, frame)

        # 2. Cabeça / Pele (Linhas 10-24)
        self._draw_head(p, emotion)

        # 3. Olhos (Linhas 16-19)
        self._draw_eyes(p, emotion, frame)

        # 4. Boca / Expressão
        self._draw_mouth(p, emotion, frame)

        # 5. Cabelo (Linhas 4-22)
        self._draw_hair(p, emotion)

        # 6. Viseira Metálica Cyberpunk (Linhas 12-16)
        visor_color = self._get_visor_color(mode, emotion)
        self._draw_visor(p, visor_color, emotion, frame)

        # 7. Efeitos específicos de estado
        if emotion == "sleep":
            self._draw_zzz(p, frame)
        elif emotion == "listening":
            self._draw_listening_waves(p, frame)
        elif emotion == "think":
            self._draw_think_sparkles(p, frame)

        p.end()
        return img

    def _draw_body(self, p: QPainter, emotion: str, frame: int) -> None:
        shift_y = 1 if (emotion == "sleep" or (emotion == "idle" and frame % 2 == 1)) else 0
        # Camisa escura central
        p.fillRect(QRect(15, 24 + shift_y, 6, 12), C_SHIRT)
        # Jaleco branco
        p.fillRect(QRect(7, 25 + shift_y, 8, 11), C_COAT)
        p.fillRect(QRect(21, 25 + shift_y, 8, 11), C_COAT)
        # Sombras e gola do jaleco
        p.fillRect(QRect(7, 26 + shift_y, 2, 10), C_COAT_SHADOW)
        p.fillRect(QRect(27, 26 + shift_y, 2, 10), C_COAT_SHADOW)
        # Manchas verde-musgo cyberpunk no ombro esquerdo
        p.fillRect(QRect(9, 27 + shift_y, 3, 2), C_COAT_MOSS)
        p.fillRect(QRect(10, 29 + shift_y, 2, 2), C_COAT_MOSS)
        # Contornos do corpo
        p.fillRect(QRect(6, 25 + shift_y, 1, 11), C_OUTLINE)
        p.fillRect(QRect(29, 25 + shift_y, 1, 11), C_OUTLINE)

    def _draw_head(self, p: QPainter, emotion: str) -> None:
        # Base do rosto
        p.fillRect(QRect(11, 11, 14, 13), C_SKIN)
        # Queixo cônico
        p.fillRect(QRect(13, 24, 10, 1), C_SKIN)
        p.fillRect(QRect(15, 25, 6, 1), C_SKIN)
        # Sombras da bochecha/pescoço
        p.fillRect(QRect(11, 22, 2, 2), C_SKIN_SHADOW)
        p.fillRect(QRect(23, 22, 2, 2), C_SKIN_SHADOW)
        p.fillRect(QRect(15, 24, 6, 2), C_SKIN_SHADOW)
        # Blush dithered
        p.fillRect(QRect(12, 20, 2, 1), C_BLUSH)
        p.fillRect(QRect(22, 20, 2, 1), C_BLUSH)

    def _draw_hair(self, p: QPainter, emotion: str) -> None:
        # Cabelo topo e laterais
        p.fillRect(QRect(10, 5, 16, 6), C_HAIR_MID)
        p.fillRect(QRect(8, 8, 3, 15), C_HAIR_DARK)
        p.fillRect(QRect(25, 8, 3, 15), C_HAIR_DARK)
        # Mechas pontiagudas laterais
        p.fillRect(QRect(7, 12, 2, 8), C_HAIR_MID)
        p.fillRect(QRect(27, 12, 2, 8), C_HAIR_MID)
        # Franja pontiaguda frontal
        p.fillRect(QRect(12, 9, 3, 5), C_HAIR_MID)
        p.fillRect(QRect(15, 10, 3, 5), C_HAIR_DARK)
        p.fillRect(QRect(18, 9, 4, 6), C_HAIR_LIGHT)
        p.fillRect(QRect(22, 10, 3, 4), C_HAIR_MID)
        # Destaque de luz no topo do cabelo
        p.fillRect(QRect(14, 6, 7, 1), C_HAIR_LIGHT)

    def _draw_eyes(self, p: QPainter, emotion: str, frame: int) -> None:
        if emotion == "sleep":
            # Olhos fechados em linha calma (- -)
            p.fillRect(QRect(13, 18, 3, 1), C_HAIR_DARK)
            p.fillRect(QRect(20, 18, 3, 1), C_HAIR_DARK)
        elif emotion == "surprised":
            # Olhos arregalados redondos
            p.fillRect(QRect(13, 16, 4, 4), C_EYE_GREEN)
            p.fillRect(QRect(19, 16, 4, 4), C_EYE_GREEN)
            p.fillRect(QRect(14, 17, 2, 2), C_EYE_DARK)
            p.fillRect(QRect(20, 17, 2, 2), C_EYE_DARK)
            p.fillRect(QRect(15, 16, 1, 1), C_PUPIL_WHITE)
            p.fillRect(QRect(21, 16, 1, 1), C_PUPIL_WHITE)
        elif emotion == "error":
            # Olhos semicerrados irritados / franzidos
            p.fillRect(QRect(13, 17, 4, 2), C_HAIR_DARK)
            p.fillRect(QRect(19, 17, 4, 2), C_HAIR_DARK)
            p.fillRect(QRect(14, 18, 2, 1), C_EYE_GREEN)
            p.fillRect(QRect(20, 18, 2, 1), C_EYE_GREEN)
        else:
            # Olhos assinatura: verdes sonolentos / semicerrados
            p.fillRect(QRect(13, 17, 4, 2), C_EYE_GREEN)
            p.fillRect(QRect(19, 17, 4, 2), C_EYE_GREEN)
            # Pálpebra superior cobrindo metade
            p.fillRect(QRect(13, 16, 4, 1), C_HAIR_DARK)
            p.fillRect(QRect(19, 16, 4, 1), C_HAIR_DARK)
            # Pupila e brilho sutil
            p.fillRect(QRect(14, 17, 2, 2), C_EYE_DARK)
            p.fillRect(QRect(20, 17, 2, 2), C_EYE_DARK)
            p.fillRect(QRect(15, 17, 1, 1), C_PUPIL_WHITE)
            p.fillRect(QRect(21, 17, 1, 1), C_PUPIL_WHITE)

    def _draw_mouth(self, p: QPainter, emotion: str, frame: int) -> None:
        if emotion == "talk" and frame % 2 == 1:
            # Boca aberta falando
            p.fillRect(QRect(17, 22, 2, 2), QColor("#A855F7"))
        elif emotion == "surprised":
            # Boca pequena redonda 'o'
            p.fillRect(QRect(17, 21, 2, 2), C_HAIR_DARK)
        elif emotion == "error":
            # Boca reta levemente contrariada
            p.fillRect(QRect(16, 22, 4, 1), C_HAIR_DARK)
        else:
            # Boca neutra kuudere discreta
            p.fillRect(QRect(17, 22, 2, 1), C_SKIN_SHADOW)

    def _draw_visor(self, p: QPainter, visor_color: QColor, emotion: str, frame: int) -> None:
        # Viseira metálica inclinada na testa/têmpora direita
        # Base metálica escura
        p.fillRect(QRect(19, 12, 7, 3), C_OUTLINE)
        # Núcleo iluminado da viseira com cor funcional de modo
        # Se erro, pisca com frame
        if emotion == "error" and frame % 2 == 1:
            glow = QColor("#FCA5A5")
        else:
            glow = visor_color
        p.fillRect(QRect(20, 13, 5, 1), glow)
        # Detalhe amarelo tech característico
        p.fillRect(QRect(25, 13, 1, 2), C_TECH_YELLOW)

    def _draw_zzz(self, p: QPainter, frame: int) -> None:
        offset = frame % 2
        p.fillRect(QRect(26, 6 - offset, 3, 1), QColor("#94A3B8"))
        p.fillRect(QRect(28, 7 - offset, 1, 1), QColor("#94A3B8"))
        p.fillRect(QRect(26, 8 - offset, 3, 1), QColor("#94A3B8"))

    def _draw_listening_waves(self, p: QPainter, frame: int) -> None:
        color = QColor("#38BDF8")
        h = 2 + (frame % 2) * 2
        p.fillRect(QRect(5, 15, 1, h), color)
        p.fillRect(QRect(3, 14, 1, h + 2), color)

    def _draw_think_sparkles(self, p: QPainter, frame: int) -> None:
        color = QColor("#FDE047") if frame % 2 == 0 else QColor("#A78BFA")
        p.fillRect(QRect(27, 4, 1, 3), color)
        p.fillRect(QRect(26, 5, 3, 1), color)

    def save_all_sprites(self, output_dir: Path | str) -> list[str]:
        """Gera e salva todos os 7 estados como arquivos PNG na pasta indicada."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        saved = []
        emotions = ["idle", "talk", "think", "surprised", "listening", "error", "sleep"]
        for emo in emotions:
            pix = self.get_pixmap(emotion=emo, mode="assistida", frame=0)
            target = out / f"nyx_{emo}.png"
            pix.save(str(target), "PNG")
            saved.append(str(target))
        return saved
