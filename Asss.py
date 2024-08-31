import telebot
from telebot import types
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import csv
from datetime import datetime

# Constants
API_TOKEN = "7021349775:AAEx7NysBRsMht30J4H7vJkFS7s6rIAB8Ew"
DEVELOPER_ID =1945109862

# Global Variables
bot = telebot.TeleBot(API_TOKEN)
authorized_users = []
user_email_accounts = {}
messages = []
report_channel_or_group_id = {}
report_subject = {}
report_message = {}
report_image = {}
message_count = {}
send_interval = {}
sending_in_progress = {}
stop_sending = {}
send_schedule = {}
user_sent_records = {}
saved_messages = {}

# Helper Functions
def is_developer(message):
    return message.from_user.id == DEVELOPER_ID

def is_authorized(user_id):
    return user_id in authorized_users

def send_email(email, password, subject, message, to_email, image=None):
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    if image:
        from email.mime.image import MIMEImage
        img = MIMEImage(image)
        msg.attach(img)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, password)
    text = msg.as_string()
    server.sendmail(email, to_email, text)
    server.quit()

def send_report(user_id):
    global sending_in_progress, stop_sending
    
    if sending_in_progress.get(user_id, False):
        bot.send_message(user_id, "عملية الإرسال جارية بالفعل.")
        return
    
    sending_in_progress[user_id] = True
    stop_sending[user_id] = False

    if not report_channel_or_group_id.get(user_id) or not report_subject.get(user_id) or not report_message.get(user_id):
        bot.send_message(user_id, "يجب تعيين البريد والموضوع والرسالة أولاً.")
        sending_in_progress[user_id] = False
        return

    successful_sends = 0
    failed_sends = 0

    status_message = bot.send_message(user_id, f"تــم بدء الارسال\n• عدد مرات الارسال الناجحة: {successful_sends}\n• عدد مرات الارسال الفاشلة: {failed_sends}")

    for i in range(message_count.get(user_id, 0)):
        for j, account in enumerate(user_email_accounts.get(user_id, [])):
            if stop_sending.get(user_id, False):
                bot.send_message(user_id, "تم إيقاف عملية الإرسال.")
                sending_in_progress[user_id] = False
                return
            try:
                send_email(account['email'], account['password'], report_subject[user_id], report_message[user_id], report_channel_or_group_id[user_id], report_image.get(user_id))
                successful_sends += 1
                bot.edit_message_text(chat_id=user_id, message_id=status_message.message_id, text=f"تــم بدء الارسال\n• عدد مرات الارسال الناجحة: {successful_sends}\n• عدد مرات الارسال الفاشلة: {failed_sends}")
            except Exception as e:
                failed_sends += 1
                bot.edit_message_text(chat_id=user_id, message_id=status_message.message_id, text=f"تــم بدء الارسال\n• عدد مرات الارسال الناجحة: {successful_sends}\n• عدد مرات الارسال الفاشلة: {failed_sends}\nفشل إرسال البريد إلى {account['email']}: {e}")
            print()

    sending_in_progress[user_id] = False
    bot.edit_message_text(chat_id=user_id, message_id=status_message.message_id, text=f"تم إنهاء عملية الإرسال بنجاح.\n• عدد مرات الارسال الناجحة: {successful_sends}\n• عدد مرات الارسال الفاشلة: {failed_sends}")
def schedule_send_report(user_id, send_time):
    global send_schedule
    send_schedule[user_id] = send_time
    bot.send_message(user_id, f"تم جدولة عملية الإرسال في {send_time}")

