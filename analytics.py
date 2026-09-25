"""
Optional per-session analytics: samples steering/gear/fps at a configurable
interval and, on exit, writes a CSV plus a quick summary chart. Off by
default so it costs nothing unless explicitly enabled in config.
"""

import csv
import time
from pathlib import Path

from config import config
from logger_setup import get_logger

log = get_logger(__name__)


class SessionAnalytics:
    def __init__(self):
        self.enabled = config.get("analytics", "enabled", default=False)
        self.sample_every = config.get("analytics", "sample_every_n_frames", default=10)
        self.export_dir = Path(config.get("analytics", "export_dir", default=str(Path.home() / ".gaming_steering" / "sessions")))
        self._frame_count = 0
        self._rows = []
        self._session_start = time.time()

    def maybe_sample(self, fps, steering_angle, strength, gear, throttle_state):
        if not self.enabled:
            return
        self._frame_count += 1
        if self._frame_count % self.sample_every != 0:
            return
        self._rows.append({
            "t": round(time.time() - self._session_start, 2),
            "fps": round(fps, 1),
            "angle_degrees": round(steering_angle, 1),
            "strength": round(strength, 3),
            "gear": gear,
            "throttle_state": throttle_state,
        })

    def export(self):
        if not self.enabled or not self._rows:
            return None
        self.export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = self.export_dir / f"session_{timestamp}.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self._rows[0].keys()))
            writer.writeheader()
            writer.writerows(self._rows)
        log.info(f"Session analytics written to {csv_path}")

        self._maybe_plot(csv_path.with_suffix(".png"))
        return csv_path

    def _maybe_plot(self, png_path):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            log.debug("matplotlib not installed; skipping summary chart")
            return

        times = [r["t"] for r in self._rows]
        angles = [r["angle_degrees"] for r in self._rows]
        fps_values = [r["fps"] for r in self._rows]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        ax1.plot(times, angles)
        ax1.set_ylabel("Steering angle (deg)")
        ax1.set_title("Session summary")

        ax2.plot(times, fps_values)
        ax2.set_ylabel("FPS")
        ax2.set_xlabel("Time (s)")

        fig.tight_layout()
        fig.savefig(png_path)
        plt.close(fig)
        log.info(f"Session summary chart written to {png_path}")
