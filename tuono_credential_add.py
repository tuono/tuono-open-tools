#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2021 Tuono, Inc.
#
#  Contributors: Scott Harrison (Tuono)
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

'''
Tuono credential add tool for Azure and AWS.

USAGE: ./tuono_credential_add.py --username <username>
                                 --password <password> (optional)
                                 (mutually exclusive)
                                 --venue azure
                                   --subscription_name <subscription_name>
                                   --app_name <app_name>
                                   --credential <credential>
                                --venue aws
                                  --iam_user <iam_user>
                                  --iam_group <iam_group>
'''

import argparse
import getpass
import json
import logging
import sys
import subprocess
import time
import requests


class Tuono():
    '''Base class'''

    def __init__(self, username, password):
        '''Instantiate a generic connection instance'''

        self.base_uri = 'https://portal.tuono.io/api/v1'

        self.headers = {'Content-Type': 'application/json'}

        self.creds = {'username': username,
                      'password': password}

        self.get_token()

    def get_token(self):
        '''Create token class object'''

        request = requests.post(url=f'{self.base_uri}/auth/login',
                                headers=self.headers,
                                data=json.dumps(self.creds))
        if not request.ok:

            print(f"Error getting auth token: {request.text}")
            sys.exit(1)

        self.token = f'Bearer {request.json()["object"]["token"]}'

        self.headers = {'Authorization': self.token,
                        'Content-Type' : 'application/json'}

    def add_credentials(self, payload, venue):
        '''Add credentials'''

        request = requests.post(url=f'{self.base_uri}/credential/{venue}',
                                headers=self.headers,
                                data=json.dumps(payload))

        return request.json()['object']


class UserNameSpace(object):
    '''User namespace object'''

    pass


def start_argparser():
    '''Initial parser'''

    parser = argparse.ArgumentParser(description='Use Case Dependent ArgParse',
                                     conflict_handler='resolve')
    return parser


def get_shared_args(parser):
    '''Shared arg parser'''

    parser.add_argument('-u', '--username',
                        required=True,
                        help="Specify the Tuono Portal username")

    parser.add_argument('-v', '--venue',
                        required=True,
                        choices=['aws', 'azure'],
                        help='Select venue: [aws, azure]')

    user_namespace = UserNameSpace()

    parser.parse_known_args(namespace=user_namespace)

    return parser, user_namespace


def get_additional_args(parser, user_namespace):
    '''Options parser'''

    if user_namespace.venue == 'aws':
        parser, args = get_aws_args(parser, user_namespace)

    elif user_namespace.venue == 'azure':
        parser, args = get_azure_args(parser, user_namespace)

    return args


def get_aws_args(parser, user_namespace):
    '''AWS arg parser'''

    parser.add_argument('-i', '--iam_user',
                        required=True,
                        help="Specify the AWS username to create")

    parser.add_argument('-g', '--iam_group',
                        required=True,
                        help="Specify the AWS group name to create")

    args = parser.parse_args(namespace=user_namespace)

    return parser, args


def get_azure_args(parser, user_namespace):
    '''Azure arg parser'''

    parser.add_argument('-n', '--subscription_name',
                        required=True,
                        help="Specify subscription name for registration")

    parser.add_argument('-a', '--app_name',
                        required=True,
                        help="Specify the App name to create")

    parser.add_argument('-c', '--credential',
                        required=True,
                        help="Specify the credential name to create")

    args = parser.parse_args(namespace=user_namespace)

    return parser, args


def get_logger(filename):
    '''Logger configuration'''

    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)

    logfile = logging.FileHandler(filename)
    logfile.setLevel(logging.DEBUG)

    screen = logging.StreamHandler()
    screen.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logfile.setFormatter(formatter)
    screen.setFormatter(formatter)

    logger.addHandler(logfile)
    logger.addHandler(screen)

    return logger