def check_and_send_scheduled_report():
    global send_schedule
    current_time = datetime.now()
    for user_id, send_time in list(send_schedule.items()):
        if send_time and current_time >= send_time:
            send_report(user_id)
            del send_schedule[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_authorized(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="المطور", url=f"tg://user?id={1945109862}")
        markup.add(button)
        bot.send_message(message.chat.id, "ݪۅتِيُ اެنِتِهَ؟؟​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​ࢪاެسُـݪ ډمِتِࢪيُ↝يُفِعٰݪكَ بُۅسُهَ​​​​​​​​​​​​​​​​​​​​​", reply_markup=markup)
    else:

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("إضافة الحسابات", callback_data='add_accounts'),
            types.InlineKeyboardButton("إضافة حسابات متعددة", callback_data='add_multiple_accounts')
        )
        keyboard.row(
            types.InlineKeyboardButton("عرض الحسابات", callback_data='view_accounts'),
            types.InlineKeyboardButton("إدارة الرسائل المحفوظة", callback_data='manage_saved_messages')
        )
        keyboard.row(
            types.InlineKeyboardButton("تحميل قائمة الإيميلات", callback_data='upload_email_list'),
            types.InlineKeyboardButton("عرض سجل الإرسال", callback_data='view_send_log')
        )
        keyboard.row(
            types.InlineKeyboardButton("تعيين البريد", callback_data='set_email'),
            types.InlineKeyboardButton("تعيين الموضوع", callback_data='set_subject')
        )
        keyboard.row(
            types.InlineKeyboardButton("تعيين الرسالة", callback_data='set_message'),
            types.InlineKeyboardButton("تعيين الصورة", callback_data='set_image')
        )
        keyboard.row(
            types.InlineKeyboardButton("تعيين عدد الإرسال", callback_data='set_message_count'),
            types.InlineKeyboardButton("تعيين الفترة الزمنية", callback_data='set_send_interval')
        )
        keyboard.row(
            types.InlineKeyboardButton("عرض المعلومات", callback_data='view_info')
        )
        keyboard.add(types.InlineKeyboardButton("بدء الإرسال", callback_data='start_sending'))
        keyboard.add(types.InlineKeyboardButton("إيقاف الإرسال", callback_data='stop_sending'))
        keyboard.add(types.InlineKeyboardButton("جدولة الإرسال", callback_data='schedule_send'))
        if is_developer(message):
            keyboard.add(types.InlineKeyboardButton("ملف الإيميلات", callback_data='email_file'))
        bot.send_message(message.chat.id, "ᯓ بُۅتِ شِډ خِاެࢪجَيُᯓ ↝❲ډيُمِتِࢪيُ❳", reply_markup=keyboard)

@bot.message_handler(func=lambda message: is_developer(message) and message.text.startswith("ترقية"))
def upgrade_user(message):
    try:
        user_id = int(message.text.split()[1])
        authorized_users.append(user_id)
        bot.send_message(user_id, "تم تفعيل استخدام البوت لك.")
    except:
        bot.send_message(message.chat.id, "خطأ في تحديد المستخدم.")

