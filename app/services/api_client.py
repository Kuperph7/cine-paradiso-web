import requests
from flask import current_app


def api_request(method, path, **kwargs):
    base_url = current_app.config["API_BASE_URL"].rstrip("/")
    url = f"{base_url}/{path.lstrip('/')}"
    return requests.request(method, url, timeout=10, **kwargs)


def api_get(path, **kwargs):
    return api_request("GET", path, **kwargs)


def api_post(path, **kwargs):
    return api_request("POST", path, **kwargs)


def api_patch(path, **kwargs):
    return api_request("PATCH", path, **kwargs)


def api_delete(path, **kwargs):
    return api_request("DELETE", path, **kwargs)

