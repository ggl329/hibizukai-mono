#! /usr/bin/python3

import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import fontforge
import psMat

from fontTools import ttx, ttLib

import common


# settings

JA_FONT_BASENAME = 'original/BIZUDGothic/BIZUDGothic'
JA_CUSTOM_BASENAME = 'original/custom/custom_p_sound'
EN_FONT_BASENAME = 'original/JetBrainsMono/JetBrainsMonoNL'
NERD_FILENAME = 'original/Nerd/SymbolsNerdFontMono-Regular.ttf'

BUILD_DIR = 'HibizukaiMono'
RELEASE_FAMILYNAME = 'HibizukaiMono'
COPYRIGHT = (
    'Copyright 2022 The BIZ UDGothic Project Authors (https://github.com/googlefonts/morisawa-biz-ud-gothic)\n'
    'Copyright 2020 The JetBrains Mono NL Project Authors (https://github.com/JetBrains/JetBrainsMono)\n'
    'Copyright (c) 2016, Ryan McIntyre (https://github.com/ryanoasis/nerd-fonts)\n'
    'Copyright 2022 Yuko Otawara (https://github.com/yuru7/bizin-gothic)\n'
    'Copyright 2025 ggl329 (https://github.com/ggl329/hibizukai-mono)\n'
)
TRADEMARK = 'BIZ UDGothic is a trademark of Morisawa Inc., JetBrains Mono is a trademark of JetBrains s.r.o.'
MANUFACTURER = 'Morisawa Inc., JetBrains, Ryan McIntyre'
DESIGNER = 'TypeBank Co., Ltd., Philipp Nurullin, Konstantin Bulenkov, Ryan McIntyre, Yuko Otawara'
LICENSE = (
    'This Font Software is licensed under the SIL Open Font License, Version 1.1. '
    'This license is available with a FAQ at: https://scripts.sil.org/OFL'
)
LICENSE_URL = 'https://scripts.sil.org/OFL'

EM_ASCENT  = 1782    # BIZ UDPGothic = 1802, JetBrains Mono = 800, Nerd Fonts = 1638
EM_DESCENT =  266    # BIZ UDPGothic =  246, JetBrains Mono = 200, Nerd Fonts =  410
FONT_ASCENT  = EM_ASCENT  + 170    # BIZ UDPGothic = 1802, JetBrains Mono = 1020, Nerd Fonts = 1638
FONT_DESCENT = EM_DESCENT + 160    # BIZ UDPGothic =  246, JetBrains Mono =  300, Nerd Fonts =  410
FONT_WIDTH = 2000

NERD_Y_OFFSET = 164

ITALIC_ANGLE = 9
ITALIC_ANGLE_MOD = 1.7


def main() -> None:
    args = parse_arguments()

    if not Path(BUILD_DIR).exists():
        Path(BUILD_DIR).mkdir()

    generate_font(for_bold=(args.style == 'bold' or args.style == 'bold-italic'),
                  for_italic=(args.style == 'italic' or args.style == 'bold-italic'),
                  version=args.version)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f'generates a font "{RELEASE_FAMILYNAME}"')
    parser.add_argument('style', choices=['regular', 'bold', 'italic', 'bold-italic'], help='font style to generate')
    parser.add_argument('version', help='version string')
    return parser.parse_args()


def generate_font(for_bold: bool, for_italic: bool, version: str) -> None:
    ja_font = open_ja_orig_font(for_bold)
    en_font = open_en_orig_font(for_bold, for_italic)

    common.scale_em(en_font, EM_ASCENT, EM_DESCENT)
    common.scale_em(ja_font, EM_ASCENT, EM_DESCENT)

    enable_slash_zero(en_font)
    clear_curly_bracket(en_font)
    copy_medium_glyphs(en_font)
    clear_jpdoc_symbols(en_font)
    clear_duplicate_circled_letter(en_font, ja_font)
    clear_duplicate_glyphs(ja_font, en_font)
    normalize_width(en_font, en_font[0x30].width, FONT_WIDTH / 2)
    normalize_width(ja_font, (EM_ASCENT + EM_DESCENT) / 2, FONT_WIDTH / 2, x_only=False)

    if for_italic:
        common.italicize(ja_font, ITALIC_ANGLE)
        common.italicize(en_font, ITALIC_ANGLE_MOD)

    common.merge_fonts(ja_font, en_font)

    add_nerd_font_glyphs(ja_font)

    edit_meta_data(ja_font, for_bold, for_italic, version)

    tmp_filename = common.make_temp_filename(suffix='.ttf', dir='.')
    ja_font.generate(tmp_filename, flags=('no-hints',))

    en_font.close()
    ja_font.close()

    autohint(tmp_filename)
    delete_vhea_vmtx(tmp_filename)
    fix_font_tables(tmp_filename, for_bold, for_italic)


