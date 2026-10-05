import sqlite3
import logging
import os
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# تنظیمات ربات
# =========================================================

BOT_TOKEN = "8991252165:AAGEglIzi3sQBcM8icgYPsVbn62W_yCZUog"

# آیدی عددی ادمین
ADMIN_ID = 7201041401

CHANNEL_USERNAME = "@HtmlCSSArsham"
SUPPORT_USERNAME = "@BN_Arsham"

# اطلاعات دوره
COURSE_PRICE = "۱٬۶۰۰٬۰۰۰ تومان"

# اطلاعات کارت
CARD_NUMBER = "6104338698766397"
CARD_OWNER = "ارشام قزوینه"

# =========================================================
# مسیر عکس خوشامدگویی
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WELCOME_IMAGE = os.path.join(
    BASE_DIR,
    "img",
    "img",
    "1.png"
)

DB_NAME = os.path.join(
    BASE_DIR,
    "html_css_bot.db"
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================================================
# دیتابیس
# =========================================================

def db():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT,
            course_access INTEGER DEFAULT 0,
            quiz_score INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            video_type TEXT,
            video_data TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            amount TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    conn.commit()

    # درس‌های پیش‌فرض
    cur.execute("SELECT COUNT(*) FROM lessons")
    count = cur.fetchone()[0]

    if count == 0:

        lessons = [
            (
                "HTML چیست؟",
                "HTML زبان ساختاردهی صفحات وب است و با استفاده از تگ‌ها ساختار سایت را می‌سازیم.",
                "html"
            ),
            (
                "ساختار HTML",
                "یک صفحه HTML معمولاً شامل html، head و body است.",
                "html"
            ),
            (
                "لینک در HTML",
                "برای ساخت لینک از تگ a استفاده می‌کنیم.",
                "html"
            ),
            (
                "تصویر در HTML",
                "برای نمایش تصویر از تگ img استفاده می‌کنیم.",
                "html"
            ),
            (
                "CSS چیست؟",
                "CSS برای طراحی ظاهر صفحات وب استفاده می‌شود.",
                "css"
            ),
            (
                "Flexbox",
                "Flexbox یکی از روش‌های مهم برای چیدمان عناصر در CSS است.",
                "css"
            ),
        ]

        for title, content, category in lessons:

            cur.execute("""
                INSERT INTO lessons
                (title, content, category, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                title,
                content,
                category,
                datetime.now().isoformat()
            ))

        conn.commit()

    conn.close()


# =========================================================
# ثبت کاربر
# =========================================================

def save_user(user):

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
        datetime.now().isoformat()
    ))

    cur.execute("""
        UPDATE users
        SET username = ?, first_name = ?
        WHERE user_id = ?
    """, (
        user.username or "",
        user.first_name or "",
        user.id
    ))

    conn.commit()
    conn.close()


# =========================================================
# منوی اصلی
# =========================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📚 آموزش HTML",
                callback_data="html_lessons"
            ),
            InlineKeyboardButton(
                "🎨 آموزش CSS",
                callback_data="css_lessons"
            ),
        ],

        [
            InlineKeyboardButton(
                "📝 آزمون HTML/CSS",
                callback_data="quiz"
            ),
        ],

        [
            InlineKeyboardButton(
                "🎬 فیلم‌های آموزشی",
                callback_data="videos"
            ),
        ],

        [
            InlineKeyboardButton(
                "💎 دوره پیشرفته",
                callback_data="course"
            ),
        ],

        [
            InlineKeyboardButton(
                "📢 کانال ما",
                url="https://t.me/HtmlCSSArsham"
            )
        ],

        [
            InlineKeyboardButton(
                "👤 درباره ما",
                callback_data="about"
            ),

            InlineKeyboardButton(
                "🆘 پشتیبانی",
                url="https://t.me/BN_Arsham"
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# پیام خوشامدگویی
# =========================================================

WELCOME_TEXT = """
🌟 به ربات آموزشی طراحی سایت خوش آمدید! 🌟

🚀 اینجا می‌تونی طراحی سایت رو از پایه تا پیشرفته یاد بگیری.

📚 آموزش HTML
🎨 آموزش CSS
📝 آزمون‌های آنلاین
🎬 ویدیوهای آموزشی
💎 دوره پیشرفته طراحی سایت
👨‍💻 پشتیبانی

🔥 اگر آماده‌ای، یادگیری رو شروع کنیم!

👇 از منوی زیر انتخاب کن:
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_user(user)

    # ریست کردن وضعیت رسید
    context.user_data["waiting_receipt"] = False

    # اگر عکس وجود داشته باشد
    if os.path.exists(WELCOME_IMAGE):

        try:

            await update.message.reply_photo(
                photo=WELCOME_IMAGE,
                caption=WELCOME_TEXT,
                reply_markup=main_menu()
            )

            return

        except Exception as e:

            logging.error(
                f"خطا در ارسال عکس خوشامدگویی: {e}"
            )

    # اگر عکس پیدا نشد
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_menu()
    )


# =========================================================
# تابع مهم برای کار کردن دکمه‌ها با پیام عکس
# =========================================================

async def edit_message(
    query,
    text,
    keyboard
):

    reply_markup = InlineKeyboardMarkup(keyboard)

    # اگر پیام شامل عکس باشد
    if query.message and query.message.photo:

        await query.edit_message_caption(
            caption=text,
            reply_markup=reply_markup
        )

    else:

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )


