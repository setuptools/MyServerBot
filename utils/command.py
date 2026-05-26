

import subprocess
import shlex
import os
import re
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum


class CommandStatus(Enum):
    """Статусы выполнения команды"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class CommandResult:
    """Результат выполнения команды"""
    status: CommandStatus
    output: str
    error: str
    exit_code: Optional[int]
    command: str


class SecureCommandExecutor:
    """
    Безопасный исполнитель команд с различными уровнями защиты
    """
    
    # Опасные команды, которые никогда не будут выполнены
    DANGEROUS_COMMANDS: Set[str] = {
        'rm', 'rmdir', 'dd', 'mkfs', 'format',
        'shutdown', 'reboot', 'halt', 'poweroff',
        'kill', 'killall', 'pkill',
        'chmod', 'chown', 'chgrp',
        '>', '>>', '|', '&', ';',
        'curl', 'wget', 'nc', 'netcat',
        'sudo', 'su',
    }
    
    # Разрешённые безопасные команды
    SAFE_COMMANDS: Set[str] = ()
        # 'ls', 'cat', 'echo', 'pwd', 'whoami',
        # 'date', 'uptime', 'df', 'du', 'free',
        # 'ps', 'top', 'htop', 'uname',
        # 'ping', 'traceroute', 'hostname',
        # 'dir','screen',
        # 'git', 'python3', 'node', 'npm',
        # 'pip', 'pip3', 'docker', 'docker-compose',
        

    def __init__(
        self,
        allowed_dirs: Optional[List[str]] = None,
        timeout: int = 5000,
        safe_mode: bool = True,
        max_output_size: int = 10000,
        whitelist_mode: bool = True
    ):
        """
        Инициализация исполнителя команд
        
        Args:
            allowed_dirs: Список разрешённых директорий для работы
            timeout: Таймаут выполнения команды в секундах
            max_output_size: Максимальный размер вывода
            whitelist_mode: Если True - разрешены только команды из SAFE_COMMANDS
        """
        self.safe_mode = safe_mode
        self.allowed_dirs = allowed_dirs or [os.getcwd()]
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.whitelist_mode = whitelist_mode
        self.command_history: List[CommandResult] = []
        
    def _sanitize_command(self, command: str) -> str:
        """Очистка команды от опасных символов"""
        # Удаляем множественные пробелы
        command = re.sub(r'\s+', ' ', command.strip())
        return command
    
    def _is_command_safe(self, command: str) -> tuple[bool, str]:
        """
        Проверка безопасности команды
        
        Returns:
            (is_safe, reason)
        """
        parts = shlex.split(command)
        if not parts:
            return False, "Пустая команда"
        
        base_command = parts[0].split('/')[-1]  
        
        # Проверка на опасные команды

        if self.safe_mode:
            for dangerous in self.DANGEROUS_COMMANDS:
                if dangerous in command:
                    return False, f"Команда содержит опасный элемент: {dangerous}"
            
        # В режиме whitelist проверяем, что команда разрешена
        if self.SAFE_COMMANDS != () and self.safe_mode and self.whitelist_mode and base_command not in self.SAFE_COMMANDS:
            return False, f"Команда '{base_command}' не входит в список разрешённых"
        
        return True, "OK"
    
    def _is_path_allowed(self, path: str) -> bool:
        """Проверка, что путь находится в разрешённых директориях"""
        abs_path = os.path.abspath(path)
        return any(
            abs_path.startswith(os.path.abspath(allowed_dir))
            for allowed_dir in self.allowed_dirs
        )
    
    def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Выполнение команды с проверками безопасности
        
        Args:
            command: Команда для выполнения
            working_dir: Рабочая директория
            env: Переменные окружения
            
        Returns:
            CommandResult с результатом выполнения
        """
        # Санитизация команды
        command = self._sanitize_command(command)
        
        # Проверка безопасности
        is_safe, reason = self._is_command_safe(command)
        if not is_safe:
            result = CommandResult(
                status=CommandStatus.BLOCKED,
                output="",
                error=f"{reason}",
                exit_code=None,
                command=command
            )
            self.command_history.append(result)
            return result
        
        # Проверка рабочей директории
        if working_dir:
            if not self._is_path_allowed(working_dir):
                result = CommandResult(
                    status=CommandStatus.BLOCKED,
                    output="",
                    error=f"Директория {working_dir} не входит в список разрешённых",
                    exit_code=None,
                    command=command
                )
                self.command_history.append(result)
                return result
        else:
            working_dir = self.allowed_dirs[0]
        
        # Выполнение команды
        try:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=env,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            # Ограничение размера вывода
            if len(stdout) > self.max_output_size:
                stdout = stdout[:self.max_output_size] + "\n... (вывод обрезан)"
            if len(stderr) > self.max_output_size:
                stderr = stderr[:self.max_output_size] + "\n... (вывод обрезан)"
            
            result = CommandResult(
                status=CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.ERROR,
                output=stdout,
                error=stderr,
                exit_code=process.returncode,
                command=command
            )
            
        except subprocess.TimeoutExpired:
            process.kill()
            result = CommandResult(
                status=CommandStatus.TIMEOUT,
                output="",
                error=f"Команда превысила таймаут ({self.timeout}s)",
                exit_code=None,
                command=command
            )
            
        except Exception as e:
            result = CommandResult(
                status=CommandStatus.ERROR,
                output="",
                error=f"Ошибка выполнения: {str(e)}",
                exit_code=None,
                command=command
            )
        
        self.command_history.append(result)
        return result
    
    def get_history(self, limit: int = 10) -> List[CommandResult]:
        """Получить историю выполненных команд"""
        return self.command_history[-limit:]
    
    def add_safe_command(self, command: str):
        """Добавить команду в список безопасных"""
        self.SAFE_COMMANDS.add(command)
    
    def remove_safe_command(self, command: str):
        """Удалить команду из списка безопасных"""
        self.SAFE_COMMANDS.discard(command)


