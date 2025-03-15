import os
import imaplib
import email
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pyrogram import Client, filters

# Bot Configuration
BOT_TOKEN = "8113578720:AAGuDsG3Gqa6XkwurIFbQRX5y3LwrtbTeU8"  # Replace with your bot token
API_ID = 17238318  # Replace with your API ID
API_HASH = "44c77084fdd15c10a6042371fda66630"  # Replace with your API HASH

EMAILS_FILE = "emails.txt"
ATTACHMENTS_FOLDER = "attachments"

# Create the attachments folder if it doesn't exist
if not os.path.exists(ATTACHMENTS_FOLDER):
    os.makedirs(ATTACHMENTS_FOLDER)

# Load email accounts from a file
def load_email_accounts():
    accounts = []
    try:
        with open(EMAILS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(":")
                if len(parts) == 2:
                    accounts.append({"email": parts[0], "password": parts[1]})
    except FileNotFoundError:
        print(f"File '{EMAILS_FILE}' not found.")
    return accounts

# Get the IMAP server for an email provider
def get_imap_server(email_address):
    if "gmail.com" in email_address:
        return "imap.gmail.com"
    elif "yahoo.com" in email_address:
        return "imap.mail.yahoo.com"
    elif "outlook.com" in email_address or "hotmail.com" in email_address:
        return "imap-mail.outlook.com"
    else:
        return None

# Read the latest emails from the inbox
def read_inbox(email_address, password):
    imap_server = get_imap_server(email_address)
    if not imap_server:
        return f"❌ IMAP server not found for {email_address}", None

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()[-5:]  # Get last 5 emails

        latest_email = ""
        for num in email_ids[::-1]:
            status, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["subject"]
                    sender = msg["from"]
                    latest_email += f"\n📧 From: {sender}\n📜 Subject: {subject}\n"

        mail.logout()
        return latest_email if latest_email else "📭 No new emails.", None

    except Exception as e:
        return f"❌ Error reading inbox: {e}", None

# Forward email
def forward_email(sender_email, sender_password, recipient_emails, subject, message, copies=1):
    try:
        smtp_server = "smtp.gmail.com" if "gmail.com" in sender_email else "smtp-mail.outlook.com" if "outlook.com" in sender_email else "smtp.mail.yahoo.com"
        server = smtplib.SMTP(smtp_server, 587)
        server.starttls()
        server.login(sender_email, sender_password)

        unique_subject = subject + " " + str(random.randint(1000, 9999))  # Unique identifier

        for _ in range(copies):
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = ", ".join(recipient_emails)
            msg["Subject"] = unique_subject
            msg.attach(MIMEText(message, "plain"))

            server.sendmail(sender_email, recipient_emails, msg.as_string())

        server.quit()
        return f"✅ Email forwarded to {', '.join(recipient_emails)} ({copies} copies)."

    except Exception as e:
        return f"❌ Failed to forward email: {e}"

# Initialize Pyrogram Client
bot = Client("email_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Command: /read_emails
@bot.on_message(filters.command("read_emails"))
def handle_read_emails(client, message):
    accounts = load_email_accounts()
    if not accounts:
        message.reply_text("❌ No email accounts configured.")
        return

    selected_email = accounts[0]["email"]
    selected_password = accounts[0]["password"]

    inbox_result, _ = read_inbox(selected_email, selected_password)
    message.reply_text(inbox_result)

# Command: /forward_email <recipient> <subject> <message> <copies>
@bot.on_message(filters.command("forward_email"))
def handle_forward_email(client, message):
    args = message.text.split(" ", 4)
    if len(args) < 5:
        message.reply_text("❌ Usage: /forward_email <recipient> <subject> <message> <copies>")
        return

    recipient = args[1]
    subject = args[2]
    email_message = args[3]
    try:
        copies = int(args[4])
    except ValueError:
        message.reply_text("❌ Copies must be a number.")
        return

    accounts = load_email_accounts()
    if not accounts:
        message.reply_text("❌ No email accounts configured.")
        return

    selected_email = accounts[0]["email"]
    selected_password = accounts[0]["password"]

    result = forward_email(selected_email, selected_password, [recipient], subject, email_message, copies)
    message.reply_text(result)

# Command: /send_email <recipient> <subject> <message>
@bot.on_message(filters.command("send_email"))
def handle_send_email(client, message):
    args = message.text.split(" ", 3)
    if len(args) < 4:
        message.reply_text("❌ Usage: /send_email <recipient> <subject> <message>")
        return

    recipient = args[1]
    subject = args[2]
    email_message = args[3]

    accounts = load_email_accounts()
    if not accounts:
        message.reply_text("❌ No email accounts configured.")
        return

    selected_email = accounts[0]["email"]
    selected_password = accounts[0]["password"]

    result = forward_email(selected_email, selected_password, [recipient], subject, email_message, copies=1)
    message.reply_text(result)

# Start the bot
print("🤖 Email Bot is running...")
bot.run()