# =========================================================
# آموزش HTML / CSS
# =========================================================

async def show_lessons(update, category):

    query = update.callback_query

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title
        FROM lessons
        WHERE category = ?
        ORDER BY id
    """, (category,))

    lessons = cur.fetchall()

    conn.close()

    if category == "html":
        title = "📚 آموزش HTML"
    else:
        title = "🎨 آموزش CSS"

    keyboard = []

    for lesson_id, lesson_title in lessons:

        keyboard.append([
            InlineKeyboardButton(
                lesson_title,
                callback_data=f"lesson_{lesson_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="home"
        )
    ])

    await edit_message(
        query,
        f"{title}\n\nیک درس را انتخاب کن 👇",
        keyboard
    )


# =========================================================
# نمایش یک درس
# =========================================================

async def show_lesson(update, lesson_id):

    query = update.callback_query

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, content, category
        FROM lessons
        WHERE id = ?
    """, (lesson_id,))

    lesson = cur.fetchone()

    conn.close()

    if not lesson:

        await query.answer(
            "درس پیدا نشد.",
            show_alert=True
        )

        return

    title, content, category = lesson

    if category == "html":
        back_callback = "html_lessons"
    else:
        back_callback = "css_lessons"

    keyboard = [

        [
            InlineKeyboardButton(
                "🔙 بازگشت به درس‌ها",
                callback_data=back_callback
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home"
            )
        ]

    ]

    await edit_message(
        query,
        f"📖 {title}\n\n{content}",
        keyboard
    )


# =========================================================
# ویدیوها
# =========================================================

async def show_videos(update):

    query = update.callback_query

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title
        FROM videos
        ORDER BY id DESC
    """)

    videos = cur.fetchall()

    conn.close()

    if not videos:

        keyboard = [
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]
        ]

        await edit_message(
            query,
            "🎬 هنوز ویدیویی اضافه نشده است.",
            keyboard
        )

        return

    keyboard = []

    for video_id, title in videos:

        keyboard.append([
            InlineKeyboardButton(
                title,
                callback_data=f"video_{video_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="home"
        )
    ])

    await edit_message(
        query,
        "🎬 فیلم‌های آموزشی\n\n"
        "ویدیوی موردنظر را انتخاب کن 👇",
        keyboard
    )


# =========================================================
# ارسال ویدیو
# =========================================================

async def send_video(update, video_id):

    query = update.callback_query

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, video_type, video_data
        FROM videos
        WHERE id = ?
    """, (video_id,))

    video = cur.fetchone()

    conn.close()

    if not video:

        await query.answer(
            "ویدیو پیدا نشد.",
            show_alert=True
        )

        return

    title, video_type, video_data = video

    await query.answer()

    if video_type == "telegram":

        await query.message.reply_video(
            video=video_data,
            caption=f"🎬 {title}"
        )

    elif video_type == "link":

        await query.message.reply_text(
            f"🎬 {title}\n\n"
            f"🔗 لینک مشاهده:\n{video_data}"
        )


# =========================================================
# دوره پیشرفته
# =========================================================

