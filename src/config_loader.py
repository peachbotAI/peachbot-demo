# src/config_loader.py

import yaml
import os


class ConfigLoader:
    def __init__(self, base_dir=None):
        """
        base_dir = project root (auto-detected if not provided)
        """
        if base_dir is None:
            # 🔥 SAFE: resolve relative to THIS FILE (not cwd)
            self.base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )
        else:
            self.base_dir = base_dir

        self.cache = {}

    # =========================
    # LOAD SINGLE FILE
    # =========================
    def load(self, *args):
        """
        Supports:
        - load("thresholds.yaml")              → defaults to config/
        - load("config", "thresholds.yaml")    → explicit
        """

        if len(args) == 1:
            folder = "config"
            filename = args[0]
        elif len(args) == 2:
            folder, filename = args
        else:
            raise ValueError("load() expects 1 or 2 arguments")

        cache_key = os.path.join(folder, filename)

        if cache_key in self.cache:
            return self.cache[cache_key]

        path = os.path.join(self.base_dir, folder, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Config not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        self.cache[cache_key] = data
        return data

    # =========================
    # LOAD ALL FILES IN FOLDER
    # =========================
    def load_all(self, folder):

        cache_key = f"ALL::{folder}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        folder_path = os.path.join(self.base_dir, folder)

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        all_rules = []

        for file in os.listdir(folder_path):
            if file.endswith(".yaml") or file.endswith(".yml"):

                full_path = os.path.join(folder_path, file)

                with open(full_path, "r") as f:
                    content = yaml.safe_load(f)

                    if content and "rules" in content:
                        all_rules.extend(content["rules"])

        self.cache[cache_key] = all_rules
        return all_rules


# Global singleton
config = ConfigLoader()