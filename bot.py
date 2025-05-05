import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from decouple import config
import requests
import phonenumbers
from phonenumbers import NumberParseError
import jdatetime
from datetime import timedelta

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for registration conversation
FULL_NAME, PHONE_NUMBER, AGE, GENDER, MEDICAL_CONDITIONS, EMAIL, REGION = range(7)

# States for order conversation
CATEGORY, SERVICE, RECIPIENT, ADDRESS, DATE, TIME, SPECIAL_CONDITIONS, PREFERRED_GENDER = range(7, 15)

# States for family member conversation
FM_FULL_NAME, FM_AGE, FM_GENDER, FM_MEDICAL_CONDITIONS, FM_EMAIL, FM_REGION, FM_RELATIONSHIP = range(15, 22)

# States for address conversation
ADDR_TITLE, ADDR_FULL_ADDRESS, ADDR_LOCATION = range(22, 25)

# Telegram Bot Token and Webhook URL
TOKEN = config('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = config('WEBHOOK_URL', default='https://your-render-app.onrender.com/telegram/webhook/')

# API Base URL
API_BASE_URL = config('API_BASE_URL', default='https://your-render-app.onrender.com/api/')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ثبت‌نام", callback_data='register')],
        [InlineKeyboardButton("پروفایل", callback_data='profile')],
        [InlineKeyboardButton("درخواست خدمت", callback_data='request_service')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('به ربات خدمات پزشکی خوش آمدید!', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'register':
        await query.message.reply_text('لطفاً نام و نام خانوادگی خود را وارد کنید:')
        return FULL_NAME
    elif query.data == 'profile':
        keyboard = [
            [InlineKeyboardButton("نمایش اطلاعات", callback_data='show_profile')],
            [InlineKeyboardButton("افزودن عضو خانواده", callback_data='add_family_member')],
            [InlineKeyboardButton("افزودن آدرس", callback_data='add_address')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('گزینه مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
    elif query.data == 'show_profile':
        telegram_id = str(query.from_user.id)
        response = requests.get(f'{API_BASE_URL}users/profile/', params={'telegram_id': telegram_id})
        if response.status_code == 200:
            user_data = response.json()[0]
            family_members = "\n".join([f"{fm['full_name']} ({fm['relationship']})" for fm in user_data['family_members']])
            addresses = "\n".join([addr['title'] for addr in user_data['addresses']])
            await query.message.reply_text(
                f"نام: {user_data['full_name']}\n"
                f"تلفن: {user_data['phone_number']}\n"
                f"سن: {user_data['age']}\n"
                f"جنسیت: {user_data['gender']}\n"
                f"بیماری‌ها: {user_data['medical_conditions']}\n"
                f"ایمیل: {user_data['email']}\n"
                f"منطقه: {user_data['region']}\n"
                f"اعضای خانواده:\n{family_members or 'هیچ عضوی ثبت نشده'}\n"
                f"آدرس‌ها:\n{addresses or 'هیچ آدرسی ثبت نشده'}"
            )
        else:
            await query.message.reply_text('لطفاً ابتدا ثبت‌نام کنید.')
    elif query.data == 'add_family_member':
        await query.message.reply_text('لطفاً نام و نام خانوادگی عضو خانواده را وارد کنید:')
        return FM_FULL_NAME
    elif query.data == 'add_address':
        await query.message.reply_text('لطفاً عنوان آدرس (مثل "خانه" یا "محل کار") را وارد کنید:')
        return ADDR_TITLE
    elif query.data == 'request_service':
        response = requests.get(f'{API_BASE_URL}services/categories/')
        if response.status_code == 200:
            categories = response.json()
            keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'cat_{cat["id"]}')] for cat in categories]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً یک دسته‌بندی انتخاب کنید:', reply_markup=reply_markup)
            return CATEGORY
    return ConversationHandler.END

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    if len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FULL_NAME
    context.user_data['full_name'] = full_name
    await update.message.reply_text('لطفاً شماره تلفن خود را وارد کنید (مثال: +989123456789):')
    return PHONE_NUMBER

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            raise NumberParseError('invalid', 'شماره تلفن نامعتبر است')
        context.user_data['phone_number'] = phone_number
        await update.message.reply_text('لطفاً سن خود را وارد کنید (بین 18 تا 120):')
        return AGE
    except NumberParseError:
        await update.message.reply_text('شماره تلفن نامعتبر است. لطفاً دوباره وارد کنید (مثال: +989123456789):')
        return PHONE_NUMBER

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age_text = update.message.text
    try:
        age = int(age_text)
        if not 18 <= age <= 120:
            raise ValueError
        context.user_data['age'] = age
        keyboard = [
            [InlineKeyboardButton("مرد", callback_data='male')],
            [InlineKeyboardButton("زن", callback_data='female')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفاً جنسیت خود را انتخاب کنید:', reply_markup=reply_markup)
        return GENDER
    except ValueError:
        await update.message.reply_text('سن باید عددی بین 18 تا 120 باشد. دوباره وارد کنید:')
        return AGE

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['gender'] = query.data
    await query.message.reply_text('لطفاً بیماری‌های زمینه‌ای خود را وارد کنید (در صورت عدم وجود، بنویسید "ندارد"):')
    return MEDICAL_CONDITIONS

async def medical_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['medical_conditions'] = update.message.text
    await update.message.reply_text('لطفاً ایمیل خود را وارد کنید (اختیاری، برای بازیابی رمز عبور):')
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if email and '@' not in email:
        await update.message.reply_text('ایمیل نامعتبر است. لطفاً دوباره وارد کنید یا برای خالی گذاشتن، "خالی" بنویسید:')
        return EMAIL
    context.user_data['email'] = email if email != 'خالی' else ''
    await update.message.reply_text('لطفاً منطقه محل زندگی خود را وارد کنید (مثال: تهران، سعادت‌آباد):')
    return REGION

async def region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['region'] = update.message.text
    telegram_id = str(update.message.from_user.id)

    # Register user via API
    data = {
        'telegram_id': telegram_id,
        'full_name': context.user_data['full_name'],
        'phone_number': context.user_data['phone_number'],
        'age': context.user_data['age'],
        'gender': context.user_data['gender'],
        'medical_conditions': context.user_data['medical_conditions'],
        'email': context.user_data['email'],
        'region': context.user_data['region'],
    }
    response = requests.post(f'{API_BASE_URL}users/profile/register/', json=data)
    if response.status_code == 200:
        await update.message.reply_text('ثبت‌نام با موفقیت انجام شد!')
    else:
        await update.message.reply_text(f'خطا در ثبت‌نام: {response.json().get("error", "لطفاً دوباره تلاش کنید")}')
    return ConversationHandler.END

async def fm_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    if len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FM_FULL_NAME
    context.user_data['fm_full_name'] = full_name
    await update.message.reply_text('لطفاً سن عضو خانواده را وارد کنید (بین 0 تا 120):')
    return FM_AGE

async def fm_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age_text = update.message.text
    try:
        age = int(age_text)
        if not 0 <= age <= 120:
            raise ValueError
        context.user_data['fm_age'] = age
        keyboard = [
            [InlineKeyboardButton("مرد", callback_data='fm_male')],
            [InlineKeyboardButton("زن", callback_data='fm_female')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفاً جنسیت عضو خانواده را انتخاب کنید:', reply_markup=reply_markup)
        return FM_GENDER
    except ValueError:
        await update.message.reply_text('سن باید عددی بین 0 تا 120 باشد. دوباره وارد کنید:')
        return FM_AGE

async def fm_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['fm_gender'] = query.data.split('_')[1]
    await query.message.reply_text('لطفاً بیماری‌های زمینه‌ای عضو خانواده را وارد کنید (در صورت عدم وجود، بنویسید "ندارد"):')
    return FM_MEDICAL_CONDITIONS

async def fm_medical_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fm_medical_conditions'] = update.message.text
    await update.message.reply_text('لطفاً ایمیل عضو خانواده را وارد کنید (اختیاری):')
    return FM_EMAIL

async def fm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if email and '@' not in email:
        await update.message.reply_text('ایمیل نامعتبر است. لطفاً دوباره وارد کنید یا برای خالی گذاشتن، "خالی" بنویسید:')
        return FM_EMAIL
    context.user_data['fm_email'] = email if email != 'خالی' else ''
    await update.message.reply_text('لطفاً منطقه محل زندگی عضو خانواده را وارد کنید (مثال: تهران، سعادت‌آباد):')
    return FM_REGION

async def fm_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fm_region'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("پدر", callback_data='fm_father')],
        [InlineKeyboardButton("مادر", callback_data='fm_mother')],
        [InlineKeyboardButton("پسر", callback_data='fm_son')],
        [InlineKeyboardButton("دختر", callback_data='fm_daughter')],
        [InlineKeyboardButton("همسر", callback_data='fm_spouse')],
        [InlineKeyboardButton("خواهر/برادر", callback_data='fm_sibling')],
        [InlineKeyboardButton("سایر", callback_data='fm_other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفاً نسبت عضو خانواده را انتخاب کنید:', reply_markup=reply_markup)
    return FM_RELATIONSHIP

async def fm_relationship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    relationship = query.data.split('_')[1]
    telegram_id = str(query.from_user.id)

    # Register family member via API
    data = {
        'full_name': context.user_data['fm_full_name'],
        'age': context.user_data['fm_age'],
        'gender': context.user_data['fm_gender'],
        'medical_conditions': context.user_data['fm_medical_conditions'],
        'email': context.user_data['fm_email'],
        'region': context.user_data['fm_region'],
        'relationship': relationship,
    }
    response = requests.post(f'{API_BASE_URL}users/family-members/', json=data, params={'telegram_id': telegram_id})
    if response.status_code == 201:
        await query.message.reply_text('عضو خانواده با موفقیت اضافه شد!')
    else:
        await query.message.reply_text('خطا در افزودن عضو خانواده. لطفاً دوباره تلاش کنید.')
    return ConversationHandler.END

async def addr_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    if len(title) < 2:
        await update.message.reply_text('عنوان آدرس باید حداقل 2 کاراکتر باشد. دوباره وارد کنید:')
        return ADDR_TITLE
    context.user_data['addr_title'] = title
    await update.message.reply_text('لطفاً آدرس کامل را وارد کنید:')
    return ADDR_FULL_ADDRESS

async def addr_full_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['addr_full_address'] = update.message.text
    await update.message.reply_text('لطفاً لوکیشن خود را از طریق تلگرام ارسال کنید یا بنویسید "خالی" برای ادامه بدون لوکیشن:')
    return ADDR_LOCATION

async def addr_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.from_user.id)
    if update.message.text == 'خالی':
        latitude, longitude = None, None
    else:
        location = update.message.location
        if not location:
            await update.message.reply_text('لوکیشن نامعتبر است. لطفاً لوکیشن ارسال کنید یا "خالی" بنویسید:')
            return ADDR_LOCATION
        latitude, longitude = location.latitude, location.longitude

    # Register address via API
    data = {
        'title': context.user_data['addr_title'],
        'full_address': context.user_data['addr_full_address'],
        'latitude': latitude,
        'longitude': longitude,
    }
    response = requests.post(f'{API_BASE_URL}users/addresses/', json=data, params={'telegram_id': telegram_id})
    if response.status_code == 201:
        await update.message.reply_text('آدرس با موفقیت اضافه شد!')
    else:
        await update.message.reply_text('خطا در افزودن آدرس. لطفاً دوباره تلاش کنید.')
    return ConversationHandler.END

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = query.data.split('_')[1]
    context.user_data['category_id'] = category_id
    response = requests.get(f'{API_BASE_URL}services/services/', params={'category': category_id})
    if response.status_code == 200:
        services = response.json()
        keyboard = [[InlineKeyboardButton(srv['name'], callback_data=f'srv_{srv["id"]}')] for srv in services]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('لطفاً یک خدمت انتخاب کنید:', reply_markup=reply_markup)
        return SERVICE
    await query.message.reply_text('خدمتی یافت نشد.')
    return ConversationHandler.END

async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_id = query.data.split('_')[1]
    context.user_data['service_id'] = service_id
    telegram_id = str(query.from_user.id)
    response = requests.get(f'{API_BASE_URL}users/profile/', params={'telegram_id': telegram_id})
    if response.status_code == 200:
        user_data = response.json()[0]
        keyboard = [[InlineKeyboardButton(user_data['full_name'], callback_data='recip_self')]]
        keyboard.extend([[InlineKeyboardButton(fm['full_name'], callback_data=f'recip_{fm["id"]}')] for fm in user_data['family_members']])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('لطفاً دریافت‌کننده خدمت را انتخاب کنید:', reply_markup=reply_markup)
        return RECIPIENT
    await query.message.reply_text('لطفاً ابتدا ثبت‌نام کنید.')
    return ConversationHandler.END

async def recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    recipient_data = query.data.split('_')
    context.user_data['recipient_id'] = None if recipient_data[1] == 'self' else recipient_data[1]
    telegram_id = str(query.from_user.id)
    response = requests.get(f'{API_BASE_URL}users/addresses/', params={'telegram_id': telegram_id})
    if response.status_code == 200:
        addresses = response.json()
        keyboard = [[InlineKeyboardButton(addr['title'], callback_data=f'addr_{addr["id"]}')] for addr in addresses]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('لطفاً آدرس مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
        return ADDRESS
    await query.message.reply_text('لطفاً ابتدا آدرس اضافه کنید.')
    return ConversationHandler.END

async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    address_id = query.data.split('_')[1]
    context.user_data['address_id'] = address_id
    today = jdatetime.date.today()
    keyboard = [
        [InlineKeyboardButton(str(today + jdatetime.timedelta(days=i)), callback_data=f'date_{i}')]
        for i in range(7)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('لطفاً تاریخ دریافت خدمت را انتخاب کنید:', reply_markup=reply_markup)
    return DATE

async def date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    days = int(query.data.split('_')[1])
    selected_date = jdatetime.date.today() + jdatetime.timedelta(days=days)
    context.user_data['selected_date'] = selected_date
    keyboard = [
        [InlineKeyboardButton(f"{h}:00", callback_data=f'time_{h}')] for h in range(8, 18)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('لطفاً ساعت دریافت خدمت را انتخاب کنید:', reply_markup=reply_markup)
    return TIME

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    hour = int(query.data.split('_')[1])
    selected_datetime = jdatetime.datetime.combine(context.user_data['selected_date'], jdatetime.time(hour, 0))
    context.user_data['scheduled_time'] = selected_datetime.strftime('%Y-%m-%d %H:%M:%S')
    await query.message.reply_text('لطفاً شرایط خاص (در صورت وجود) را وارد کنید یا بنویسید "ندارد":')
    return SPECIAL_CONDITIONS

async def special_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['special_conditions'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("مرد", callback_data='pref_male')],
        [InlineKeyboardButton("زن", callback_data='pref_female')],
        [InlineKeyboardButton("فرقی ندارد", callback_data='pref_any')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('آیا جنسیت درمانگر برای شما مهم است؟', reply_markup=reply_markup)
    return PREFERRED_GENDER

async def preferred_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pref_gender = query.data.split('_')[1]
    context.user_data['preferred_gender'] = pref_gender

    # Register order via API
    data = {
        'service_id': context.user_data['service_id'],
        'address_id': context.user_data['address_id'],
        'recipient_id': context.user_data['recipient_id'],
        'preferred_gender': pref_gender,
        'special_conditions': context.user_data['special_conditions'],
        'scheduled_time': context.user_data['scheduled_time'],
    }
    response = requests.post(f'{API_BASE_URL}orders/orders/', json=data)
    if response.status_code == 201:
        order = response.json()
        recipient_name = order['recipient']['full_name'] if order['recipient'] else order['user']['full_name']
        await query.message.reply_text(
            f"درخواست شما ثبت شد:\n"
            f"دریافت‌کننده: {recipient_name}\n"
            f"خدمت: {order['service']['name']}\n"
            f"آدرس: {order['address']['title']}\n"
            f"زمان: {order['scheduled_time']}\n"
            f"جنسیت درمانگر: {pref_gender}\n"
            f"شرایط خاص: {order['special_conditions']}"
        )
    else:
        await query.message.reply_text('خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('عملیات لغو شد.')
    return ConversationHandler.END

async def webhook_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^(register|request_service|add_family_member|add_address)$')],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_number)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            GENDER: [CallbackQueryHandler(gender, pattern='^(male|female)$')],
            MEDICAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, medical_conditions)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, region)],
            FM_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_full_name)],
            FM_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_age)],
            FM_GENDER: [CallbackQueryHandler(fm_gender, pattern='^fm_(male|female)$')],
            FM_MEDICAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_medical_conditions)],
            FM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_email)],
            FM_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_region)],
            FM_RELATIONSHIP: [CallbackQueryHandler(fm_relationship, pattern='^fm_')],
            ADDR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addr_title)],
            ADDR_FULL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, addr_full_address)],
            ADDR_LOCATION: [MessageHandler(filters.TEXT | filters.LOCATION, addr_location)],
            CATEGORY: [CallbackQueryHandler(category, pattern='^cat_')],
            SERVICE: [CallbackQueryHandler(service, pattern='^srv_')],
            RECIPIENT: [CallbackQueryHandler(recipient, pattern='^recip_')],
            ADDRESS: [CallbackQueryHandler(address, pattern='^addr_')],
            DATE: [CallbackQueryHandler(date, pattern='^date_')],
            TIME: [CallbackQueryHandler(time, pattern='^time_')],
            SPECIAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, special_conditions)],
            PREFERRED_GENDER: [CallbackQueryHandler(preferred_gender, pattern='^pref_')],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button))

    # Set webhook
    application.run_webhook(
        listen='0.0.0.0',
        port=int(os.environ.get('PORT', 8443)),
        url_path='telegram/webhook/',
        webhook_url=WEBHOOK_URL,
    )

if __name__ == '__main__':
    main()
