import csv

__author__ = 'paulnaoki'
from unittest import TestCase
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from DomainFinderSrc.GoogleCom.Oauth2 import *
import DomainFinderSrc.GoogleCom.Oauth2
from DomainFinderSrc.Utilities.FileIO import FileHandler
import requests
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
import oauth2
from oauth2.clients import smtp


# from email import
normal_email_provider = {'host': 'box1089.bluehost.com', 'port': 465}
normal_auth = {'user': 'support@areyoucozy.com', 'password': 'iamthe111'}

gmail_provider = {'host': 'smtp.gmail.com', 'port': 587}

smtp_auth_url = "https://mail.google.com/mail/b/serpdrive@gmail.com/smtp/"
credentials_local_path = "D:/Test/gmail_oauth2_credentials.txt"

client_id = "998809885567-fbars3pjch0ln7nqsl20ol54ocnonk3a.apps.googleusercontent.com"
client_secret = "d8R9KLGAEiB1U87gL8OHNsd4"

flow = OAuth2WebServerFlow(client_id=client_id,
                           client_secret=client_secret,
                           scope='https://mail.google.com',
                           redirect_uri='http://serpdrive.com/',
                           access_type="offline", approval_prompt="force")


class EmailTest(TestCase):

    def testGmailTokenPermissionLink(self):
        url = GeneratePermissionUrl(client_id, scope="https://mail.google.com")
        response = requests.get(url)
        print(response.text)

    def testGmailAuth(self):
        # from oauth2client.client import flow_from_clientsecrets
        # flow = flow_from_clientsecrets('C:/Users/paulnaoki/Downloads/client_id.json',
        #                                 scope='https://mail.google.com',
        #                                 redirect_uri='http://example.com/auth_return')
        auth_uri = flow.step1_get_authorize_url()
        print(auth_uri)

    def testGmailAuthStep2(self):
        code = "4/zZRbhzmhulAsl6pasBMqmuOv5PCsdRuITTxyAWLkJOI#"
        credentials = flow.step2_exchange(code)
        access_token = credentials.access_token
        refresh_token = credentials.refresh_token
        print("access_token:", access_token, " refresh_token:", refresh_token)
        jsoned = credentials.to_json()
        FileHandler.remove_file_if_exist(credentials_local_path)
        FileHandler.append_line_to_file(credentials_local_path, str(jsoned))
        print(jsoned)


def get_msg(me, you):
        # me == my email address
        # you == recipient's email address
        html_file_path = "D:/Test/email_content_saved.txt"
        text_file_path = "D:/Test/email_text.txt"

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "100+ HIGH TF/CF/DA EXPIRED DOMAINS TO BUY ONLY $10 EACH"
        msg['From'] = me
        msg['To'] = you

        # Create the body of the message (a plain-text and an HTML version).
        text = ""
        html = FileHandler.read_all_from_file(html_file_path, 't')

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)
        return msg


class EmailmsgTest(TestCase):

    def testMsgGen(self):
        email_template_path = "D:/Test/email_content_template.txt"
        email_content_save_path = "D:/Test/email_content_saved.txt"
        email_lines_before_table_path = "D:/Test/email_text_before_table.txt"
        email_lines_after_table_path = "D:/Test/email_text_after_table.txt"
        data_file_path = "D:/Test/data_sample.csv"
        # th for head cell, td for data cell
        email_template = FileHandler.read_all_from_file(email_template_path)
        cell_item_template = '<{0:s} style="-webkit-box-sizing: border-box;-moz-box-sizing: border-box;box-sizing: ' \
                             'border-box;padding: 8px;text-align: left;line-height: 1.42857143;vertical-align: ' \
                             'bottom;border-top: 1px solid #ddd;border-bottom: 2px solid #ddd;border: 1px solid ' \
                             '#ddd!important;border-bottom-width: 2px;background-color: #fff!important;">' \
                             '{1:s}</{0:s}>'
        row_item_template = '<tr style="-webkit-box-sizing: border-box;-moz-box-sizing: border-box;box-sizing:' \
                            ' border-box;page-break-inside: avoid;">{0:s}</tr>'
        line_format = '<p style="-webkit-box-sizing: border-box;-moz-box-sizing: border-box;box-sizing: ' \
                      'border-box;orphans: 3;widows: 3;margin: 0 0 10px;">{0:s}</p><br>'
        before_table_lines = FileHandler.read_lines_from_file(email_lines_before_table_path, remove_blank_line=False)
        after_table_lines =  FileHandler.read_lines_from_file(email_lines_after_table_path, remove_blank_line=False)

        before_table_str = "".join([line_format.format(x,) for x in before_table_lines])
        after_table_str = "".join([line_format.format(x,) for x in after_table_lines])
        table_cells_str = ""
        with open(data_file_path, mode='r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            header = next(reader)
            header_row_str = row_item_template.format("".join([cell_item_template.format("th", x,) for x in header]))
            for row in reader:
                table_cells_str += row_item_template.format("".join([cell_item_template.format("td", x,) for x in row]))

        email_content = email_template.format(before_table_str, 50, header_row_str, table_cells_str, after_table_str)
        FileHandler.remove_file_if_exist(email_content_save_path)
        FileHandler.append_line_to_file(email_content_save_path, email_content)
        return email_content

    def testEmailLogin(self):
        # Send the message via local SMTP server using Oauth2.
        from Email.SMTP import SMTP
        import httplib2
        from Email.Utility.Oauth2 import CustomOAuth2Credentials
        me = "serpdrive@gmail.com"
        you = "paulnaokii@gmail.com"

        msg = get_msg(me, you)
        http = httplib2.Http()
        credentials = OAuth2Credentials.from_json(FileHandler.read_all_from_file(credentials_local_path))
        # scopes = credentials.retrieve_scopes(http)
        # for item in scopes:
        #     print(item)
        if credentials.access_token_expired:
            # http = credentials.authorize(http)
            credentials.refresh(http)
            jsoned = credentials.to_json()
            FileHandler.remove_file_if_exist(credentials_local_path)
            FileHandler.append_line_to_file(credentials_local_path, str(jsoned))
        auth_str = GenerateOAuth2String(me, access_token=credentials.access_token)
        s = SMTP(**gmail_provider)
        s.set_debuglevel(debuglevel=4)
        s.ehlo()
        s.starttls()
        s.authenticate_oauth2(auth_str)
        s.sendmail(me, you, msg.as_string())
        s.quit()


    def testEmailHtml(self):
        # Send the message via local SMTP server.
        me = "support@areyoucozy.com"
        you = "will@susodigital.com"
        msg = get_msg(me, you)
        s = smtplib.SMTP_SSL(**normal_email_provider)
        s.set_debuglevel(debuglevel=1)
        s.login(**normal_auth)
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(me, you, msg.as_string())
        s.quit()