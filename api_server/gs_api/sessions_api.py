from __future__ import annotations
import abc
from types import ModuleType

class GS_API(abc.ABC):
    @abc.abstractmethod
    def init_radio(self, **kwargs) -> bytes:
        ...

    @abc.abstractmethod
    def send_packet(self, msg: list[int] | bytes, timeout: float = 2):
        ...

    @abc.abstractmethod
    def read_buffer(self) -> bytes:
        ...

    @abc.abstractmethod
    def wait_answer(self, timeout: float = 1000) -> bytes:
        ...

    @abc.abstractmethod
    def import_module(self, module_name: str) -> ModuleType:
        ...



