#!/usr/bin/env python3
"""
VEH Bulk Generator Bot — One file per series.
Send series list → bot sends one .txt per series (0000-9999 each).
"""

import os
import re
import io
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# ═══════════════════════════════════════════════════════
#  ⚙️  CONFIG
# ═══════════════════════════════════════════════════════
BOT_TOKEN = "8945339641:AAHMCE0qtJX6TIlit9fMlWr-mVhnLploovw"
ALLOWED_USERS = []

NUM_START = 0
NUM_END = 9999
# ═══════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_allowed(user_id):
    return not ALLOWED_USERS or user_id in ALLOWED_USERS


def parse_series(series):
    series = series.strip().upper().replace(" ", "")
    m = re.match(r"^([A-Z]{2})(\d{1,2})([A-Z]{1,3})$", series)
    if not m:
        return None
    return m.groups()


def build_series_file(series):
    parsed = parse_series(series)
    if not parsed:
        return None
    state, rto, ser = parsed
    lines = []
    for i in range(NUM_START, NUM_END + 1):
        lines.append(f"{state}{rto}{ser}{i:04d}")
    return lines


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    text = (
        "🚗  *VEH Bulk Generator*\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Send a list of series → bot sends back\n"
        "*one file per series* (10,000 numbers each).\n\n"
        "*Example input*\n"
        "```\n"
        "GJ01WY\n"
        "GJ01WW\n"
        "GJ01WQ\n"
        "GJ06RD\n"
        "```\n\n"
        "*Example output*\n"
        "📁 `GJ01WY.txt` — 10,000 lines\n"
        "📁 `GJ01WW.txt` — 10,000 lines\n"
        "📁 `GJ01WQ.txt` — 10,000 lines\n"
        "📁 `GJ06RD.txt` — 10,000 lines\n\n"
        "*Commands*\n"
        "`/bulk` — start\n"
        "`/help` — this menu"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def bulk_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    await update.message.reply_text(
        "📋 *Send your series list* — one per line:\n\n"
        "```\nGJ01WY\nGJ01WW\nGJ01WQ\nGJ01WX\nGJ06RD\nGJ01WU\n```",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    lines = [l.strip().upper() for l in update.message.text.strip().split("\n") if l.strip()]

    valid = []
    invalid = []
    for line in lines:
        if parse_series(line):
            valid.append(line)
        else:
            invalid.append(line)

    if not valid:
        await update.message.reply_text(
            "❌ No valid series found.\n"
            "Format: `GJ01WY` (2 letters + 1-2 digits + 1-3 letters)",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"⏳ Generating *{len(valid)}* files × 10,000 lines each...\n"
        f"📊 Total: *{len(valid) * 10000:,}* numbers",
        parse_mode="Markdown"
    )

    sent = 0
    failed = 0

    for series in valid:
        numbers = build_series_file(series)
        if not numbers:
            failed += 1
            continue

        content = "\n".join(numbers)
        filename = f"{series}.txt"

        try:
            buf = io.BytesIO(content.encode("utf-8"))
            buf.name = filename
            await update.message.reply_document(
                document=buf,
                filename=filename,
                caption=f"📁 *{filename}* — {len(numbers):,} lines"
            )
            sent += 1
        except Exception as e:
            logger.error(f"Send error for {series}: {e}")
            await update.message.reply_text(f"❌ Failed: `{series}` — {str(e)[:80]}", parse_mode="Markdown")
            failed += 1

        # Small delay between files to avoid Telegram rate limit
        await asyncio.sleep(1.2)

    summary = (
        f"✅ *Bulk job complete!*\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📁 Files sent: *{sent}*\n"
        f"📊 Total lines: *{sent * 10000:,}*\n"
    )
    if invalid:
        summary += f"⚠️ Invalid series skipped: *{len(invalid)}*\n"
    if failed:
        summary += f"❌ Failed to send: *{failed}*\n"

    await update.message.reply_text(summary, parse_mode="Markdown")


async def post_init(app: Application):
    logger.info("Bot ready")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("bulk", bulk_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚗 VEH Bulk Generator Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
