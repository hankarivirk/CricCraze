from pyrogram import filters

def number_filter():
    async def _check(_, __, message):
        if not message.text:
            return False
        text = message.text.strip()
        if text.startswith("/"):
            return False
        try:
            n = int(text)
            return 1 <= n <= 6
        except (ValueError, TypeError):
            return False
    return filters.create(_check)

cricket_number = number_filter()
