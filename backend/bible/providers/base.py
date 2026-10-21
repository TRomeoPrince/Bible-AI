from abc import ABC, abstractmethod
from backend.bible.models import PassageResult, TranslationInfo


class BibleProvider(ABC):
    @abstractmethod
    def translations(self) -> list[TranslationInfo]:
        raise NotImplementedError

    @abstractmethod
    def get_passage(self, translation: str, reference: str) -> PassageResult:
        raise NotImplementedError

    def supports(self, translation: str) -> bool:
        wanted = translation.upper()
        return any(item.code.upper() == wanted for item in self.translations())
