# ============================================================
#   CONFIG - Yahan apni settings bharo
# ============================================================

# BotFather se mila token
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Apna Telegram User ID (admin)
ADMIN_IDS = [123456789]  # Apna user ID yahan rakho (multiple bhi ho sakte hain)

# ── Channels & Groups ──────────────────────────────────────
# Jitne chahe utne add karo
# Bot ko pehle admin banana padega har channel/group mein
REQUIRED_CHANNELS = [
    {"name": "Main Channel",  "username": "@yourchannel1", "url": "https://t.me/yourchannel1"},
    {"name": "Second Channel","username": "@yourchannel2", "url": "https://t.me/yourchannel2"},
]

REQUIRED_GROUPS = [
    {"name": "Main Group",   "username": "@yourgroup1",   "url": "https://t.me/yourgroup1"},
]

# ── Earning Settings ────────────────────────────────────────
JOIN_BONUS        = 5      # Pehli baar join karne par (Rs)
REFER_BONUS       = 15     # Har 10 refers par (Rs)
REFERS_NEEDED     = 10     # Kitne refers par bonus milega
MIN_WITHDRAW      = 20     # Minimum withdrawal amount (Rs)

# ── Database ────────────────────────────────────────────────
DATABASE_NAME = "bot_database.db"

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
