# 🤖 Refer & Earn Telegram Bot

## Features
- ✅ Multi-channel/group join verification
- 💰 Join bonus ₹5
- 👥 Refer system (10 refers = ₹15)
- 💳 Withdrawal system (min ₹20)
- 🔧 Full admin panel
- 📢 Broadcast to all users
- ➕ Dynamic channel add/remove

---

## ⚙️ Setup (config.py)

```python
BOT_TOKEN   = "YOUR_BOT_TOKEN"       # BotFather se lo
ADMIN_IDS   = [YOUR_TELEGRAM_ID]     # Apna user ID

REQUIRED_CHANNELS = [
    {"name": "My Channel", "username": "@mychannel", "url": "https://t.me/mychannel"},
]
REQUIRED_GROUPS = [
    {"name": "My Group", "username": "@mygroup", "url": "https://t.me/mygroup"},
]
```

> ⚠️ Bot ko har channel/group mein **Admin** banana zaruri hai!

---

## 🚀 Render Par Deploy Karo (FREE)

1. GitHub par naya repo banao
2. Sab files upload karo
3. [render.com](https://render.com) par jao → New → Background Worker
4. GitHub repo connect karo
5. Environment Variables add karo:
   - `BOT_TOKEN` = your bot token
6. Deploy!

> Render par `DATABASE_NAME` path change karo `config.py` mein:
> ```python
> DATABASE_NAME = "/data/bot_database.db"
> ```

---

## 🚀 Heroku Par Deploy Karo

```bash
# 1. Heroku CLI install karo
heroku login

# 2. App banao
heroku create my-refer-bot

# 3. Environment variable set karo
heroku config:set BOT_TOKEN=your_token_here

# 4. Deploy karo
git init
git add .
git commit -m "Initial commit"
git push heroku main

# 5. Worker start karo
heroku ps:scale worker=1
```

---

## 📋 User Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot start karo |
| `/balance` | Balance dekho |
| `/refer` | Refer link lo |
| `/withdraw` | Paise nikalo |
| `/history` | Withdrawal history |

## 🔧 Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Admin panel |
| `/stats` | Bot statistics |
| `/pending` | Pending withdrawals |
| `/approve [id]` | Approve withdrawal |
| `/reject [id]` | Reject withdrawal |
| `/addbalance [uid] [amount]` | Balance add karo |
| `/removebalance [uid] [amount]` | Balance remove karo |
| `/userinfo [uid]` | User info dekho |
| `/broadcast [msg]` | Sab users ko message |
| `/addchannel @username Name URL [type]` | Channel add karo |
| `/removechannel @username` | Channel remove karo |
| `/listchannels` | Sab channels dekho |

---

## 💰 Earning Structure

| Action | Amount |
|--------|--------|
| Join Bonus (one-time) | ₹5 |
| Har 10 Refers | ₹15 |
| Minimum Withdrawal | ₹20 |

---

## 📁 File Structure

```
telegram-bot/
├── bot.py           ← Main bot
├── database.py      ← Database functions
├── config.py        ← Settings (EDIT THIS)
├── requirements.txt
├── Procfile         ← Heroku
├── render.yaml      ← Render
├── runtime.txt      ← Python version
└── README.md
```
