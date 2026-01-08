from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class Vacancy:
    title: Optional[str]
    salary: Optional[str]
    experience: Optional[str]
    address: str
    url: Optional[str]

    def has_salary(self) -> bool:
        return bool(self.salary)
    
    def full_url(self) -> Optional[str]:
        if self.url and self.url.startswith('/'):
            return f"https://hh.ru{self.url}"
        return self.url





