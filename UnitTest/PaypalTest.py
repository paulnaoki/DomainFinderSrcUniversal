import paypal
from paypal import PayPalConfig
from unittest import TestCase
__author__ = 'paulnaoki'

default_dict = {'API_ENVIRONMENT': 'SANDBOX', 'API_AUTHENTICATION_MODE': '3TOKEN',
                'API_USERNAME': 'musabdi2009-facilitator_api1.gmail.com',
                'API_PASSWORD': 'WWHE385N4YPTQAX8',
                'API_SIGNATURE': 'AFcWxV21C7fd0v3bYYYRCpSSRl31AveX6CrHoCvMaN31RGX4mxlV2LkH'}
# PayPalConfig.API_USERNAME = 'musabdi2009-facilitator_api1.gmail.com'
# PayPalConfig.API_PASSWORD = 'WWHE385N4YPTQAX8'
# PayPalConfig.API_SIGNATURE = 'AFcWxV21C7fd0v3bYYYRCpSSRl31AveX6CrHoCvMaN31RGX4mxlV2LkH'
default_config = PayPalConfig(**default_dict)

default_buyer = {'PAYERID': 'muzazar@gmail.com', 'PROFILESTARTDATE': '2016-01-27T00:00:00Z',
                 'DESC': 'Enroll for subscription.', 'BILLINGPERIOD': 'Month', 'BILLINGFREQUENCY': 1, 'AMT':10,
                 'CURRENCYCODE':'USD', 'COUNTRYCODE': 'GB', 'MAXFAILEDPAYMENTS':3}

interface = paypal.PayPalInterface(config=default_config)


class PaypalTest(TestCase):
    def testSubstriptionStatus(self):
        result = {}
        try:
            # profile = interface.create_recurring_payments_profile(**default_buyer)
            result = interface.get_recurring_payments_profile_details('3TXTXECKF1234')
        except Exception as ex:
            print(ex)
        finally:
            print(result.__dict__)

    def testSetupAuth(self):
        result = {}
        request = {
            "L_BILLINGTYPE0": "RecurringPayments",
            "L_BILLINGAGREEMENTDESCRIPTION0": "Enroll for subscription",
            # "PAYMENTREQUEST_0_AMT": 10,
            # "PAYMENTREQUEST_0_PAYMENTACTION":
            "RETURNURL": 'http://www.yourdomain.com/success.html',
            "CANCELURL": 'http://www.yourdomain.com/cancel.html'}
        try:
            # profile = interface.create_recurring_payments_profile(**default_buyer)
            result = interface.set_express_checkout(**request)
        except Exception as ex:
            print(ex)
        finally:
            print(result.__dict__)
            temp = result.raw
            return temp['TOKEN'][0], temp['TIMESTAMP'][0]
