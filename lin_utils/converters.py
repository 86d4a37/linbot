import opencc

kata = ("ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピ"
        "フブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ")
hira = ("ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴ"
        "ふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ")

s2tw = opencc.OpenCC('s2tw').convert
tw2s = opencc.OpenCC('tw2s').convert
s2twp = opencc.OpenCC('s2twp').convert


def hira2kata(string):
    return string.translate(str.maketrans(hira, kata))
