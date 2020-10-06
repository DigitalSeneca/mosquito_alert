# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import TigaUser, Report
from tigascoring.xp_scoring import compute_user_score_in_xp_v2_fast


def compute_all_scores():
    users_with_reports = Report.objects.all().values('user').distinct()
    all_users = TigaUser.objects.filter(user_UUID__in=users_with_reports)
    print("Cleaning up...")
    TigaUser.objects.all().update(score_v2=0)
    TigaUser.objects.all().update(score_v2_adult=0)
    TigaUser.objects.all().update(score_v2_site=0)
    TigaUser.objects.all().update(score_v2_bite=0)
    print("Starting...")
    goal = len(all_users)
    start = 1
    for user in all_users:
        score = compute_user_score_in_xp_v2_fast(user.user_UUID)
        user.score_v2 = score['total_score']
        user.score_v2_adult = score['score_detail']['adult']['score']
        user.score_v2_site = score['score_detail']['site']['score']
        #user.score_v2_bite = score['score_detail']['bite']['score']
        user.save()
        if user.profile is not None:
            all_users_in_profile = TigaUser.objects.filter(profile=user.profile)
            all_users_in_profile.update(score_v2=user.score_v2)
            all_users_in_profile.update(score_v2_adult=user.score_v2_adult)
            all_users_in_profile.update(score_v2_site=user.score_v2_site)
        print("Done {0} of {1}".format( start, goal ))
        start += 1


compute_all_scores()
