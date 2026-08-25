def validate_social_links(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in value.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(
                f"Некорректная строка: «{line}».\n"
                "Формат: <code>Название: ссылка</code>"
            )
        name, url = line.split(":", 1)
        name, url = name.strip(), url.strip()
        if not name or not url:
            raise ValueError(f"Некорректная строка: «{line}»")
        result[name] = url

    if not result:
        raise ValueError("Добавьте хотя бы одну ссылку")
    return result