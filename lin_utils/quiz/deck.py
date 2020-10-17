import json
from typing import Dict, Set, Tuple

from pkg_resources import resource_filename, resource_listdir

from lin_utils.converters import hira2kata, tw2s

langs = ('ko', 'ja', 'zh_CN', 'zh_TW')


def get_decks() -> Tuple[Set[str], Dict[str, Set[str]]]:
    deck_set = set()
    deck_dict = {}
    for lang in langs:
        deck_dict[lang] = {file[:-5] for file in resource_listdir(
            f'resources.quiz.deck.{lang}', '') if file.endswith('.json')}
        deck_set = deck_set.union(deck_dict[lang])
    return deck_set, deck_dict


class Deck:
    def __init__(self, deck_name: str, lang: str) -> None:
        self.lang = lang
        with open(resource_filename(f'resources.quiz.deck.{lang}',
                                    f'{deck_name}.json')) as f:
            self.quiz_data = json.load(f)

        equivalency_dict = {
            'ja': self.japanese_equivalency,
            'ko': self.generic_equivalency,
            'zh_CN': self.chinese_equivalency,
            'zh_TW': self.chinese_equivalency,
        }
        self.equivalency = equivalency_dict[self.lang]

        if 'type' not in self.quiz_data:
            self.type = 'image'
        elif self.quiz_data['type'] in {'image', 'url', 'text'}:
            self.type = self.quiz_data['type']
        else:
            raise ValueError(f'Type {self.quiz_data["type"]} not supported')

        self.timeout = (self.quiz_data['timeout'] if 'timeout'
                        in self.quiz_data else 20.0)
        self.description = \
            (self.quiz_data['description'] if 'description' in self.quiz_data
             else 'No description found.')

    def __len__(self):
        return len(self.quiz_data['deck'])

    def __getitem__(self, idx):
        return self.quiz_data['deck'][idx]

    def print_answers(self, idx, sep='\n'):
        return sep.join(self[idx]['answers'])

    @staticmethod
    def chinese_equivalency(ans: str) -> str:
        ans = ans.lower()
        ans = ans.strip()
        ans = ans.replace('v', 'ü')
        ans = ans.replace(' ', '')
        ans = ans.replace('　', '')
        ans = ans.replace('5', '')
        ans = ans.replace('ê', 'e')
        ans = ans.replace('ˉ', '')
        ans = tw2s(ans)
        return ans

    @staticmethod
    def japanese_equivalency(ans: str) -> str:
        return hira2kata(ans).strip().lower()

    @staticmethod
    def generic_equivalency(ans: str) -> str:
        return ans.strip().lower()

    def check_equivalency(self, idx: int, guess: str) -> bool:
        answers = self[idx]['answers']
        return self.equivalency(guess) in {self.equivalency(answer) for answer
                                           in answers}
