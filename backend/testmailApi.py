# Code taken from http://docs.python.org/2/library/email-examples.html
import os
import smtplib
import traceback
# For guessing MIME type based on file name extension
import mimetypes

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape,Template

COMMASPACE = ', '

def read_template(filename, data):
    with open(filename, 'r') as f:
        html_string = f.read()
    j2_template = Template(html_string)
    body=j2_template.render(data)
    return body

def loadMailSettings(partnerId, systemEmailSettings=False):
    # data = {'username': 'pavan.nivas@algofusiontech.com', 'toUsers': [], 'server': 'smtp.gmail.com',
    # 'connection': 'STARTTLS', 'fromUser': 'pavan.nivas@algofusiontech.com', 'password': 'abgl jiby bwvd jouw',
    # 'port': 587}
    data = {'username': 'recon.support@algofusiontech.com', 'toUsers': [], 'server': 'smtp.gmail.com',
    'connection': 'STARTTLS', 'fromUser': 'recon.support@algofusiontech.com', 'password': 'eqlu pbvf vgzr qnbu',
    'port': 587}
    mailData = dict()
    mailData['fromUser'] = data.get('fromUser', '')
    mailData['username'] = data.get('username', '')
    mailData['password'] = data.get('password', '')
    mailData['server'] = data.get('server', '')
    mailData['port'] = data.get('port', -1)
    mailData['toUsers'] = data.get('toUsers', '')
    mailData['connection'] = data.get('connection', 'STARTTLS')
    # if data.get('smtp_ssl', False):
    #     mailData['connection'] = 'SSL/TLS'
    # elif data.get('smtp_start_tls', False):   
    #     mailData['connection'] = 'STARTTLS'
    # else:
    #     mailData['connection'] = ''
    return True, mailData


def sendemail(subject, body, toEmail=None, attachFiles=None, onlyToEmail=False, fromuser=None, isHtml=False,
              testMail=False, mailSettings=None, partnerId=None, fromSystemMail=False):
    try:
        (status, mailData) = loadMailSettings("", "")
        if fromuser is not None:
            mailData['fromUser'] = fromuser

        if 'testMail' in mailData.keys() and testMail:
            mailData['toUsers'] = mailData['testMail']
        if isHtml:
            outer = MIMEMultipart('alternative')
        else:
            outer = MIMEMultipart()
        outer['Subject'] = subject
        # if onlyToEmail is True, mail will be sent to only emails specified in toEmail
        if onlyToEmail:
            mailData['toUsers'] = []
        if toEmail is not None:
            if not isinstance(toEmail, list):
                mailData['toUsers'] += toEmail.split(",")
            else:
                mailData['toUsers'] = toEmail
        outer['To'] = COMMASPACE.join(mailData['toUsers'])
        outer['From'] = mailData['fromUser']
        outer.preamble = 'This mail contains attachment.\n'
        if isHtml:
            part1 = MIMEText(body, 'html')
        else:
            part1 = MIMEText(body, 'plain')
        outer.attach(part1)

        if attachFiles is not None:
            for filename in attachFiles:
                if not os.path.isfile(filename):
                    continue
                # Guess the content type based on the file's extension.  Encoding
                # will be ignored, although we should check for simple things like
                # gzip'd or compressed files.
                ctype, encoding = mimetypes.guess_type(filename)
                if ctype is None or encoding is not None:
                    # No guess could be made, or the file is encoded (compressed), so
                    # use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                if maintype == 'text':
                    fp = open(filename)
                    # Note: we should handle calculating the charset
                    msg = MIMEText(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == 'image':
                    fp = open(filename, 'rb')
                    msg = MIMEImage(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == 'audio':
                    fp = open(filename, 'rb')
                    msg = MIMEAudio(fp.read(), _subtype=subtype)
                    fp.close()
                else:
                    fp = open(filename, 'rb')
                    msg = MIMEBase(maintype, subtype)
                    msg.set_payload(fp.read())
                    fp.close()
                    # Encode the payload using Base64
                    encoders.encode_base64(msg)
                    # Set the filename parameter
                msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filename))
                outer.attach(msg)
                # Now send or store the message

        if mailData['connection'] == "SSL/TLS":
            s = smtplib.SMTP_SSL(mailData['server'], mailData['port'], timeout=10)
        else:
            s = smtplib.SMTP(mailData['server'], mailData['port'], timeout=20)
            s.starttls()
            s.login(mailData['fromUser'], mailData['password'])
        #s.ehlo()
        #if mailData['connection'] == "STARTTLS":
        #    print('After')
        #    #s.starttls()
        #    #s.ehlo()
        #if len(mailData['username']) > 0 and mailData['connection'] != "none":
        #    #s.login(mailData['username'], None)
        #    print('here')
        #    #s.login(mailData['username'], mailData['password'])
        #mailData['toUsers'].append('')
        print(mailData)
        # print(s.sendmail(mailData['fromUser'], mailData['toUsers'], outer.as_string()))
        s.sendmail(mailData['fromUser'], mailData['toUsers'], outer.as_string())

        # s.sendmail('recontechsupport@testbsp.com.pg', 'santosh@jmrinfotech.com', outer.as_string())
        s.close()
        return True, 'Success'
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return True, e


if __name__=="__main__":
    sendemail('test','test', attachFiles=[])
    
