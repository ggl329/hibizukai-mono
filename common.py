import math
from pathlib import Path
import uuid

import fontforge
import psMat


# STYLE_TABLE[(for_bold, for_italic)]
STYLE_TABLE = {
    (False, False): 'Regular',
    (False, True): 'Italic',
    (True, False): 'Bold',
    (True, True): 'Bold Italic',
}


def italicize(font: fontforge.font, angle: float) -> None:
    font.italicangle = -angle
    angle_rad = math.pi * angle / 180
    trans_mat = psMat.compose(
        psMat.skew(angle_rad),
        psMat.translate(-math.tan(angle_rad) * (font.ascent - font.descent) / 2, 0)
    )
    select_worth_outputting(font)
    font.transform(trans_mat, ('noWidth',))


def merge_fonts(font1: fontforge.font, font2: fontforge.font) -> None:
    tmp_filename = make_temp_filename(suffix='.sfd', dir='.')
    font2.save(tmp_filename)
    font1.mergeFonts(tmp_filename)
    Path(tmp_filename).unlink()


def make_temp_filename(suffix: str = '', prefix: str = 'tmp_', dir: Path = Path('/tmp'), retries: int = 10) -> str:
    dir = Path(dir)
    for _ in range(retries):
        filename = f'{prefix}{uuid.uuid4().hex}{suffix}'
        path = dir / filename
        if not path.exists():
            return path.name
    raise FileExistsError(f'Could not generate a unique filename in {dir} after {retries} attempts.')


def remove_lookups(font, remove_gsub=True, remove_gpos=True):
    if remove_gsub:
        for lookup in font.gsub_lookups:
            font.removeLookup(lookup)
    if remove_gpos:
        for lookup in font.gpos_lookups:
            font.removeLookup(lookup)


def scale_em(font: fontforge.font, ascent: int, descent: int) -> None:
    if font.em != ascent + descent:
        font.em = ascent + descent
    font.ascent = ascent
    font.descent = descent


def select_worth_outputting(font: fontforge.font) -> None:
    font.selection.none()
    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            font.selection.select(('more',), glyph)