async def show_course(update):

    query = update.callback_query

    user_id = query.from_user.id

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT course_access
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    access = result[0] if result else 0

    if access == 1:

        keyboard = [

            [
                InlineKeyboardButton(
                    "📚 سرفصل دوره",
                    callback_data="course_topics"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]

        ]

        text = """
💎 دوره پیشرفته طراحی سایت

✅ دسترسی شما فعال است.

🎓 دوره از سطح صفر تا پیشرفته طراحی شده است.

🚀 موفق باشی!
"""

    else:

        keyboard = [

            [
                InlineKeyboardButton(
                    "📚 سرفصل دوره",
                    callback_data="course_topics"
                )
            ],

            [
                InlineKeyboardButton(
                    "💳 خرید دوره",
                    callback_data="buy_course"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]

        ]

        text = f"""
💎 دوره پیشرفته طراحی سایت

🎓 آموزش از صفر تا پیشرفته

💰 قیمت:

{COURSE_PRICE}

در این دوره قدم‌به‌قدم طراحی سایت را یاد می‌گیری.

👇 برای مشاهده سرفصل یا خرید انتخاب کن.
"""

    await edit_message(
        query,
        text,
        keyboard
    )


# =========================================================
# سرفصل دوره
# =========================================================

async def course_topics(update):

    query = update.callback_query

    text = """
📚 سرفصل دوره پیشرفته

1️⃣ HTML از پایه
2️⃣ ساختار حرفه‌ای صفحات
3️⃣ فرم‌ها
4️⃣ تصاویر و لینک‌ها
5️⃣ CSS از پایه
6️⃣ رنگ‌ها و فونت‌ها
7️⃣ Box Model
8️⃣ Flexbox
9️⃣ Grid
🔟 Responsive Design
1️⃣1️⃣ طراحی منو
1️⃣2️⃣ انیمیشن‌های CSS
1️⃣3️⃣ پروژه‌های واقعی
1️⃣4️⃣ طراحی سایت حرفه‌ای

🚀 از صفر شروع می‌کنیم و مرحله‌به‌مرحله جلو می‌ریم.
"""

    keyboard = [

        [
            InlineKeyboardButton(
                "💳 خرید دوره",
                callback_data="buy_course"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="course"
            )
        ]

    ]

    await edit_message(
        query,
        text,
        keyboard
    )


# =========================================================
# خرید دوره
# =========================================================

async def buy_course(update):

    query = update.callback_query

    text = f"""
💎 خرید دوره پیشرفته

💰 مبلغ:

{COURSE_PRICE}

💳 شماره کارت:

{CARD_NUMBER}

👤 به نام:

{CARD_OWNER}

━━━━━━━━━━━━━━

📌 بعد از واریز مبلغ، تصویر رسید پرداخت را برای ربات ارسال کن.

⚠️ پس از بررسی توسط مدیریت، دسترسی دوره برایت فعال می‌شود.
"""

    keyboard = [

        [
            InlineKeyboardButton(
                "📨 ارسال رسید پرداخت",
                callback_data="send_receipt"
            )
        ],

        [
            InlineKeyboardButton(
                "🆘 پشتیبانی",
                url="https://t.me/BN_Arsham"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home"
            )
        ]

    ]

    await edit_message(
        query,
        text,
        keyboard
    )


# =========================================================
# درخواست ارسال رسید
# =========================================================

async def send_receipt(update, context):

    query = update.callback_query

    await query.answer()

    context.user_data["waiting_receipt"] = True

    await query.message.reply_text(
        """
📨 ارسال رسید پرداخت

لطفاً تصویر رسید پرداخت را همینجا ارسال کن.

⏳ بعد از ارسال، رسید برای مدیریت فرستاده می‌شود.

✅ پس از تأیید مدیریت، دوره برایت فعال خواهد شد.
"""
    )


# =========================================================
# دریافت عکس رسید
# =========================================================

async def photo_handler(update, context):

    user = update.effective_user

    save_user(user)

    # اگر کاربر در حالت ارسال رسید نیست
    if not context.user_data.get("waiting_receipt", False):

        await update.message.reply_text(
            "📌 اگر می‌خواهی رسید پرداخت بفرستی،"
            " ابتدا وارد بخش خرید دوره شو."
        )

        return

    photo = update.message.photo[-1]

    file_id = photo.file_id

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO payments
        (user_id, username, amount, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        COURSE_PRICE,
        "pending",
        datetime.now().isoformat()
    ))

    payment_id = cur.lastrowid

    conn.commit()
    conn.close()

    # خروج از حالت انتظار رسید
    context.user_data["waiting_receipt"] = False

    keyboard = [

        [
            InlineKeyboardButton(
                "✅ تایید پرداخت",
                callback_data=f"approve_{payment_id}_{user.id}"
            ),

            InlineKeyboardButton(
                "❌ رد پرداخت",
                callback_data=f"reject_{payment_id}_{user.id}"
            )
        ]

    ]

    try:

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=(
                "💳 رسید پرداخت جدید\n\n"
                f"👤 نام: {user.first_name}\n"
                f"🆔 ID: {user.id}\n"
                f"📱 Username: @{user.username or 'ندارد'}\n"
                f"💰 مبلغ: {COURSE_PRICE}\n\n"
                f"🧾 شماره پرداخت: {payment_id}"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text(
            """
✅ رسید شما با موفقیت دریافت شد.

⏳ رسید برای مدیریت ارسال شد.

📌 بعد از بررسی، نتیجه برای شما ارسال می‌شود.
"""
        )

    except Exception as e:

        logging.error(
            f"خطا در ارسال رسید به ادمین: {e}"
        )

        await update.message.reply_text(
            """
❌ در ارسال رسید مشکلی پیش آمد.

🆘 لطفاً با پشتیبانی تماس بگیر.
"""
        )


# =========================================================
# ارسال پیام به کاربر
# =========================================================

async def context_bot_send(update, user_id, text):

    try:

        await update.get_bot().send_message(
            chat_id=user_id,
            text=text
        )

    except Exception as e:

        logging.error(
            f"خطا در ارسال پیام به کاربر: {e}"
        )


# =========================================================
# تایید پرداخت
# =========================================================

async def approve_payment(update, payment_id, user_id):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE payments
        SET status = 'approved'
        WHERE id = ?
    """, (payment_id,))

    cur.execute("""
        UPDATE users
        SET course_access = 1
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    await query.answer(
        "پرداخت تایید شد. ✅"
    )

    try:

        await query.edit_message_reply_markup(
            reply_markup=None
        )

    except Exception:
        pass

    await context_bot_send(
        update,
        user_id,
        """
🎉 پرداخت شما تایید شد!

💎 دسترسی دوره پیشرفته برای شما فعال شد.

🚀 از یادگیری لذت ببر!
"""
    )


# =========================================================
# رد پرداخت
# =========================================================

async def reject_payment(update, payment_id, user_id):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )

        return

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE payments
        SET status = 'rejected'
        WHERE id = ?
    """, (payment_id,))

    conn.commit()
    conn.close()

    await query.answer(
        "پرداخت رد شد."
    )

    try:

        await query.edit_message_reply_markup(
            reply_markup=None
        )

    except Exception:
        pass

    await context_bot_send(
        update,
        user_id,
        """
❌ رسید پرداخت شما تایید نشد.

اگر فکر می‌کنی اشتباهی رخ داده است، با پشتیبانی تماس بگیر:

@BN_Arsham
"""
    )


# =========================================================
# آزمون
# =========================================================

QUIZ = [

    (
        "HTML برای چه کاری استفاده می‌شود؟",
        [
            "ساختار صفحه",
            "ساخت سیستم عامل",
            "ساخت آنتی‌ویروس",
            "ساخت سخت‌افزار"
        ],
        0
    ),

    (
        "کدام تگ برای عنوان اصلی استفاده می‌شود؟",
        [
            "h1",
            "p",
            "img",
            "div"
        ],
        0
    ),

    (
        "کدام تگ برای لینک استفاده می‌شود؟",
        [
            "a",
            "link",
            "url",
            "href"
        ],
        0
    ),

    (
        "CSS برای چه کاری است؟",
        [
            "طراحی ظاهر سایت",
            "ساخت دیتابیس",
            "ساخت سرور",
            "ساخت سیستم عامل"
        ],
        0
    ),

    (
        "کدام ویژگی رنگ متن را تغییر می‌دهد؟",
        [
            "color",
            "background",
            "font",
            "text"
        ],
        0
    ),

    (
        "کدام ویژگی رنگ پس‌زمینه را تغییر می‌دهد؟",
        [
            "background-color",
            "color",
            "bg",
            "back"
        ],
        0
    ),

    (
        "کدام مورد برای Flexbox استفاده می‌شود؟",
        [
            "display: flex",
            "display: block",
            "position: fixed",
            "float"
        ],
        0
    ),

    (
        "پسوند فایل HTML چیست؟",
        [
            ".html",
            ".css",
            ".js",
            ".php"
        ],
        0
    ),

    (
        "پسوند فایل CSS چیست؟",
        [
            ".css",
            ".html",
            ".js",
            ".txt"
        ],
        0
    ),

    (
        "کدام تگ برای تصویر استفاده می‌شود؟",
        [
            "img",
            "image",
            "picture",
            "src"
        ],
        0
    ),
]


quiz_states = {}


# =========================================================
# شروع آزمون
# =========================================================

async def start_quiz(update):

    query = update.callback_query

    user_id = query.from_user.id

    quiz_states[user_id] = {
        "question": 0,
        "score": 0
    }

    await send_quiz_question(
        update,
        user_id
    )


# =========================================================
# سوال آزمون
# =========================================================

async def send_quiz_question(update, user_id):

    state = quiz_states[user_id]

    number = state["question"]

    if number >= len(QUIZ):

        score = state["score"]

        conn = db()
        cur = conn.cursor()

        cur.execute("""
            UPDATE users
            SET quiz_score = ?
            WHERE user_id = ?
        """, (
            score,
            user_id
        ))

        conn.commit()
        conn.close()

        text = f"""
🏆 آزمون تمام شد!

📊 نتیجه شما:

✅ پاسخ صحیح: {score}
❌ پاسخ غلط: {len(QUIZ) - score}

🎯 امتیاز: {score * 10}/100

🔥 آفرین که آزمون را کامل کردی!
"""

        keyboard = [

            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]

        ]

        await edit_message(
            update.callback_query,
            text,
            keyboard
        )

        del quiz_states[user_id]

        return

    question, options, correct = QUIZ[number]

    keyboard = []

    for i, option in enumerate(options):

        keyboard.append([
            InlineKeyboardButton(
                option,
                callback_data=f"answer_{i}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "❌ خروج از آزمون",
            callback_data="home"
        )
    ])

    text = (
        f"📝 سوال {number + 1} از {len(QUIZ)}\n\n"
        f"{question}"
    )

    await edit_message(
        update.callback_query,
        text,
        keyboard
    )


# =========================================================
# درباره ما
# =========================================================

async def about(update):

    query = update.callback_query

    text = """
👨‍💻 درباره ما

به ربات آموزشی طراحی سایت خوش آمدید.

در این ربات می‌توانید:

📚 HTML یاد بگیرید
🎨 CSS یاد بگیرید
📝 آزمون بدهید
🎬 ویدیوهای آموزشی ببینید
💎 در دوره پیشرفته شرکت کنید

📢 کانال آموزشی:

@HtmlCSSArsham

🆘 پشتیبانی:

@BN_Arsham

🚀 هدف ما آموزش ساده و کاربردی طراحی سایت است.
"""

    keyboard = [

        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home"
            )
        ]

    ]

    await edit_message(
        query,
        text,
        keyboard
    )


# =========================================================
# پنل ادمین
# =========================================================

async def admin(update):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "⛔ شما دسترسی مدیریت ندارید."
        )

        return

    keyboard = [

        [
            InlineKeyboardButton(
                "📊 آمار",
                callback_data="admin_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 کاربران",
                callback_data="admin_users"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home"
            )
        ]

    ]

    await update.message.reply_text(
        "👑 پنل مدیریت",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# مدیریت دکمه‌ها
# =========================================================

async def button_handler(update, context):

    query = update.callback_query

    data = query.data

    await query.answer()

    user = query.from_user

    save_user(user)

    # =====================================================
    # خانه
    # =====================================================

    if data == "home":

        await edit_message(
            query,
            WELCOME_TEXT,
            main_menu().inline_keyboard
        )

    # =====================================================
    # HTML
    # =====================================================

    elif data == "html_lessons":

        await show_lessons(
            update,
            "html"
        )

    # =====================================================
    # CSS
    # =====================================================

    elif data == "css_lessons":

        await show_lessons(
            update,
            "css"
        )

    # =====================================================
    # درس
    # =====================================================

    elif data.startswith("lesson_"):

        lesson_id = int(
            data.split("_")[1]
        )

        await show_lesson(
            update,
            lesson_id
        )

    # =====================================================
    # ویدیو
    # =====================================================

    elif data == "videos":

        await show_videos(
            update
        )

    elif data.startswith("video_"):

        video_id = int(
            data.split("_")[1]
        )

        await send_video(
            update,
            video_id
        )

    # =====================================================
    # آزمون
    # =====================================================

    elif data == "quiz":

        await start_quiz(
            update
        )

    # =====================================================
    # جواب آزمون
    # =====================================================

    elif data.startswith("answer_"):

        user_id = user.id

        if user_id not in quiz_states:
            return

        selected = int(
            data.split("_")[1]
        )

        state = quiz_states[user_id]

        question_number = state["question"]

        correct_answer = QUIZ[question_number][2]

        if selected == correct_answer:

            state["score"] += 1

        state["question"] += 1

        await send_quiz_question(
            update,
            user_id
        )

    # =====================================================
    # دوره
    # =====================================================

    elif data == "course":

        await show_course(
            update
        )

    # =====================================================
    # سرفصل
    # =====================================================

    elif data == "course_topics":

        await course_topics(
            update
        )

    # =====================================================
    # خرید
    # =====================================================

    elif data == "buy_course":

        await buy_course(
            update
        )

    # =====================================================
    # ارسال رسید
    # =====================================================

    elif data == "send_receipt":

        await send_receipt(
            update,
            context
        )

    # =====================================================
    # تایید پرداخت
    # =====================================================

    elif data.startswith("approve_"):

        parts = data.split("_")

        payment_id = int(parts[1])

        user_id = int(parts[2])

        await approve_payment(
            update,
            payment_id,
            user_id
        )

    # =====================================================
    # رد پرداخت
    # =====================================================

    elif data.startswith("reject_"):

        parts = data.split("_")

        payment_id = int(parts[1])

        user_id = int(parts[2])

        await reject_payment(
            update,
            payment_id,
            user_id
        )

    # =====================================================
    # درباره ما
    # =====================================================

    elif data == "about":

        await about(
            update
        )

    # =====================================================
    # آمار
    # =====================================================

    elif data == "admin_stats":

        if user.id != ADMIN_ID:
            return

        conn = db()
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM users"
        )

        users_count = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM payments"
        )

        payments = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM payments
            WHERE status = 'approved'
        """)

        approved = cur.fetchone()[0]

        conn.close()

        text = f"""
📊 آمار ربات

👥 تعداد کاربران:

{users_count}

💳 تعداد پرداخت‌ها:

{payments}

✅ پرداخت‌های تایید شده:

{approved}
"""

        keyboard = [

            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]

        ]

        await edit_message(
            query,
            text,
            keyboard
        )

    # =====================================================
    # کاربران
    # =====================================================

    elif data == "admin_users":

        if user.id != ADMIN_ID:
            return

        conn = db()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, username, first_name, course_access
            FROM users
            ORDER BY joined_at DESC
            LIMIT 20
        """)

        users = cur.fetchall()

        conn.close()

        if not users:

            text = "👥 هنوز کاربری وجود ندارد."

        else:

            text = "👥 آخرین کاربران:\n\n"

            for uid, username, first_name, access in users:

                status = (
                    "✅ دوره فعال"
                    if access
                    else
                    "❌ بدون دوره"
                )

                text += (
                    f"👤 {first_name}\n"
                    f"🆔 {uid}\n"
                    f"📱 @{username or 'ندارد'}\n"
                    f"{status}\n"
                    f"────────────\n"
                )

        keyboard = [

            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]

        ]

        await edit_message(
            query,
            text,
            keyboard
        )


# =========================================================
# خطا
# =========================================================

async def error_handler(update, context):

    logging.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# =========================================================
# اجرای ربات
# =========================================================

def main():

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_handler
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("🤖 ربات با موفقیت اجرا شد...")
    print("📱 ربات آماده دریافت پیام است.")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()