import os
import json
import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import aiosqlite

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
DB_PATH = "tarix_bot.db"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]

class ProfileState(StatesGroup):
    name = State()
    school = State()
    goal = State()

class NoteState(StatesGroup):
    writing = State()

MOTIVATSIYA = [
    "🌟 Har bir o'qilgan sahifa — bilimga bir qadam!",
    "💪 Bugun qiyin bo'lsa ham — ertaga oson bo'ladi!",
    "📚 Tarixni bilgan kishi — kelajakni ko'ra oladi.",
    "🔥 Ketma-ket o'qish — eng kuchli odat!",
    "🏆 Imtihon kuni — bugungi mehnatni ko'rsatadi.",
    "⭐ Amir Temur ham bir qadam bilan boshlagan!",
]

DAYS = [
    (1,1,"Kirish","O'zbekiston tarixi — umumiy tushuncha","Darslik 1-bobini o'qing. O'zbekiston qayerda joylashganini atlasdan toping."),
    (1,2,"Ibtidoiy","Ibtidoiy jamoa davri (tosh asri)","Tosh davri, bronza davri, temir davri farqini jadval ko'rinishida yozing."),
    (1,3,"Sopolli","Sopolli tepa — O'zbekistonning eng qadimgi shahri","Sopolli tepa qaysi viloyatda? Nima uchun muhim? 3 ta fakt yozing."),
    (1,4,"Xorazm","Qadimgi Xorazm davlati","Xorazm qayerda? Amudaryo nima uchun muhim edi?"),
    (1,5,"Baqtriya","Qadimgi Baqtriya va Sug'd davlatlari","Ikkala davlatni solishtiring. Poytaxtlarini yozing."),
    (1,6,"Avesto","Avesto — qadimgi yozma yodgorlik","Avesto nima? Kim yozgan? Zardushtiylik asosiy g'oyasi?"),
    (1,7,"Takrorlash","1-hafta takrorlash","1-6 kunlarning asosiy sanalarini yozing. 5 ta savol tuzing."),
    (2,8,"Yunon","Iskandar Zulqarnayn yurishlari","Iskandar O'rta Osiyoga qachon keldi? Spitamen kimdir?"),
    (2,9,"Kushon","Kushon podsholigi — buyuk savdo davlati","Buyuk Ipak yo'li nima? Kushon davlati unga qanday ta'sir qilgan?"),
    (2,10,"Eftalit","Eftalitlar davlati (V-VI asrlar)","Eftalitlar kimlar? Qaysi hududlarni egallagan?"),
    (2,11,"Turk","Turk hoqonligi (VI-VII asrlar)","G'arbiy Turk hoqonligi nima? O'rta Osiyoga ta'siri?"),
    (2,12,"Ipak","Buyuk Ipak yo'li va savdo","Ipak yo'lining 3 ta asosiy shahri. Nima savdo qilingan?"),
    (2,13,"Arab","Arab fathi va Islomning tarqalishi","Qutayba ibn Muslim kimdir? Islom qachon keldi?"),
    (2,14,"Takrorlash","2-hafta takrorlash","Mil.av. IV asrdan VIII asrgacha voqealarni jadval qiling."),
    (3,15,"Tohiriy","Tohiriylar — birinchi mustaqil sulola","Tohiriylar qachon tashkil topgan? Nima uchun muhim?"),
    (3,16,"Somoniy","Somoniylar davlati — ilm markazi","Somoniylar poytaxti? Ibn Sino qaysi davrda yashagan?"),
    (3,17,"IbnSino","Abu Ali Ibn Sino — buyuk olim","Ibn Sino qachon tug'ilgan? 3 ta asarini yozing."),
    (3,18,"Buxoriy","Imom Al-Buxoriy","Al-Buxoriy qayerda tug'ilgan? Sahih al-Buxoriy nima?"),
    (3,19,"Forobiy","Al-Forobiy va Qoraxoniylar","Al-Forobiy kim? Muallimi soniy nima degani?"),
    (3,20,"Mahmud","Mahmud G'aznaviy va Beruniy","Mahmud G'aznaviy kimdir? Beruniy nima qilgan?"),
    (3,21,"Takrorlash","3-hafta takrorlash","Barcha sulolalarni jadvalda yozing."),
    (4,22,"Mo'g'ul","Mo'g'ul istilosi (XIII asr)","Chingizxon kim? O'rta Osiyoga qachon keldi?"),
    (4,23,"Temur","Amir Temur — buyuk davlat arbobi","Temur qachon, qayerda tug'ilgan? 3 ta yurishi."),
    (4,24,"Samarqand","Samarqand — Temuriylar poytaxti","Registon, Bibixonim, Shohizinda haqida yozing."),
    (4,25,"Ulugbek","Mirzo Ulug'bek — olim shoh","Ulug'bek rasadxonasi nima? Nima uchun o'ldirilgan?"),
    (4,26,"Navoiy","Alisher Navoiy — adabiyot sultoni","Navoiy qachon tug'ilgan? Xamsa nima?"),
    (4,27,"Shayboniy","Shayboniylar va Buxoro xonligi","Shayboniyxon Temuriylarni qanday mag'lub etdi?"),
    (4,28,"Xonliklar","Buxoro, Xiva, Qo'qon xonliklari","Uch xonlikning poytaxti va asoschisini yozing."),
    (4,29,"Yodgorlik","UNESCO — Tarixiy yodgorliklar","Samarqand, Buxoro, Xiva qachon UNESCO ga kirgan?"),
    (4,30,"YAKUNIY","30 kunlik to'liq takrorlash!","Barcha davrlarni jadvalda yozing. O'zingizni sinang!"),
]FLASHCARDS = [
    ("Sopolli tepa qaysi viloyatda?", "Surxondaryo viloyati"),
    ("Avesto qanday asar?", "Zardushtiylik dinining muqaddas kitobi"),
    ("Iskandar O'rta Osiyoga qachon keldi?", "Miloddan avvalgi 329-327 yillarda"),
    ("Spitamen kim?", "Iskandarга qarshi kurashgan sug'diyonali qahramon"),
    ("Buyuk Ipak yo'li nima?", "Xitoydan Evropagacha cho'zilgan savdo yo'li"),
    ("Qutayba ibn Muslim kim?", "O'rta Osiyoni fath qilgan arab qo'mondoni"),
    ("Somoniylar poytaxti?", "Buxoro shahri"),
    ("Ibn Sino qayerda tug'ilgan?", "Buxoro yaqinidagi Afshona qishlog'ida"),
    ("Ibn Sinoning asosiy asari?", "Tib qonunlari (al-Qonun fit-tib)"),
    ("Al-Buxoriy qayerda tug'ilgan?", "Buxoro shahrida 810-yilda"),
    ("Al-Forobiyning laqabi?", "Muallimi soniy — ikkinchi muallim"),
    ("Amir Temur qachon tug'ilgan?", "1336-yil, Kesh (Shahrisabz)da"),
    ("Amir Temur poytaxti?", "Samarqand shahri"),
    ("Registon nima?", "Samarqandda uch madrasadan iborat ansambl"),
    ("Ulug'bek rasadxonasi qachon qurilgan?", "1428-1429 yillarda Samarqandda"),
    ("Navoiy qachon tug'ilgan?", "1441-yil, Hirot shahrida"),
    ("Navoiyning Xamsa asari nima?", "5 ta dostondan iborat asar"),
    ("Shayboniyxon kim?", "Temuriylarni mag'lub etib Shayboniylar sulolasini tuzgan"),
    ("Buxoro xonligi qachon tashkil topgan?", "XVI asr boshida"),
    ("Samarqand UNESCO ga qachon kirgan?", "2001-yilda"),
    ("Chingizxon qachon keldi?", "1219-1221 yillarda"),
    ("Bibixonim masjidi kim qurgan?", "Amir Temur, 1399-1404 yillarda"),
    ("Ulug'bek qachon vafot etgan?", "1449-yilda, o'z o'g'li tomonidan"),
    ("Xiva xonligi poytaxti?", "Xiva shahri"),
    ("Kushon podsholigi qachon?", "Miloddan avvalgi I asr — milodiy IV asr"),
]

