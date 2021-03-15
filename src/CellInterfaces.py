import json
import abc


###-------CELL DATA---------


class CellData(abc.ABC):

        @abc.abstractmethod
        def parse(self, stringData: str):
                pass

        @abc.abstractmethod
        def toString(self) -> str:
                pass


class EmptyCData(CellData):
        Data = None

        def toString(self):
                return ""

        def parse(self, stringData: str):
                self.Data = None


#------NUCLEAR DATA-----------


class NuclearData(abc.ABC):

        @abc.abstractmethod
        def parse(self, stringData: str):
                pass

        @abc.abstractmethod
        def toString(self) -> str:
                pass


class EmptyNData(NuclearData):
        Data = None

        def toString(self):
                return ""

        def parse(self, stringData: str):
                self.Data = None


