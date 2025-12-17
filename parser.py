import datetime
import asyncio

import aiohttp
from bs4 import BeautifulSoup


URL = 'https://службакровифмба66.рф/donorform/'


async def get_free_days() -> list[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            html = await response.text()
            with open('test.html', 'r', encoding='utf-8') as file:
                loc = file.read()
            soup = BeautifulSoup(loc, 'html.parser')
            calendars = soup.find_all('div', class_='donorform-calendar')
            free_days = []
            
            now = datetime.datetime.now()
            current_date_str = now.strftime("%Y-%m-%d")
            
            for calendar in calendars:
                month_elem = calendar.find('span', class_='donorform-calendar__month')
                year_elem = calendar.find('span', class_='donorform-calendar__year')
                
                if month_elem and year_elem:
                    month = month_elem.text.strip()
                    year = year_elem.text.strip()
                    
                    month_names_ru = {
                        'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4,
                        'Май': 5, 'Июнь': 6, 'Июль': 7, 'Август': 8,
                        'Сентябрь': 9, 'Октябрь': 10, 'Ноябрь': 11, 'Декабрь': 12
                    }
                    
                    month_num = month_names_ru.get(month)
                    
                    date_cells = calendar.find_all('td', class_=lambda x: x and ('active' in x or 'current_day' in x))
                    for cell in date_cells:
                        link = cell.find('a')
                        if link:
                            day = link.text.strip()
                            if day.isdigit():
                                title_attr = link.get('title', '')
                                
                                day_int = int(day)
                                cell_date = datetime.datetime(int(year), month_num, day_int)
                                cell_date_str = cell_date.strftime("%Y-%m-%d")
                                
                                if cell_date_str != current_date_str:
                                    free_days.append(f"{day} {month}")
                                else:
                                    if await has_future_time_slots(title_attr, now):
                                        free_days.append(f"{day} {month}")
            
            return free_days

async def has_future_time_slots(title_text: str, current_time: datetime.datetime) -> bool:
    """
    Проверяет, есть ли доступные временные слоты в будущем для текущей даты.
    """
    if not title_text:
        return False
    
    lines = title_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if 'свободных мест' in line and '-' in line:
            try:
                time_part = line.split('свободных мест')[0].strip()
                time_str = time_part.strip()
                
                free_slots = int(line.split('-')[-1].strip())
                
                if free_slots > 0:
                    slot_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                    slot_datetime = datetime.datetime.combine(current_time.date(), slot_time)
                    
                    if slot_datetime > current_time:
                        return True
            except (ValueError, IndexError) as e:
                continue
    
    return False


async def main():
    print(await get_free_days())


if __name__ == "__main__":
    asyncio.run(main())