def aws_user_group_create(args, logger):
    '''Create AWS user and group'''

    logger.info("Creating IAM user")
    user = subprocess.run(f"aws iam create-user --user-name {args.iam_user} "
                          f"--output json",
                          check=True, shell=True, capture_output=True)
    user = json.loads(user.stdout)
    logger.debug(json.dumps(user, indent=2, sort_keys=True))

    logger.info("Creating IAM group")
    group = subprocess.run(f"aws iam create-group --group-name "
                           f"{args.iam_group} --output json",
                           check=True, shell=True, capture_output=True)
    group = json.loads(group.stdout)
    logger.debug(json.dumps(group, indent=2, sort_keys=True))

    permissions = ("AmazonEC2FullAccess",
                   "AWSCertificateManagerFullAccess",
                   "AmazonRoute53FullAccess",
                   "AmazonS3FullAccess",
                   "ResourceGroupsandTagEditorFullAccess",
                   "AmazonRDSReadOnlyAccess")

    logger.info("Adding IAM permissions to group")
    for permission in permissions:
        subprocess.run(f"aws iam attach-group-policy "
                       f"--policy-arn arn:aws:iam::aws:policy/{permission} "
                       f"--group-name {args.iam_group} --output json",
                       check=True, shell=True)

    logger.info("Adding user to group")
    subprocess.run(f"aws iam add-user-to-group --user-name {args.iam_user} "
                   f"--group-name {args.iam_group} --output json",
                   check=True, shell=True)

    logger.info("Generating secret")
    keys = subprocess.run(f"aws iam create-access-key --user-name "
                          f"{args.iam_user} --output json",
                          check=True, shell=True, capture_output=True)

    logger.info("Waiting 20s to reconcile changes")
    time.sleep(20)

    return (user, group, json.loads(keys.stdout)['AccessKey'])


def azure_app_create(args, logger):
    '''Create Azure registration ond credentials'''

    logger.info("Generating Subscription details")
    subscriptions = subprocess.run("az account list",
                                   check=True, shell=True, capture_output=True)
    for subscription in json.loads(subscriptions.stdout):
        if subscription["name"] == args.subscription_name:
            current = subscription
    logger.debug(json.dumps(current, indent=2, sort_keys=True))

    logger.info("Creating App Registration")
    app = subprocess.run(f"az ad app create --display-name {args.app_name}",
                         check=True, shell=True, capture_output=True)
    app = json.loads(app.stdout)
    logger.debug(json.dumps(app, indent=2, sort_keys=True))

    app_id = app['appId']

    logger.info("Generating Client Secret")
    values = subprocess.run(f'az ad app credential reset --id {app_id} '
                            f'--credential-description {args.credential} '
                            f'--end-date `date -d "+5 years" +%F`',
                            check=True, shell=True, capture_output=True)
    logger.info("Waiting 20s reconcile the secret creation")
    time.sleep(20)

    logger.info("Creating Service Principal")
    subprocess.run(f"az ad sp create --id {app_id}",
                   check=True, shell=True, capture_output=True)
    logger.info("Waiting 20s reconcile the Service Principal creation")
    time.sleep(20)

    logger.info("Creating role assignment")
    subprocess.run(f"az role assignment create --assignee {app_id} "
                   f"--role Contributor --subscription {current['id']}",
                   check=True, shell=True, capture_output=True)
    logger.info("Waiting 20s reconcile role assignment")
    time.sleep(20)

    return (current, app, json.loads(values.stdout))


def main():
    '''Main'''

    parser = start_argparser()
    parser, user_namespace = get_shared_args(parser)
    args = get_additional_args(parser, user_namespace)

    password = getpass.getpass((f"\nPlease enter the Password for "
                                f"{args.username}: "))

    if args.venue == "azure":

        log = 'tuono_azure_setup.txt'
        logger = get_logger(log)

        subscription, app, values = azure_app_create(args, logger)

        payload = {"cred_type"   : "static",
                   "name"        : args.app_name,
                   "venue"       : "azure",
                   "client"      : app['appId'],
                   "secret"      : values['password'],
                   "subscription": subscription['id'],
                   "tenant"      : values['tenant']}

    if args.venue == "aws":

        log = 'tuono_aws_setup.txt'
        logger = get_logger(log)

        user, group, keys = aws_user_group_create(args, logger)

        payload = {"cred_type" : "static",
                   "name"      : args.iam_user,
                   "venue"     : "aws",
                   "access_key": keys['AccessKeyId'],
                   "secret_key": keys['SecretAccessKey']}

    tuono = Tuono(args.username, password)

    logger.info("Credential details for the Tuono Portal. "
                "THESE WILL NOT BE LOGGED:")
    # The REST payload is printed to screen, but not logged.
    print(f"\n{json.dumps(payload, indent=2, sort_keys=True)}\n")
    logger.info("Keep these details in a secure place. If you lose these "
                "you will need to recreate the registration")
    logger.info("Making REST call to add credentials to the Tuono Portal")
    if args.venue == "azure":
        creds = tuono.add_credentials(payload, "azure")
    if args.venue == "aws"
        creds = tuono.add_credentials(payload, "aws")
    logger.debug(f"{json.dumps(creds, indent=2, sort_keys=True)}")
    logger.info(f"To see DEBUG logs, please review {log}")


if __name__ == '__main__':

    main()
