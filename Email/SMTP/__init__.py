import smtplib
import base64

__author__ = 'paulnaoki'


class SMTP(smtplib.SMTP):
    def authenticate_oauth2(self, auth_string: str):
        self.docmd('AUTH', 'XOAUTH2 ' + auth_string)