TESTS = [
    {"q":"Sopolli tepa qaysi viloyatda?","options":["Toshkent","Surxondaryo","Samarqand","Farg'ona"],"answer":1,"explanation":"Sopolli tepa Surxondaryo viloyatida joylashgan."},
    {"q":"Avesto qanday asar?","options":["Arab yilnomalari","Zardushtiylik kitobi","Yunon manbasi","Xitoy hujjati"],"answer":1,"explanation":"Avesto zardushtiylik dinining muqaddas kitobi."},
    {"q":"Ipak yo'li qaysi mamlakatdan boshlanadi?","options":["Hindiston","Eron","Xitoy","Rim"],"answer":2,"explanation":"Buyuk Ipak yo'li Xitoydan boshlanadi."},
    {"q":"Iskandarга qarshi kim kurashgan?","options":["Qutayba","Spitamen","Temur","Shayboniy"],"answer":1,"explanation":"Spitamen sug'diyonali qahramon, Iskandarга qarshi kurashgan."},
    {"q":"Ibn Sino qayerda tug'ilgan?","options":["Samarqand","Xiva","Afshona","Toshkent"],"answer":2,"explanation":"Ibn Sino 980-yilda Afshona qishlog'ida tug'ilgan."},
    {"q":"Al-Forobiyning laqabi?","options":["Muallimi avval","Muallimi soniy","Muallimi oliy","Ustozi a'zam"],"answer":1,"explanation":"Al-Forobiy Muallimi soniy deb atalgan."},
    {"q":"Amir Temur qayerda tug'ilgan?","options":["Samarqand","Buxoro","Kesh (Shahrisabz)","Xiva"],"answer":2,"explanation":"Amir Temur 1336-yilda Kesh shahrida tug'ilgan."},
    {"q":"Registon qaysi shaharda?","options":["Buxoro","Xiva","Samarqand","Toshkent"],"answer":2,"explanation":"Registon maydoni Samarqandda joylashgan."},
    {"q":"Ulug'bek rasadxonasi qachon qurilgan?","options":["1336","1428","1500","1220"],"answer":1,"explanation":"Ulug'bek rasadxonasi 1428-yilda qurilgan."},
    {"q":"Navoiyning Xamsa asari necha dostondan iborat?","options":["3","4","5","7"],"answer":2,"explanation":"Xamsa 5 ta dostondan iborat."},
    {"q":"Somoniylar poytaxti?","options":["Samarqand","Buxoro","Urganch","Termiz"],"answer":1,"explanation":"Somoniylar poytaxti Buxoro edi."},
    {"q":"Chingizxon qachon keldi?","options":["1100","1150","1219","1300"],"answer":2,"explanation":"Chingizxon 1219-yilda keldi."},
    {"q":"Al-Buxoriy qayerda tug'ilgan?","options":["Samarqand","Buxoro","Termiz","Xiva"],"answer":1,"explanation":"Al-Buxoriy 810-yilda Buxoroda tug'ilgan."},
    {"q":"Samarqand UNESCO ga qachon kirgan?","options":["1990","1995","2001","2010"],"answer":2,"explanation":"Samarqand 2001-yilda UNESCO ga kirgan."},
    {"q":"Bibixonim kim qurgan?","options":["Ulug'bek","Amir Temur","Shayboniy","Navoiy"],"answer":1,"explanation":"Bibixonim Amir Temur tomonidan qurilgan."},
]

