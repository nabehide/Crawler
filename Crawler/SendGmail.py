import smtplib
try:
    from email.MIMEText import MIMEText
except ImportError:
    from email.mime.text import MIMEText


class SendGmail(object):

    def __init__(self, address, password):
        self.address = address
        self.password = password

    def create_message(self, from_addr, to_addr, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr
        return msg

    def send_via_gmail(self, from_addr, to_addr, msg):
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(to_addr, self.password)
        s.sendmail(from_addr, [to_addr], msg.as_string())
        s.close()

    def send(self, subject=None, message=None):
        from_addr = 'user'
        to_addr = self.address
        msg = self.create_message(from_addr, to_addr, subject, str(message))
        self.send_via_gmail(from_addr, to_addr, msg)


if __name__ == '__main__':
    from private import address, password
    sg = SendGmail(address, password)
    sg.send(subject="test", message="test")
