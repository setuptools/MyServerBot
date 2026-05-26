from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import logging

from keyboards.file_manager import file_actions_keyboard, folder_keyboard
from config import ALLOWED_DIRS, ALLOWED_EXTENSIONS

__router__ = Router()


class FileManagerStates(StatesGroup):
    browsing = State()
    uploading = State()
    editing = State()
    creating_file = State()
    creating_folder = State()
    renaming = State()


@__router__.message(F.text == "📁 Файловый менеджер")
async def file_manager_handler(message: Message, state: FSMContext):

    await state.clear()

    start_path = ALLOWED_DIRS[0] if ALLOWED_DIRS else "/"
    await state.update_data(current_path=start_path)
    await show_directory(message, start_path, state)


async def show_directory(message: Message, path: str, state: FSMContext, page: int = 0):
    if ALLOWED_DIRS and not any(path.startswith(allowed) for allowed in ALLOWED_DIRS):
        await message.answer("❌ Доступ к этой директории запрещен")
        return

    try:
        items = os.listdir(path)
        folders = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(path, item))]
        
        if ALLOWED_EXTENSIONS:
            files = [f for f in files if any(f.endswith(ext) for ext in ALLOWED_EXTENSIONS)]

        folders.sort()
        files.sort()

        text = f"📂 <b>Текущая директория:</b>\n<code>{path}</code>\n\n"
        text += f"📁 Папок: {len(folders)}\n📄 Файлов: {len(files)}"

        await state.update_data(current_path=path, current_page=page)
        await state.set_state(FileManagerStates.browsing)

        if isinstance(message, Message):
            await message.answer(text, reply_markup=folder_keyboard(path, folders, files, page), parse_mode="HTML")
        else:
            await message.message.edit_text(text, reply_markup=folder_keyboard(path, folders, files, page), parse_mode="HTML")

    except PermissionError:
        await message.answer("❌ Нет доступа к этой директории")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@__router__.callback_query(F.data.startswith("fm_folder:"))
async def open_folder_callback(callback: CallbackQuery, state: FSMContext):
    folder_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    new_path = os.path.join(current_path, folder_name)
    await show_directory(callback, new_path, state)
    await callback.answer()


@__router__.callback_query(F.data.startswith("fm_file:"))
async def file_action_callback(callback: CallbackQuery, state: FSMContext):
    file_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    file_path = os.path.join(current_path, file_name)
    
    await state.update_data(selected_file=file_path)
    
    file_size = os.path.getsize(file_path)
    size_mb = file_size / (1024 * 1024)
    
    text = f"📄 <b>Файл:</b> <code>{file_name}</code>\n"
    text += f"📊 <b>Размер:</b> {size_mb:.2f} MB\n"
    text += f"📂 <b>Путь:</b> <code>{file_path}</code>"
    
    await callback.message.edit_text(text, reply_markup=file_actions_keyboard(file_name), parse_mode="HTML")
    await callback.answer()


@__router__.callback_query(F.data == "fm_back")
async def back_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    
    # Если мы в меню действий с файлом, возвращаемся к списку
    if "selected_file" in data:
        await state.update_data(selected_file=None)
        await show_directory(callback, current_path, state)
        await callback.answer()
        return
    
    # Иначе поднимаемся на уровень выше
    parent_path = os.path.dirname(current_path)
    
    if parent_path and (not ALLOWED_DIRS or any(parent_path.startswith(allowed) for allowed in ALLOWED_DIRS)):
        await show_directory(callback, parent_path, state)
    else:
        await callback.answer("❌ Нельзя подняться выше", show_alert=True)
    
    await callback.answer()


@__router__.callback_query(F.data == "fm_upload")
async def upload_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FileManagerStates.uploading)
    await callback.message.edit_text("📤 Отправьте файл для загрузки\n\n❌ /cancel - отменить")
    await callback.answer()


@__router__.callback_query(F.data == "fm_create_file")
async def create_file_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FileManagerStates.creating_file)
    await callback.message.edit_text("📝 Создание нового файла\n\nОтправьте имя файла (например: document.txt)\n\n❌ /cancel - отменить")
    await callback.answer()


