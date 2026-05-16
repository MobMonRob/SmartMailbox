import http
import tomllib
import logging
from pathlib import Path
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


def _get_config_value(
    data: dict[str, Any],
    key: str,
    default: str | int | float,
    expected_type: type,
    validator: Callable[[Any], bool],
) -> int | str | float:
    if key not in data:
        logger.warning(f"Missing configuration key: '{key}'. Using default: {default}.")
        return default

    value: str | int | float = data[key]

    if not isinstance(value, expected_type):
        logger.error(
            f"Configuration key '{key}' must be of type {expected_type.__name__}. Found {type(value).__name__}. Using default: {default}."
        )
        return default

    if validator and not validator(value):
        logger.error(
            f"Configuration value for '{key}' is invalid: {value}. Using default: {default}."
        )
        return default

    assert isinstance(value, str) or isinstance(value, int) or isinstance(value, float), "Only str, int and float are supported."

    return value


class Config:
    _instance = None

    # Default values
    number_of_images = 10
    warm_up_time_in_sec: float = 2.
    img_format = "jpg"
    img_name_prefix = "capture"
    archive_name_prefix = "images_archive"
    images_endpoint_url = "http://localhost:8000/images"
    household_id = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = Path(__file__).parent.parent / "config.toml"
        data: Dict[str, str | int] = {}

        if not config_path.exists():
            logger.warning(
                f"Config file not found at {config_path}. Using default values."
            )
            return

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse config file: {e}. Using default values.")

        self.number_of_images = _get_config_value(
            data,
            "number_of_images",
            self.number_of_images,
            int,
            lambda x: x > 0,
        )
        self.img_format = _get_config_value(
            data,
            "img_format",
            self.img_format,
            str,
            lambda x: x.lower() in ["jpeg", "png"],  # jpeg / png / bmp / gif
        )
        self.img_name_prefix = _get_config_value(
            data,
            "img_name_prefix",
            self.img_name_prefix,
            str,
            lambda x: len(x) > 0,
        )
        self.archive_name_prefix = _get_config_value(
            data,
            "archive_name_prefix",
            self.archive_name_prefix,
            str,
            lambda x: len(x) > 0,
        )
        self.images_endpoint_url = _get_config_value(
            data,
            "images_endpoint_url",
            self.images_endpoint_url,
            str,
            lambda x: len(x) > 0,
        )
        self.warm_up_time_in_sec = _get_config_value(
            data,
            "warm_up_time_in_sec",
            self.warm_up_time_in_sec,
            float,
            lambda x: x >= 0,
        )
        self.household_id = _get_config_value(
            data,
            "household_id",
            self.household_id,
            int,
            lambda x: x > 0,
        )


# Global instance
cfg = Config()
