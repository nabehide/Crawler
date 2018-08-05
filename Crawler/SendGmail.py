import smtplib
import mimetypes
try:
    from email.MIMEText import MIMEText
    from email.MIMEBase import MIMEBase
    from email.MIMEMultipart import MIMEMultipart
    from email import Encoders as encoders
except ImportError:
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email import encoders


class SendGmail(object):

    def __init__(self, address, password):
        self.address = address
        self.password = password

    def create_message(self, from_addr, to_addr, subject, body, attach):
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr

        body = MIMEText(body)
        msg.attach(body)

        if attach is not None:
            name = attach.split("/")[-1]
            TYPE = mimetypes.guess_type(name)
            TYPE = TYPE[0].split("/")
            attachment = MIMEBase(TYPE[0], TYPE[1])
            with open(attach, "rb") as f:
                attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            msg.attach(attachment)
            attachment.add_header(
                "Content-Disposition", "attachment", filename=name)

        return msg

    def send_via_gmail(self, from_addr, to_addr, msg):
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(to_addr, self.password)
        s.sendmail(from_addr, [to_addr], msg.as_string())
        s.close()

    def send(self, subject=None, message=None, attach=None):
        from_addr = 'user'
        to_addr = self.address
        msg = self.create_message(
            from_addr, to_addr, subject, str(message), attach)
        self.send_via_gmail(from_addr, to_addr, msg)


if __name__ == '__main__':
    from private import address, password
    sg = SendGmail(address, password)
    attach = "./test.png"
    sg.send(subject="test", message="test", attach=attach)
