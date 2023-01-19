# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

import csv
from django.contrib.auth.models import User, Group
from tigaserver_app.models import EuropeCountry

USERS_FILE = '/home/webuser/Documents/filestigaserver/registre_usuaris_aimcost/test_users_14072020.csv'


def split_name(s):
    split = s.split(" ")
    name = split[0]
    first_name = split[1]
    return { "name": name, "last_name": first_name }


def make_user_regional_manager(user, country):
    user.userstat.national_supervisor_of = country
    user.save()

def assign_user_to_country(user, country):
    user.userstat.native_of = country
    user.save()


def perform_checks():
    with open(USERS_FILE) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            country_iso = row[7]
            try:
                print("Looking for country {0} with iso_code {1}".format(row[2], row[7]))
                e = EuropeCountry.objects.get(iso3_code=country_iso)
                print("Exists, doing nothing")
            except EuropeCountry.DoesNotExist:
                print("{0} country with iso_code {1} does not exist".format(row[2],row[7]))

    try:
        eu_group = Group.objects.get(name="eu_group_europe")
    except Group.DoesNotExist:
        print("Eu group does not exist, create")
        eu_group = Group.objects.create(name="eu_group_europe")
        eu_group.save()

    try:
        es_group = Group.objects.get(name="eu_group_spain")
    except Group.DoesNotExist:
        print("Es group does not exist, create")
        es_group = Group.objects.create(name="eu_group_spain")
        es_group.save()


def create_users(add_users_to_euro_groups=True, ignore_regional_managers = False):
    perform_checks()
    experts_group = Group.objects.get(name="expert")
    with open(USERS_FILE) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            name = row[0]
            email = row[1]
            country = row[2]
            sp = split_name(name)
            username = row[3]
            password = row[4]
            country_iso = row[7]
            user = User.objects.create_user(username=username,first_name=sp['name'],last_name=sp['last_name'],email=email,password=password)
            if add_users_to_euro_groups:
                regional_group = Group.objects.get(name=row[5])
                regional_group.user_set.add(user)
            experts_group.user_set.add(user)
            country = EuropeCountry.objects.get(iso3_code=country_iso)
            assign_user_to_country(user,country)
            if not ignore_regional_managers:
                if row[6] == '1':
                    print("Making user regional manager")
                    make_user_regional_manager(user, country)

            print("{0} {1} {2}".format( username, email, password ))

create_users(add_users_to_euro_groups=False, ignore_regional_managers = True)