@__router__.message(FileManagerStates.creating_file, F.text)
async def create_file_handler(message: Message, state: FSMContext):
    if message.text.startswith("/cancel"):
        await cancel_operation(message, state)
        return
    
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    file_name = message.text.strip()
    
    if "/" in file_name or "\\" in file_name:
        await message.answer("❌ Имя файла не может содержать / или \\")
        return
    
    if ALLOWED_EXTENSIONS and not any(file_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        await message.answer(f"❌ Тип файла не разрешен. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}")
        return
    
    file_path = os.path.join(current_path, file_name)
    
    if os.path.exists(file_path):
        await message.answer("❌ Файл с таким именем уже существует")
        return
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        await message.answer(f"✅ Файл <code>{file_name}</code> создан\n\nОтправьте содержимое файла или /skip чтобы оставить пустым", parse_mode="HTML")
        await state.update_data(selected_file=file_path)
        await state.set_state(FileManagerStates.editing)
    except Exception as e:
        await message.answer(f"❌ Ошибка создания: {str(e)}")


@__router__.callback_query(F.data == "fm_create_folder")
async def create_folder_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FileManagerStates.creating_folder)
    await callback.message.edit_text("📁 Создание новой папки\n\nОтправьте имя папки\n\n❌ /cancel - отменить")
    await callback.answer()


@__router__.message(FileManagerStates.creating_folder, F.text)
async def create_folder_handler(message: Message, state: FSMContext):
    if message.text.startswith("/cancel"):
        await cancel_operation(message, state)
        return
    
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    folder_name = message.text.strip()
    
    if "/" in folder_name or "\\" in folder_name:
        await message.answer("❌ Имя папки не может содержать / или \\")
        return
    
    folder_path = os.path.join(current_path, folder_name)
    
    if os.path.exists(folder_path):
        await message.answer("❌ Папка с таким именем уже существует")
        return
    
    try:
        os.makedirs(folder_path)
        await message.answer(f"✅ Папка <code>{folder_name}</code> создана", parse_mode="HTML")
        await state.set_state(FileManagerStates.browsing)
        await show_directory(message, current_path, state)
    except Exception as e:
        await message.answer(f"❌ Ошибка создания: {str(e)}")


