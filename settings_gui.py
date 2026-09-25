"""
Small pre-launch settings editor. Run this instead of main.py when you want
to change sensitivity, control mode, theme, or toggle voice/analytics
without hand-editing config.json. Saves and exits; then run main.py.

This finally uses customtkinter, which sat unused in the original repo's
requirements.txt.
"""

import customtkinter as ctk

from config import config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class SettingsWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gaming Steering — Settings")
        self.geometry("420x520")

        row = 0
        ctk.CTkLabel(self, text="Steering", font=("", 16, "bold")).grid(row=row, column=0, columnspan=2, pady=(15, 5), padx=15, sticky="w")
        row += 1

        self.dead_zone_var = ctk.DoubleVar(value=config.get("steering", "dead_zone_degrees", default=6))
        self._slider_row("Dead zone (deg)", self.dead_zone_var, 0, 20, row); row += 1

        self.max_angle_var = ctk.DoubleVar(value=config.get("steering", "max_angle_degrees", default=45))
        self._slider_row("Max angle (deg)", self.max_angle_var, 15, 90, row); row += 1

        self.smoothing_var = ctk.DoubleVar(value=config.get("steering", "smoothing_factor", default=0.35))
        self._slider_row("Smoothing (higher=snappier)", self.smoothing_var, 0.05, 1.0, row); row += 1

        self.curve_var = ctk.StringVar(value=config.get("steering", "response_curve", default="linear"))
        ctk.CTkLabel(self, text="Response curve").grid(row=row, column=0, padx=15, sticky="w")
        ctk.CTkOptionMenu(self, values=["linear", "exponential"], variable=self.curve_var).grid(row=row, column=1, padx=15)
        row += 1

        ctk.CTkLabel(self, text="Controller", font=("", 16, "bold")).grid(row=row, column=0, columnspan=2, pady=(20, 5), padx=15, sticky="w")
        row += 1

        self.mode_var = ctk.StringVar(value=config.get("controller", "mode", default="auto"))
        ctk.CTkLabel(self, text="Output mode").grid(row=row, column=0, padx=15, sticky="w")
        ctk.CTkOptionMenu(self, values=["auto", "gamepad", "keyboard"], variable=self.mode_var).grid(row=row, column=1, padx=15)
        row += 1

        ctk.CTkLabel(self, text="Extras", font=("", 16, "bold")).grid(row=row, column=0, columnspan=2, pady=(20, 5), padx=15, sticky="w")
        row += 1

        self.voice_var = ctk.BooleanVar(value=config.get("voice", "enabled", default=False))
        ctk.CTkCheckBox(self, text="Enable voice commands", variable=self.voice_var).grid(row=row, column=0, columnspan=2, padx=15, pady=5, sticky="w")
        row += 1

        self.analytics_var = ctk.BooleanVar(value=config.get("analytics", "enabled", default=False))
        ctk.CTkCheckBox(self, text="Enable session analytics (CSV + chart)", variable=self.analytics_var).grid(row=row, column=0, columnspan=2, padx=15, pady=5, sticky="w")
        row += 1

        ctk.CTkButton(self, text="Save & Close", command=self._save).grid(row=row, column=0, columnspan=2, pady=25)

    def _slider_row(self, label, var, lo, hi, row):
        ctk.CTkLabel(self, text=label).grid(row=row, column=0, padx=15, sticky="w")
        ctk.CTkSlider(self, from_=lo, to=hi, variable=var).grid(row=row, column=1, padx=15)

    def _save(self):
        config.set("steering", "dead_zone_degrees", self.dead_zone_var.get(), save=False)
        config.set("steering", "max_angle_degrees", self.max_angle_var.get(), save=False)
        config.set("steering", "smoothing_factor", self.smoothing_var.get(), save=False)
        config.set("steering", "response_curve", self.curve_var.get(), save=False)
        config.set("controller", "mode", self.mode_var.get(), save=False)
        config.set("voice", "enabled", self.voice_var.get(), save=False)
        config.set("analytics", "enabled", self.analytics_var.get(), save=True)
        self.destroy()


if __name__ == "__main__":
    SettingsWindow().mainloop()
