import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"

DAYS = [(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),
        (2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),
        (3,15),(3,16),(3,17),(3,18),(3,19),(3,20),(3,21),
        (4,22),(4,23),(4,24),(4,25),(4,26),(4,27),(4,28),
        (4,29),(4,30)]

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE,"r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE,"w") as f:
        json.dump(data,f)

def main_menu_kb():
    kb = [
        [KeyboardButton(text="📚 Bugungi dars")],
        [KeyboardButton(text="📊 Statistika")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_user(uid):
    data = load_data()
    return data.get(str(uid))

async def save_user(uid, user):
    data = load_data()
    data[str(uid)] = user
    save_data(data)

async def get_progress(uid):
    user = await get_user(uid)
    if not user:
        return {}
    return user.get("progress",{})

async def set_done(uid, day):
    data = load_data()
    user = data.get(str(uid))
    if not user:
        return
    if "progress" not in user:
        user["progress"]={}
    user["progress"][str(day)]={"done":True}
    save_data(data)

@dp.message(CommandStart())
async def start(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user:
        user={
            "today_day":1,
            "progress":{}
        }
        await save_user(msg.from_user.id,user)
    await msg.answer("📚 30 kunlik tarix challenge boshlandi!", reply_markup=main_menu_kb())

@dp.message(F.text=="📚 Bugungi dars")
async def today_lesson(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user:
        return

    today=user["today_day"]

    if today>30:
        await msg.answer("🎉 Challenge tugagan!")
        return

    await msg.answer(f"📖 Bugungi kun: {today}\nTarix mavzusini o‘rganing.")

    await set_done(msg.from_user.id,today)
    user["today_day"]=today+1
    await save_user(msg.from_user.id,user)

@dp.message(F.text=="📊 Statistika")
async def statistika(msg: types.Message):
    user = await get_user(msg.from_user.id)
    prog = await get_progress(msg.from_user.id)
    if not user:
        return

    done=sum(1 for v in prog.values() if v["done"])
    pct=round(done/30*100) if done>0 else 0
    today=user["today_day"] or 1

    pend=sum(
        1 for d in DAYS
        if not prog.get(str(d[1]),{}).get("done") and d[1]<today
    )

    streak=0
    for d in range(today-1,0,-1):
        if prog.get(str(d),{}).get("done"):
            streak+=1
        else:
            break

    daraja=(
        "🏆 Akademik" if done>=25 else
        "🥇 Katta Tarixchi" if done>=18 else
        "🥈 Tarixchi" if done>=10 else
        "🥉 Talaba" if done>=5 else
        "🌱 Yangi"
    )

    week_stats=[]
    for w in range(1,5):
        w_days=[d[1] for d in DAYS if d[0]==w]
        w_done=sum(1 for d in w_days if prog.get(str(d),{}).get("done"))
        week_stats.append(f"Hafta {w}: {w_done}/{len(w_days)}")

    text=(
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"✅ Bajarilgan kunlar: <b>{done}/30</b>\n"
        f"📈 Progress: <b>{pct}%</b>\n"
        f"🔥 Streak: <b>{streak}</b>\n"
        f"📍 Bugungi kun: <b>{today}</b>\n"
        f"⏳ Orqada qolgan: <b>{pend}</b>\n"
        f"🎖 Daraja: <b>{daraja}</b>\n\n"
        f"📅 Haftalar:\n"
        + "\n".join(week_stats)
    )

    await msg.answer(text, parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())