DAVRLAR = [
    ("Tosh davri","Mil.av. 1 mln yil","Ibtidoiy jamoa, tosh qurollar"),
    ("Bronza davri","Mil.av. III-II ming yillik","Sopolli tepa sivilizatsiyasi"),
    ("Temir davri","Mil.av. I ming yillik","Baqtriya, Sug'd, Xorazm"),
    ("Iskandar fathi","Mil.av. 329-327","Spitamen qarshiligi"),
    ("Kushon podsholigi","Mil.av. I — Mil. IV","Ipak yo'li yuksalishi"),
    ("Arab fathi","VII-VIII asrlar","Islom tarqalishi"),
    ("Somoniylar","875-999","Ibn Sino, Al-Buxoriy davri"),
    ("Mo'g'ul istilosi","1219-1221","Shaharlar vayron bo'ldi"),
    ("Temuriylar","1370-1500","Oltin asr — Temur, Ulug'bek, Navoiy"),
    ("Xonliklar","XVI-XIX asr","Buxoro, Xiva, Qo'qon"),
]

SHAXSLAR = [
    ("Spitamen","Mil.av. IV asr","Iskandarга qarshi kurashgan qahramon."),
    ("Al-Buxoriy","810-870","Sahih al-Buxoriy muallifi, Buxoroda tug'ilgan."),
    ("Al-Forobiy","872-950","Muallimi soniy, 160+ asar yozgan faylasuf."),
    ("Ibn Sino","980-1037","Tib qonunlari muallifi, buyuk tabib."),
    ("Amir Temur","1336-1405","Samarqandni jahon markaziga aylantirgan."),
    ("Mirzo Ulug'bek","1394-1449","Rasadxona qurgan olim shoh."),
    ("Alisher Navoiy","1441-1501","O'zbek adabiyotining sultoni, Xamsa muallifi."),
    ("Zahiriddin Babur","1483-1530","Boburiylar imperiyasini tashkil etgan."),
]async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT,
            full_name TEXT DEFAULT '', school TEXT DEFAULT '',
            goal TEXT DEFAULT '', today_day INTEGER DEFAULT 1,
            streak INTEGER DEFAULT 0, last_active TEXT DEFAULT '',
            score INTEGER DEFAULT 0, registered TEXT DEFAULT '')""")
        await db.execute("""CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER, day_num INTEGER, done INTEGER DEFAULT 0,
            done_at TEXT DEFAULT '', note TEXT DEFAULT '',
            PRIMARY KEY (user_id, day_num))""")
        await db.execute("""CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, score INTEGER, total INTEGER, taken_at TEXT)""")
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone()

async def upsert_user(user_id, username, full_name="", school="", goal=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO users (user_id,username,full_name,school,goal,registered)
            VALUES (?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username""",
            (user_id, username, full_name, school, goal, datetime.now().isoformat()))
        await db.commit()

