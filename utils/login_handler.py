from pathlib import Path

import dash
import yaml

from utils.get_users import get_users


# Accounts and roles should be read from the DB

ACCOUNTS = get_users()


def _load_page_config():
    CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "pages.yaml"
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    role_groups = config.get("roles", {})
    page_config = {}
    page_names = {}

    for page_path, page_info in (config.get("pages") or {}).items():
        access_level = page_info.get("access_level")
        access_role_group = page_info.get("access_role_group")

        if access_level is None and access_role_group:
            access_level = role_groups.get(access_role_group, [])

        page_config[page_path] = {
            "access_level": list(dict.fromkeys(access_level or [])),
        }

        if page_info.get("name"):
            page_names[page_path] = page_info["name"]

    return page_config, page_names


restricted_page, pages_name = _load_page_config()


def get_accessible_pages_by_role(role):
    accessible_pages = {}
    for page, config in restricted_page.items():
        if role in config.get("access_level", []):
            accessible_pages[pages_name.get(page, page)] = page
    return accessible_pages


def require_login(page, **kwargs):
    """Mark a registered Dash page as restricted.

    Page modules should call this immediately after dash.register_page().
    If Dash has not registered the page yet, raise a clear error instead of
    silently doing nothing and leaving the page unprotected.
    """
    if page not in dash.page_registry:
        raise RuntimeError(
            "Page {!r} is not registered. Call dash.register_page() before require_login().".format(page)
        )

    path = dash.page_registry[page]["path"]
    existing_config = restricted_page.get(path, {})
    access_level = kwargs.get("access_level", existing_config.get("access_level", []))

    restricted_page[path] = {
        **existing_config,
        "restricted": True,
        "access_level": access_level,
    }


def has_access(user, path):
    if not user or not getattr(user, "is_authenticated", False):
        return False

    account = ACCOUNTS.get(user.id)
    if not account:
        return False

    page_config = restricted_page.get(path)
    if not page_config:
        return False

    return account.get("role") in page_config.get("access_level", [])
