import imaplib
import email
import os
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAILS_FILE = "output.txt"
ATTACHMENTS_FOLDER = "attachments"
MESSAGE_BODY_FILE = "msg.txt"  # Message body file

if not os.path.exists(ATTACHMENTS_FOLDER):
    os.makedirs(ATTACHMENTS_FOLDER)

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

def load_message_body():
    try:
        with open(MESSAGE_BODY_FILE, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ Message body file '{MESSAGE_BODY_FILE}' not found.")
        return ""

def get_imap_server(email_address):
    if "gmail.com" in email_address:
        return "imap.gmail.com"
    elif "yahoo.com" in email_address:
        return "imap.mail.yahoo.com"
    elif "outlook.com" or "hotmail.com" in email_address:
        return "imap-mail.outlook.com"
    else:
        return None

def read_inbox(email_address, password):
    imap_server = get_imap_server(email_address)
    if not imap_server:
        print(f"❌ IMAP server not found for {email_address}")
        return None, None

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()[-5:]  # Get last 5 emails

        latest_email = None
        latest_subject = None
        latest_body = ""

        print(f"\n📩 Latest Emails from {email_address}:")
        for num in email_ids[::-1]:
            status, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg["subject"]
                    sender = msg["from"]
                    print(f"\n📧 From: {sender}\n📜 Subject: {subject}")

                    latest_email = sender
                    latest_subject = subject

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_maintype() == "multipart":
                                continue
                            if part.get("Content-Disposition") is None:
                                latest_body = part.get_payload(decode=True).decode(errors="ignore")
                    else:
                        latest_body = msg.get_payload(decode=True).decode(errors="ignore")

                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue
                        if part.get("Content-Disposition") is None:
                            continue
                        filename = part.get_filename()
                        if filename:
                            filepath = os.path.join(ATTACHMENTS_FOLDER, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            print(f"📎 Attachment saved: {filename}")

        mail.logout()
        return latest_subject, latest_body

    except Exception as e:
        print(f"❌ Error reading inbox for {email_address}: {e}")
        return None, None

def forward_email(sender_email, sender_password, recipient_emails, subject, message, copies=1):
    try:
        smtp_server = "smtp.gmail.com" if "gmail.com" in sender_email else "smtp-mail.outlook.com" if "outlook.com" in sender_email else "smtp.mail.yahoo.com"
        server = smtplib.SMTP(smtp_server, 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # Modify the subject to add a unique identifier (timestamp or random number)
        unique_subject = subject + " " + str(random.randint(1000, 9999))  # Removed the "Fwd:" prefix

        for _ in range(copies):  # Send the email 'copies' times
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = ", ".join(recipient_emails)
            msg["Subject"] = unique_subject
            msg["Message-ID"] = f"<{random.randint(100000, 999999)}@example.com>"  # Unique Message-ID
            msg["References"] = ""  # Remove References header to avoid threading

            msg.attach(MIMEText(message, "plain"))

            server.sendmail(sender_email, recipient_emails, msg.as_string())
            print(f"✅ Email forwarded from {sender_email} to {', '.join(recipient_emails)} (Copy {_ + 1})")

        server.quit()

    except Exception as e:
        print(f"❌ Failed to forward email from {sender_email}: {e}")

accounts = load_email_accounts()
if not accounts:
    print("No email accounts found in the file.")
    exit()

print("\nAvailable Email Accounts:")
for i, acc in enumerate(accounts, 1):
    print(f"{i}. {acc['email']}")

choice = input("\n(1) Read Emails \n(2) Bulk Forward Emails \n(3) Send Email to Specific Address? \nDo you want to: (1/2/3) ")

if choice == "1":
    selected = int(input("\nSelect an email account (number): ")) - 1
    if selected < 0 or selected >= len(accounts):
        print("Invalid choice.")
        exit()
    
    selected_email = accounts[selected]["email"]
    selected_password = accounts[selected]["password"]
    subject, body = read_inbox(selected_email, selected_password)

elif choice == "2":
    recipient_list = input("\nEnter recipient email(s) (comma separated): ").split(",")
    subject = input("Enter email subject to forward: ")
    message = load_message_body()  # File se body load karna

    copies = int(input("How many copies would you like to send? (1 for one copy, 2 for two copies, etc.): "))

    for acc in accounts:
        print(f"\n🚀 Forwarding from {acc['email']}...")
        forward_email(acc["email"], acc["password"], recipient_list, subject, message, copies)

elif choice == "3":
    recipient = input("\nEnter recipient email address: ")
    subject = input("Enter email subject: ")
    message = load_message_body()  # File se body load karna
    copies = int(input("How many copies would you like to send? (1 for one copy, 2 for two copies, etc.): "))
    
    selected = int(input("\nSelect an email account (number): ")) - 1
    if selected < 0 or selected >= len(accounts):
        print("Invalid choice.")
        exit()
    
    selected_email = accounts[selected]["email"]
    selected_password = accounts[selected]["password"]
    forward_email(selected_email, selected_password, [recipient], subject, message, copies)