async def update_user_field(user_id, field, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, user_id))
        await db.commit()

async def get_progress(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT day_num,done,note FROM progress WHERE user_id=?", (user_id,)) as cur:
            rows = await cur.fetchall()
    return {r["day_num"]: dict(r) for r in rows}

async def mark_day(user_id, day_num, done, note=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO progress (user_id,day_num,done,done_at,note)
            VALUES (?,?,?,?,?) ON CONFLICT(user_id,day_num) DO UPDATE SET
            done=excluded.done,done_at=excluded.done_at,note=excluded.note""",
            (user_id, day_num, 1 if done else 0, datetime.now().isoformat() if done else "", note))
        await db.commit()
    prog = await get_progress(user_id)
    await update_user_field(user_id, "score", sum(1 for v in prog.values() if v["done"]) * 10)

async def save_test_result(user_id, score, total):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO test_results (user_id,score,total,taken_at) VALUES (?,?,?,?)",
            (user_id, score, total, datetime.now().isoformat()))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY score DESC") as cur:
            return await cur.fetchall()

def main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📅 30 Kunlik Challenge")
    kb.button(text="📚 Darsliklar (6-sinf)")
    kb.button(text="🃏 Flashcard O'yini")
    kb.button(text="📝 Test")
    kb.button(text="📊 Statistika")
    kb.button(text="👤 Profilim")
    kb.button(text="📖 Tarix Atlasi")
    kb.button(text="🏅 Reyting")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def back_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🏠 Bosh sahifa")
    return kb.as_markup(resize_keyboard=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext):
    await upsert_user(msg.from_user.id, msg.from_user.username or "")
    user = await get_user(msg.from_user.id)
    if user and user["full_name"]:
        await msg.answer(f"🏛️ Xush kelibsiz, <b>{user['full_name']}</b>!\n\nQuyidagi bo'limlardan birini tanlang:",
            parse_mode="HTML", reply_markup=main_menu_kb())
    else:
        await msg.answer("🏛️ <b>O'zbekiston Tarixi — 30 Kunlik Challenge</b>\n\nSalom! Avval ro'yxatdan o'tamiz.\n\n<b>Ismingizni</b> yozing:",
            parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        await state.set_state(ProfileState.name)

@dp.message(ProfileState.name)
async def profile_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await msg.answer("🏫 <b>Maktab nomingizni</b> yozing:", parse_mode="HTML")
    await state.set_state(ProfileState.school)

@dp.message(ProfileState.school)
async def profile_school(msg: types.Message, state: FSMContext):
    await state.update_data(school=msg.text.strip())
    await msg.answer("🎯 <b>30 kunlik maqsadingiz nima?</b>\n\nMasalan: Imtihonda 5 baho olish", parse_mode="HTML")
    await state.set_state(ProfileState.goal)

@dp.message(ProfileState.goal)
async def profile_goal(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    await update_user_field(msg.from_user.id, "full_name", data["name"])
    await update_user_field(msg.from_user.id, "school", data["school"])
    await update_user_field(msg.from_user.id, "goal", msg.text.strip())
    await state.clear()
    await msg.answer(f"✅ <b>Profil saqlandi!</b>\n\n👤 {data['name']}\n🏫 {data['school']}\n🎯 {msg.text.strip()}\n\n{random.choice(MOTIVATSIYA)}",
        parse_mode="HTML", reply_markup=main_menu_kb())

@dp.message(F.text.in_({"🏠 Bosh sahifa"}))
async def go_home(msg: types.Message):
    await msg.answer("🏠 Bosh sahifa", reply_markup=main_menu_kb())

@dp.message(F.text == "📅 30 Kunlik Challenge")
async def challenge_menu(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user:
        await msg.answer("Avval /start yozing!")
        return
    prog = await get_progress(msg.from_user.id)
    done_cnt = sum(1 for v in prog.values() if v["done"])
    today_day = user["today_day"] or 1
    pct = round(done_cnt / 30 * 100)
    filled = round(pct / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)
    text = f"📅 <b>30 Kunlik Challenge</b>\n\n{bar} <b>{pct}%</b>\n✅ Bajarildi: <b>{done_cnt}/30</b> | 📍 Bugun: <b>{today_day}</b>\n\n"
    if today_day <= 30:
        d = DAYS[today_day - 1]
        status = "✅" if prog.get(today_day, {}).get("done") else "📌"
        text += f"━━━━━━━━━━━━━━━━\n{status} <b>Kun {today_day}: {d[3]}</b>\n🏷 <i>{d[2]}</i>\n\n📋 {d[4]}\n\n━━━━━━━━━━━━━━━━\n"
    kb = InlineKeyboardBuilder()
    if today_day <= 30 and not prog.get(today_day, {}).get("done"):
        kb.button(text="✅ Bajarildi", callback_data=f"done:{today_day}")
        kb.button(text="📝 Konspekt", callback_data=f"note:{today_day}")
    if today_day < 30:
        kb.button(text="➡️ Keyingi", callback_data=f"nextday:{today_day}")
    if today_day > 1:
        kb.button(text="⬅️ Oldingi", callback_data=f"prevday:{today_day}")
    kb.button(text="📋 Barcha kunlar", callback_data="alldays:0")
    kb.adjust(2)
    await msg.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("done:"))
async def cb_done(call: types.CallbackQuery):
    day_num = int(call.data.split(":")[1])
    await mark_day(call.from_user.id, day_num, True)
    user = await get_user(call.from_user.id)
    if user and user["today_day"] == day_num and day_num < 30:
        await update_user_field(call.from_user.id, "today_day", day_num + 1)
    await call.answer(f"✅ {day_num}-kun bajarildi!")
    await call.message.edit_text(f"🎉 <b>{day_num}-kun bajarildi!</b>\n\n{random.choice(MOTIVATSIYA)}\n\nKeyingi kun: <b>{day_num+1}</b> kutmoqda! 💪",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📅 Challengga qaytish", callback_data="back_challenge")]]))

@dp.callback_query(F.data == "back_challenge")
async def cb_back_challenge(call: types.CallbackQuery):
    await call.message.delete()
    await challenge_menu(call.message)

@dp.callback_query(F.data.startswith("nextday:"))
async def cb_nextday(call: types.CallbackQuery):
    day = int(call.data.split(":")[1])
    if day < 30:
        await update_user_field(call.from_user.id, "today_day", day + 1)
    await call.answer()
    await call.message.delete()
    await challenge_menu(call.message)

@dp.callback_query(F.data.startswith("prevday:"))
async def cb_prevday(call: types.CallbackQuery):
    day = int(call.data.split(":")[1])
    if day > 1:
        await update_user_field(call.from_user.id, "today_day", day - 1)
    await call.answer()
    await call.message.delete()
    await challenge_menu(call.message)

@dp.callback_query(F.data == "alldays:0")
async def cb_alldays(call: types.CallbackQuery):
    prog = await get_progress(call.from_user.id)
    user = await get_user(call.from_user.id)
    today = user["today_day"] if user else 1
    lines = ["📋 <b>Barcha 30 kun:</b>\n"]
    for w,wname in [(1,"🔴 Qadimgi davr"),(2,"🟢 O'rta asrlar"),(3,"🟡 Mustaqil davlatlar"),(4,"🟤 Temuriylar")]:
        lines.append(f"\n<b>{wname}</b>")
        for d in DAYS:
            if d[0]!=w: continue
            dn=d[1]
            icon = "✅" if prog.get(dn,{}).get("done") else "⭐" if dn==today else "⚠️" if dn<today else "🔒"
            lines.append(f"{icon} Kun {dn}: {d[3]}")
    await call.message.edit_text("\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_challenge")]]))

@dp.callback_query(F.data.startswith("note:"))
async def cb_note_start(call: types.CallbackQuery, state: FSMContext):
    day_num = int(call.data.split(":")[1])
    await state.set_state(NoteState.writing)
    await state.update_data(day_num=day_num)
    await call.message.answer(f"📝 <b>Kun {day_num} uchun konspekt yozing:</b>", parse_mode="HTML", reply_markup=back_kb())
    await call.answer()

@dp.message(NoteState.writing)
async def note_received(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    day_num = data.get("day_num", 1)
    prog = await get_progress(msg.from_user.id)
    done = prog.get(day_num, {}).get("done", False)
    await mark_day(msg.from_user.id, day_num, done, note=msg.text)
    await state.clear()
    await msg.answer(f"✅ <b>Kun {day_num} konspekt saqlandi!</b>", parse_mode="HTML", reply_markup=main_menu_kb())

@dp.message(F.text == "📊 Statistika")
async def statistika(msg: types.Message):
    user = await get_user(msg.from_user.id)
    prog = await get_progress(msg.from_user.id)
    if not user: return
    done = sum(1 for v in prog.values() if v["done"])
    pct = round(done/30*100)
    today = user["today_day"] or 1
    pend = sum(1 for d in DAYS if not prog.get(d[1],{}).get("done") and d[1] < today)
    streak = 0
    for d in range(today-1, 0, -1):
        if prog.get(d,{}).get("done"): streak+=1
        else: break
    daraja = "🏆 Akademik" if done>=25 else "🥇 Katta Tarixchi" if done>=18 else "🥈 Tarixchi" if done>=10 else "🥉 Talaba" if done>=5 else "🌱 Yangi"
    week_stats = []
    for w in range(1,5):
        w_days=[d[1] for d in DAYS if d[0]==w]
        w_done=sum(1 for d in w_days if prog.get(d,{}).get("done"))
        week_stats.append(f"Hafta {w}: {'🟩'*w_done}{'⬜'*(7-w_done)} {w_done}/7")
    await msg.answer(f"📊 <b>Statistika</b>\n\n🎓 {daraja}\n⭐ Ball: <b>{user['score'] or 0}</b>\n\n✅ Bajarildi: <b>{done}/30</b> ({pct}%)\n📍 Hozirgi kun: <b>{today}</b>\n🔥 Ketma-ket: <b>{streak} kun</b>\n⚠️ Kechikkan: <b>{pend}</b>\n\n" + "\n".join(week_stats),
        parse_mode="HTML", reply_markup=main_menu_kb())

@dp.message(F.text == "👤 Profilim")
async def profilim(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if not user or not user["full_name"]:
        await msg.answer("Avval /start yozing!", reply_markup=main_menu_kb()); return
    await msg.answer(f"👤 <b>Profilim</b>\n\n📛 {user['full_name']}\n🏫 {user['school'] or '—'}\n🎯 {user['goal'] or '—'}\n⭐ Ball: {user['score'] or 0}",
        parse_mode="HTML", reply_markup=main_menu_kb())

@dp.message(F.text == "📚 Darsliklar (6-sinf)")
async def darsliklar(msg: types.Message):
    kb = InlineKeyboardBuilder()
    boblar = [("1-bob","Tosh va bronza davri"),("2-bob","Qadimgi davlatlar"),("3-bob","Buyuk Ipak yo'li"),
              ("4-bob","Iskandar va Kushonlar"),("5-bob","Arab fathi va Islom"),("6-bob","Somoniylar va olimlar"),
              ("7-bob","Mo'g'ul istilosi"),("8-bob","Temuriylar oltin asri"),("9-bob","Xonliklar davri")]
    for code,title in boblar:
        kb.button(text=f"📖 {title}", callback_data=f"bob:{code}")
    kb.adjust(1)
    await msg.answer("📚 <b>6-sinf O'zbekiston Tarixi — Boblar</b>\n\nO'rganmoqchi bo'lgan bobni tanlang:",
        parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("bob:"))
async def cb_bob(call: types.CallbackQuery):
    bob_key = call.data.split(":")[1]
    boblar = {
        "1-bob":"📖 <b>1-bob: Tosh va bronza davri</b>\n\n• Paleolit — qadimgi tosh davri\n• Mezolit — o'rta tosh davri\n• Neolit — yangi tosh davri\n• Bronza davri — mil.av. III-II ming yillik\n\n🏛️ <b>Sopolli tepa</b> — Surxondaryoda, mil.av. II ming yillik\n\n❓ Savol: Sopolli tepa qaysi viloyatda?",
        "2-bob":"📖 <b>2-bob: Qadimgi davlatlar</b>\n\n1. <b>Baqtriya</b> — Janubiy O'zbekiston\n2. <b>Sug'diyona</b> — Zarafshon vodiysi, poytaxti Marakanda\n3. <b>Xorazm</b> — Amudaryo quyi oqimi\n\n📜 <b>Avesto</b> — zardushtiylik muqaddas kitobi\n\n❓ Savol: Sug'diyona poytaxti qayerda?",
        "3-bob":"📖 <b>3-bob: Buyuk Ipak yo'li</b>\n\n🛤️ Xitoydan Evropagacha — 12 000 km\n\n🏙️ Asosiy shaharlar:\n• Samarqand\n• Buxoro\n• Marv\n\n📦 Savdo: Ipak, chinni, ot, oltin\n\n❓ Savol: Ipak yo'li qaysi qit'alarni bog'lagan?",
        "4-bob":"📖 <b>4-bob: Iskandar va Kushonlar</b>\n\n⚔️ Iskandar (mil.av. 329-327)\n• Spitamen — 3 yil qarshilik ko'rsatgan\n\n👑 Kushon podsholigi\n• Ipak yo'lida kuchli davlat\n• Kanishka — eng mashhur hukmdor\n\n❓ Savol: Spitamen kim?",
        "5-bob":"📖 <b>5-bob: Arab fathi va Islom</b>\n\n🌙 Arab fathi (705-715)\n• Qutayba ibn Muslim — bosh qo'mondon\n• Buxoro, Samarqand fath qilindi\n\n☪️ Islom tarqaldi\n• Arab tili ilm tili bo'ldi\n• Al-Xorazmiy, Al-Farg'oniy yetishdi\n\n❓ Savol: Qutayba qaysi yillarda fath qildi?",
        "6-bob":"📖 <b>6-bob: Somoniylar va olimlar</b>\n\n🏰 Somoniylar (875-999) — poytaxti Buxoro\n\n🧪 Ibn Sino (980-1037)\n• Afshonada tug'ilgan\n• Tib qonunlari — 5 jild\n\n📿 Al-Buxoriy (810-870)\n• Buxoroda tug'ilgan\n• Sahih al-Buxoriy muallifi\n\n❓ Savol: Ibn Sinoning asosiy asari?",
        "7-bob":"📖 <b>7-bob: Mo'g'ul istilosi</b>\n\n⚔️ Chingizxon (1219-1221)\n• 200 000 qo'shin bilan keldi\n• Samarqand, Buxoro vayron qilindi\n\n😔 Oqibatlar:\n• Shaharlar vayron bo'ldi\n• Ilm-fan tanazzul topdi\n\n❓ Savol: Mo'g'ul istilosi qanday oqibat keltirdi?",
        "8-bob":"📖 <b>8-bob: Temuriylar oltin asri</b>\n\n👑 Amir Temur (1336-1405)\n• Keshda tug'ilgan\n• Samarqandni poytaxt qildi\n\n🔭 Ulug'bek (1394-1449)\n• Rasadxona qurdi (1428)\n\n✍️ Navoiy (1441-1501)\n• Xamsa — 5 ta doston\n\n❓ Savol: Amir Temur qayerda tug'ilgan?",
        "9-bob":"📖 <b>9-bob: Xonliklar davri</b>\n\n1. <b>Buxoro xonligi</b> — poytaxti Buxoro\n2. <b>Xiva xonligi</b> — poytaxti Xiva\n3. <b>Qo'qon xonligi</b> — poytaxti Qo'qon\n\n📜 Shayboniyxon — 1500-yilda Temuriylarni mag'lub etdi\n\n❓ Savol: Xiva xonligi poytaxti qayerda?",
    }
    content = boblar.get(bob_key, "Kontent tayyorlanmoqda...")
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Boblar ro'yxati", callback_data="back_boblar")
    await call.message.edit_text(content, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "back_boblar")
async def cb_back_boblar(call: types.CallbackQuery):
    await call.message.delete()
    await darsliklar(call.message)

user_flash_state = {}

@dp.message(F.text == "🃏 Flashcard O'yini")
async def flashcard_start(msg: types.Message):
    cards = FLASHCARDS.copy()
    random.shuffle(cards)
    user_flash_state[msg.from_user.id] = {"cards": cards, "idx": 0, "score": 0}
    await send_flashcard(msg, msg.from_user.id)

async def send_flashcard(obj, user_id):
    st = user_flash_state.get(user_id, {})
    cards = st.get("cards", [])
    idx = st.get("idx", 0)
    score = st.get("score", 0)
    if idx >= len(cards):
        text = f"🎉 <b>Flashcard tugadi!</b>\n\n✅ Bilgan: <b>{score}/{len(cards)}</b>\n📊 Natija: <b>{round(score/len(cards)*100)}%</b>\n\n{'🏆 Ajoyib!' if score>=20 else '💪 Davom eting!'}"
        fn = obj.answer if hasattr(obj,'answer') else obj.message.answer
        await fn(text, parse_mode="HTML", reply_markup=main_menu_kb())
        return
    q, a = cards[idx]
    kb = InlineKeyboardBuilder()
    kb.button(text="💡 Javobni ko'rish", callback_data=f"flash_show:{idx}")
    kb.button(text="⏭ O'tkazish", callback_data=f"flash_skip:{idx}")
    kb.adjust(2)
    text = f"🃏 <b>Karta {idx+1}/{len(cards)}</b> | ✅ {score}\n\n❓ {q}"
    if hasattr(obj,'answer'):
        await obj.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    else:
        await obj.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("flash_show:"))
async def cb_flash_show(call: types.CallbackQuery):
    idx = int(call.data.split(":")[1])
    st = user_flash_state.get(call.from_user.id, {})
    q, a = st["cards"][idx]
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Bildim!", callback_data=f"flash_yes:{idx}")
    kb.button(text="❌ Bilmadim", callback_data=f"flash_no:{idx}")
    kb.adjust(2)
    await call.message.edit_text(f"🃏 <b>Savol:</b>\n{q}\n\n💡 <b>Javob:</b>\n{a}", parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("flash_yes:"))
async def cb_flash_yes(call: types.CallbackQuery):
    st = user_flash_state.get(call.from_user.id, {})
    st["idx"] = st.get("idx",0)+1
    st["score"] = st.get("score",0)+1
    user_flash_state[call.from_user.id] = st
    await call.answer("✅ To'g'ri!")
    await send_flashcard(call, call.from_user.id)

@dp.callback_query(F.data.startswith("flash_no:"))
async def cb_flash_no(call: types.CallbackQuery):
    st = user_flash_state.get(call.from_user.id, {})
    st["idx"] = st.get("idx",0)+1
    user_flash_state[call.from_user.id] = st
    await call.answer("❌ Eslab qoling!")
    await send_flashcard(call, call.from_user.id)

@dp.callback_query(F.data.startswith("flash_skip:"))
async def cb_flash_skip(call: types.CallbackQuery):
    st = user_flash_state.get(call.from_user.id, {})
    st["idx"] = st.get("idx",0)+1
    user_flash_state[call.from_user.id] = st
    await send_flashcard(call, call.from_user.id)

user_test_state = {}

@dp.message(F.text == "📝 Test")
async def test_start(msg: types.Message):
    questions = random.sample(TESTS, min(10, len(TESTS)))
    user_test_state[msg.from_user.id] = {"questions": questions, "idx": 0, "score": 0}
    await send_test_question(msg, msg.from_user.id)

async def send_test_question(obj, user_id):
    st = user_test_state.get(user_id, {})
    qs = st.get("questions", [])
    idx = st.get("idx", 0)
    if idx >= len(qs):
        score = st.get("score",0)
        total = len(qs)
        await save_test_result(user_id, score, total)
        grade = "🏆 A'lo (5)" if score>=9 else "👍 Yaxshi (4)" if score>=7 else "😊 Qoniqarli (3)" if score>=5 else "📚 Ko'proq o'qing (2)"
        fn = obj.answer if hasattr(obj,'answer') else obj.message.answer
        await fn(f"📊 <b>Test yakunlandi!</b>\n\n✅ To'g'ri: <b>{score}/{total}</b>\n📈 {round(score/total*100)}%\n🎓 {grade}\n\n{random.choice(MOTIVATSIYA)}",
            