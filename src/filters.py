from src.models import Vacancy


def format_vacancy_message(v):
    return (
        f"🔥 <b>{v.get('title', '')}</b>\n"
        f"💰 {v.get('salary', '')}\n"
        f"📍 {v.get('address', '')}\n"
        f"🧠 {v.get('experience', '')}\n\n"
        f"<a href='{v.get('url', '')}'>Открыть вакансию</a>"
    )

def format_random_vacancy_message(vacancy: Vacancy) -> str:
    return (
        "🎯 <b>Случайная вакансия без опыта</b>\n\n"
        f"📌 <b>{vacancy.title}</b>\n"
        f"💰 {vacancy.salary or 'зарплата не указана'}\n"
        f"📍 {vacancy.address or 'адрес не указан'}\n\n"
        f"🔗 <a href='{vacancy.full_url()}'>Открыть вакансию</a>"
    )