def open_ja_orig_font(for_bold: bool) -> fontforge.font:
    font = fontforge.open(f'{JA_FONT_BASENAME}-{common.STYLE_TABLE[(for_bold, False)]}.ttf')
    common.select_worth_outputting(font)
    font.unlinkReferences()

    # 日本語フォントにカスタムグリフを適用する
    # ぱぴぷぺぽ パピプペポ の半濁点を拡大
    for uni in [0x3071, 0x3074, 0x3077, 0x307A, 0x307D, 0x30D1, 0x30D4, 0x30D7, 0x30DA, 0x30DD]:
        glyph = font[uni]
        glyph.clear()
    font.mergeFonts(f'{JA_CUSTOM_BASENAME}-{common.STYLE_TABLE[(for_bold, False)]}.sfd')

    return font


def open_en_orig_font(for_bold: bool, for_italic: bool) -> fontforge.font:
    font = fontforge.open(f'{EN_FONT_BASENAME}-{common.STYLE_TABLE[(for_bold, for_italic)].replace(" ", "")}.ttf')
    common.select_worth_outputting(font)
    font.unlinkReferences()
    return font


def enable_slash_zero(en_font: fontforge.font) -> None:
    en_font.selection.select('zero.zero')
    en_font.copy()
    en_font.selection.select('zero')
    en_font.clear()
    en_font.paste()


def clear_curly_bracket(en_font: fontforge.font) -> None:
    en_font.selection.select(0xFF5B)
    en_font.clear()
    en_font.selection.select(0xFF5D)
    en_font.clear()


def copy_medium_glyphs(en_font: fontforge.font) -> None:
    # ■□を BLACK/WHITE MEDIUM SQUARE にコピー
    en_font.selection.select('U+25A0')
    en_font.copy()
    en_font.selection.select('U+25FC')
    en_font.clear()
    en_font.paste()
    en_font.selection.select('U+25A1')
    en_font.copy()
    en_font.selection.select('U+25FB')
    en_font.clear()
    en_font.paste()
    # ●○を MEDIUM BLACK/WHITE CIRCLE にコピー
    en_font.selection.select('U+25CF')
    en_font.copy()
    en_font.selection.select('U+26AB')
    en_font.clear()
    en_font.paste()
    en_font.selection.select('U+25CB')
    en_font.copy()
    en_font.selection.select('U+26AA')
    en_font.clear()
    en_font.paste()


def clear_jpdoc_symbols(font: fontforge.font) -> None:
    font.selection.none()
    # § (U+00A7)
    font.selection.select(("more", "unicode"), 0x00A7)
    # ± (U+00B1)
    font.selection.select(("more", "unicode"), 0x00B1)
    # ¶ (U+00B6)
    font.selection.select(("more", "unicode"), 0x00B6)
    # ÷ (U+00F7)
    font.selection.select(("more", "unicode"), 0x00F7)
    # × (U+00D7)
    font.selection.select(("more", "unicode"), 0x00D7)
    # ⇒ (U+21D2)
    font.selection.select(("more", "unicode"), 0x21D2)
    # ⇔ (U+21D4)
    font.selection.select(("more", "unicode"), 0x21D4)
    # ■-□ (U+25A0-U+25A1)
    font.selection.select(("more", "ranges"), 0x25A0, 0x25A1)
    # ▲-△ (U+25B2-U+25B3)
    font.selection.select(("more", "ranges"), 0x25A0, 0x25B3)
    # ▼-▽ (U+25BC-U+25BD)
    font.selection.select(("more", "ranges"), 0x25BC, 0x25BD)
    # ◆-◇ (U+25C6-U+25C7)
    font.selection.select(("more", "ranges"), 0x25C6, 0x25C7)
    # ○ (U+25CB)
    font.selection.select(("more", "unicode"), 0x25CB)
    # ◎-● (U+25CE-U+25CF)
    font.selection.select(("more", "ranges"), 0x25CE, 0x25CF)
    # ◥ (U+25E5)
    font.selection.select(("more", "unicode"), 0x25E5)
    # ◯ (U+25EF)
    font.selection.select(("more", "unicode"), 0x25EF)
    # √ (U+221A)
    font.selection.select(("more", "unicode"), 0x221A)
    # ∞ (U+221E)
    font.selection.select(("more", "unicode"), 0x221E)
    # ‐ (U+2010)
    font.selection.select(("more", "unicode"), 0x2010)
    # ‘-‚ (U+2018-U+201A)
    # font.selection.select(("more", "ranges"), 0x2018, 0x201A)
    # “-„ (U+201C-U+201E)
    # font.selection.select(("more", "ranges"), 0x201C, 0x201E)
    # †-‡ (U+2020-U+2021)
    font.selection.select(("more", "ranges"), 0x2020, 0x2021)
    # … (U+2026)
    font.selection.select(("more", "unicode"), 0x2026)
    # ‰ (U+2030)
    font.selection.select(("more", "unicode"), 0x2030)
    # ←-↓ (U+2190-U+2193)
    font.selection.select(("more", "ranges"), 0x2190, 0x2193)
    # ∀ (U+2200)
    font.selection.select(("more", "unicode"), 0x2200)
    # ∂-∃ (U+2202-U+2203)
    font.selection.select(("more", "ranges"), 0x2202, 0x2203)
    # ∈ (U+2208)
    font.selection.select(("more", "unicode"), 0x2208)
    # ∋ (U+220B)
    font.selection.select(("more", "unicode"), 0x220B)
    # ∑ (U+2211)
    font.selection.select(("more", "unicode"), 0x2211)
    # ∥ (U+2225)
    font.selection.select(("more", "unicode"), 0x2225)
    # ∧-∬ (U+2227-U+222C)
    font.selection.select(("more", "ranges"), 0x2227, 0x222C)
    # ∴-∵ (U+2234-U+2235)
    font.selection.select(("more", "ranges"), 0x2234, 0x2235)
    # ∽ (U+223D)
    font.selection.select(("more", "unicode"), 0x223D)
    # ≒ (U+2252)
    font.selection.select(("more", "unicode"), 0x2252)
    # ≠-≡ (U+2260-U+2261)
    font.selection.select(("more", "ranges"), 0x2260, 0x2261)
    # ≦-≧ (U+2266-U+2267)
    font.selection.select(("more", "ranges"), 0x2266, 0x2267)
    # ⊂-⊃ (U+2282-U+2283)
    font.selection.select(("more", "ranges"), 0x2282, 0x2283)
    # ⊆-⊇ (U+2286-U+2287)
    font.selection.select(("more", "ranges"), 0x2286, 0x2287)
    # ─-╿ (Box Drawing) (U+2500-U+257F)
    font.selection.select(("more", "ranges"), 0x2500, 0x257F)
    for glyph in font.selection.byGlyphs:
        if glyph.isWorthOutputting():
            glyph.clear()


