# Code taken from http://docs.python.org/2/library/email-examples.html
import os
import ssl
import boto3
import base64
import smtplib
# For guessing MIME type based on file name extension
import mimetypes
import botocore.exceptions
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

COMMASPACE = ', '


def loadMailSettings(partnerId='', mailSettings=None):
    mailData = dict()
    if not mailSettings:
        aws_access_key_id = ""
        aws_secret_access_key = ""
        region_name = 'us-east-1'
        return True, {"region_name": region_name, "aws_access_key_id": aws_access_key_id, "aws_secret_access_key": aws_secret_access_key}, "ses"
    else:
        mailData['fromUser'] = mailSettings.get('smtp_from_addr', '')
        mailData['username'] = mailSettings.get('smtp_username', '')
        mailData['secret'] = mailSettings.get('smtp_password', '')
        mailData['server'] = mailSettings.get('smtp_host', '')
        mailData['port'] = mailSettings.get('smtp_port', -1)
        mailData['toUsers'] = []
        if mailSettings.get('smtp_ssl'):
            mailData['connection'] = 'SSL/TLS'
        else:
            mailData['connection'] = 'STARTTLS'
    return True, mailData, ""


def sendemail(subject, body, toEmail=None, attachFiles=None, onlyToEmail=False, fromuser=None, isHtml=False,
              testMail=False, mailSettings=None, partnerId=None, fromSystemMail=False, replyTo=None):
    status, mailData, creType = loadMailSettings('', mailSettings)
    client = None
    if creType == "ses":
        fromuser = "support@cybercns.com"
        client = boto3.client('ses', **mailData)
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
    if toEmail is not None and 'toUsers' not in mailData:
        mailData['toUsers'] = []
    if toEmail is not None:
        mailData['toUsers'] += toEmail.split(",")
    outer['To'] = COMMASPACE.join(mailData['toUsers'])
    outer['From'] = mailData['fromUser']
    if replyTo:
        outer['reply-to'] = replyTo
    outer.preamble = 'This mail contains attachment.\n'
    if isHtml:
        part1 = MIMEText(body, 'html')
    else:
        part1 = MIMEText(body, 'plain')
    outer.attach(part1)

    try:
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
        if creType == "ses":
            response = client.send_raw_email(
                Source=fromuser,
                Destinations=mailData['toUsers'],
                RawMessage={
                    'Data': outer.as_string(),
                }
            )
        else:
            context = ssl.create_default_context()
            if mailData['connection'] == "SSL/TLS":
                s = smtplib.SMTP_SSL(mailData['server'], mailData['port'], timeout=10, context=context)
            else:
                s = smtplib.SMTP(mailData['server'], mailData['port'], timeout=10)
            s.ehlo()
            if mailData['connection'] == "STARTTLS":
                s.ehlo()  # Can be omitted
                s.starttls(context=context)
                s.ehlo()  # Can be omitted
            if len(mailData['username']) > 0 and mailData['connection'] != "none":
                s.login(mailData['username'], mailData['secret'])
            s.sendmail(mailData['fromUser'], mailData['toUsers'], outer.as_string())
            s.close()
        return True, "Success"
    except smtplib.SMTPAuthenticationError as e:
        print("Send Email Authentication Exception %s" % e)
        return False, str(e)
    except smtplib.SMTPDataError as e:
        print("Send Email Data Exception %s" % e)
        return False, str(e)
    except ssl.SSLError as e:
        print("Send Email SSL Exception %s" % e)
        return False, "SSL Error"
    except OSError as e:
        return False, str(e)
    except botocore.exceptions.ClientError as e:
        return False, "Client Connection Error"
    except Exception as e:
        print("Send Email Generic Exception %s" % e)
        return False, str(e)

