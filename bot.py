import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from decouple import config
import requests
import jdatetime
from datetime import datetime
from django.utils import timezone

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for registration conversation
FULL_NAME, PHONE_NUMBER, GENDER, MEDICAL_CONDITIONS, EMAIL = range(5)

# States for order conversation
CATEGORY, SERVICE, RECIPIENT, ADDRESS, DATE, TIME, SPECIAL_CONDITIONS, PREFERRED_GENDER = range(5, 13)

# States for family member conversation
FM_FULL_NAME, FM_BIRTH_DATE, FM_GENDER, FM_MEDICAL_CONDITIONS, FM_EMAIL, FM_REGION, FM_RELATIONSHIP = range(13, 20)

# States for address conversation
ADDR_TITLE, ADDR_FULL_ADDRESS, ADDR_LOCATION = range(20, 23)

# States for cancel order conversation
CANCEL_ORDER = 23

# States for edit address conversation
EDIT_ADDRESS, EDIT_ADDR_TITLE, EDIT_ADDR_FULL_ADDRESS, EDIT_ADDR_LOCATION = range(24, 28)

# States for document upload conversation
UPLOAD_DOCUMENT, DOCUMENT_DESCRIPTION = range(28, 30)

# States for profile edit conversation
EDIT_PROFILE, EDIT_BIRTH_DATE, EDIT_REGION = range(30, 33)