def clear_duplicate_circled_letter(font1: fontforge.font, font2: fontforge.font) -> None:
    font1.selection.none()
    font2.selection.none()
    for glyph2 in font2.glyphs():
        if (glyph2.isWorthOutputting()
            and (0x2460 <= glyph2.unicode <= 0x24FF
                 or 0x2776 <= glyph2.unicode <= 0x2793
                 or 0x3251 <= glyph2.unicode <= 0x325F
                 or 0x32B1 <= glyph2.unicode <= 0x32BF)):
            font1.selection.select(('unicode',), glyph2.unicode)
            font1.clear()


def clear_duplicate_glyphs(font1: fontforge.font, font2: fontforge.font) -> None:
    for glyph2 in font2.glyphs():
        if glyph2.isWorthOutputting() and glyph2.unicode > 0:
            font1.selection.select(('unicode',), glyph2.unicode)
            font1.clear()


def normalize_width(font: fontforge.font, pre_halfwidth: int, post_halfwidth: int, x_only: bool = True) -> None:
    mag = float(post_halfwidth) / pre_halfwidth
    trans_mat = psMat.scale(mag, 1.0) if x_only else psMat.scale(mag)
    for glyph in font.glyphs():
        if glyph.width > 0:
            coeff = round(float(glyph.width) / pre_halfwidth)
            glyph.transform(trans_mat)
            glyph.width = round(post_halfwidth * coeff)


def add_nerd_font_glyphs(font: fontforge.font):
    nerd_font = fontforge.open(NERD_FILENAME)
    common.scale_em(nerd_font, EM_ASCENT, EM_DESCENT)
    normalize_width(nerd_font, 1024, FONT_WIDTH / 2)

    glyph_names = set()
    for nerd_glyph in nerd_font.glyphs():
        # Nerd Fontsのグリフ名をユニークにするため接尾辞を付ける
        nerd_glyph.glyphname = f"{nerd_glyph.glyphname}-nf"
        # postテーブルでのグリフ名重複対策
        # fonttools merge で合成した後、MacOSで `'post'テーブルの使用性` エラーが発生することへの対処
        if nerd_glyph.glyphname in glyph_names:
            nerd_glyph.glyphname = f"{nerd_glyph.glyphname}-{nerd_glyph.encoding}"
        glyph_names.add(nerd_glyph.glyphname)
        # グリフの縦位置を直す
        nerd_glyph.transform(psMat.translate(0, NERD_Y_OFFSET))

    common.merge_fonts(font, nerd_font)


