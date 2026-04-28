import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from telegram.error import TelegramError

import config
import database as db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ConversationHandler states
WAITING_UPI = 1

# ── Helpers ──────────────────────────────────────────────────

def is_admin(user_id):
    return user_id in config.ADMIN_IDS

def get_all_required(context=None):
    """Config + DB channels/groups combine karke return karo"""
    items = []
    for ch in config.REQUIRED_CHANNELS:
        items.append({**ch, "type": "channel"})
    for gr in config.REQUIRED_GROUPS:
        items.append({**gr, "type": "group"})
    # DB se dynamic channels
    for row in db.get_db_channels():
        items.append({"name": row["name"], "username": row["username"],
                      "url": row["url"], "type": row["type"]})
    return items

async def check_membership(bot, user_id):
    """Sabhi channels/groups check karo"""
    not_joined = []
    for item in get_all_required():
        try:
            member = await bot.get_chat_member(item["username"], user_id)
            if member.status in ("left", "kicked", "banned"):
                not_joined.append(item)
        except TelegramError:
            not_joined.append(item)
    return not_joined

def join_keyboard():
    """Sabhi channels ke buttons + Joined button"""
    buttons = []
    for item in get_all_required():
        emoji = "📢" if item["type"] == "channel" else "👥"
        buttons.append([InlineKeyboardButton(
            f"{emoji} {item['name']} Join Karo",
            url=item["url"]
        )])
    buttons.append([InlineKeyboardButton("✅ Maine Join Kar Liya!", callback_data="verify_join")])
    return InlineKeyboardMarkup(buttons)

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance",    callback_data="balance"),
         InlineKeyboardButton("👥 Refer Link", callback_data="refer")],
        [InlineKeyboardButton("💳 Withdraw",   callback_data="withdraw"),
         InlineKeyboardButton("📊 My Stats",   callback_data="stats")],
        [InlineKeyboardButton("❓ Help",        callback_data="help")],
    ])

