from textwrap import wrap
from typing import Tuple, Union

from discord import File
from discord.ext.commands import Context
from PIL import Image, ImageDraw, ImageFont
from pkg_resources import resource_filename

# These fonts are distributed under the SIL Open Font License
JA_FONT_PATH = resource_filename('resources.quiz.image', 'NotoSerifCJKjp-SemiBold.otf')
KO_FONT_PATH = resource_filename('resources.quiz.image', 'NotoSerifCJKkr-SemiBold.otf')
ZH_CN_FONT_PATH = resource_filename('resources.quiz.image', 'NotoSerifCJKsc-SemiBold.otf')
ZH_TW_FONT_PATH = resource_filename('resources.quiz.image', 'NotoSerifCJKtc-SemiBold.otf')


def send_image_of_text(ctx: Context, lang: str, txt: str, size: int = 100,
                       path: Union[str, None] = None, embed: bool = False) -> Tuple[File, str]:
    if lang == 'ja':
        fontpath = JA_FONT_PATH
    elif lang == 'zh_TW':
        fontpath = ZH_TW_FONT_PATH
    elif lang == 'zh_CN':
        fontpath = ZH_CN_FONT_PATH
    else:
        fontpath = KO_FONT_PATH

    font = ImageFont.truetype(fontpath, size)

    if font.getsize_multiline(txt)[0] > int(size * 20):
        txt = '\n'.join(['\n'.join(wrap(line, 12,
                         replace_whitespace=False))
                         for line in txt.splitlines()])
        size *= 1.5
        size = int(size)
        font = ImageFont.truetype(fontpath, size)

    bg_color = (47, 49, 54) if embed else (54, 57, 62)

    image = Image.new("RGBA", (font.getsize_multiline(txt)[0], font.getsize_multiline(txt)[1]),
                      bg_color)
    draw = ImageDraw.Draw(image)

    draw.text((0, -int(0.2 * size)), txt, (255, 255, 255), font=font)

    if path is None:
        path = f'tmp/{ctx.message.channel.id}.png'

    image.save(path, format='png')
    f = File(path, filename=str(ctx.message.channel.id) + '.png')
    return f, str(ctx.message.channel.id) + '.png'