# API Base URL
API_BASE_URL = config('API_BASE_URL', default='https://your-render-app.onrender.com/api/')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ثبت‌نام", callback_data='register')],
        [InlineKeyboardButton("پروفایل", callback_data='profile')],
        [InlineKeyboardButton("درخواست خدمت", callback_data='request_service')],
        [InlineKeyboardButton("لغو درخواست", callback_data='cancel_order')],
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
            [InlineKeyboardButton("ویرایش پروفایل", callback_data='edit_profile')],
            [InlineKeyboardButton("افزودن عضو خانواده", callback_data='add_family_member')],
            [InlineKeyboardButton("ویرایش/حذف عضو خانواده", callback_data='manage_family_member')],
            [InlineKeyboardButton("افزودن آدرس", callback_data='add_address')],
            [InlineKeyboardButton("ویرایش/حذف آدرس", callback_data='manage_address')],
            [InlineKeyboardButton("آپلود مدارک پزشکی", callback_data='upload_document')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('گزینه مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
    elif query.data == 'show_profile':
        phone_number = context.user_data.get('phone_number')
        if not phone_number:
            await query.message.reply_text('لطفاً ابتدا ثبت‌نام کنید.')
            return ConversationHandler.END
        response = requests.get(f'{API_BASE_URL}users/profile/', params={'phone_number': phone_number})
        if response.status_code == 200:
            user_data = response.json()[0]
            family_members = "\n".join([f"{fm['full_name']} ({fm['relationship']})" for fm in user_data['family_members']])
            addresses = "\n".join([addr['title'] for addr in user_data['addresses']])
            documents = "\n".join([f"{fm['full_name']}: {doc['description']}" for fm in user_data['family_members'] for doc in fm.get('documents', [])])
            birth_date = user_data['birth_date']
            if birth_date:
                birth_date = jdatetime.date.fromgregorian(date=datetime.strptime(birth_date, '%Y-%m-%d')).strftime('%Y/%m/%d')
            else:
                birth_date = 'وارد نشده'
            region = user_data['region'] or 'وارد نشده'
            age = user_data['age'] or 'محاسبه نشده'
            await query.message.reply_text(
                f"نام: {user_data['full_name']}\n"
                f"تلفن: {user_data['phone_number']}\n"
                f"تاریخ تولد: {birth_date}\n"
                f"سن: {age}\n"
                f"جنسیت: {user_data['gender']}\n"
                f"بیماری‌ها: {user_data['medical_conditions']}\n"
                f"ایمیل: {user_data['email']}\n"
                f"منطقه: {region}\n"
                f"اعضای خانواده:\n{family_members or 'هیچ عضوی ثبت نشده'}\n"
                f"آدرس‌ها:\n{addresses or 'هیچ آدرسی ثبت نشده'}\n"
                f"مدارک پزشکی:\n{documents or 'هیچ مدرکی ثبت نشده'}"
            )
        else:
            await query.message.reply_text('لطفاً ابتدا ثبت‌نام کنید.')
    elif query.data == 'edit_profile':
        keyboard = [
            [InlineKeyboardButton("ویرایش تاریخ تولد", callback_data='edit_birth_date')],
            [InlineKeyboardButton("ویرایش منطقه", callback_data='edit_region')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('کدام اطلاعات را می‌خواهید ویرایش کنید؟', reply_markup=reply_markup)
        return EDIT_PROFILE
    elif query.data == 'edit_birth_date':
        await query.message.reply_text('لطفاً تاریخ تولد خود را به فرمت جلالی وارد کنید (مثال: 1369/05/15):')
        return EDIT_BIRTH_DATE
    elif query.data == 'edit_region':
        await query.message.reply_text('لطفاً منطقه محل زندگی خود را وارد کنید (مثال: تهران، سعادت‌آباد) یا "خالی" برای حذف:')
        return EDIT_REGION
    elif query.data == 'add_family_member':
        await query.message.reply_text('لطفاً نام و نام خانوادگی عضو خانواده را وارد کنید:')
        return FM_FULL_NAME
    elif query.data == 'manage_family_member':
        phone_number = context.user_data.get('phone_number')
        response = requests.get(f'{API_BASE_URL}users/family-members/', params={'phone_number': phone_number})
        if response.status_code == 200:
            family_members = response.json()
            keyboard = [
                [InlineKeyboardButton(f"{fm['full_name']} (ویرایش)", callback_data=f'edit_fm_{fm["id"]}'),
                 InlineKeyboardButton(f"{fm['full_name']} (حذف)", callback_data=f'delete_fm_{fm["id"]}')]
                for fm in family_members
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('عضو خانواده را برای ویرایش یا حذف انتخاب کنید:', reply_markup=reply_markup)
            return FM_FULL_NAME
        await query.message.reply_text('هیچ عضوی یافت نشد.')
        return ConversationHandler.END
    elif query.data.startswith('edit_fm_'):
        fm_id = query.data.split('_')[2]
        context.user_data['fm_id'] = fm_id
        await query.message.reply_text('لطفاً نام و نام خانوادگی جدید را وارد کنید:')
        return FM_FULL_NAME
    elif query.data.startswith('delete_fm_'):
        fm_id = query.data.split('_')[2]
        phone_number = context.user_data.get('phone_number')
        response = requests.delete(f'{API_BASE_URL}users/family-members/{fm_id}/', params={'phone_number': phone_number})
        if response.status_code == 204:
            await query.message.reply_text('عضو خانواده با موفقیت حذف شد.')
        else:
            await query.message.reply_text('خطا در حذف عضو خانواده.')
        return ConversationHandler.END
    elif query.data == 'add_address':
        await query.message.reply_text('لطفاً عنوان آدرس (مثل "خانه" یا "محل کار") را وارد کنید:')
        return ADDR_TITLE
    elif query.data == 'manage_address':
        phone_number = context.user_data.get('phone_number')
        response = requests.get(f'{API_BASE_URL}users/addresses/', params={'phone_number': phone_number})
        if response.status_code == 200:
            addresses = response.json()
            keyboard = [
                [InlineKeyboardButton(f"{addr['title']} (ویرایش)", callback_data=f'edit_addr_{addr["id"]}'),
                 InlineKeyboardButton(f"{addr['title']} (حذف)", callback_data=f'delete_addr_{addr["id"]}')]
                for addr in addresses
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('آدرس مورد نظر برای ویرایش یا حذف را انتخاب کنید:', reply_markup=reply_markup)
            return EDIT_ADDRESS
        await query.message.reply_text('هیچ آدرسی یافت نشد.')
        return ConversationHandler.END
    elif query.data.startswith('edit_addr_'):
        addr_id = query.data.split('_')[2]
        context.user_data['addr_id'] = addr_id
        await query.message.reply_text('لطفاً عنوان جدید آدرس را وارد کنید:')
        return EDIT_ADDR_TITLE
    elif query.data.startswith('delete_addr_'):
        addr_id = query.data.split('_')[2]
        phone_number = context.user_data.get('phone_number')
        response = requests.delete(f'{API_BASE_URL}users/addresses/{addr_id}/', params={'phone_number': phone_number})
        if response.status_code == 204:
            await query.message.reply_text('آدرس با موفقیت حذف شد.')
        else:
            await query.message.reply_text('خطا در حذف آدرس.')
        return ConversationHandler.END
    elif query.data == 'upload_document':
        phone_number = context.user_data.get('phone_number')
        response = requests.get(f'{API_BASE_URL}users/family-members/', params={'phone_number': phone_number})
        if response.status_code == 200:
            family_members = response.json()
            keyboard = [[InlineKeyboardButton(fm['full_name'], callback_data=f'upload_doc_{fm["id"]}')] for fm in family_members]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً عضو خانواده‌ای که می‌خواهید مدرک برای او آپلود کنید را انتخاب کنید:', reply_markup=reply_markup)
            return UPLOAD_DOCUMENT
        await query.message.reply_text('لطفاً ابتدا عضو خانواده اضافه کنید.')
        return ConversationHandler.END
    elif query.data.startswith('upload_doc_'):
        fm_id = query.data.split('_')[2]
        context.user_data['fm_id'] = fm_id
        await query.message.reply_text('لطفاً فایل مدرک پزشکی (PDF، JPEG، یا PNG، حداکثر 5MB) را آپلود کنید:')
        return UPLOAD_DOCUMENT
    elif query.data == 'request_service':
        response = requests.get(f'{API_BASE_URL}services/categories/')
        if response.status_code == 200:
            categories = response.json()
            keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'cat_{cat["id"]}')] for cat in categories]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً یک دسته‌بندی انتخاب کنید:', reply_markup=reply_markup)
            return CATEGORY
    elif query.data == 'cancel_order':
        phone_number = context.user_data.get('phone_number')
        response = requests.get(f'{API_BASE_URL}orders/orders/', params={'phone_number': phone_number})
        if response.status_code == 200:
            orders = response.json()
            now = jdatetime.datetime.now()
            keyboard = [
                [InlineKeyboardButton(
                    f"{order['service']['name']} - {order['scheduled_time']}",
                    callback_data=f'cancel_{order["id"]}'
                )] for order in orders if (
                    jdatetime.datetime.strptime(order['scheduled_time'], '%Y-%m-%d %H:%M:%S') > now + jdatetime.timedelta(hours=24)
                    and order['status'] != 'canceled'
                )
            ]
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text('درخواست مورد نظر برای لغو را انتخاب کنید:', reply_markup=reply_markup)
                return CANCEL_ORDER
            await query.message.reply_text('هیچ درخواست قابل لغوی یافت نشد.')
        return ConversationHandler.END
    elif query.data == 'contact_support':
        await query.message.reply_text('لطفاً با پشتیبانی در شماره 123456789 تماس بگیرید یا پیام دهید.')
    elif query.data.startswith('confirm_'):
        order_id = query.data.split('_')[1]
        phone_number = context.user_data.get('phone_number')
        response = requests.patch(f'{API_BASE_URL}orders/orders/{order_id}/', json={'status': 'confirmed'}, params={'phone_number': phone_number})
        if response.status_code == 200:
            await query.message.reply_text('حضور شما تأیید شد.')
        else:
            await query.message.reply_text('خطا در تأیید حضور.')
    return ConversationHandler.END

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    if len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FULL_NAME
    context.user_data['full_name'] = full_name
    keyboard = [[KeyboardButton("اشتراک‌گذاری شماره", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        'لطفاً شماره تلفن خود را وارد کنید یا از دکمه زیر برای اشتراک‌گذاری استفاده کنید:',
        reply_markup=reply_markup
    )
    return PHONE_NUMBER

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
    if not phone_number or len(phone_number) < 10:
        keyboard = [[KeyboardButton("اشتراک‌گذاری شماره", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            'شماره تلفن نامعتبر است. لطفاً شماره‌ای معتبر وارد کنید یا از دکمه زیر استفاده کنید:',
            reply_markup=reply_markup
        )
        return PHONE_NUMBER
    context.user_data['phone_number'] = phone_number
    keyboard = [
        [InlineKeyboardButton("مرد", callback_data='male')],
        [InlineKeyboardButton("زن", callback_data='female')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفاً جنسیت خود را انتخاب کنید:', reply_markup=reply_markup)
    return GENDER

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
    # Register user via API
    data = {
        'phone_number': context.user_data['phone_number'],
        'full_name': context.user_data['full_name'],
        'gender': context.user_data['gender'],
        'medical_conditions': context.user_data['medical_conditions'],
        'email': context.user_data['email'],
    }
    response = requests.post(f'{API_BASE_URL}users/profile/register/', json=data)
    if response.status_code == 200:
        await update.message.reply_text('ثبت‌نام با موفقیت انجام شد!')
    else:
        await update.message.reply_text(f'خطا در ثبت‌نام: {response.json().get("error", "لطفاً دوباره تلاش کنید")}')
    return ConversationHandler.END

async def edit_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    birth_date_text = update.message.text
    try:
        year, month, day = map(int, birth_date_text.split('/'))
        jalali_date = jdatetime.date(year, month, day)
        if jalali_date > jdatetime.date.today():
            await update.message.reply_text('تاریخ تولد نمی‌تواند در آینده باشد. دوباره وارد کنید:')
            return EDIT_BIRTH_DATE
        if jdatetime.date.today().year - year < 18:
            await update.message.reply_text('کاربر باید حداقل 18 سال سن داشته باشد. دوباره وارد کنید:')
            return EDIT_BIRTH_DATE
        birth_date = jalali_date.togregorian()  # Convert to Gregorian for storage
        context.user_data['birth_date'] = birth_date
        phone_number = context.user_data.get('phone_number')
        response = requests.put(
            f'{API_BASE_URL}users/profile/',
            json={'birth_date': birth_date.strftime('%Y-%m-%d')},
            params={'phone_number': phone_number}
        )
        if response.status_code == 200:
            await update.message.reply_text('تاریخ تولد با موفقیت به‌روزرسانی شد!')
        else:
            await update.message.reply_text('خطا در به‌روزرسانی تاریخ تولد.')
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('فرمت تاریخ نامعتبر است. لطفاً به فرمت 1369/05/15 وارد کنید:')
        return EDIT_BIRTH_DATE

async def edit_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text if update.message.text != 'خالی' else ''
    phone_number = context.user_data.get('phone_number')
    response = requests.put(f'{API_BASE_URL}users/profile/', json={'region': region}, params={'phone_number': phone_number})
    if response.status_code == 200:
        await update.message.reply_text('منطقه با موفقیت به‌روزرسانی شد!')
    else:
        await update.message.reply_text('خطا در به‌روزرسانی منطقه.')
    return ConversationHandler.END

async def fm_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    if len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FM_FULL_NAME
    context.user_data['fm_full_name'] = full_name
    await update.message.reply_text('لطفاً تاریخ تولد عضو خانواده را به فرمت جلالی وارد کنید (مثال: 1369/05/15) یا "خالی" برای ادامه بدون تاریخ تولد:')
    return FM_BIRTH_DATE

async def fm_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    birth_date_text = update.message.text
    if birth_date_text == 'خالی':
        context.user_data['fm_birth_date'] = None
    else:
        try:
            year, month, day = map(int, birth_date_text.split('/'))
            jalali_date = jdatetime.date(year, month, day)
            if jalali_date > jdatetime.date.today():
                await update.message.reply_text('تاریخ تولد نمی‌تواند در آینده باشد. دوباره وارد کنید:')
                return FM_BIRTH_DATE
            birth_date = jalali_date.togregorian()  # Convert to Gregorian for storage
            context.user_data['fm_birth_date'] = birth_date
        except ValueError:
            await update.message.reply_text('فرمت تاریخ نامعتبر است. لطفاً به فرمت 1369/05/15 وارد کنید یا "خالی" بنویسید:')
            return FM_BIRTH_DATE
    keyboard = [
        [InlineKeyboardButton("مرد", callback_data='fm_male')],
        [InlineKeyboardButton("زن", callback_data='fm_female')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفاً جنسیت عضو خانواده را انتخاب کنید:', reply_markup=reply_markup)
    return FM_GENDER

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
    await update.message.reply_text('لطفاً منطقه محل زندگی عضو خانواده را وارد کنید (اختیاری، مثال: تهران، سعادت‌آباد) یا "خالی" بنویسید:')
    return FM_REGION

async def fm_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fm_region'] = update.message.text if update.message.text != 'خالی' else ''
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
    phone_number = context.user_data.get('phone_number')

    # Register or update family member via API
    data = {
        'full_name': context.user_data['fm_full_name'],
        'birth_date': context.user_data['fm_birth_date'].strftime('%Y-%m-%d') if context.user_data['fm_birth_date'] else None,
        'gender': context.user_data['fm_gender'],
        'medical_conditions': context.user_data['fm_medical_conditions'],
        'email': context.user_data['fm_email'],
        'region': context.user_data['fm_region'],
        'relationship': relationship,
    }
    if 'fm_id' in context.user_data:
        response = requests.put(f'{API_BASE_URL}users/family-members/{context.user_data["fm_id"]}/', json=data, params={'phone_number': phone_number})
        context.user_data.pop('fm_id')
    else:
        response = requests.post(f'{API_BASE_URL}users/family-members/', json=data, params={'phone_number': phone_number})
    if response.status_code in (200, 201):
        await query.message.reply_text('عضو خانواده با موفقیت اضافه/ویرایش شد!')
    else:
        await query.message.reply_text('خطا در افزودن/ویرایش عضو خانواده.')
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
    phone_number = context.user_data.get('phone_number')
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
    response = requests.post(f'{API_BASE_URL}users/addresses/', json=data, params={'phone_number': phone_number})
    if response.status_code == 201:
        await update.message.reply_text('آدرس با موفقیت اضافه شد!')
    else:
        await update.message.reply_text('خطا در افزودن آدرس.')
    return ConversationHandler.END

async def edit_addr_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    if len(title) < 2:
        await update.message.reply_text('عنوان آدرس باید حداقل 2 کاراکتر باشد. دوباره وارد کنید:')
        return EDIT_ADDR_TITLE
    context.user_data['addr_title'] = title
    await update.message.reply_text('لطفاً آدرس کامل جدید را وارد کنید:')
    return EDIT_ADDR_FULL_ADDRESS

async def edit_addr_full_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['addr_full_address'] = update.message.text
    await update.message.reply_text('لطفاً لوکیشن جدید را از طریق تلگرام ارسال کنید یا بنویسید "خالی" برای ادامه بدون لوکیشن:')
    return EDIT_ADDR_LOCATION

async def edit_addr_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = context.user_data.get('phone_number')
    if update.message.text == 'خالی':
        latitude, longitude = None, None
    else:
        location = update.message.location
        if not location:
            await update.message.reply_text('لوکیشن نامعتبر است. لطفاً لوکیشن ارسال کنید یا "خالی" بنویسید:')
            return EDIT_ADDR_LOCATION
        latitude, longitude = location.latitude, location.longitude

    # Update address via API
    data = {
        'title': context.user_data['addr_title'],
        'full_address': context.user_data['addr_full_address'],
        'latitude': latitude,
        'longitude': longitude,
    }
    response = requests.put(f'{API_BASE_URL}users/addresses/{context.user_data["addr_id"]}/', json=data, params={'phone_number': phone_number})
    if response.status_code == 200:
        await update.message.reply_text('آدرس با موفقیت ویرایش شد!')
    else:
        await update.message.reply_text('خطا در ویرایش آدرس.')
    context.user_data.pop('addr_id')
    return ConversationHandler.END

async def upload_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text('لطفاً یک فایل معتبر (PDF، JPEG، یا PNG) آپلود کنید:')
        return UPLOAD_DOCUMENT
    document = update.message.document
    if document.file_size > 5 * 1024 * 1024:  # 5MB limit
        await update.message.reply_text('فایل باید کمتر از 5MB باشد. لطفاً فایل دیگری آپلود کنید:')
        return UPLOAD_DOCUMENT
    if document.mime_type not in ['application/pdf', 'image/jpeg', 'image/png']:
        await update.message.reply_text('فقط فایل‌های PDF، JPEG، یا PNG مجاز هستند. لطفاً فایل دیگری آپلود کنید:')
        return UPLOAD_DOCUMENT
    context.user_data['document'] = document
    await update.message.reply_text('لطفاً توضیح مختصری برای مدرک وارد کنید (مثلاً "نسخه پزشک"):')
    return DOCUMENT_DESCRIPTION

async def document_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    phone_number = context.user_data.get('phone_number')
    document = context.user_data['document']
    file = await document.get_file()
    file_data = await file.download_as_bytearray()
    
    # Upload document via API
    files = {'file': (document.file_name, file_data, document.mime_type)}
    data = {
        'description': description,
        'family_member_id': context.user_data['fm_id'],
        'phone_number': phone_number,
    }
    response = requests.post(f'{API_BASE_URL}users/documents/', files=files, data=data)
    if response.status_code == 201:
        await update.message.reply_text('مدرک پزشکی با موفقیت آپلود شد!')
    else:
        await update.message.reply_text('خطا در آپلود مدرک.')
    context.user_data.pop('fm_id')
    context.user_data.pop('document')
    return ConversationHandler.END

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = query.data.split('_')[1]
    context.user_data['category_id'] = category_id
    phone_number = context.user_data.get('phone_number')
    response = requests.get(f'{API_BASE_URL}users/profile/', params={'phone_number': phone_number})
    if response.status_code == 200:
        user_data = response.json()[0]
        recipient_age = user_data['age'] or 30  # Default age if not provided
        family_members = user_data['family_members']
        recipient_id = context.user_data.get('recipient_id')
        if recipient_id:
            recipient = next((fm for fm in family_members if fm['id'] == int(recipient_id)), None)
            recipient_age = recipient['age'] if recipient else recipient_age
        response = requests.get(f'{API_BASE_URL}services/services/', params={'category': category_id})
        if response.status_code == 200:
            services = response.json()
            filtered_services = [srv for srv in services if (
                (recipient_age < 18 and 'کودکان' in srv['name']) or
                (recipient_age >= 60 and 'سالمندان' in srv['name']) or
                (18 <= recipient_age < 60)
            )]
            keyboard = [[InlineKeyboardButton(srv['name'], callback_data=f'srv_{srv["id"]}')] for srv in filtered_services]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً یک خدمت انتخاب کنید:', reply_markup=reply_markup)
            return SERVICE
        await query.message.reply_text('خدمتی یافت نشد.')
        return ConversationHandler.END
    await query.message.reply_text('لطفاً ابتدا ثبت‌نام کنید.')
    return ConversationHandler.END

async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_id = query.data.split('_')[1]
    context.user_data['service_id'] = service_id
    phone_number = context.user_data.get('phone_number')
    response = requests.get(f'{API_BASE_URL}users/profile/', params={'phone_number': phone_number})
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
    phone_number = context.user_data.get('phone_number')
    response = requests.get(f'{API_BASE_URL}users/addresses/', params={'phone_number': phone_number})
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
        await query.message.reply_text('خطا در ثبت درخواست.')
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = query.data.split('_')[1]
    phone_number = context.user_data.get('phone_number')
    response = requests.patch(f'{API_BASE_URL}orders/orders/{order_id}/', json={'status': 'canceled'}, params={'phone_number': phone_number})
    if response.status_code == 200:
        await query.message.reply_text('درخواست با موفقیت لغو شد.')
    else:
        await query.message.reply_text('خطا در لغو درخواست.')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('عملیات لغو شد.')
    return ConversationHandler.END

def setup_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^(register|request_service|add_family_member|add_address|manage_family_member|cancel_order|manage_address|upload_document|edit_profile)$')],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND | filters.CONTACT, phone_number)],
            GENDER: [CallbackQueryHandler(gender, pattern='^(male|female)$')],
            MEDICAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, medical_conditions)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            FM_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_full_name)],
            FM_BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_birth_date)],
            FM_GENDER: [CallbackQueryHandler(fm_gender, pattern='^fm_(male|female)$')],
            FM_MEDICAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_medical_conditions)],
            FM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_email)],
            FM_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_region)],
            FM_RELATIONSHIP: [CallbackQueryHandler(fm_relationship, pattern='^fm_')],
            ADDR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, addr_title)],
            ADDR_FULL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, addr_full_address)],
            ADDR_LOCATION: [MessageHandler(filters.TEXT | filters.LOCATION, addr_location)],
            EDIT_ADDRESS: [CallbackQueryHandler(button, pattern='^(edit_addr_|delete_addr_)')],
            EDIT_ADDR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_addr_title)],
            EDIT_ADDR_FULL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_addr_full_address)],
            EDIT_ADDR_LOCATION: [MessageHandler(filters.TEXT | filters.LOCATION, edit_addr_location)],
            UPLOAD_DOCUMENT: [MessageHandler(filters.Document.ALL, upload_document)],
            DOCUMENT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, document_description)],
            CATEGORY: [CallbackQueryHandler(category, pattern='^cat_')],
            SERVICE: [CallbackQueryHandler(service, pattern='^srv_')],
            RECIPIENT: [CallbackQueryHandler(recipient, pattern='^recip_')],
            ADDRESS: [CallbackQueryHandler(address, pattern='^addr_')],
            DATE: [CallbackQueryHandler(date, pattern='^date_')],
            TIME: [CallbackQueryHandler(time, pattern='^time_')],
            SPECIAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, special_conditions)],
            PREFERRED_GENDER: [CallbackQueryHandler(preferred_gender, pattern='^pref_')],
            CANCEL_ORDER: [CallbackQueryHandler(cancel_order, pattern='^cancel_')],
            EDIT_PROFILE: [CallbackQueryHandler(button, pattern='^(edit_birth_date|edit_region)$')],
            EDIT_BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_birth_date)],
            EDIT_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_region)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button))
    