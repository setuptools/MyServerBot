from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def processes_keyboard(processes: list, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура со списком процессов и пагинацией"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки самих процессов
    for p in processes:
        # Обрезаем имя, чтобы оно не ломало верстку кнопок
        name_short = p['name'][:10] + ".." if len(p['name']) > 10 else p['name']
        btn_text = f"{name_short} ({p['pid']})"
        # Передаем PID и текущую страницу, чтобы потом вернуться на неё
        builder.button(text=btn_text, callback_data=f"tm_p:{p['pid']}:{current_page}")
        
    builder.adjust(2) # По 2 процесса в ряд
    
    # --- Блок пагинации ---
    nav_row = []
    
    # Кнопка "Назад"
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"tm_page:{current_page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text=" ", callback_data="tm_ignore"))
        
    # Кнопка "Счетчик" (неактивная)
    nav_row.append(InlineKeyboardButton(text=f"{current_page + 1} / {total_pages}", callback_data="tm_ignore"))
    
    # Кнопка "Вперед"
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"tm_page:{current_page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text=" ", callback_data="tm_ignore"))
        
    builder.row(*nav_row)
    
    # Кнопка обновления текущей страницы
    builder.row(InlineKeyboardButton(text="🔄 Обновить страницу", callback_data=f"tm_page:{current_page}"))
    
    return builder.as_markup()

def process_actions_keyboard(pid: int, page: int) -> InlineKeyboardMarkup:
    """Клавиатура действий над процессом"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки управления процессом
    builder.button(text="🔄 Перезапустить", callback_data=f"tm_restart:{pid}:{page}")
    builder.button(text="🛑 Остановить (Терм.)", callback_data=f"tm_term:{pid}:{page}")
    builder.button(text="☠️ Убить (Мгновенно)", callback_data=f"tm_kill:{pid}:{page}")
    builder.button(text="🔙 Назад к списку", callback_data=f"tm_page:{page}")
    
    # Устанавливаем по одной кнопке в ряд
    builder.adjust(1)
    return builder.as_markup()