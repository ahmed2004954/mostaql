import asyncio
import html
import os

from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def build_message(project: dict) -> str:
    title = html.escape(project.get("title", "—"))
    url = project.get("url", "")
    details = html.escape(project.get("details", "—"))
    published_at = html.escape(project.get("published_at", "—"))
    budget = html.escape(project.get("budget", "—"))
    execution_duration = html.escape(project.get("execution_duration", "—"))
    hiring_rate = html.escape(project.get("hiring_rate", "—"))
    applicants_count = html.escape(project.get("applicants_count", "—"))

    return (
        f"🆕 <b>مشروع جديد على مستقل — برمجة</b>\n\n"
        f"📌 <b>{title}</b>\n"
        f"📝 <b>تفاصيل المشروع:</b> {details}\n"
        f"🕒 <b>تاريخ النشر:</b> {published_at}\n"
        f"💰 <b>الميزانية:</b> {budget}\n"
        f"⏳ <b>مدة التنفيذ:</b> {execution_duration}\n"
        f"📊 <b>معدل التوظيف:</b> {hiring_rate}\n"
        f"👥 <b>عدد المتقدمين:</b> {applicants_count}\n"
        f"🔗 <a href='{url}'>فتح المشروع</a>"
    )


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
