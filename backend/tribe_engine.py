"""Wrapper around TRIBE v2 that turns predicted fMRI into an engagement score.

Engagement proxy = L2 norm of predicted BOLD across all cortical vertices per
second. Higher magnitude = stronger differential cortical response = more
engaging stimulus. Normalized to 0-100 against an internal reference scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class EngagementResult:
    score: float
    curve: list[float]
    peak_seconds: list[int]
    duration_s: int
    n_vertices: int


class TribeEngine:
    REFERENCE_SCALE = 8.0

    def __init__(self, cache_folder: str = "./cache"):
        self._ensure_tribev2_importable()
        from tribev2.demo_utils import TribeModel

        self.cache_folder = Path(cache_folder)
        self.cache_folder.mkdir(parents=True, exist_ok=True)
        self.model = TribeModel.from_pretrained(
            "facebook/tribev2", cache_folder=self.cache_folder
        )

    @staticmethod
    def _ensure_tribev2_importable() -> None:
        import sys

        try:
            import tribev2.demo_utils  # noqa: F401
            return
        except ModuleNotFoundError:
            pass

        candidates = [
            "/content/tribev2",
            str(Path(__file__).resolve().parent.parent.parent / "tribev2"),
        ]
        for path in candidates:
            if (Path(path) / "tribev2" / "demo_utils.py").exists():
                if path not in sys.path:
                    sys.path.insert(0, path)
                return

    def analyze(self, video_path: str | Path) -> EngagementResult:
        df = self.model.get_events_dataframe(video_path=str(video_path))
        preds, _ = self.model.predict(events=df)

        preds = np.asarray(preds)
        magnitudes = np.linalg.norm(preds, axis=1)
        curve = self._to_0_100(magnitudes)
        score = float(np.mean(curve))
        peaks = self._top_peaks(curve, k=5)

        return EngagementResult(
            score=round(score, 2),
            curve=[round(float(x), 2) for x in curve],
            peak_seconds=peaks,
            duration_s=int(preds.shape[0]),
            n_vertices=int(preds.shape[1]),
        )

    def _to_0_100(self, magnitudes: np.ndarray) -> np.ndarray:
        scaled = magnitudes / self.REFERENCE_SCALE * 100.0
        return np.clip(scaled, 0.0, 100.0)

    def _top_peaks(self, curve: np.ndarray, k: int) -> list[int]:
        if len(curve) <= k:
            return list(range(len(curve)))
        return sorted(int(i) for i in np.argsort(curve)[-k:])
