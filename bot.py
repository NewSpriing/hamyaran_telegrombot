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
import json

# Enable detailed logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# States for registration conversation
FULL_NAME, PHONE_NUMBER, AGE, GENDER, MEDICAL_CONDITIONS, EMAIL, REGION = range(7)

# States for order conversation
CATEGORY, SERVICE, RECIPIENT, ADDRESS, DATE, TIME, SPECIAL_CONDITIONS, PREFERRED_GENDER = range(7, 15)

# States for family member conversation
FM_FULL_NAME, FM_AGE, FM_GENDER, FM_MEDICAL_CONDITIONS, FM_EMAIL, FM_REGION, FM_RELATIONSHIP = range(15, 22)

# States for address conversation
ADDR_TITLE, ADDR_FULL_ADDRESS, ADDR_LOCATION = range(22, 25)

# States for edit family member conversation
FM_EDIT_FULL_NAME, FM_EDIT_AGE, FM_EDIT_GENDER, FM_EDIT_MEDICAL_CONDITIONS, FM_EDIT_EMAIL, FM_EDIT_REGION, FM_EDIT_RELATIONSHIP = range(25, 32)

# Telegram Bot Token and Webhook URL
TOKEN = config('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = config('WEBHOOK_URL', default='https://medical-bot-tpl6.onrender.com/telegram/webhook/')
ADMIN_CHAT_ID = config('ADMIN_CHAT_ID', default=None)  # Optional: Set admin chat ID for error notifications

# API Base URL
API_BASE_URL = config('API_BASE_URL', default='https://medical-bot-tpl6.onrender.com/api/')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received /start command from user %s", update.effective_user.id)
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
    logger.debug("Received callback query: %s from user %s", query.data, query.from_user.id)

    if query.data == 'register':
        await query.message.reply_text('لطفاً نام و نام خانوادگی خود را وارد کنید:')
        return FULL_NAME
    elif query.data == 'profile':
        keyboard = [
            [InlineKeyboardButton("نمایش اطلاعات", callback_data='show_profile')],
            [InlineKeyboardButton("افزودن عضو خانواده", callback_data='add_family_member')],
            [InlineKeyboardButton("مدیریت اعضای خانواده", callback_data='manage_family_members')],
            [InlineKeyboardButton("افزودن آدرس", callback_data='add_address')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('گزینه مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
    elif query.data == 'show_profile':
        telegram_id = str(query.from_user.id)
        try:
            response = requests.get(f'{API_BASE_URL}users/profile/', params={'telegram_id': telegram_id})
            logger.debug("Profile API response: %s", response.status_code)
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
        except Exception as e:
            logger.error("Error fetching profile: %s", e)
            await query.message.reply_text('خطا در دریافت اطلاعات پروفایل.')
            await notify_admin(context, f"Error fetching profile for user {telegram_id}: {e}")
    elif query.data == 'add_family_member':
        await query.message.reply_text('لطفاً نام و نام خانوادگی عضو خانواده را وارد کنید:')
        return FM_FULL_NAME
    elif query.data == 'manage_family_members':
        telegram_id = str(query.from_user.id)
        try:
            response = requests.get(f'{API_BASE_URL}users/family-members/', params={'telegram_id': telegram_id})
            logger.debug("Family members API response: %s", response.status_code)
            if response.status_code == 200:
                family_members = response.json()
                keyboard = [
                    [InlineKeyboardButton(f"{fm['full_name']} ({fm['relationship']})", callback_data=f'fm_manage_{fm["id"]}')]
                    for fm in family_members
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text('عضو خانواده را برای مدیریت انتخاب کنید:', reply_markup=reply_markup)
            else:
                await query.message.reply_text('هیچ عضوی ثبت نشده است.')
        except Exception as e:
            logger.error("Error fetching family members: %s", e)
            await query.message.reply_text('خطا در دریافت اعضای خانواده.')
            await notify_admin(context, f"Error fetching family members for user {telegram_id}: {e}")
    elif query.data.startswith('fm_manage_'):
        fm_id = query.data.split('_')[2]
        context.user_data['fm_id'] = fm_id
        keyboard = [
            [InlineKeyboardButton("ویرایش", callback_data='fm_edit')],
            [InlineKeyboardButton("حذف", callback_data='fm_delete')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('اقدام مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
    elif query.data == 'fm_edit':
        await query.message.reply_text('لطفاً نام و نام خانوادگی جدید را وارد کنید (یا برای نگه داشتن مقدار قبلی، "بدون تغییر" بنویسید):')
        return FM_EDIT_FULL_NAME
    elif query.data == 'fm_delete':
        fm_id = context.user_data['fm_id']
        telegram_id = str(query.from_user.id)
        try:
            response = requests.delete(f'{API_BASE_URL}users/family-members/{fm_id}/delete/', params={'telegram_id': telegram_id})
            logger.debug("Delete family member API response: %s", response.status_code)
            if response.status_code == 204:
                await query.message.reply_text('عضو خانواده با موفقیت حذف شد.')
            else:
                await query.message.reply_text('خطا در حذف عضو خانواده.')
        except Exception as e:
            logger.error("Error deleting family member: %s", e)
            await query.message.reply_text('خطا در حذف عضو خانواده.')
            await notify_admin(context, f"Error deleting family member {fm_id} for user {telegram_id}: {e}")
        return ConversationHandler.END
    elif query.data == 'add_address':
        await query.message.reply_text('لطفاً عنوان آدرس (مثل "خانه" یا "محل کار") را وارد کنید:')
        return ADDR_TITLE
    elif query.data == 'request_service':
        try:
            response = requests.get(f'{API_BASE_URL}services/categories/')
            logger.debug("Categories API response: %s", response.status_code)
            if response.status_code == 200:
                categories = response.json()
                keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'cat_{cat["id"]}')] for cat in categories]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text('لطفاً یک دسته‌بندی انتخاب کنید:', reply_markup=reply_markup)
                return CATEGORY
            await query.message.reply_text('خطا در دریافت دسته‌بندی‌ها.')
        except Exception as e:
            logger.error("Error fetching categories: %s", e)
            await query.message.reply_text('خطا در دریافت دسته‌بندی‌ها.')
            await notify_admin(context, f"Error fetching categories for user {query.from_user.id}: {e}")
    return ConversationHandler.END

async def full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    logger.debug("Received full name: %s from user %s", full_name, update.effective_user.id)
    if len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FULL_NAME
    context.user_data['full_name'] = full_name
    await update.message.reply_text('لطفاً شماره تلفن خود را وارد کنید (مثال: +989123456789):')
    return PHONE_NUMBER

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    logger.debug("Received phone number: %s from user %s", phone_number, update.effective_user.id)
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
    logger.debug("Received age: %s from user %s", age_text, update.effective_user.id)
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
    logger.debug("Received gender: %s from user %s", query.data, query.from_user.id)
    await query.message.reply_text('لطفاً بیماری‌های زمینه‌ای خود را وارد کنید (در صورت عدم وجود، بنویسید "ندارد"):')
    return MEDICAL_CONDITIONS

async def medical_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['medical_conditions'] = update.message.text
    logger.debug("Received medical conditions: %s from user %s", update.message.text, update.effective_user.id)
    await update.message.reply_text('لطفاً ایمیل خود را وارد کنید (اختیاری، برای بازیابی رمز عبور):')
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    logger.debug("Received email: %s from user %s", email, update.effective_user.id)
    if email and '@' not in email:
        await update.message.reply_text('ایمیل نامعتبر است. لطفاً دوباره وارد کنید یا برای خالی گذاشتن، "خالی" بنویسید:')
        return EMAIL
    context.user_data['email'] = email if email != 'خالی' else ''
    await update.message.reply_text('لطفاً منطقه محل زندگی خود را وارد کنید (مثال: تهران، سعادت‌آباد):')
    return REGION

async def region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['region'] = update.message.text
    logger.debug("Received region: %s from user %s", update.message.text, update.effective_user.id)
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
    try:
        response = requests.post(f'{API_BASE_URL}users/profile/register/', json=data)
        logger.debug("Register API response: %s", response.status_code)
        if response.status_code == 200:
            await update.message.reply_text('ثبت‌نام با موفقیت انجام شد!')
        else:
            await update.message.reply_text(f'خطا در ثبت‌نام: {response.json().get("error", "لطفاً دوباره تلاش کنید")}')
    except Exception as e:
        logger.error("Error registering user: %s", e)
        await update.message.reply_text('خطا در ثبت‌نام.')
        await notify_admin(context, f"Error registering user {telegram_id}: {e}")
    return ConversationHandler.END

async def fm_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    logger.debug("Received family member full name: %s from user %s", full_name, update.effective_user.id)
    if len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FM_FULL_NAME
    context.user_data['fm_full_name'] = full_name
    await update.message.reply_text('لطفاً سن عضو خانواده را وارد کنید (بین 0 تا 120):')
    return FM_AGE

async def fm_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age_text = update.message.text
    logger.debug("Received family member age: %s from user %s", age_text, update.effective_user.id)
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
    logger.debug("Received family member gender: %s from user %s", query.data, query.from_user.id)
    await query.message.reply_text('لطفاً بیماری‌های زمینه‌ای عضو خانواده را وارد کنید (در صورت عدم وجود، بنویسید "ندارد"):')
    return FM_MEDICAL_CONDITIONS

async def fm_medical_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fm_medical_conditions'] = update.message.text
    logger.debug("Received family member medical conditions: %s from user %s", update.message.text, update.effective_user.id)
    await update.message.reply_text('لطفاً ایمیل عضو خانواده را وارد کنید (اختیاری):')
    return FM_EMAIL

async def fm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    logger.debug("Received family member email: %s from user %s", email, update.effective_user.id)
    if email and '@' not in email:
        await update.message.reply_text('ایمیل نامعتبر است. لطفاً دوباره وارد کنید یا برای خالی گذاشتن، "خالی" بنویسید:')
        return FM_EMAIL
    context.user_data['fm_email'] = email if email != 'خالی' else ''
    await update.message.reply_text('لطفاً منطقه محل زندگی عضو خانواده را وارد کنید (مثال: تهران، سعادت‌آباد):')
    return FM_REGION

async def fm_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fm_region'] = update.message.text
    logger.debug("Received family member region: %s from user %s", update.message.text, update.effective_user.id)
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
    logger.debug("Received family member relationship: %s from user %s", relationship, query.from_user.id)

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
    try:
        response = requests.post(f'{API_BASE_URL}users/family-members/', json=data, params={'telegram_id': telegram_id})
        logger.debug("Add family member API response: %s", response.status_code)
        if response.status_code == 201:
            await query.message.reply_text('عضو خانواده با موفقیت اضافه شد!')
        else:
            await query.message.reply_text('خطا در افزودن عضو خانواده.')
    except Exception as e:
        logger.error("Error adding family member: %s", e)
        await query.message.reply_text('خطا در افزودن عضو خانواده.')
        await notify_admin(context, f"Error adding family member for user {telegram_id}: {e}")
    return ConversationHandler.END

async def fm_edit_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    logger.debug("Received edit family member full name: %s from user %s", full_name, update.effective_user.id)
    if full_name != 'بدون تغییر' and len(full_name) < 3:
        await update.message.reply_text('نام و نام خانوادگی باید حداقل 3 کاراکتر باشد. دوباره وارد کنید:')
        return FM_EDIT_FULL_NAME
    context.user_data['fm_edit_full_name'] = full_name
    await update.message.reply_text('لطفاً سن جدید را وارد کنید (بین 0 تا 120، یا "بدون تغییر"):')
    return FM_EDIT_AGE

async def fm_edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age_text = update.message.text
    logger.debug("Received edit family member age: %s from user %s", age_text, update.effective_user.id)
    if age_text != 'بدون تغییر':
        try:
            age = int(age_text)
            if not 0 <= age <= 120:
                raise ValueError
            context.user_data['fm_edit_age'] = age
        except ValueError:
            await update.message.reply_text('سن باید عددی بین 0 تا 120 باشد. دوباره وارد کنید:')
            return FM_EDIT_AGE
    else:
        context.user_data['fm_edit_age'] = None
    keyboard = [
        [InlineKeyboardButton("مرد", callback_data='fm_edit_male')],
        [InlineKeyboardButton("زن", callback_data='fm_edit_female')],
        [InlineKeyboardButton("بدون تغییر", callback_data='fm_edit_nochange')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفاً جنسیت جدید را انتخاب کنید:', reply_markup=reply_markup)
    return FM_EDIT_GENDER

async def fm_edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    gender = query.data.split('_')[2] if query.data != 'fm_edit_nochange' else None
    context.user_data['fm_edit_gender'] = gender
    logger.debug("Received edit family member gender: %s from user %s", gender, query.from_user.id)
    await query.message.reply_text('لطفاً بیماری‌های زمینه‌ای جدید را وارد کنید (یا "بدون تغییر" یا "ندارد"):')
    return FM_EDIT_MEDICAL_CONDITIONS

async def fm_edit_medical_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    medical_conditions = update.message.text
    context.user_data['fm_edit_medical_conditions'] = medical_conditions if medical_conditions != 'بدون تغییر' else None
    logger.debug("Received edit family member medical conditions: %s from user %s", medical_conditions, update.effective_user.id)
    await update.message.reply_text('لطفاً ایمیل جدید را وارد کنید (اختیاری، یا "بدون تغییر" یا "خالی"):')
    return FM_EDIT_EMAIL

async def fm_edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    logger.debug("Received edit family member email: %s from user %s", email, update.effective_user.id)
    if email != 'بدون تغییر' and email != 'خالی' and '@' not in email:
        await update.message.reply_text('ایمیل نامعتبر است. لطفاً دوباره وارد کنید یا "بدون تغییر" یا "خالی" بنویسید:')
        return FM_EDIT_EMAIL
    context.user_data['fm_edit_email'] = email if email not in ('بدون تغییر', 'خالی') else ('' if email == 'خالی' else None)
    await update.message.reply_text('لطفاً منطقه جدید را وارد کنید (مثال: تهران، سعادت‌آباد، یا "بدون تغییر"):')
    return FM_EDIT_REGION

async def fm_edit_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text
    context.user_data['fm_edit_region'] = region if region != 'بدون تغییر' else None
    logger.debug("Received edit family member region: %s from user %s", region, update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("پدر", callback_data='fm_edit_father')],
        [InlineKeyboardButton("مادر", callback_data='fm_edit_mother')],
        [InlineKeyboardButton("پسر", callback_data='fm_edit_son')],
        [InlineKeyboardButton("دختر", callback_data='fm_edit_daughter')],
        [InlineKeyboardButton("همسر", callback_data='fm_edit_spouse')],
        [InlineKeyboardButton("خواهر/برادر", callback_data='fm_edit_sibling')],
        [InlineKeyboardButton("سایر", callback_data='fm_edit_other')],
        [InlineKeyboardButton("بدون تغییر", callback_data='fm_edit_nochange')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('لطفاً نسبت جدید را انتخاب کنید:', reply_markup=reply_markup)
    return FM_EDIT_RELATIONSHIP

async def fm_edit_relationship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    relationship = query.data.split('_')[2] if query.data != 'fm_edit_nochange' else None
    telegram_id = str(query.from_user.id)
    fm_id = context.user_data['fm_id']
    logger.debug("Received edit family member relationship: %s from user %s", relationship, query.from_user.id)

    # Update family member via API
    data = {
        'full_name': context.user_data['fm_edit_full_name'] if context.user_data['fm_edit_full_name'] != 'بدون تغییر' else None,
        'age': context.user_data['fm_edit_age'],
        'gender': context.user_data['fm_edit_gender'],
        'medical_conditions': context.user_data['fm_edit_medical_conditions'],
        'email': context.user_data['fm_edit_email'],
        'region': context.user_data['fm_edit_region'],
        'relationship': relationship,
    }
    data = {k: v for k, v in data.items() if v is not None}
    try:
        response = requests.put(f'{API_BASE_URL}users/family-members/{fm_id}/edit/', json=data, params={'telegram_id': telegram_id})
        logger.debug("Edit family member API response: %s", response.status_code)
        if response.status_code == 200:
            await query.message.reply_text('عضو خانواده با موفقیت ویرایش شد!')
        else:
            await query.message.reply_text('خطا در ویرایش عضو خانواده.')
    except Exception as e:
        logger.error("Error editing family member: %s", e)
        await query.message.reply_text('خطا در ویرایش عضو خانواده.')
        await notify_admin(context, f"Error editing family member {fm_id} for user {telegram_id}: {e}")
    return ConversationHandler.END

async def addr_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    logger.debug("Received address title: %s from user %s", title, update.effective_user.id)
    if len(title) < 2:
        await update.message.reply_text('عنوان آدرس باید حداقل 2 کاراکتر باشد. دوباره وارد کنید:')
        return ADDR_TITLE
    context.user_data['addr_title'] = title
    await update.message.reply_text('لطفاً آدرس کامل را وارد کنید:')
    return ADDR_FULL_ADDRESS

async def addr_full_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['addr_full_address'] = update.message.text
    logger.debug("Received full address: %s from user %s", update.message.text, update.effective_user.id)
    await update.message.reply_text('لطفاً لوکیشن خود را از طریق تلگرام ارسال کنید یا بنویسید "خالی" برای ادامه بدون لوکیشن:')
    return ADDR_LOCATION

async def addr_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.from_user.id)
    logger.debug("Received address location: %s from user %s", update.message.text or update.message.location, update.effective_user.id)
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
    try:
        response = requests.post(f'{API_BASE_URL}users/addresses/', json=data, params={'telegram_id': telegram_id})
        logger.debug("Add address API response: %s", response.status_code)
        if response.status_code == 201:
            await update.message.reply_text('آدرس با موفقیت اضافه شد!')
        else:
            await update.message.reply_text('خطا در افزودن آدرس.')
    except Exception as e:
        logger.error("Error adding address: %s", e)
        await update.message.reply_text('خطا در افزودن آدرس.')
        await notify_admin(context, f"Error adding address for user {telegram_id}: {e}")
    return ConversationHandler.END

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = query.data.split('_')[1]
    context.user_data['category_id'] = category_id
    logger.debug("Received category: %s from user %s", category_id, query.from_user.id)
    try:
        response = requests.get(f'{API_BASE_URL}services/services/', params={'category': category_id})
        logger.debug("Services API response: %s", response.status_code)
        if response.status_code == 200:
            services = response.json()
            keyboard = [[InlineKeyboardButton(srv['name'], callback_data=f'srv_{srv["id"]}')] for srv in services]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً یک خدمت انتخاب کنید:', reply_markup=reply_markup)
            return SERVICE
        await query.message.reply_text('خدمتی یافت نشد.')
    except Exception as e:
        logger.error("Error fetching services: %s", e)
        await query.message.reply_text('خطا در دریافت خدمات.')
        await notify_admin(context, f"Error fetching services for user {query.from_user.id}: {e}")
    return ConversationHandler.END

async def service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_id = query.data.split('_')[1]
    context.user_data['service_id'] = service_id
    telegram_id = str(query.from_user.id)
    logger.debug("Received service: %s from user %s", service_id, query.from_user.id)
    try:
        response = requests.get(f'{API_BASE_URL}users/profile/', params={'telegram_id': telegram_id})
        logger.debug("Profile API response for service: %s", response.status_code)
        if response.status_code == 200:
            user_data = response.json()[0]
            keyboard = [[InlineKeyboardButton(user_data['full_name'], callback_data='recip_self')]]
            keyboard.extend([[InlineKeyboardButton(fm['full_name'], callback_data=f'recip_{fm["id"]}')] for fm in user_data['family_members']])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً دریافت‌کننده خدمت را انتخاب کنید:', reply_markup=reply_markup)
            return RECIPIENT
        await query.message.reply_text('لطفاً ابتدا ثبت‌نام کنید.')
    except Exception as e:
        logger.error("Error fetching profile for service: %s", e)
        await query.message.reply_text('خطا در دریافت پروفایل.')
        await notify_admin(context, f"Error fetching profile for service for user {telegram_id}: {e}")
    return ConversationHandler.END

async def recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    recipient_data = query.data.split('_')
    context.user_data['recipient_id'] = None if recipient_data[1] == 'self' else recipient_data[1]
    telegram_id = str(query.from_user.id)
    logger.debug("Received recipient: %s from user %s", recipient_data, query.from_user.id)
    try:
        response = requests.get(f'{API_BASE_URL}users/addresses/', params={'telegram_id': telegram_id})
        logger.debug("Addresses API response: %s", response.status_code)
        if response.status_code == 200:
            addresses = response.json()
            keyboard = [[InlineKeyboardButton(addr['title'], callback_data=f'addr_{addr["id"]}')] for addr in addresses]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text('لطفاً آدرس مورد نظر را انتخاب کنید:', reply_markup=reply_markup)
            return ADDRESS
        await query.message.reply_text('لطفاً ابتدا آدرس اضافه کنید.')
    except Exception as e:
        logger.error("Error fetching addresses: %s", e)
        await query.message.reply_text('خطا در دریافت آدرس‌ها.')
        await notify_admin(context, f"Error fetching addresses for user {telegram_id}: {e}")
    return ConversationHandler.END

async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    address_id = query.data.split('_')[1]
    context.user_data['address_id'] = address_id
    logger.debug("Received address: %s from user %s", address_id, query.from_user.id)
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
    logger.debug("Received date: %s from user %s", selected_date, query.from_user.id)
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
    logger.debug("Received time: %s from user %s", selected_datetime, query.from_user.id)
    await query.message.reply_text('لطفاً شرایط خاص (در صورت وجود) را وارد کنید یا بنویسید "ندارد":')
    return SPECIAL_CONDITIONS

async def special_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['special_conditions'] = update.message.text
    logger.debug("Received special conditions: %s from user %s", update.message.text, update.effective_user.id)
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
    logger.debug("Received preferred gender: %s from user %s", pref_gender, query.from_user.id)

    # Register order via API
    data = {
        'service_id': context.user_data['service_id'],
        'address_id': context.user_data['address_id'],
        'recipient_id': context.user_data['recipient_id'],
        'preferred_gender': pref_gender,
        'special_conditions': context.user_data['special_conditions'],
        'scheduled_time': context.user_data['scheduled_time'],
    }
    try:
        response = requests.post(f'{API_BASE_URL}orders/orders/', json=data)
        logger.debug("Order API response: %s", response.status_code)
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
    except Exception as e:
        logger.error("Error creating order: %s", e)
        await query.message.reply_text('خطا در ثبت درخواست.')
        await notify_admin(context, f"Error creating order for user {query.from_user.id}: {e}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Conversation cancelled by user %s", update.effective_user.id)
    await update.message.reply_text('عملیات لغو شد.')
    return ConversationHandler.END

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received /status command from user %s", update.effective_user.id)
    try:
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getWebhookInfo')
        logger.debug("Webhook info API response: %s", response.status_code)
        if response.status_code == 200:
            webhook_info = response.json()['result']
            await update.message.reply_text(
                f"وضعیت Webhook:\n"
                f"URL: {webhook_info['url']}\n"
                f"Pending Updates: {webhook_info.get('pending_update_count', 0)}\n"
                f"Last Error: {webhook_info.get('last_error_message', 'هیچ خطایی')}"
            )
        else:
            await update.message.reply_text('خطا در بررسی وضعیت Webhook.')
    except Exception as e:
        logger.error("Error fetching webhook status: %s", e)
        await update.message.reply_text('خطا در بررسی وضعیت.')
        await notify_admin(context, f"Error fetching webhook status for user {update.effective_user.id}: {e}")
    return ConversationHandler.END

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received /reset command from user %s", update.effective_user.id)
    try:
        # Delete webhook to clear pending updates
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/deleteWebhook')
        logger.debug("Delete webhook API response: %s", response.status_code)
        if response.status_code == 200:
            # Re-set webhook
            response = requests.get(f'https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}')
            logger.debug("Set webhook API response: %s", response.status_code)
            if response.status_code == 200:
                await update.message.reply_text('Webhook با موفقیت ریست شد. لطفاً دوباره /start را امتحان کنید.')
            else:
                await update.message.reply_text('خطا در تنظیم مجدد Webhook.')
        else:
            await update.message.reply_text('خطا در حذف Webhook.')
    except Exception as e:
        logger.error("Error resetting webhook: %s", e)
        await update.message.reply_text('خطا در ریست Webhook.')
        await notify_admin(context, f"Error resetting webhook for user {update.effective_user.id}: {e}")
    return ConversationHandler.END

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
            logger.debug("Sent error notification to admin: %s", message)
        except Exception as e:
            logger.error("Failed to notify admin: %s", e)

async def webhook_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received webhook update from user %s: %s", update.effective_user.id, json.dumps(update.to_dict(), indent=2))
    try:
        if update.message and update.message.text == '/start':
            return await start(update, context)
        elif update.message and update.message.text == '/status':
            return await status(update, context)
        elif update.message and update.message.text == '/reset':
            return await reset(update, context)
        else:
            return await start(update, context)  # Fallback to start
    except Exception as e:
        logger.error("Error processing webhook update: %s", e)
        await notify_admin(context, f"Webhook error for user {update.effective_user.id}: {e}")
        raise  # Re-raise to return 500 and avoid 400

def main():
    logger.info("Starting bot with token: %s", TOKEN[:10] + "...")
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^(register|request_service|add_family_member|manage_family_members|fm_manage_|fm_edit|fm_delete|add_address)$')],
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
            FM_EDIT_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_edit_full_name)],
            FM_EDIT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_edit_age)],
            FM_EDIT_GENDER: [CallbackQueryHandler(fm_edit_gender, pattern='^fm_edit_(male|female|nochange)$')],
            FM_EDIT_MEDICAL_CONDITIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_edit_medical_conditions)],
            FM_EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_edit_email)],
            FM_EDIT_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, fm_edit_region)],
            FM_EDIT_RELATIONSHIP: [CallbackQueryHandler(fm_edit_relationship, pattern='^fm_edit_')],
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
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('reset', reset))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button))

    # Set webhook
    try:
        logger.info("Setting webhook to %s", WEBHOOK_URL)
        application.run_webhook(
            listen='0.0.0.0',
            port=int(os.environ.get('PORT', 8443)),
            url_path='telegram/webhook/',
            webhook_url=WEBHOOK_URL,
        )
        logger.info("Webhook set successfully to %s", WEBHOOK_URL)
    except Exception as e:
        logger.error("Failed to set webhook: %s", e)
        raise

if __name__ == '__main__':
    main()