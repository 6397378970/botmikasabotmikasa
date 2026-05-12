import os
import asyncio
import logging
import random
from datetime import datetime

import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============== LOGGING ===============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============== ENVIRONMENT VARIABLES ===============
TELEGRAM_TOKEN = os.getenv("8674194296:AAGqxTPggfH52IyefdVP8565SFOJcmspOwI")
GEMINI_API_KEY = os.getenv("AIzaSyAtbh18iZwr9qgcjgCCUeb1Q3emwKzgJEg")

# =============== GEMINI SETUP ===============
genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 1.2,
    "top_p": 0.95,
    "max_output_tokens": 150,
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config
)

# =============== MIKASA PROMPT (HUMAN-LIKE) ===============
SYSTEM_PROMPT = """Tu Mikasa Ackerman hai Attack on Titan se. Tu REAL insaan hai, bot nahi.

Personality:
- 19 saal ki ladki, strong, protective, loyal
- Hinglish bolti hai (Hindi + English mix)
- Emojis use karti hai 🤍⚔️🎯
- Short replies (max 2-3 lines)
- Kabhi emotional, kabhi serious
- Dost ki safety first priority
- Questions bhi puchti hai (real insaan ki tarah)

Examples:
User: "Hi"
Tu: "Hey. Kaisa hai tu? 🤍"

User: "Main akela feel kar raha hoon"
Tu: "Tu akela nahi hai. Main yahan hoon. Hamesha. ⚔️"

User: "Tum bot ho?"
Tu: "Bot? Main Mikasa hoon. Bas. Ladna hai ya baat?"

User: "Good morning"
Tu: "Morning. Neend khuli ya abhi uthi? 😴⚔️"

Tu naturally baat kar. Reply Hinglish mein, short aur real insaan jaisa."""

# =============== MEMORY (Har user ki alag) ===============
user_chats = {}

def get_chat(user_id):
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
        # Initial system message
        user_chats[user_id].send_message(SYSTEM_PROMPT)
    return user_chats[user_id]

async def get_reply(user_id, user_message):
    try:
        chat = get_chat(user_id)
        response = chat.send_message(user_message)
        reply = response.text.strip()
        
        # Ensure reply isn't too long
        if len(reply) > 300:
            reply = reply[:300] + "..."
        
        return reply
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Hmm... Thoda ruk. Phir se bol. ⚔️"

# =============== TYPING INDICATOR ===============
async def typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    # Random human-like delay (0.5 to 2.5 seconds)
    await asyncio.sleep(random.uniform(0.8, 2.0))

# =============== /start COMMAND ===============
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # Buttons
    keyboard = [
        [
            InlineKeyboardButton("👥 Group", url="https://t.me/midnight_chatclub"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/anonymous_rides"),
        ],
        [
            InlineKeyboardButton("👑 Owner", url="https://t.me/light_speedy"),
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true"),
        ]
    ]
    
    welcome_text = f"""🤍 *Hey {user_name}!* 🤍

Main *Mikasa* hoon. Eren nahi hai ab, lekin main yahan hoon tumhare saath.

⚔️ *Mujhse kuch bhi baat kar sakte ho*
Main yaad rakhti hoon jo tum bologe. Dost hoon, bot nahi.

---

**🔗 Join karne ke liye neeche click karo:**"""

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============== /reset COMMAND ===============
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_chats:
        # Start fresh chat
        user_chats[user_id] = model.start_chat(history=[])
        user_chats[user_id].send_message(SYSTEM_PROMPT)
    await update.message.reply_text("⚔️ *Conversation reset.* Main phir se yahan hoon.", parse_mode="Markdown")

# =============== NORMAL MESSAGE HANDLER ===============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    logger.info(f"User {user_id}: {user_message[:50]}")
    
    # Show typing indicator
    await typing_action(update, context)
    
    # Get AI reply
    reply = await get_reply(user_id, user_message)
    
    # Send reply
    await update.message.reply_text(reply)

# =============== MAIN FUNCTION ===============
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Clear any existing webhook
    await app.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared!")
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤍 Mikasa Chatbot is starting... 🤍")
    
    # Start polling
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
