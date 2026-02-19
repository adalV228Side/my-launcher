import customtkinter as ctk

class AppCard(ctk.CTkFrame):
    def __init__(self, parent, plugin, click_command, drop_command, toggle_fav_command, is_favorite):
        super().__init__(
            parent,
            border_width=2,
            border_color="#F1C40F" if is_favorite else plugin.color,
            corner_radius=15,
            cursor="hand2"
        )
        self.plugin = plugin
        self.click_command = click_command
        self.drop_command = drop_command
        self.toggle_fav_command = toggle_fav_command
        self.is_favorite = is_favorite
        self.ghost = None

        self.pack_propagate(False)
        self.configure(width=320, height=180)

        fav_text = "★" if is_favorite else "☆"
        self.fav_btn = ctk.CTkButton(
            self, text=fav_text, width=30, height=30,
            fg_color="transparent", text_color="#F1C40F",
            hover_color="#333333", font=("Arial", 20),
            command=self.toggle_fav
        )
        self.fav_btn.place(relx=0.95, rely=0.05, anchor="ne")

        self.icon_label = ctk.CTkLabel(self, text=plugin.icon, font=("Arial", 40))
        self.icon_label.pack(pady=(20, 10))

        self.title_label = ctk.CTkLabel(self, text=plugin.title, font=("Arial", 18, "bold"))
        self.title_label.pack()

        self.desc_label = ctk.CTkLabel(self, text=plugin.description, text_color="gray")
        self.desc_label.pack(pady=5)

        widgets = [self, self.icon_label, self.title_label, self.desc_label]
        for widget in widgets:
            widget.bind("<ButtonPress-1>", self.on_press)
            widget.bind("<B1-Motion>", self.on_motion)
            widget.bind("<ButtonRelease-1>", self.on_release)

    def toggle_fav(self):
        self.toggle_fav_command(self.plugin.id)

    def on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.is_dragging = False

    def on_motion(self, event):
        if not hasattr(self, 'start_x'):
            return
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y
        if not self.is_dragging and (abs(dx) > 10 or abs(dy) > 10):
            self.is_dragging = True
            self.create_ghost()
        if self.is_dragging and self.ghost:
            main_app = self.winfo_toplevel()
            new_x = event.x_root - main_app.winfo_rootx() - self.ghost_offset_x
            new_y = event.y_root - main_app.winfo_rooty() - self.ghost_offset_y
            self.ghost.place(x=new_x, y=new_y)

    def on_release(self, event):
        if not getattr(self, 'is_dragging', False):
            self.click_command()
            return
        success = self.drop_command(self, event.x_root, event.y_root)
        if success:
            self.destroy_ghost()
        else:
            self.animate_ghost_back()
        self.is_dragging = False

    def create_ghost(self):
        main_app = self.winfo_toplevel()
        self.ghost = ctk.CTkFrame(
            main_app,
            width=self.winfo_width(),
            height=self.winfo_height(),
            corner_radius=15,
            border_width=2,
            border_color="#FFFFFF"
        )
        self.ghost.pack_propagate(False)
        ctk.CTkLabel(self.ghost, text=self.plugin.icon, font=("Arial", 30)).pack(pady=5)
        ctk.CTkLabel(self.ghost, text=self.plugin.title, font=("Arial", 14, "bold")).pack()
        self.ghost_offset_x = self.start_x - self.winfo_rootx()
        self.ghost_offset_y = self.start_y - self.winfo_rooty()
        x = self.winfo_rootx() - main_app.winfo_rootx()
        y = self.winfo_rooty() - main_app.winfo_rooty()
        self.ghost.place(x=x, y=y)
        self.ghost.lift()
        self.configure(border_color="#222222")

    def destroy_ghost(self):
        if self.ghost:
            self.ghost.destroy()
            self.ghost = None
            self.configure(border_color="#F1C40F" if self.is_favorite else self.plugin.color)

    def animate_ghost_back(self):
        if not self.ghost:
            return
        main_app = self.winfo_toplevel()
        target_x = self.winfo_rootx() - main_app.winfo_rootx()
        target_y = self.winfo_rooty() - main_app.winfo_rooty()
        try:
            curr_x = int(self.ghost.place_info()['x'])
            curr_y = int(self.ghost.place_info()['y'])
        except:
            self.destroy_ghost()
            return
        steps = 10
        dx = (target_x - curr_x) / steps
        dy = (target_y - curr_y) / steps
        def move_step(count):
            if count < steps and self.ghost:
                self.ghost.place(x=curr_x + dx * (count+1), y=curr_y + dy * (count+1))
                self.after(10, lambda: move_step(count + 1))
            else:
                self.destroy_ghost()
        move_step(0)