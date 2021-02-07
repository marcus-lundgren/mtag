from datetime import datetime


def expand_tags(url: str, dt: datetime) -> str:
    if url is None:
        return ""

    url = url.replace("{{date}}", dt.strftime('%Y-%m-%d'))
    return url
