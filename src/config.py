"""配置加载：YAML + .env（设计文档 §4）。"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def _load_yaml(name: str) -> dict:
    path = ROOT / "config" / name
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Settings:
    """轻量配置对象：YAML 分层 + .env 凭据。"""

    def __init__(self) -> None:
        load_dotenv(ROOT / ".env")
        self.raw: dict = _load_yaml("settings.yaml")
        self.models: dict = _load_yaml("models.yaml")

    # ── 嵌套取值助手 ──
    def get(self, dotted: str, default=None):
        node = self.raw
        for key in dotted.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    # ── 凭据（来自 .env）──
    @property
    def api_key(self) -> str:
        return os.environ.get("API_KEY", "")

    @property
    def base_url(self) -> str:
        return os.environ.get("BASE_URL", "")

    @property
    def qwen_model(self) -> str:
        return os.environ.get("QWEN_MODEL", self.models.get("default_model", ""))

    @property
    def qq_app_id(self) -> str:
        return os.environ.get("app_ID", os.environ.get("QQ_APP_ID", ""))

    @property
    def qq_app_secret(self) -> str:
        return os.environ.get("app_SECRET", os.environ.get("QQ_APP_SECRET", ""))

    # ── 路径 ──
    @property
    def root(self) -> Path:
        return ROOT
