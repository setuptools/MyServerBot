from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import psutil
import math
import subprocess

import asyncio

from keyboards.task_manager import processes_keyboard, process_actions_keyboard

__router__ = Router()

class TaskManagerStates(StatesGroup):
    viewing_list = State()

PAGE_SIZE = 10  # Количество процессов на одной странице

@__router__.message(F.text == "⚡️ Диспетчер задач")
async def task_manager_handler(message: Message, state: FSMContext):
    await show_process_list(message, state, page=0)

async def show_process_list(event, state: FSMContext, page: int = 0):
    """Показывает список всех процессов с пагинацией"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Сортируем по потреблению памяти по убыванию
        processes = sorted(
            processes, 
            key=lambda p: p['memory_info'].rss if p.get('memory_info') else 0, 
            reverse=True
        )

        total_processes = len(processes)
        total_pages = math.ceil(total_processes / PAGE_SIZE)

        # Защита от выхода за пределы страниц
        if page < 0: page = 0
        if page >= total_pages and total_pages > 0: page = total_pages - 1

        start_idx = page * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        current_page_procs = processes[start_idx:end_idx]

        text = f"💻 <b>Все процессы (Стр. {page + 1}/{total_pages}):</b>\n"
        text += f"📊 <b>Всего процессов:</b> {total_processes}\n\n"
        
        for p in current_page_procs:
            mem_mb = p['memory_info'].rss / (1024 * 1024) if p.get('memory_info') else 0
            text += f"🔹 <code>{p['name'][:15]}</code> (PID: {p['pid']}) — {mem_mb:.1f} MB\n"

        await state.set_state(TaskManagerStates.viewing_list)

        markup = processes_keyboard(current_page_procs, page, total_pages)
        
        if isinstance(event, Message):
            await event.answer(text, reply_markup=markup, parse_mode="HTML")
        else:
            await event.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

    except Exception as e:
        error_msg = f"❌ Ошибка получения процессов: {str(e)}"
        if isinstance(event, Message):
            await event.answer(error_msg)
        else:
            await event.answer(error_msg, show_alert=True)

@__router__.callback_query(F.data.startswith("tm_page:"))
async def pagination_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик перелистывания страниц"""
    page = int(callback.data.split(":")[1])
    await show_process_list(callback, state, page)
    await callback.answer()

@__router__.callback_query(F.data.startswith("tm_p:"))
async def process_info_callback(callback: CallbackQuery, state: FSMContext):
    """Детальная информация о процессе"""
    _, pid_str, page_str = callback.data.split(":")
    pid = int(pid_str)
    page = int(page_str)
    
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            name = proc.name()
            status = proc.status()
            mem_mb = proc.memory_info().rss / (1024 * 1024)
            cpu_percent = proc.cpu_percent(interval=0.1)
            
            try:
                exe_path = proc.exe()
            except psutil.AccessDenied:
                exe_path = "Доступ запрещен (нужны права)"
            
        text = f"⚙️ <b>Процесс:</b> <code>{name}</code>\n"
        text += f"🆔 <b>PID:</b> <code>{pid}</code>\n"
        text += f"📊 <b>Статус:</b> {status}\n"
        text += f"📈 <b>CPU:</b> {cpu_percent}%\n"
        text += f"💾 <b>RAM:</b> {mem_mb:.2f} MB\n\n"
        text += f"📂 <b>Путь:</b>\n<code>{exe_path}</code>"
        
        await callback.message.edit_text(text, reply_markup=process_actions_keyboard(pid, page), parse_mode="HTML")
        await callback.answer()
        
    except psutil.NoSuchProcess:
        await callback.answer("❌ Процесс уже закрыт", show_alert=True)
        await show_process_list(callback, state, page)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

@__router__.callback_query(F.data.startswith("tm_term:") | F.data.startswith("tm_kill:"))
async def kill_process_callback(callback: CallbackQuery, state: FSMContext):
    """Остановка или завершение процесса через консольный sudo kill"""
    action, pid_str, page_str = callback.data.split(":")
    pid = int(pid_str)
    page = int(page_str)
    
    try:
        # Формируем команду для консоли в зависимости от действия
        if action == "tm_term":
            # Мгновенный аналог terminate в консоли (SIGTERM)
            cmd = ["sudo", "kill", str(pid)]
            msg_success = f"⏳ Сигнал остановки (SIGTERM) отправлен процессу {pid} через sudo"
        else:
            # Жесткое убийство процесса (SIGKILL / -9)
            cmd = ["sudo", "kill", "-9", str(pid)]
            msg_success = f"☠️ Процесс {pid} принудительно убит (SIGKILL) через sudo"
        
        # Выполняем команду в консоли
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # returncode == 0 означает, что команда выполнена успешно
        if result.returncode == 0:
            await callback.answer(msg_success, show_alert=True)
        else:
            # Если консоль вернула ошибку (например, процесса нет или sudo просит пароль)
            error_msg = result.stderr.strip()
            await callback.answer(f"❌ Ошибка консоли:\n{error_msg}", show_alert=True)
            
        # Обновляем список процессов на той же странице
        await show_process_list(callback, state, page)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка выполнения: {str(e)}", show_alert=True)


@__router__.callback_query(F.data.startswith("tm_restart:"))
async def restart_process_callback(callback: CallbackQuery, state: FSMContext):
    """Перезапуск процесса (Получение инфо -> Убийство через sudo kill -> Новый запуск)"""
    _, pid_str, page_str = callback.data.split(":")
    pid = int(pid_str)
    page = int(page_str)
    
    try:
        # 1. Сначала Пытаемся получить параметры запуска старого процесса, пока он жив
        # ВНИМАНИЕ: Если исходный процесс системный/чужой, psutil.cmdline() может выдать AccessDenied.
        try:
            proc = psutil.Process(pid)
            cmdline = proc.cmdline()
            cwd = proc.cwd()
        except psutil.AccessDenied:
            await callback.answer("❌ Ошибка: psutil не может прочитать cmdline этого процесса (Доступ запрещен). Перезапуск невозможен.", show_alert=True)
            return
        except psutil.NoSuchProcess:
            await callback.answer("❌ Процесс уже закрыт или не существует", show_alert=True)
            await show_process_list(callback, state, page)
            return
            
        if not cmdline:
            await callback.answer("❌ Не удалось определить команду запуска процесса.", show_alert=True)
            return

        # 2. Валим старый процесс через консольный sudo kill (сначала мягко)
        subprocess.run(["sudo", "kill", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем до 3 секунд, проверяя, умер ли он
        for _ in range(3):
            if not psutil.pid_exists(pid):
                break
            await asyncio.sleep(1)
        else:
            # Если не умер по-хорошему — фигачим жестко через kill -9
            subprocess.run(["sudo", "kill", "-9", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 3. Запускаем процесс заново
        # Обратите внимание: он запустится с правами пользователя, под которым работает БОТ.
        # Если вам нужно, чтобы он и запускался заново под sudo, раскомментируйте строку ниже:
        # cmdline = ["sudo"] + cmdline
        
        subprocess.Popen(cmdline, cwd=cwd)
        
        await callback.answer("✅ Процесс успешно убит через sudo и запущен заново!", show_alert=True)
        await show_process_list(callback, state, page)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка перезапуска: {str(e)}", show_alert=True)


@__router__.callback_query(F.data == "tm_ignore")
async def ignore_callback(callback: CallbackQuery):
    """Пустой обработчик для неактивных кнопок пагинации"""
    await callback.answer()