def edit_meta_data(font: fontforge.font, for_bold: bool, for_italic: bool, version: str) -> None:
    stylename = common.STYLE_TABLE[(for_bold, for_italic)]

    # PS Names
    font.fontname = f'{RELEASE_FAMILYNAME}-{stylename.replace(" ", "")}'
    font.familyname = RELEASE_FAMILYNAME.replace('-', ' ')
    font.fullname = f'{RELEASE_FAMILYNAME.replace("-", " ")} {stylename.replace(" ", "")}'
    font.version = version
    font.sfntRevision = None
    font.copyright = COPYRIGHT

    # OS/2
    font.os2_weight = 700 if for_bold else 400    # 400 = Regular, 700 = Bold
    font.os2_vendor = 'HBZM'
    if for_bold and for_italic:
        font.os2_stylemap = 0x21
    elif for_bold and not for_italic:
        font.os2_stylemap = 0x20
    elif not for_bold and for_italic:
        font.os2_stylemap = 0x01
    elif not for_bold and not for_italic:
        font.os2_stylemap = 0x40

    font.os2_winascent = FONT_ASCENT
    font.os2_windescent = FONT_DESCENT
    font.os2_typoascent = font.ascent
    font.os2_typodescent = -font.descent
    font.os2_typolinegap = 0
    font.hhea_ascent = FONT_ASCENT
    font.hhea_descent = -FONT_DESCENT
    font.hhea_linegap = 0
    font.os2_capheight = round(font[0x48].boundingBox()[3])
    font.os2_xheight = round(font[0x78].boundingBox()[3])

    font.os2_panose = (
        2,     # Family Kind (2 = Latin: Text and Display)
        11,    # Serifs (11 = normal sans)
        8 if for_bold else 5,    # Weight (5 = Book, 8 = Bold)
        9,     # Proportion (9 = Monospaced)
        0,
        0,
        0,
        0,
        0,
        0
    )

    # TTF names
    font.sfnt_names = (
        ('English (US)', 'Copyright', ''),  # to be inherited
        ('English (US)', 'Family', ''),  # to be inherited
        ('English (US)', 'SubFamily', stylename),
        ('English (US)', 'UniqueID', f'{version};HBZM;{stylename.replace(" ", "")}'),
        ('English (US)', 'Fullname', ''),  # to be inherited
        ('English (US)', 'Version', f'Version {version}'),
        ('English (US)', 'Trademark', TRADEMARK),
        ('English (US)', 'Manufacturer', MANUFACTURER),
        ('English (US)', 'Designer', DESIGNER),
        ('English (US)', 'Vendor URL', ''),
        ('English (US)', 'Designer URL', ''),
        ('English (US)', 'License', LICENSE),
        ('English (US)', 'License URL', LICENSE_URL),
        ('Japanese', 'Copyright', ''),
        ('Japanese', 'Family', RELEASE_FAMILYNAME),
        ('Japanese', 'SubFamily', stylename),
        ('Japanese', 'Fullname', f'{RELEASE_FAMILYNAME} {stylename.replace(" ", "")}'),
        ('Japanese', 'Version', f'Version {version}'),
    )


def autohint(filename: str) -> None:
    tmp_filename = common.make_temp_filename(suffix='.ttf', dir='.')
    subprocess.run(
        (
            'ttfautohint',
            '-l', '6',
            '-r', '45',
            '-D', 'latn',
            '-f', 'none',
            '-S',
            '-W',
            '-X', '',
            '-n',
            filename,
            tmp_filename,
        )
    )
    Path(tmp_filename).rename(filename)


def delete_vhea_vmtx(filename: str) -> None:
    font = ttLib.TTFont(filename)
    if 'vhea' in font:
        del font['vhea']
    if 'vmtx' in font:
        del font['vmtx']
    font.save(filename)


def fix_font_tables(filename: str, for_bold: bool, for_italic: bool) -> None:
    ttx_filename = common.make_temp_filename(suffix='.ttx', dir='.')

    ttx.main(['-t', 'OS/2', '-t', 'post', '-f', '-o', ttx_filename, filename])
    xml = ET.parse(ttx_filename)

    # OS/2
    xml.find('OS_2/xAvgCharWidth').set('value', str(round(FONT_WIDTH / 2)))

    # post
    xml.find('post/isFixedPitch').set('value', '1')

    xml.write(ttx_filename, encoding='utf-8', xml_declaration=True)

    release_filename = (
        f'{BUILD_DIR}/{RELEASE_FAMILYNAME}-{common.STYLE_TABLE[(for_bold, for_italic)].replace(" ", "")}.ttf'
    )
    ttx.main(['-o', release_filename, '-m', filename, ttx_filename])

    Path(ttx_filename).unlink()
    Path(filename).unlink()


if __name__ == '__main__':
    main()
