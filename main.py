import customtkinter as ctk
import importlib.util
import os
import sys
import traceback

from app_card import AppCard
from settings import load_settings, save_settings
from updater import check_for_updates, CURRENT_VERSION

settings = load_settings()
ctk.set_appearance_mode(settings["theme"])
ctk.set_default_color_theme("dark-blue")

class AppLauncher(ctk.CTk):
    def __init__(self):
        super().__init__() 
        self.geometry("1100x750")
        self.title("💋 Лаунчер Side")
        
        self.settings_window = None
        self.tiles_per_row = settings["tiles_per_row"]
        self.current_frame = None
        self.plugin_frames = {}
        self.search_query = ""
        
        # Добавляем надпись версии в углу для контроля
        self.version_label = ctk.CTkLabel(self, text=f"v{CURRENT_VERSION}", text_color="gray")
        self.version_label.place(relx=0.99, rely=0.99, anchor="se")

        # Запускаем проверку обновлений через 3 секунды после старта, 
        # чтобы окно успело отрисоваться
        self.after(3000, check_for_updates)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.plugins = [] # Все загруженные плагины
        self.cards = []
        
        self.load_plugins()
        self.apply_saved_order()
        self.build_ui()

    def load_plugins(self):
        # ... (код загрузки остается без изменений)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        sys.path.insert(0, base_path)
        loaded_ids = set()
        
        for file in os.listdir(base_path):
            if file.startswith("plugin_") and file.endswith(".py"):
                try:
                    module_name = file[:-3]
                    file_path = os.path.join(base_path, file)
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        plugin_instance = getattr(module, "plugin", None) or (module.Plugin() if hasattr(module, "Plugin") else None)
                        if plugin_instance and plugin_instance.id not in loaded_ids:
                            self.plugins.append(plugin_instance)
                            loaded_ids.add(plugin_instance.id)
                except Exception:
                    traceback.print_exc()

    def apply_saved_order(self):
        if settings["plugin_order"]:
            valid_order = [pid for pid in settings["plugin_order"] if pid in [p.id for p in self.plugins]]
            plugin_dict = {p.id: p for p in self.plugins}
            ordered = [plugin_dict[pid] for pid in valid_order]
            ordered += [p for p in self.plugins if p.id not in valid_order]
            self.plugins = ordered

    def build_ui(self):
        self.main = ctk.CTkFrame(self.container)
        self.main.pack(fill="both", expand=True)

        # Верхняя панель
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(top, text="🚀 Лаунчер", font=("Arial", 28, "bold")).pack(side="left", padx=(0, 20))

        # Поле поиска
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        self.search_entry = ctk.CTkEntry(
            top, 
            placeholder_text="Поиск плагинов...", 
            width=350, 
            height=35,
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", padx=10)

        ctk.CTkButton(top, text="⚙️", width=40, command=self.open_settings).pack(side="right")

        # Область карточек
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.scrollable_frame._scrollbar.configure(width=0)
        
        self.grid_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

        self.render_cards()
        self.after(100, self.check_scrollbar_visibility)

    def on_search_change(self, *args):
        self.search_query = self.search_var.get().lower()
        self.render_cards()

    def render_cards(self):
        """Отрисовка карточек с учетом фильтрации"""
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cards.clear()

        # Фильтруем список плагинов
        filtered_plugins = [
            p for p in self.plugins 
            if self.search_query in p.title.lower() or self.search_query in p.description.lower()
        ]

        for i in range(self.tiles_per_row):
            self.grid_frame.grid_columnconfigure(i, weight=1)

        for i, plugin in enumerate(filtered_plugins):
            row, col = divmod(i, self.tiles_per_row)
            card = AppCard(
                self.grid_frame,
                plugin,
                lambda p=plugin: self.launch_plugin(p),
                self.handle_drop
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            self.cards.append(card)
        
        self.check_scrollbar_visibility()

    def toggle_favorite(self, plugin_id):
        if plugin_id in settings["favorites"]:
            settings["favorites"].remove(plugin_id)
        else:
            settings["favorites"].append(plugin_id)
        
        save_settings(settings)
        self.render_cards()

    def render_cards(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cards.clear()

        # 1. Фильтрация по поиску
        filtered = [
            p for p in self.plugins 
            if self.search_query in p.title.lower() or self.search_query in p.description.lower()
        ]

        # 2. Сортировка: Сначала избранные, потом остальные
        # Мы сохраняем относительный порядок из self.plugins (который учитывает перетаскивание)
        sorted_plugins = sorted(
            filtered, 
            key=lambda p: p.id not in settings["favorites"]
        )

        for i in range(self.tiles_per_row):
            self.grid_frame.grid_columnconfigure(i, weight=1)

        for i, plugin in enumerate(sorted_plugins):
            row, col = divmod(i, self.tiles_per_row)
            is_fav = plugin.id in settings["favorites"]
            
            card = AppCard(
                self.grid_frame,
                plugin,
                lambda p=plugin: self.launch_plugin(p),
                self.handle_drop,
                self.toggle_favorite, # Передаем команду избранного
                is_fav
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            self.cards.append(card)
        
        self.check_scrollbar_visibility()
        
    def handle_drop(self, dragged_card, x, y):
        # Drag-and-drop работает только когда поиск пустой (чтобы не ломать логику порядка)
        if self.search_query != "":
            return False

        target_card = None
        for card in self.cards:
            if card == dragged_card: continue
            bx, by = card.winfo_rootx(), card.winfo_rooty()
            bw, bh = card.winfo_width(), card.winfo_height()
            if bx < x < bx + bw and by < y < by + bh:
                target_card = card
                break

        if target_card:
            i1, i2 = self.plugins.index(dragged_card.plugin), self.plugins.index(target_card.plugin)
            self.plugins[i1], self.plugins[i2] = self.plugins[i2], self.plugins[i1]
            settings["plugin_order"] = [p.id for p in self.plugins]
            save_settings(settings)
            self.after(50, self.render_cards)
            return True
        return False

    def check_scrollbar_visibility(self):
        self.grid_frame.update_idletasks()
        if self.grid_frame.winfo_reqheight() > self.scrollable_frame.winfo_height():
            self.scrollable_frame._scrollbar.configure(width=12)
        else:
            self.scrollable_frame._scrollbar.configure(width=0)

    def launch_plugin(self, plugin):
        self.main.pack_forget()
        if plugin.id not in self.plugin_frames:
            f = ctk.CTkFrame(self.container, fg_color="transparent")
            try:
                content = plugin.create(f, lambda: [f.pack_forget(), self.main.pack(fill="both", expand=True)])
                content.pack(fill="both", expand=True)
                self.plugin_frames[plugin.id] = f
            except:
                traceback.print_exc()
                self.main.pack(fill="both", expand=True)
                return
        self.current_frame = self.plugin_frames[plugin.id]
        self.current_frame.pack(fill="both", expand=True)

    def open_settings(self):
        # ... (код настроек остается без изменений)
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        win = ctk.CTkToplevel(self)
        self.settings_window = win
        win.geometry("300x260")
        win.title("Настройки")
        win.grab_set()
        
        theme = ctk.StringVar(value=settings["theme"])
        tiles = ctk.StringVar(value=str(self.tiles_per_row))
        
        ctk.CTkLabel(win, text="Тема").pack(pady=5)
        ctk.CTkOptionMenu(win, values=["dark", "light", "system"], variable=theme).pack()
        ctk.CTkLabel(win, text="Плиток в строке").pack(pady=10)
        ctk.CTkEntry(win, textvariable=tiles).pack()

        def apply():
            try: settings["tiles_per_row"] = self.tiles_per_row = max(1, min(8, int(tiles.get())))
            except: pass
            settings["theme"] = theme.get()
            save_settings(settings)
            ctk.set_appearance_mode(settings["theme"])
            self.render_cards()
            win.destroy()
        
        ctk.CTkButton(win, text="Применить", command=apply).pack(pady=20)

if __name__ == "__main__":
    app = AppLauncher()
    app.mainloop()