# ── /start ───────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    args  = context.args

    referred_by = None
    if args:
        try:
            referred_by = int(args[0])
            if referred_by == user.id:
                referred_by = None
        except ValueError:
            pass

    # User register karo
    db.add_user(user.id, user.username or "", user.full_name, referred_by)

    db_user = db.get_user(user.id)

    # Agar pehle se join bonus mil chuka hai
    if db_user["join_bonus"]:
        await update.message.reply_text(
            config.ALREADY_MEMBER_MSG.format(
                balance=db_user["balance"],
                refer_link=f"https://t.me/{context.bot.username}?start={user.id}"
            ),
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    # Channels join karne ko kaho
    await update.message.reply_text(
        config.WELCOME_MSG.format(
            name=user.first_name,
            join_bonus=config.JOIN_BONUS,
            refer_bonus=config.REFER_BONUS,
            min_withdraw=config.MIN_WITHDRAW
        ),
        parse_mode="Markdown",
        reply_markup=join_keyboard()
    )

# ── Verify Join ──────────────────────────────────────────────

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user    = query.from_user
    await query.answer()

    not_joined = await check_membership(context.bot, user.id)

    if not_joined:
        names = "\n".join([f"❌ {i['name']}" for i in not_joined])
        await query.edit_message_text(
            f"⚠️ *Aapne yeh join nahi kiye:*\n\n{names}\n\nPehle join karo phir ✅ button dabao!",
            parse_mode="Markdown",
            reply_markup=join_keyboard()
        )
        return

    db_user = db.get_user(user.id)

    # Join bonus nahi mila abhi tak
    if not db_user["join_bonus"]:
        db.give_join_bonus(user.id, config.JOIN_BONUS)
        refer_link = f"https://t.me/{context.bot.username}?start={user.id}"

        # Referrer ko credit karo
        if db_user["referred_by"]:
            referrer_id = db_user["referred_by"]
            bonus_given = db.add_refer_count(referrer_id, config.REFER_BONUS, config.REFERS_NEEDED)
            referrer_db = db.get_user(referrer_id)
            if referrer_db:
                try:
                    msg = f"🎉 *{user.first_name}* ne aapka refer use kiya!\n👥 Total Refers: {referrer_db['refer_count']}"
                    if bonus_given:
                        msg += f"\n\n💰 *₹{config.REFER_BONUS} Bonus Mila! 10 Refers Complete!*"
                    await context.bot.send_message(referrer_id, msg, parse_mode="Markdown")
                except Exception:
                    pass

        await query.edit_message_text(
            config.JOIN_SUCCESS_MSG.format(
                name=user.first_name,
                bonus=config.JOIN_BONUS,
                refer_link=refer_link
            ),
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        await query.edit_message_text(
            "✅ Aap pehle se verified hain!",
            reply_markup=main_keyboard()
        )

# ── /balance ─────────────────────────────────────────────────

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)
    if not db_user:
        await update.message.reply_text("Pehle /start karo!")
        return
    refer_link = f"https://t.me/{context.bot.username}?start={user.id}"
    text = (
        f"💰 *Aapka Balance*\n\n"
        f"├ Current Balance: ₹{db_user['balance']:.2f}\n"
        f"├ Total Earned:    ₹{db_user['total_earned']:.2f}\n"
        f"├ Total Refers:    {db_user['refer_count']}\n"
        f"└ Min Withdraw:    ₹{config.MIN_WITHDRAW}\n\n"
        f"🔗 Refer Link:\n`{refer_link}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def balance_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user    = query.from_user
    db_user = db.get_user(user.id)
    if not db_user:
        await query.edit_message_text("Pehle /start karo!")
        return
    refer_link = f"https://t.me/{context.bot.username}?start={user.id}"
    text = (
        f"💰 *Aapka Balance*\n\n"
        f"├ Current Balance: ₹{db_user['balance']:.2f}\n"
        f"├ Total Earned:    ₹{db_user['total_earned']:.2f}\n"
        f"├ Total Refers:    {db_user['refer_count']}\n"
        f"└ Min Withdraw:    ₹{config.MIN_WITHDRAW}\n\n"
        f"🔗 Refer Link:\n`{refer_link}`"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ── /refer ───────────────────────────────────────────────────

async def refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)
    if not db_user:
        await update.message.reply_text("Pehle /start karo!")
        return
    refer_link = f"https://t.me/{context.bot.username}?start={user.id}"
    next_bonus = config.REFERS_NEEDED - (db_user["refer_count"] % config.REFERS_NEEDED)
    text = (
        f"👥 *Refer & Earn*\n\n"
        f"🔗 Aapka Link:\n`{refer_link}`\n\n"
        f"📊 *Stats:*\n"
        f"├ Total Refers:    {db_user['refer_count']}\n"
        f"├ Next Bonus Mein: {next_bonus} refers\n"
        f"└ Har 10 Refers:   ₹{config.REFER_BONUS}\n\n"
        f"💡 Yeh link share karo apne dosto ke saath!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def refer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user    = query.from_user
    db_user = db.get_user(user.id)
    if not db_user:
        await query.edit_message_text("Pehle /start karo!")
        return
    refer_link = f"https://t.me/{context.bot.username}?start={user.id}"
    next_bonus = config.REFERS_NEEDED - (db_user["refer_count"] % config.REFERS_NEEDED)
    text = (
        f"👥 *Refer & Earn*\n\n"
        f"🔗 Aapka Link:\n`{refer_link}`\n\n"
        f"📊 *Stats:*\n"
        f"├ Total Refers:    {db_user['refer_count']}\n"
        f"├ Next Bonus Mein: {next_bonus} refers\n"
        f"└ Har 10 Refers:   ₹{config.REFER_BONUS}\n\n"
        f"💡 Yeh link share karo apne dosto ke saath!"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ── /withdraw ────────────────────────────────────────────────

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user    = query.from_user
    db_user = db.get_user(user.id)
    if not db_user:
        await query.edit_message_text("Pehle /start karo!")
        return
    if db_user["balance"] < config.MIN_WITHDRAW:
        await query.edit_message_text(
            f"❌ *Insufficient Balance!*\n\n"
            f"├ Aapka Balance: ₹{db_user['balance']:.2f}\n"
            f"└ Minimum:       ₹{config.MIN_WITHDRAW}\n\n"
            f"Refer karo aur balance badhao!",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return
    await query.edit_message_text(
        f"💳 *Withdrawal Request*\n\n"
        f"Aapka Balance: ₹{db_user['balance']:.2f}\n\n"
        f"📲 Apna UPI ID bhejo (e.g. name@upi):",
        parse_mode="Markdown"
    )
    context.user_data["withdrawing"] = True
    return WAITING_UPI

async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    db_user = db.get_user(user.id)
    if not db_user:
        await update.message.reply_text("Pehle /start karo!")
        return ConversationHandler.END
    if db_user["balance"] < config.MIN_WITHDRAW:
        await update.message.reply_text(
            f"❌ Balance kam hai!\nAapka: ₹{db_user['balance']:.2f}\nMinimum: ₹{config.MIN_WITHDRAW}"
        )
        return ConversationHandler.END
    await update.message.reply_text(
        f"💳 Withdrawal ke liye apna UPI ID bhejo:\n(Balance: ₹{db_user['balance']:.2f})"
    )
    return WAITING_UPI

async def receive_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    upi_id  = update.message.text.strip()
    db_user = db.get_user(user.id)

    if not db_user or db_user["balance"] < config.MIN_WITHDRAW:
        await update.message.reply_text("❌ Balance nahi hai!", reply_markup=main_keyboard())
        return ConversationHandler.END

    amount = db_user["balance"]
    db.create_withdrawal(user.id, amount, upi_id)
    db.deduct_balance(user.id, amount)

    await update.message.reply_text(
        f"✅ *Withdrawal Request Submit Ho Gayi!*\n\n"
        f"├ Amount: ₹{amount:.2f}\n"
        f"├ UPI ID: `{upi_id}`\n"
        f"└ Status: Pending\n\n"
        f"Admin 24 ghante mein process karega!",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

    # Admin ko notify karo
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"💳 *New Withdrawal Request!*\n\n"
                f"├ User: {user.full_name} (@{user.username})\n"
                f"├ ID:   `{user.id}`\n"
                f"├ Amount: ₹{amount:.2f}\n"
                f"└ UPI: `{upi_id}`\n\n"
                f"/pending - Sab requests dekho",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancel ho gaya.", reply_markup=main_keyboard())
    return ConversationHandler.END

# ── Stats & Help ─────────────────────────────────────────────

async def stats_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user    = query.from_user
    db_user = db.get_user(user.id)
    if not db_user:
        return
    withdrawals = db.get_user_withdrawals(user.id)
    w_text = ""
    for w in withdrawals:
        emoji = "✅" if w["status"] == "approved" else ("❌" if w["status"] == "rejected" else "⏳")
        w_text += f"\n{emoji} ₹{w['amount']:.2f} - {w['status']} ({w['requested_at'][:10]})"
    text = (
        f"📊 *Aapki Stats*\n\n"
        f"├ Balance:       ₹{db_user['balance']:.2f}\n"
        f"├ Total Earned:  ₹{db_user['total_earned']:.2f}\n"
        f"├ Total Refers:  {db_user['refer_count']}\n"
        f"└ Joined:        {db_user['joined_at'][:10]}\n\n"
        f"💳 *Last Withdrawals:*{w_text if w_text else chr(10)+'Koi nahi abhi tak'}"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def help_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "❓ *Help & Commands*\n\n"
        "/start - Bot start karo\n"
        "/balance - Balance dekho\n"
        "/refer - Refer link lo\n"
        "/withdraw - Paise nikalo\n"
        "/history - Withdrawal history\n\n"
        f"💰 *Earning:*\n"
        f"├ Join Bonus: ₹{config.JOIN_BONUS}\n"
        f"├ 10 Refers:  ₹{config.REFER_BONUS}\n"
        f"└ Min Withdraw: ₹{config.MIN_WITHDRAW}"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user        = update.effective_user
    withdrawals = db.get_user_withdrawals(user.id)
    if not withdrawals:
        await update.message.reply_text("Koi withdrawal history nahi hai abhi tak.")
        return
    text = "💳 *Aapki Withdrawal History:*\n\n"
    for w in withdrawals:
        emoji = "✅" if w["status"] == "approved" else ("❌" if w["status"] == "rejected" else "⏳")
        text += f"{emoji} ₹{w['amount']:.2f} | {w['upi_id']} | {w['status']} | {w['requested_at'][:10]}\n"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ── ADMIN COMMANDS ───────────────────────────────────────────

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    total_users, total_earned, pending_count, approved_total = db.get_stats()
    text = (
        f"🔧 *Admin Panel*\n\n"
        f"📊 *Stats:*\n"
        f"├ Total Users:     {total_users}\n"
        f"├ Total Earned:    ₹{total_earned:.2f}\n"
        f"├ Pending Withdrawals: {pending_count}\n"
        f"└ Total Paid Out:  ₹{approved_total:.2f}\n\n"
        f"*Commands:*\n"
        f"/pending - Pending withdrawals\n"
        f"/approve [id] - Approve withdrawal\n"
        f"/reject [id] - Reject withdrawal\n"
        f"/addbalance [user_id] [amount]\n"
        f"/removebalance [user_id] [amount]\n"
        f"/userinfo [user_id]\n"
        f"/broadcast [message]\n"
        f"/addchannel @username Name URL\n"
        f"/removechannel @username\n"
        f"/listchannels\n"
        f"/stats"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    total_users, total_earned, pending_count, approved_total = db.get_stats()
    await update.message.reply_text(
        f"📊 *Bot Stats*\n\n"
        f"├ Total Users:     {total_users}\n"
        f"├ Total Earned:    ₹{total_earned:.2f}\n"
        f"├ Pending:         {pending_count}\n"
        f"└ Paid Out:        ₹{approved_total:.2f}",
        parse_mode="Markdown"
    )

async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    rows = db.get_pending_withdrawals()
    if not rows:
        await update.message.reply_text("✅ Koi pending withdrawal nahi hai!")
        return
    for row in rows:
        text = (
            f"⏳ *Withdrawal #{row['id']}*\n\n"
            f"├ User:   {row['full_name']} (@{row['username']})\n"
            f"├ ID:     `{row['user_id']}`\n"
            f"├ Amount: ₹{row['amount']:.2f}\n"
            f"├ UPI:    `{row['upi_id']}`\n"
            f"└ Date:   {row['requested_at'][:16]}\n\n"
            f"/approve {row['id']}  |  /reject {row['id']}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve [withdrawal_id]")
        return
    wid = int(context.args[0])
    conn = db.get_conn()
    row  = conn.execute("SELECT * FROM withdrawals WHERE id=?", (wid,)).fetchone()
    conn.close()
    if not row:
        await update.message.reply_text("❌ ID nahi mila!")
        return
    db.update_withdrawal_status(wid, "approved")
    await update.message.reply_text(f"✅ Withdrawal #{wid} approved!")
    try:
        await context.bot.send_message(
            row["user_id"],
            f"✅ *Withdrawal Approved!*\n\n"
            f"├ Amount: ₹{row['amount']:.2f}\n"
            f"└ UPI: `{row['upi_id']}`\n\n"
            f"Paise aapke account mein bhej diye gaye hain!",
            parse_mode="Markdown"
        )
    except Exception:
        pass

async def reject_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /reject [withdrawal_id]")
        return
    wid = int(context.args[0])
    conn = db.get_conn()
    row  = conn.execute("SELECT * FROM withdrawals WHERE id=?", (wid,)).fetchone()
    conn.close()
    if not row:
        await update.message.reply_text("❌ ID nahi mila!")
        return
    db.update_withdrawal_status(wid, "rejected")
    db.update_balance(row["user_id"], row["amount"])  # Balance wapis karo
    await update.message.reply_text(f"❌ Withdrawal #{wid} rejected! Balance wapis kiya.")
    try:
        await context.bot.send_message(
            row["user_id"],
            f"❌ *Withdrawal Rejected*\n\n"
            f"₹{row['amount']:.2f} aapke balance mein wapis aa gaye.\n"
            f"Admin se contact karo: @admin",
            parse_mode="Markdown"
        )
    except Exception:
        pass

async def addbalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addbalance [user_id] [amount]")
        return
    uid    = int(context.args[0])
    amount = float(context.args[1])
    db.update_balance(uid, amount)
    await update.message.reply_text(f"✅ ₹{amount} add kiya user {uid} ko!")
    try:
        await context.bot.send_message(uid, f"💰 Admin ne ₹{amount} aapke account mein add kiye!")
    except Exception:
        pass

async def removebalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /removebalance [user_id] [amount]")
        return
    uid    = int(context.args[0])
    amount = float(context.args[1])
    db.deduct_balance(uid, amount)
    await update.message.reply_text(f"✅ ₹{amount} remove kiya user {uid} se!")

async def userinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /userinfo [user_id]")
        return
    uid     = int(context.args[0])
    db_user = db.get_user(uid)
    if not db_user:
        await update.message.reply_text("❌ User nahi mila!")
        return
    await update.message.reply_text(
        f"👤 *User Info*\n\n"
        f"├ Name:    {db_user['full_name']}\n"
        f"├ Username: @{db_user['username']}\n"
        f"├ ID:      `{db_user['user_id']}`\n"
        f"├ Balance: ₹{db_user['balance']:.2f}\n"
        f"├ Earned:  ₹{db_user['total_earned']:.2f}\n"
        f"├ Refers:  {db_user['refer_count']}\n"
        f"├ Referred By: {db_user['referred_by'] or 'None'}\n"
        f"└ Joined:  {db_user['joined_at'][:10]}",
        parse_mode="Markdown"
    )

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast [message]")
        return
    msg     = " ".join(context.args)
    users   = db.get_all_users()
    success = 0
    fail    = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 *Announcement:*\n\n{msg}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
    await update.message.reply_text(f"✅ Broadcast done!\nSent: {success}\nFailed: {fail}")

async def addchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /addchannel @username Channel_Name https://t.me/username channel|group"""
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /addchannel @username ChannelName https://t.me/link [channel|group]"
        )
        return
    username = context.args[0]
    name     = context.args[1]
    url      = context.args[2]
    ctype    = context.args[3] if len(context.args) > 3 else "channel"
    ok       = db.add_db_channel(name, username, url, ctype)
    if ok:
        await update.message.reply_text(f"✅ {name} ({username}) add ho gaya!")
    else:
        await update.message.reply_text("❌ Already exists ya error!")

async def removechannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /removechannel @username")
        return
    db.remove_db_channel(context.args[0])
    await update.message.reply_text(f"✅ {context.args[0]} remove ho gaya!")

async def listchannels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    all_ch = get_all_required()
    if not all_ch:
        await update.message.reply_text("Koi channel/group nahi hai.")
        return
    text = "📋 *All Channels & Groups:*\n\n"
    for i, ch in enumerate(all_ch, 1):
        text += f"{i}. {ch['name']} ({ch['username']}) [{ch['type']}]\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ── Main ─────────────────────────────────────────────────────

def main():
    db.init_db()

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Withdraw conversation
    withdraw_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(withdraw_cb, pattern="^withdraw$"),
            CommandHandler("withdraw", withdraw_cmd),
        ],
        states={
            WAITING_UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_upi)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # User handlers
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("refer",   refer_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(withdraw_conv)

    # Callback handlers
    app.add_handler(CallbackQueryHandler(verify_join, pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(balance_cb,  pattern="^balance$"))
    app.add_handler(CallbackQueryHandler(refer_cb,    pattern="^refer$"))
    app.add_handler(CallbackQueryHandler(stats_cb,    pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(help_cb,     pattern="^help$"))

    # Admin handlers
    app.add_handler(CommandHandler("admin",         admin_cmd))
    app.add_handler(CommandHandler("stats",         stats_admin_cmd))
    app.add_handler(CommandHandler("pending",       pending_cmd))
    app.add_handler(CommandHandler("approve",       approve_cmd))
    app.add_handler(CommandHandler("reject",        reject_cmd))
    app.add_handler(CommandHandler("addbalance",    addbalance_cmd))
    app.add_handler(CommandHandler("removebalance", removebalance_cmd))
    app.add_handler(CommandHandler("userinfo",      userinfo_cmd))
    app.add_handler(CommandHandler("broadcast",     broadcast_cmd))
    app.add_handler(CommandHandler("addchannel",    addchannel_cmd))
    app.add_handler(CommandHandler("removechannel", removechannel_cmd))
    app.add_handler(CommandHandler("listchannels",  listchannels_cmd))

    print("🤖 Bot chal raha hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
