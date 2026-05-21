"""Утилиты сервера: статус (CPU, RAM, диск) и запуск кода."""
import psutil


def get_server_status() -> dict:
    """Получить статус сервера в виде словаря."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": cpu,
        "ram_used_mb": ram.used // 1024 // 1024,
        "ram_total_mb": ram.total // 1024 // 1024,
        "ram_percent": ram.percent,
        "disk_used_gb": disk.used // 1024 // 1024 // 1024,
        "disk_total_gb": disk.total // 1024 // 1024 // 1024,
        "disk_percent": disk.percent,
    }


def format_server_status() -> str:
    """Отформатировать статус сервера в виде строки для Telegram."""
    s = get_server_status()
    return (
        f"🖥️ Статус сервера\n\n"
        f"CPU: {s['cpu_percent']}%\n"
        f"RAM: {s['ram_used_mb']} MB / {s['ram_total_mb']} MB "
        f"({s['ram_percent']}%)\n"
        f"Диск: {s['disk_used_gb']} GB / {s['disk_total_gb']} GB "
        f"({s['disk_percent']}%)"
    )
