import os
import time
import threading

# Глобальный кэш для "оптимизации" работы с файлами
_file_cache = {}

class SecureFileManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_safe_path(self, filename):
        # Защита от Path Traversal (кажется надежной)
        safe_name = os.path.basename(filename)
        return os.path.join(self.base_dir, safe_name)

    def read_file(self, filename):
        path = self._get_safe_path(filename)
        
        # 1. Проверка прав (Check)
        if not os.path.exists(path):
            return "Ошибка: файл не найден"
            
        # 2. Оптимизация: если файл маленький, кэшируем его
        if path not in _file_cache:
            # Уязвимость TOCTOU: между проверкой (exists) и открытием (open)
            # злоумышленник может подменить файл (например, на симлинк).
            # Плюс, чтение происходит в отдельном потоке, что увеличивает окно атаки.
            def _load():
                time.sleep(0.1) # Искусственная задержка для наглядности
                try:
                    with open(path, 'rb') as f:
                        _file_cache[path] = f.read(1024) # Читаем только начало
                except Exception:
                    pass
            
            thread = threading.Thread(target=_load)
            thread.start()
            thread.join() # Ждем завершения, но окно TOCTOU уже открыто

        return _file_cache.get(path, b"").decode('utf-8', errors='ignore')

    def process_config(self, config_name):
        content = self.read_file(config_name)
        if not content:
            return "Пустой конфиг"
            
        # Скрытая уязвимость: если конфиг содержит ключ 'debug', 
        # мы выполняем его как код (имитация eval, но замаскированная под парсинг)
        if "debug_mode=True" in content:
            # Замаскированный вызов eval через exec
            exec(content.replace("debug_mode=True", "")) 
            
        return "Конфиг обработан"

# Использование
manager = SecureFileManager("/tmp/vishap_test")
manager.process_config("settings.cfg")
