from django.test import TestCase
from tigaserver_app.models import EuropeCountry, TigaUser, TigaProfile, Report, ExpertReportAnnotation, Award, AwardCategory, \
    Notification, NotificationContent, get_translation_in, ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP, \
    ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP, ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP
from tigacrafting.models import Categories
from tigaserver_project import settings as conf
from tigascoring.xp_scoring import compute_user_score_in_xp_v2
from django.utils import timezone
from datetime import datetime, timedelta, date
import pytz
from random import seed, random
from django.template.loader import render_to_string
import html.entities
from django.contrib.auth.models import User, Group

VALIDATION_VALUE_POSSIBLE = 1
VALIDATION_VALUE_CONFIRMED = 2


class ScoringTestCase(TestCase):
    fixtures = ['awardcategory.json', 'tigaprofile.json', 'tigausers.json', 'reritja_like.json', 'categories.json','europe_countries.json', 'granter_user.json']

    def uuid_to_number(self,uuid):
        number_part = uuid.split('-')[4]
        number_part_number = int(number_part)
        return number_part_number

    def pad_to_left(self, pad_character, original_string, final_length):
        original_string_len = len(original_string)
        add_num = final_length - original_string_len
        retval = ''
        for i in range(add_num):
            retval += pad_character
        retval += original_string
        return retval

    def number_to_uuid(self,number):
        uuid = '00000000-0000-0000-0000-'
        number_str = str(number)
        return uuid + self.pad_to_left('0',number_str,12)

    def delete_report(self,report):
        utc = pytz.UTC
        d = datetime.now()
        ld = utc.localize(d)
        old_uuid = report.version_UUID
        old_number = self.uuid_to_number(old_uuid)
        new_number = old_number + 1
        new_uuid = self.number_to_uuid(new_number)
        new_report = Report(
            version_UUID=new_uuid,
            version_number=-1,
            report_id=report.report_id,
            user_id=report.user.user_UUID,
            phone_upload_time=report.phone_upload_time,
            server_upload_time=report.server_upload_time,
            creation_time=report.creation_time,
            version_time=ld,
            location_choice="current",
            current_location_lon=report.current_location_lon,
            current_location_lat=report.current_location_lat,
            type=report.type,
            app_language=report.app_language,
            package_version=report.package_version
            # This is important for notifications: no notifs issued for null or <32 package version numbers
        )
        new_report.save()
        return new_report

    def create_single_report(self, day, month, year, user, id, report_id='', hour=None, minute=None, second=None, report_app_language='es'):
        utc = pytz.UTC
        if hour is None:
            hour = 0
        if minute is None:
            minute = 0
        if second is None:
            second = 0
        d = datetime(year, month, day, hour, minute, second)
        ld = utc.localize(d)
        seed(1)
        value_x = random()
        value_y = random()
        long = -180 + (value_x * (360))
        lat = -90 + (value_y * (180))
        r = Report(
            version_UUID=id,
            version_number=0,
            user_id=user.user_UUID,
            report_id=report_id,
            phone_upload_time=ld,
            server_upload_time=ld,
            creation_time=ld,
            version_time=ld,
            location_choice="current",
            current_location_lon=long,
            current_location_lat=lat,
            type='adult',
            app_language=report_app_language,
            package_version=32 #This is important for notifications: no notifs issued for null or <32 package version numbers
        )
        return r

    def test_compute_score_for_new_user(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        retval = compute_user_score_in_xp_v2(user_id)
        self.assertEqual(retval['total_score'], 0)

    def test_score_non_validated_adult_report(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        report_in_season = self.create_single_report(conf.SEASON_START_DAY, conf.SEASON_START_MONTH, 2020, user,
                                                     '00000000-0000-0000-0000-000000000002')
        report_in_season.save()
        retval = compute_user_score_in_xp_v2(user_id)
        # 6 points first of season
        # 6 points first of day
        # no awards for mosquito. not yet classified
        self.assertEqual(retval['total_score'], 12)

    def test_score_for_aedes_adult_report(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        report_in_season = self.create_single_report(conf.SEASON_START_DAY, conf.SEASON_START_MONTH, 2020, user,
                                                     '00000000-0000-0000-0000-000000000002')
        report_in_season.save()
        reritja_user = User.objects.get(pk=25)
        superexperts_group = Group.objects.create(name='superexpert')
        superexperts_group.user_set.add(reritja_user)
        c_4 = Categories.objects.get(pk=4)  # Aedes albopictus
        anno_reritja = ExpertReportAnnotation.objects.create(user=reritja_user, report=report_in_season, category=c_4,
                                                             validation_complete=True, revise=True,
                                                             validation_value=VALIDATION_VALUE_CONFIRMED)
        retval = compute_user_score_in_xp_v2(user_id)
        # 6 points first of season
        # 6 points first of day
        # 6 points geolocated
        self.assertEqual(retval['total_score'], 18)
        # we hide the report, it does not yield any points
        report_in_season.hide = True
        report_in_season.save()
        retval = compute_user_score_in_xp_v2(user_id)
        self.assertEqual(retval['total_score'], 0)

    def test_first_of_season_awarded(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        day_before_start_of_season = conf.SEASON_START_DAY - 1
        month_before_start_of_season = conf.SEASON_START_MONTH - 1
        user = TigaUser.objects.get(pk=user_id)

        #should not be granted
        report_before_season = self.create_single_report(day_before_start_of_season, month_before_start_of_season, 2018, user, '00000000-0000-0000-0000-000000000001')
        report_before_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).count(), 0)

        # should be granted for season 2020
        report_in_season = self.create_single_report(conf.SEASON_START_DAY, conf.SEASON_START_MONTH, 2020, user, '00000000-0000-0000-0000-000000000002')
        report_in_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2020).count(), 1)

        # should be granted for season 2018
        report_in_other_season = self.create_single_report(conf.SEASON_START_DAY, conf.SEASON_START_MONTH, 2018, user, '00000000-0000-0000-0000-000000000003')
        report_in_other_season.report_id = 'AAAA'
        report_in_other_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2018).count(), 1)

        report_in_other_season_version = Report(
            version_UUID='00000000-0000-0000-0000-000000000004',
            version_number=1,
            report_id=report_in_other_season.report_id,
            user_id=report_in_other_season.user.user_UUID,
            phone_upload_time=report_in_other_season.phone_upload_time,
            server_upload_time=report_in_other_season.server_upload_time,
            creation_time=report_in_other_season.creation_time,
            version_time=report_in_other_season.version_time,
            location_choice="current",
            current_location_lon=report_in_other_season.lon,
            current_location_lat=report_in_other_season.lat,
            type='adult',
        )
        report_in_other_season_version.save()
        #award should be transferred to report_in_other_season_version
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2018).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season_version).count(),1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season).count(), 0)

        report_in_other_season_version_2 = Report(
            version_UUID='00000000-0000-0000-0000-000000000005',
            version_number=2,
            report_id=report_in_other_season_version.report_id,
            user_id=report_in_other_season_version.user.user_UUID,
            phone_upload_time=report_in_other_season_version.phone_upload_time,
            server_upload_time=report_in_other_season_version.server_upload_time,
            creation_time=report_in_other_season_version.creation_time,
            version_time=report_in_other_season_version.version_time,
            location_choice="current",
            current_location_lon=report_in_other_season_version.lon,
            current_location_lat=report_in_other_season_version.lat,
            type='adult',
        )
        report_in_other_season_version_2.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2018).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season_version_2).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season_version).count(), 0)

    def test_first_of_day(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        day = 1
        month = 1
        year = 2015
        hour_1 = 1
        hour_2 = 2
        hour_3 = 3
        first_report_of_day = self.create_single_report(day, month, year, user, '00000000-0000-0000-0000-000000000001', hour_1)
        first_report_of_day.save()
        second_report_of_day = self.create_single_report(day, month, year, user, '00000000-0000-0000-0000-000000000002', hour_2)
        second_report_of_day.save()
        third_report_of_day = self.create_single_report(day, month, year, user, '00000000-0000-0000-0000-000000000003', hour_3)
        third_report_of_day.save()
        #just one first of day was granted
        self.assertEqual(Award.objects.filter(category__id=2).count(), 1)
        #it was granted to first_report_of_day
        self.assertEqual(Award.objects.get(category__id=2).report.version_UUID, first_report_of_day.version_UUID)

    def test_two_day_streak(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        day_1 = 1
        day_2 = 2
        day_3 = 3
        month = 1
        year = 2015
        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()
        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()
        report_of_day_3 = self.create_single_report(day_3, month, year, user, '00000000-0000-0000-0000-000000000003')
        report_of_day_3.save()
        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)

    def three_day_streak(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        day_1 = 1
        day_2 = 2
        day_3 = 3 # --> 3 streak
        day_4 = 4
        month = 1
        year = 2015
        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()
        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()
        report_of_day_3 = self.create_single_report(day_3, month, year, user, '00000000-0000-0000-0000-000000000003')
        report_of_day_3.save()
        report_of_day_4 = self.create_single_report(day_4, month, year, user, '00000000-0000-0000-0000-000000000004')
        report_of_day_4.save()
        self.assertEqual(Award.objects.filter(category__id=4).count(), 1)
        self.assertEqual(Award.objects.get(category__id=4).report.version_UUID, report_of_day_3.version_UUID)

    def test_three_and_two_combined(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        #All days are in the same week
        day_1 = 5
        day_2 = 6 # --> 2 streak
        day_3 = 7 # --> 3 streak
        day_4 = 8
        day_5 = 9 # --> 2 streak
        day_6 = 10 # --> 3 streak
        day_7 = 11
        month = 1
        year = 2015
        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()

        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()

        report_of_day_3 = self.create_single_report(day_3, month, year, user, '00000000-0000-0000-0000-000000000003')
        report_of_day_3.save()

        report_of_day_4 = self.create_single_report(day_4, month, year, user, '00000000-0000-0000-0000-000000000004')
        report_of_day_4.save()

        report_of_day_5 = self.create_single_report(day_5, month, year, user, '00000000-0000-0000-0000-000000000005')
        report_of_day_5.save()

        report_of_day_6 = self.create_single_report(day_6, month, year, user, '00000000-0000-0000-0000-000000000006')
        report_of_day_6.save()

        report_of_day_7 = self.create_single_report(day_7, month, year, user, '00000000-0000-0000-0000-000000000007')
        report_of_day_7.save()

        self.assertEqual(Award.objects.filter(category__id=4).count(), 2)
        self.assertEqual(Award.objects.filter(category__id=4).filter(report__version_UUID=report_of_day_3.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=4).filter(report__version_UUID=report_of_day_6.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).count(), 2)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_5.version_UUID).count(), 1)

    def test_corner_cases_daily_participation_midnight(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        day_1 = 5  # --> Daily participation
        day_2 = 6  # --> Daily participation, 2 streak
        month = 1
        hour_1 = 23
        hour_2 = 0
        year = 2015

        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001', hour_1)
        report_of_day_1.save()

        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002', hour_2)
        report_of_day_2.save()

        self.assertEqual(Award.objects.filter(category__id=2).count(), 2) #Daily participation given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)  #Two day streak given to one of the reports
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_1.version_UUID).count(), 1) #Check each of the reports has first day
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1) #Check second report has 2 day streak

    def test_corner_cases_daily_participation_different_months(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        day_1 = 30  # --> Daily participation
        day_2 = 1  # --> Daily participation, 2 streak
        month_1 = 4
        month_2 = 5
        year = 2020

        report_of_day_1 = self.create_single_report(day_1, month_1, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()

        report_of_day_2 = self.create_single_report(day_2, month_2, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()

        self.assertEqual(Award.objects.filter(category__id=2).count(),2)  # Daily participation given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)  # Two day streak given to one of the reports
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_1.version_UUID).count(),1)  # Check each of the reports has first day
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_2.version_UUID).count(),1)  # Check second report has 2 day streak

    @staticmethod
    def get_notification_body_es(category_label, xp):
        context_es = {}
        context_es['amount_awarded'] = xp
        context_es['reason_awarded'] = get_translation_in(category_label, 'es')
        return render_to_string('tigaserver_app/award_notification_es.html', context_es).encode('ascii', 'xmlcharrefreplace').decode('UTF-8')

    @staticmethod
    def get_notification_body_for_locale(category_label, xp, locale):
        context = {}
        context['amount_awarded'] = xp
        context['reason_awarded'] = get_translation_in(category_label, locale)
        return render_to_string('tigaserver_app/award_notification_' + locale + '.html', context).encode('ascii', 'xmlcharrefreplace').decode('UTF-8')

    def test_10_report_achievement(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,11,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i))
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body).count(), 1)

    def test_20_report_achievement(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,21,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i))
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_20_reports').count(), 1)  # Ten report achievement granted

        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body_10 = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            notification_body_20 = self.get_notification_body_es(ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_10).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_20).count(), 1)

    def test_50_report_achievement(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        year = 2020

        for i in range(1, 3, 1):
            for j in range(1, 27 , 1):
                r = self.create_single_report(j, i, year, user, '00000000-0000-0000-0000-000000000' + str(j) + str(i))
                r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_20_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_50_reports').count(), 1)  # Ten report achievement granted

        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body_10 = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            notification_body_20 = self.get_notification_body_es(ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)
            notification_body_50 = self.get_notification_body_es(ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_10).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_20).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_50).count(), 1)


    def test_corner_cases_first_of_season_different_users(self):
        user_id_1 = '00000000-0000-0000-0000-000000000000'
        user_id_2 = '00000000-0000-0000-0000-000000000001'

        day_1 = 30  # --> Daily participation, first of season
        month_1 = 4
        year = 2020

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        report_1_user_1 = self.create_single_report(day_1, month_1, year, user_1, '00000000-0000-0000-0000-000000000001')
        report_1_user_1.save()
        report_1_user_2 = self.create_single_report(day_1, month_1, year, user_2, '00000000-0000-0000-0000-000000000002')
        report_1_user_2.save()

        self.assertEqual(Award.objects.filter(category__id=1).count(),2)  # Daily participation given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=2).count(),2)  # First of season given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=1).filter(report__version_UUID=report_1_user_1.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report__version_UUID=report_1_user_2.version_UUID).count(), 1)


    def test_10_day_achievement_for_sq_locale(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,11,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i), report_app_language='sq')
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body = self.get_notification_body_for_locale(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP,'sq')
            #The english notification should be in Albanian
            # for n in Notification.objects.all():
            #     print("<---- SEPARATOR ---->")
            #     print(n.notification_content.body_html_en)
            #     print("<---- END SEPARATOR ---->")
            self.assertEqual(Notification.objects.filter(notification_content__body_html_en=notification_body).count(), 1)

    def test_profile_first_of_season(self):
        user_id_1 = '00000000-0000-0000-0000-000000000002'
        user_id_2 = '00000000-0000-0000-0000-000000000003'

        day_1 = 30  # --> Daily participation, first of season
        month_1 = 4
        year = 2020

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        report_1_user_1 = self.create_single_report(day_1, month_1, year, user_1,
                                                    '00000000-0000-0000-0000-000000000001')
        report_1_user_1.save()
        report_1_user_2 = self.create_single_report(day_1, month_1, year, user_2,
                                                    '00000000-0000-0000-0000-000000000002')
        report_1_user_2.save()
        # only user_1 should have any awards
        self.assertEqual(Award.objects.filter(category__id=1).count(),
                         1)  # Only one award given for two qualifyable reports of the same profile
        a = Award.objects.filter(category__id=1).first()
        self.assertEqual(a.given_to, user_1)  # Should have been given to user_1

    def test_profile_first_of_day(self):
        user_id_1 = '00000000-0000-0000-0000-000000000002'
        user_id_2 = '00000000-0000-0000-0000-000000000003'

        day_1 = 30  # --> Daily participation, first of season
        month_1 = 4
        year = 2020

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        report_1_user_1 = self.create_single_report(day_1, month_1, year, user_1,
                                                    '00000000-0000-0000-0000-000000000001')
        report_1_user_1.save()
        report_1_user_2 = self.create_single_report(day_1, month_1, year, user_2,
                                                    '00000000-0000-0000-0000-000000000002')
        report_1_user_2.save()
        # only user_1 should have any awards
        self.assertEqual(Award.objects.filter(category__id=2).count(),
                         1)  # Only one award given for two qualifyable reports of the same profile
        a = Award.objects.filter(category__id=1).first()
        self.assertEqual(a.given_to, user_1)  # Should have been given to user_1

    def test_10_day_achievement_across_profiles(self):
        user_id_1 = '00000000-0000-0000-0000-000000000002'
        user_id_2 = '00000000-0000-0000-0000-000000000003'

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        month_1 = 1
        year = 2020

        for i in range(1, 11, 1):
            if i <= 4:
                r = self.create_single_report(i, month_1, year, user_1, '00000000-0000-0000-0000-0000000000' + str(i))
            else:
                r = self.create_single_report(i, month_1, year, user_2, '00000000-0000-0000-0000-0000000000' + str(i))
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(),1)  # Ten report achievement granted
        a = Award.objects.get(special_award_text='achievement_10_reports')
        self.assertEqual(a.given_to, user_2)  # Should have been given to user_2
        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body).count(),1)

    def test_20_report_achievement_across_profiles(self):
        user_id_1 = '00000000-0000-0000-0000-000000000002'
        user_id_2 = '00000000-0000-0000-0000-000000000003'

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        month_1 = 1
        year = 2020

        for i in range(1,21,1):
            if i <= 12:
                r = self.create_single_report(i, month_1, year, user_1, '00000000-0000-0000-0000-0000000000' + str(i))
            else:
                r = self.create_single_report(i, month_1, year, user_2, '00000000-0000-0000-0000-0000000000' + str(i))
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_20_reports').count(), 1)  # Ten report achievement granted
        a = Award.objects.get(special_award_text='achievement_10_reports')
        self.assertEqual(a.given_to, user_1)  # Should have been given to user_1
        a = Award.objects.get(special_award_text='achievement_20_reports')
        self.assertEqual(a.given_to, user_2)  # Should have been given to user_2

        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body_10 = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            notification_body_20 = self.get_notification_body_es(ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_10).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_20).count(), 1)

    def test_50_report_achievement_across_profiles(self):
        user_id_1 = '00000000-0000-0000-0000-000000000002'
        user_id_2 = '00000000-0000-0000-0000-000000000003'

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        year = 2020

        global_report_counter = 1
        for i in range(1, 3, 1):
            for j in range(1, 27 , 1):
                if global_report_counter < 30:
                    r = self.create_single_report(j, i, year, user_1, '00000000-0000-0000-0000-000000000' + str(j) + str(i))
                else:
                    r = self.create_single_report(j, i, year, user_2, '00000000-0000-0000-0000-000000000' + str(j) + str(i))
                r.save()
                global_report_counter += 1
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_20_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_50_reports').count(), 1)  # Ten report achievement granted

        a = Award.objects.get(special_award_text='achievement_10_reports')
        self.assertEqual(a.given_to, user_1)  # Should have been given to user_1
        a = Award.objects.get(special_award_text='achievement_20_reports')
        self.assertEqual(a.given_to, user_1)  # Should have been given to user_1
        a = Award.objects.get(special_award_text='achievement_50_reports')
        self.assertEqual(a.given_to, user_2)  # Should have been given to user_2

        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body_10 = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            notification_body_20 = self.get_notification_body_es(ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)
            notification_body_50 = self.get_notification_body_es(ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_10).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_20).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_50).count(), 1)

    def test_first_of_season_transfer(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        day_before_start_of_season = conf.SEASON_START_DAY - 1
        month_before_start_of_season = conf.SEASON_START_MONTH - 1
        user = TigaUser.objects.get(pk=user_id)

        # should be granted for season 2020
        #(self, day, month, year, user, id, hour=None, minute=None, second=None, report_app_language='es')
        report_in_season = self.create_single_report(day=conf.SEASON_START_DAY, month=conf.SEASON_START_MONTH, year=2020, user=user, id='00000000-0000-0000-0000-000000001000', report_id='ABCD')
        report_in_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2020).count(), 1)
        # there should be one start of season notification for this report
        start_of_season_en_text = get_translation_in('start_of_season', 'en')
        self.assertEqual(Notification.objects.filter(report=report_in_season).filter(notification_content__body_html_en__icontains=start_of_season_en_text).count(), 1)

        report_later_in_season = self.create_single_report(day=conf.SEASON_START_DAY + 1, month=conf.SEASON_START_MONTH, year=2020, user=user, id='00000000-0000-0000-0000-000000001003', report_id='DEFG')
        report_later_in_season.save()

        report_even_later_in_season = self.create_single_report(day=conf.SEASON_START_DAY + 2, month=conf.SEASON_START_MONTH,year=2020, user=user,id='00000000-0000-0000-0000-000000001004', report_id='AAAA')
        report_even_later_in_season.save()

        self.delete_report(report_in_season)
        # first of season should be transferred to earliest valid report after deleted
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2020).filter(report=report_later_in_season).count(), 1)
        # notification should now be in report_later_in_season
        self.assertEqual(Notification.objects.filter(report=report_later_in_season).filter(notification_content__body_html_en__icontains=start_of_season_en_text).count(), 1)

    def test_first_of_season_removed_notification(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        day_before_start_of_season = conf.SEASON_START_DAY - 1
        month_before_start_of_season = conf.SEASON_START_MONTH - 1
        user = TigaUser.objects.get(pk=user_id)

        report_in_season = self.create_single_report(day=conf.SEASON_START_DAY, month=conf.SEASON_START_MONTH,year=2020, user=user, id='00000000-0000-0000-0000-000000001000',report_id='ABCD')
        report_in_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2020).count(), 1)
        # there should be one start of season notification for this report
        start_of_season_en_text = get_translation_in('start_of_season', 'en')
        self.assertEqual(Notification.objects.filter(report=report_in_season).filter(notification_content__body_html_en__icontains=start_of_season_en_text).count(), 1)

        self.delete_report(report_in_season)
        # there sould not be first of season
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2020).count(), 0)