from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


async def start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика сервера")],
            [KeyboardButton(text="📁 Файловый менеджер")],
        ],
        resize_keyboard=True
    )
    return keyboard


def folder_keyboard(current_path: str, folders: list, files: list, page: int = 0):
    """
    Создает клавиатуру файлового менеджера с пагинацией
    
    Args:
        current_path: текущий путь
        folders: список папок
        files: список файлов
        page: номер текущей страницы (начинается с 0)
    """
    buttons = []
    items_per_page = 10  # Количество элементов на странице
    
    # Объединяем папки и файлы в один список с пометками
    all_items = [('folder', f) for f in folders] + [('file', f) for f in files]
    total_items = len(all_items)
    total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
    
    # Ограничиваем номер страницы
    page = max(0, min(page, total_pages - 1))
    
    # Вычисляем диапазон элементов для текущей страницы
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Добавляем элементы текущей страницы
    for item_type, item_name in all_items[start_idx:end_idx]:
        if item_type == 'folder':
            buttons.append([
                InlineKeyboardButton(text=f"📁 {item_name}", callback_data=f"fm_folder:{item_name}"),
                InlineKeyboardButton(text="⚙️", callback_data=f"fm_folder_actions:{item_name}")
            ])
        else:  # file
            file_display = item_name[:35] + "..." if len(item_name) > 35 else item_name
            buttons.append([InlineKeyboardButton(
                text=f"📄 {file_display}",
                callback_data=f"fm_file:{item_name}"
            )])
    
    # Кнопки пагинации (если элементов больше чем на одну страницу)
    if total_pages > 1:
        pagination_buttons = []
        
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"fm_page:{page-1}")
            )
        
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"• {page + 1}/{total_pages} •",
                callback_data="fm_page_info"
            )
        )
        
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="След. ➡️", callback_data=f"fm_page:{page+1}")
            )
        
        buttons.append(pagination_buttons)
    
    # Контрольные кнопки
    control_buttons = []
    
    if current_path != "/":
        control_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="fm_back"))
    
    control_buttons.append(InlineKeyboardButton(text="🔄", callback_data="fm_refresh"))
    
    if control_buttons:
        buttons.append(control_buttons)
    
    # Кнопки действий
    action_buttons = [
        InlineKeyboardButton(text="📝 Новый файл", callback_data="fm_create_file"),
        InlineKeyboardButton(text="📁 Новая папка", callback_data="fm_create_folder")
    ]
    buttons.append(action_buttons)
    
    buttons.append([InlineKeyboardButton(text="📤 Загрузить файл", callback_data="fm_upload")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def file_actions_keyboard(file_name: str):
    buttons = [
        [
            InlineKeyboardButton(text="📥 Скачать", callback_data=f"fm_download:{file_name}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"fm_edit:{file_name}")
        ],
        [
            InlineKeyboardButton(text="🔄 Переименовать", callback_data=f"fm_rename:{file_name}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"fm_delete:{file_name}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="fm_back")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def folder_actions_keyboard(folder_name: str):
    buttons = [
        [
            InlineKeyboardButton(text="📂 Открыть", callback_data=f"fm_folder:{folder_name}")
        ],
        [
            InlineKeyboardButton(text="🔄 Переименовать", callback_data=f"fm_rename:{folder_name}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"fm_delete_folder:{folder_name}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="fm_back")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
