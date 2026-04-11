import asyncio
import html
import os
from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def _clean(text: str, limit: int | None = None) -> str:
    text = (text or "—").strip()
    text = " ".join(text.split())
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return html.escape(text)


def build_message(project: dict) -> str:
    title = _clean(project.get("title"))
    url = project.get("url", "").strip()
    details = _clean(project.get("details"), 450)
    published_at = _clean(project.get("published_at"))
    budget = _clean(project.get("budget"))
    execution_duration = _clean(project.get("execution_duration"))
    hiring_rate = _clean(project.get("hiring_rate"))
    applicants_count = _clean(project.get("applicants_count"))

    lines = [
        "🚀 <b>مشروع جديد على مستقل</b>",
        "",
        f"🧩 <b>العنوان:</b> {title}",
        "",
        f"📝 <b>التفاصيل:</b> {details}",
        "",
        "📊 <b>معلومات سريعة</b>",
        f"💰 <b>الميزانية:</b> {budget}",
        f"⏳ <b>مدة التنفيذ:</b> {execution_duration}",
        f"📅 <b>تاريخ النشر:</b> {published_at}",
        f"📈 <b>معدل التوظيف:</b> {hiring_rate}",
        f"👥 <b>عدد المتقدمين:</b> {applicants_count}",
    ]

    if url:
        safe_url = html.escape(url, quote=True)
        lines += ["", f'🔗 <a href="{safe_url}">فتح المشروع</a>']

    return "\n".join(lines)


async def _send(text: str):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def notify(project: dict):
    message = build_message(project)
    asyncio.run(_send(message))