@__router__.message(FileManagerStates.uploading, F.document)
async def upload_file_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    
    file = message.document
    file_name = file.file_name
    file_path = os.path.join(current_path, file_name)
    
    if ALLOWED_EXTENSIONS and not any(file_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        await message.answer(f"❌ Тип файла не разрешен. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}")
        return
    
    try:
        await message.bot.download(file, destination=file_path)
        await message.answer(f"✅ Файл <code>{file_name}</code> успешно загружен", parse_mode="HTML")
        await state.set_state(FileManagerStates.browsing)
        await show_directory(message, current_path, state)
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки: {str(e)}")


@__router__.callback_query(F.data.startswith("fm_download:"))
async def download_callback(callback: CallbackQuery, state: FSMContext):
    file_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    file_path = data.get("selected_file")
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 500 * 1024 * 1024:
            await callback.answer("❌ Файл слишком большой (>500MB)", show_alert=True)
            return
        
        await callback.message.answer_document(FSInputFile(file_path), caption=f"📄 {file_name}")
        await callback.answer("✅ Файл отправлен")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@__router__.callback_query(F.data.startswith("fm_folder_actions:"))
async def folder_actions_callback(callback: CallbackQuery, state: FSMContext):
    folder_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    folder_path = os.path.join(current_path, folder_name)
    
    await state.update_data(selected_folder=folder_path)
    
    from keyboards.file_manager import folder_actions_keyboard
    
    text = f"📁 <b>Папка:</b> <code>{folder_name}</code>\n"
    text += f"📂 <b>Путь:</b> <code>{folder_path}</code>"
    
    await callback.message.edit_text(text, reply_markup=folder_actions_keyboard(folder_name), parse_mode="HTML")
    await callback.answer()


@__router__.callback_query(F.data.startswith("fm_delete_folder:"))
async def delete_folder_callback(callback: CallbackQuery, state: FSMContext):
    folder_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    folder_path = data.get("selected_folder")
    
    try:
        import shutil
        shutil.rmtree(folder_path)
        await callback.answer(f"✅ Папка {folder_name} удалена", show_alert=True)
        current_path = data.get("current_path", "/")
        await state.update_data(selected_folder=None)
        await show_directory(callback, current_path, state)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@__router__.callback_query(F.data.startswith("fm_rename:"))
async def rename_callback(callback: CallbackQuery, state: FSMContext):
    item_name = callback.data.split(":", 1)[1]
    await state.set_state(FileManagerStates.renaming)
    await callback.message.edit_text(
        f"✏️ Переименование: <code>{item_name}</code>\n\n"
        f"Отправьте новое имя\n\n❌ /cancel - отменить",
        parse_mode="HTML"
    )
    await callback.answer()


@__router__.message(FileManagerStates.renaming, F.text)
async def rename_handler(message: Message, state: FSMContext):
    if message.text.startswith("/cancel"):
        await cancel_operation(message, state)
        return
    
    data = await state.get_data()
    new_name = message.text.strip()
    
    if "/" in new_name or "\\" in new_name:
        await message.answer("❌ Имя не может содержать / или \\")
        return
    
    old_path = data.get("selected_file") or data.get("selected_folder")
    if not old_path:
        await message.answer("❌ Ошибка: не выбран файл или папка")
        return
    
    current_path = data.get("current_path", "/")
    new_path = os.path.join(current_path, new_name)
    
    if os.path.exists(new_path):
        await message.answer("❌ Файл или папка с таким именем уже существует")
        return
    
    try:
        os.rename(old_path, new_path)
        await message.answer(f"✅ Переименовано в <code>{new_name}</code>", parse_mode="HTML")
        await state.update_data(selected_file=None, selected_folder=None)
        await state.set_state(FileManagerStates.browsing)
        await show_directory(message, current_path, state)
    except Exception as e:
        await message.answer(f"❌ Ошибка переименования: {str(e)}")


async def cancel_operation(message: Message, state: FSMContext):
    await message.answer("❌ Операция отменена")
    await state.set_state(FileManagerStates.browsing)
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    await show_directory(message, current_path, state)
async def delete_callback(callback: CallbackQuery, state: FSMContext):
    file_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    file_path = data.get("selected_file")
    
    try:
        os.remove(file_path)
        await callback.answer(f"✅ Файл {file_name} удален", show_alert=True)
        current_path = data.get("current_path", "/")
        await show_directory(callback, current_path, state)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@__router__.callback_query(F.data.startswith("fm_edit:"))
async def edit_callback(callback: CallbackQuery, state: FSMContext):
    file_name = callback.data.split(":", 1)[1]
    data = await state.get_data()
    file_path = data.get("selected_file")
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:
            await callback.answer("❌ Файл слишком большой для редактирования (>1MB)", show_alert=True)
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > 3000:
            content = content[:3000] + "\n\n... (обрезано)"
        
        await callback.message.edit_text(
            f"✏️ <b>Редактирование:</b> <code>{file_name}</code>\n\n"
            f"<code>{content}</code>\n\n"
            f"📝 Отправьте новое содержимое файла\n❌ /cancel - отменить",
            parse_mode="HTML"
        )
        await state.set_state(FileManagerStates.editing)
        await callback.answer()
    except UnicodeDecodeError:
        await callback.answer("❌ Файл не является текстовым", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@__router__.message(FileManagerStates.editing, F.text)
async def edit_file_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    file_path = data.get("selected_file")
    
    if message.text.startswith("/cancel"):
        await cancel_operation(message, state)
        return
    
    if message.text.startswith("/skip"):
        await message.answer("✅ Файл оставлен пустым")
        await state.set_state(FileManagerStates.browsing)
        current_path = data.get("current_path", "/")
        await show_directory(message, current_path, state)
        return

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(message.text)
        
        await message.answer(f"✅ Файл успешно сохранен")
        await state.set_state(FileManagerStates.browsing)
        current_path = data.get("current_path", "/")
        await show_directory(message, current_path, state)
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {str(e)}")


@__router__.callback_query(F.data == "fm_refresh")
async def refresh_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    current_page = data.get("current_page", 0)
    await show_directory(callback, current_path, state, current_page)
    await callback.answer("🔄 Обновлено")



@__router__.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await cancel_operation(message, state)

@__router__.callback_query(F.data == "fm_page_info")
async def page_info_callback(callback: CallbackQuery):
    """Обработчик клика на индикатор страницы (ничего не делает)"""
    await callback.answer()

@__router__.callback_query(F.data.startswith("fm_page:"))
async def page_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик переключения страниц"""
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    current_path = data.get("current_path", "/")
    await show_directory(callback, current_path, state, page)
    await callback.answer()