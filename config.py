# ============================================================
#   CONFIG - Yahan apni settings bharo
# ============================================================

# BotFather se mila token
BOT_TOKEN = "8652222167:AAEko4vYMvAH-POCmgZE0M1m5i8BFfNu9_U"  # ⚠️ Sirf yeh change karo - BotFather se lo

# Apna Telegram User ID (admin)
ADMIN_IDS = [1804574038]

# ── Channels & Groups ──────────────────────────────────────
# Bot ko pehle admin banana padega har channel/group mein
REQUIRED_CHANNELS = [
    {"name": "Captain Earn",        "username": "@captain_earn",  "url": "https://t.me/captain_earn"},
    {"name": "Captain Earn Group",  "username": None,             "url": "https://t.me/+mkZzN7ES1pFkNGQ1"},
]

REQUIRED_GROUPS = []

# ── Earning Settings ────────────────────────────────────────
JOIN_BONUS        = 5      # Pehli baar join karne par (Rs)
REFER_BONUS       = 15     # Har 10 refers par (Rs)
REFERS_NEEDED     = 10     # Kitne refers par bonus milega
MIN_WITHDRAW      = 20     # Minimum withdrawal amount (Rs)

# ── Database ────────────────────────────────────────────────
DATABASE_NAME = "/data/bot_database.db"  # Render ke liye

# ── Messages ────────────────────────────────────────────────
WELCOME_MSG = """
👋 *Swagat hai {name}!*

🎉 Hamare *Refer & Earn* Bot mein aapka swagat hai!

💰 *Earning Structure:*
├ ✅ Join Bonus: ₹{join_bonus}
├ 👥 Har 10 Refers: ₹{refer_bonus}  
└ 💳 Min Withdraw: ₹{min_withdraw}

📌 Pehle neeche diye channels & groups join karo!
"""

ALREADY_MEMBER_MSG = """
✅ *Verification Complete!*

🎊 Aap pehle se member hain!
💰 Aapka balance: ₹{balance}

📤 Refer karo aur kamaao:
🔗 `{refer_link}`
"""

JOIN_SUCCESS_MSG = """
🎉 *Congratulations {name}!*

✅ Aapne sabhi channels join kar liye!
💰 *₹{bonus} aapke account mein add ho gaye!*

🔗 *Aapka Referral Link:*
`{refer_link}`

👆 Yeh link share karo aur kamaao:
├ Har 10 refers = ₹15 bonus
└ Minimum withdraw = ₹20

/balance - Balance dekho
/refer - Refer link dekho  
/withdraw - Paise nikalo
"""
