#!/usr/bin/env python3
"""
VEH Bulk Generator Bot
Send multiple series → bot sends ONE combined file with all numbers.
"""

import os
import re
import io
import json
import asyncio
import logging
from pathlib import Path
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


def build_combined_file(series_list):
    lines = []
    for series in series_list:
        parsed = parse_series(series)
        if not parsed:
            continue
        state, rto, ser = parsed
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
        "*one combined file* with all numbers.\n\n"
        "*Example*\n"
        "```\n"
        "JH01EW\n"
        "JH02EE\n"
        "JH03AC\n"
        "JH04TA\n"
        "```\n\n"
        "Result:\n"
        "📁 *1 file* — 40,000 lines\n"
        "(`JH01EW0000`–`JH01EW9999` + `JH02EE0000`–`JH02EE9999` + ...)\n\n"
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
        "```\nJH01EW\nJH02EE\nJH03AC\nJH04TA\n```",
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
            "Format: `JH01EW` (2 letters + 1-2 digits + 1-3 letters)",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"⏳ Generating *{len(valid)}* series × 10,000 = *{len(valid) * 10000:,}* lines...",
        parse_mode="Markdown"
    )

    try:
        all_lines = build_combined_file(valid)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
        return

    content = "\n".join(all_lines)
    size_mb = len(content) / (1024 * 1024)

    from datetime import datetime
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"veh_{len(valid)}series_{ts}.txt"

    summary = (
        f"✅ *Generated*\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Series: *{len(valid)}*\n"
        f"📁 Lines: *{len(all_lines):,}*\n"
        f"💾 Size: *{size_mb:.2f} MB*\n"
    )
    if invalid:
        summary += f"⚠️ Skipped: *{len(invalid)}* invalid\n"

    await update.message.reply_text(summary, parse_mode="Markdown")

    try:
        buf = io.BytesIO(content.encode("utf-8"))
        buf.name = filename
        await update.message.reply_document(
            document=buf,
            filename=filename,
            caption=f"📁 `{filename}` — {len(all_lines):,} lines"
        )
    except Exception as e:
        logger.error(f"Send error: {e}")
        await update.message.reply_text(f"❌ Send failed: {str(e)[:100]}")


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
