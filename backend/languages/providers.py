from abc import ABC, abstractmethod

from backend.languages.models import LexiconEntry, WordStudyEntry


class OriginalLanguageProvider(ABC):
    @abstractmethod
    def words_for_reference(self, reference: str) -> list[WordStudyEntry]:
        raise NotImplementedError


class LexiconProvider(ABC):
    @abstractmethod
    def lookup_strong(self, strong_number: str) -> list[LexiconEntry]:
        raise NotImplementedError
