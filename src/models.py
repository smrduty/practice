from dataclasses import dataclass
from typing import Optional, Tuple
import re

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

    def parse_salary(self) -> Tuple[Optional[int], Optional[int]]:
        if not self.salary:
            return None, None
        
        clean_salary_str = self.salary.replace(" ", "")
        numbers = list(map(int, re.findall(r"\d+", clean_salary_str)))

        if not numbers:
            return None, None
        
        if "от" in self.salary:
            return numbers[0], None
        
        if "до" in self.salary:
            return None, numbers[0]
        
        if len(numbers) > 1:
            return numbers[0], numbers[1]
        
        return numbers[0], numbers[0]





