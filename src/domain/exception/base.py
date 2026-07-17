class DomainError(Exception):
    
    @property
    def message(self) -> str:
        return f"Ошибка в домене: {self.__class__.__name__}"