@bot.message_handler(func=lambda message: is_developer(message) and message.text.startswith("خلع"))
def downgrade_user(message):
    try:
        user_id = int(message.text.split()[1])
        authorized_users.remove(user_id)
        bot.send_message(user_id, "تم خلعك من قبل المطور.")
    except:
        bot.send_message(message.chat.id, "خطأ في تحديد المستخدم.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if is_authorized(call.from_user.id):
        user_id = call.from_user.id
        if call.data == 'add_accounts':
            msg = bot.send_message(call.message.chat.id, "أرسل الإيميل والباسورد بتنسيق email:password")
            bot.register_next_step_handler(msg, add_email_account)
        elif call.data == 'add_multiple_accounts':
            msg = bot.send_message(call.message.chat.id, "أرسل قائمة الحسابات بتنسيق CSV (email,password)")
            bot.register_next_step_handler(msg, add_multiple_email_accounts)
        elif call.data == 'view_accounts':
            if user_id in user_email_accounts:
                accounts = user_email_accounts[user_id]
                keyboard = types.InlineKeyboardMarkup()
                for idx, account in enumerate(accounts):
                    keyboard.row(
                        types.InlineKeyboardButton(account['email'], callback_data=f'account_{idx}'),
                        types.InlineKeyboardButton("حذف", callback_data=f'delete_account_{idx}')
                    )
                bot.send_message(call.message.chat.id, "الحسابات المضافة:", reply_markup=keyboard)
            else:
                bot.send_message(call.message.chat.id, "لا توجد حسابات مضافة.")
        elif call.data.startswith('delete_account_'):
            account_idx = int(call.data.split('_')[-1])
            if user_id in user_email_accounts and account_idx < len(user_email_accounts[user_id]):
                del user_email_accounts[user_id][account_idx]
                bot.send_message(call.message.chat.id, "تم حذف الحساب بنجاح.")
                # Refresh the accounts list view
                callback_query(types.CallbackQuery(
                    id=call.id, 
                    from_user=call.from_user, 
                    message=call.message, 
                    chat_instance=call.chat_instance, 
data='view_accounts'
                ))
        elif call.data == 'manage_saved_messages':
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("إضافة رسالة محفوظة", callback_data='add_saved_message'))
            if user_id in saved_messages:
                for idx, saved_message in enumerate(saved_messages[user_id]):
                    keyboard.add(types.InlineKeyboardButton(f"رسالة {idx + 1}", callback_data=f'saved_message_{idx}'))
            bot.send_message(call.message.chat.id, "إدارة الرسائل المحفوظة:", reply_markup=keyboard)
        elif call.data == 'add_saved_message':
            msg = bot.send_message(call.message.chat.id, "أرسل الرسالة المراد حفظها")
            bot.register_next_step_handler(msg, save_message)
        elif call.data.startswith('saved_message_'):
            message_idx = int(call.data.split('_')[-1])
            if user_id in saved_messages and message_idx < len(saved_messages[user_id]):
                saved_msg = saved_messages[user_id][message_idx]
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("حذف الرسالة", callback_data=f'delete_saved_message_{message_idx}'))
                bot.send_message(call.message.chat.id, f"الرسالة المحفوظة {message_idx + 1}:\n{saved_msg}", reply_markup=keyboard)
        elif call.data.startswith('delete_saved_message_'):
            message_idx = int(call.data.split('_')[-1])
            if user_id in saved_messages and message_idx < len(saved_messages[user_id]):
                del saved_messages[user_id][message_idx]
                bot.send_message(call.message.chat.id, "تم حذف الرسالة المحفوظة بنجاح.")
                # Refresh the saved messages view
                callback_query(types.CallbackQuery(
                    id=call.id, 
                    from_user=call.from_user, 
                    message=call.message, 
                    chat_instance=call.chat_instance, 
                    data='manage_saved_messages'
                ))
        elif call.data == 'upload_email_list':
            msg = bot.send_message(call.message.chat.id, "أرسل قائمة الإيميلات بتنسيق CSV")
            bot.register_next_step_handler(msg, upload_email_list)
        elif call.data == 'view_send_log':
            send_log = user_sent_records.get(user_id, [])
            if send_log:
                bot.send_message(call.message.chat.id, "\n".join(send_log))
            else:
                bot.send_message(call.message.chat.id, "لا توجد سجلات للإرسال.")
        elif call.data == 'set_email':
            msg = bot.send_message(call.message.chat.id, "أرسل البريد المراد الإرسال إليه")
            bot.register_next_step_handler(msg, set_email)
        elif call.data == 'set_subject':
            msg = bot.send_message(call.message.chat.id, "أرسل الموضوع")
            bot.register_next_step_handler(msg, set_subject)
        elif call.data == 'set_message':
            msg = bot.send_message(call.message.chat.id, "أرسل الرسالة")
            bot.register_next_step_handler(msg, set_message)
        elif call.data == 'set_image':
            msg = bot.send_message(call.message.chat.id, "أرسل الصورة")
            bot.register_next_step_handler(msg, set_image)
        elif call.data == 'set_message_count':
            msg = bot.send_message(call.message.chat.id, "أرسل عدد مرات الإرسال")
            bot.register_next_step_handler(msg, set_message_count)
        elif call.data == 'set_send_interval':
            msg = bot.send_message(call.message.chat.id, "أرسل الفترة الزمنية بين كل إرسال (بالثواني)")
            bot.register_next_step_handler(msg, set_send_interval)
        elif call.data == 'view_info':
            email = report_channel_or_group_id.get(user_id, "لم يتم التعيين")
            subject = report_subject.get(user_id, "لم يتم التعيين")
            message = report_message.get(user_id, "لم يتم التعيين")
            img_info = "موجودة" if user_id in report_image else "لم يتم التعيين"
            count = message_count.get(user_id, "لم يتم التعيين")
            interval = send_interval.get(user_id, "لم يتم التعيين")
            info_message = (f"معلومات الإرسال:\n"
                            f"• البريد: {email}\n"
                            f"• الموضوع: {subject}\n"
                            f"• الرسالة: {message}\n"
                            f"• الصورة: {img_info}\n"
                            f"• عدد مرات الإرسال: {count}\n"
                            f"• الفترة الزمنية: {interval} ثانية")
            bot.send_message(call.message.chat.id, info_message)
        elif call.data == 'start_sending':
            send_report(user_id)
        elif call.data == 'stop_sending':
            stop_sending[user_id] = True
        elif call.data == 'schedule_send':
            msg = bot.send_message(call.message.chat.id, "أرسل تاريخ ووقت الإرسال بتنسيق YYYY-MM-DD HH:MM")
            bot.register_next_step_handler(msg, schedule_send)
        elif call.data == 'email_file' and is_developer(call.message):
            with open('email_list.csv', 'r') as file:
                email_data = file.read()
            bot.send_message(call.message.chat.id, f"ملف الإيميلات:\n{email_data}")

