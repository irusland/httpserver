import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from secret_tokens.email_secret import LOGIN, PASSWORD
from ihttpy.environment import BACKEND_ADDRESS


def send(receiver_email, body: MIMEText):
    sender_email = LOGIN
    message = MIMEMultipart("alternative")
    message["Subject"] = "Restaurant reservation"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.attach(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                          context=context,
                          timeout=100) as server:
        server.login(sender_email, PASSWORD)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


if __name__ == '__main__':
    validation_url = 'asd'
    link = f'http://{BACKEND_ADDRESS}/orders/{validation_url}'
    html = f"""\
    <html>
      <body>
        <p>Hello, to confirm your reservation press 
        <a href="{link}">CONFIRM</a>
        </p>
      </body>
    </html>
    """
    mimetext = MIMEText(html, "html")
    send("ruslangamechannel+to@gmail.com", mimetext)
