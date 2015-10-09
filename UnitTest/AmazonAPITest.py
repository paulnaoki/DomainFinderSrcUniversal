from unittest import TestCase
import boto3
import requests


aws_access_key_id = "YOUR_KEY"
aws_secret_access_key = "YOUR_SECRET"
default_region = "us-west-2"


class AmazonTest(TestCase):
    def testDescribeInstances(self):
        agent = boto3.client()