# Bot Next Step Handlers
def add_email_account(message):
    user_id = message.from_user.id
    try:
        email, password = message.text.split(":")
        user_email_accounts.setdefault(user_id, []).append({'email': email, 'password': password})
        bot.send_message(message.chat.id, "تم إضافة الحساب بنجاح.")
    except:
        bot.send_message(message.chat.id, "خطأ في تنسيق الحساب. يرجى المحاولة مرة أخرى.")

def add_multiple_email_accounts(message):
    user_id = message.from_user.id
    try:
        accounts = csv.reader(message.text.split("\n"))
        for email, password in accounts:
            user_email_accounts.setdefault(user_id, []).append({'email': email, 'password': password})
        bot.send_message(message.chat.id, "تم إضافة الحسابات بنجاح.")
    except:
        bot.send_message(message.chat.id, "خطأ في تنسيق الحسابات. يرجى المحاولة مرة أخرى.")

def save_message(message):
    user_id = message.from_user.id
    saved_messages.setdefault(user_id, []).append(message.text)
    bot.send_message(message.chat.id, "تم حفظ الرسالة بنجاح.")

def upload_email_list(message):
    user_id = message.from_user.id
    try:
        email_list = csv.reader(message.text.split("\n"))
        user_sent_records[user_id] = []
        for email in email_list:
            user_sent_records[user_id].append(email[0])
        bot.send_message(message.chat.id, "تم تحميل قائمة الإيميلات بنجاح.")
    except:
        bot.send_message(message.chat.id, "خطأ في تنسيق قائمة الإيميلات. يرجى المحاولة مرة أخرى.")

def set_email(message):
    user_id = message.from_user.id
    report_channel_or_group_id[user_id] = message.text
    bot.send_message(message.chat.id, "تم تعيين البريد بنجاح.")

def set_subject(message):
    user_id = message.from_user.id
    report_subject[user_id] = message.text
    bot.send_message(message.chat.id, "تم تعيين الموضوع بنجاح.")

def set_message(message):
    user_id = message.from_user.id
    report_message[user_id] = message.text
    bot.send_message(message.chat.id, "تم تعيين الرسالة بنجاح.")

def set_image(message):
    user_id = message.from_user.id
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        report_image[user_id] = downloaded_file
        bot.send_message(message.chat.id, "تم تعيين الصورة بنجاح.")
    else:
        bot.send_message(message.chat.id, "يرجى إرسال صورة صحيحة.")

def set_message_count(message):
    user_id = message.from_user.id
    try:
        count = int(message.text)
        message_count[user_id] = count
        bot.send_message(message.chat.id, "تم تعيين عدد مرات الإرسال بنجاح.")
    except:
        bot.send_message(message.chat.id, "خطأ في تحديد العدد. يرجى المحاولة مرة أخرى.")

def set_send_interval(message):
    user_id = message.from_user.id
    try:
        interval = int(message.text)
        send_interval[user_id] = interval
        bot.send_message(message.chat.id, "تم تعيين الفترة الزمنية بنجاح.")
    except:
        bot.send_message(message.chat.id, "خطأ في تحديد الفترة الزمنية. يرجى المحاولة مرة أخرى.")

def schedule_send(message):
    user_id = message.from_user.id
    try:
        send_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        schedule_send_report(user_id, send_time)
        bot.send_message(message.chat.id, f"تم جدولة الإرسال في {send_time}.")
    except:
        bot.send_message(message.chat.id, "خطأ في تحديد الوقت. يرجى استخدام التنسيق الصحيح YYYY-MM-DD HH:MM.")

# Start the bot
def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(15)

if __name__ == '__main__':
    main()