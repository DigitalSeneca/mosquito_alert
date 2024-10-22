"""MODELS."""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from tigaserver_app.models import Fix as TigaserverAppFix, Notification, NotificationContent, Report

AuthUser = User = get_user_model()
Userfixes = TigaserverAppFix

class NotificationImageFormModel(models.Model):
    """NotificationImageFormModel."""

    image = models.ImageField(upload_to='media/')

    class Meta:
        """Meta."""

        db_table = None


class ProvinceManager(models.Manager):
    """Province manager. Ordering."""

    def get_queryset(self):
        """Just ordering province name."""
        return super(ProvinceManager, self).get_queryset().order_by('name')


class Province(models.Model):
    """Provinces."""

    id = models.CharField(primary_key=True, max_length=2)
    nomprov = models.CharField(max_length=255, null=False)

    def get_queryset(self):
        """"get_queryset."""
        return super(Province, self).order_by('nomprov')

    def __str__(self):
        """Convert the object into a string."""
        return self.nomprov

    class Meta:
        """Meta."""

        db_table = 'provincies_4326'


class MunicipalitiesManager(models.Manager):
    """Municipalities manager."""

    def get_queryset(self):
        """"get_queryset."""
        return super(MunicipalitiesManager, self).get_queryset().filter(
            tipo='Municipio'
        ).order_by('codprov', 'nombre')


class Municipalities(models.Model):
    """Municipalities."""

    gid = models.AutoField(primary_key=True)
    municipality_id = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=254, blank=True)
    tipo = models.CharField(max_length=10, blank=True)
    pertenenci = models.CharField(max_length=50, blank=True)
    codigoine = models.CharField(max_length=5, blank=True)
    codprov = models.ForeignKey(Province, db_column='codprov',
                                on_delete=models.CASCADE)
    cod_ccaa = models.CharField(max_length=2, blank=True)

    objects = MunicipalitiesManager()

    def __str__(self):
        """Convert the object into a string."""
        return self.nombre + ' (' + self.codprov.nomprov + ')'

    class Meta:
        """Meta."""

        db_table = 'municipis_4326'


class ReportsMapData(models.Model):
    """All mosquito observations."""

    id = models.IntegerField(primary_key=True)
    version_uuid = models.CharField(max_length=36, blank=True, null=True)
    c = models.IntegerField()
    observation_date = models.DateTimeField(null=True, blank=True)
    expert_validation_result = models.CharField(max_length=50, blank=True,
                                                null=True)
    category = models.CharField(max_length=100, blank=True)
    month = models.CharField(max_length=6, blank=True)
    lon = models.FloatField()
    lat = models.FloatField()
    geohashlevel = models.IntegerField()

    class Meta:
        """Meta."""

        managed = False
        db_table = 'reports_map_data'
        unique_together = ('geohashlevel', 'lon', 'lat', 'month', 'category')


class MapAuxReports(models.Model):
    """All mosquito observations."""

    id = models.IntegerField(primary_key=True)
    version_uuid = models.OneToOneField(Report, db_column='version_uuid', related_name='map_aux_report',on_delete=models.CASCADE)
    user_id = models.CharField(max_length=36, blank=True)
    observation_date = models.DateTimeField(null=True, blank=True)
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    ref_system = models.CharField(max_length=36, blank=True)
    type = models.CharField(max_length=7, blank=True)

    expert_validated = models.NullBooleanField()
    expert_validation_result = models.CharField(max_length=100, blank=True)
    simplified_expert_validation_result = models.CharField(max_length=100,
                                                           blank=True)
    site_cat = models.IntegerField(blank=True, null=True)
    storm_drain_status = models.CharField(max_length=50, blank=True)
    edited_user_notes = models.CharField(max_length=4000, blank=True)
    photo_url = models.CharField(max_length=255, blank=True)
    photo_license = models.CharField(max_length=100, blank=True)
    dataset_license = models.CharField(max_length=100, blank=True)
    single_report_map_url = models.CharField(max_length=255, blank=True)
    private_webmap_layer = models.CharField(max_length=255, blank=True)
    final_expert_status = models.IntegerField()
    note = models.TextField()
    tags = models.TextField()
    municipality = models.ForeignKey(Municipalities, null=True,
                                     on_delete=models.CASCADE)
    breeding_site_answers = models.CharField(max_length=100, blank=True)
    mosquito_answers = models.CharField(max_length=100, blank=True)
    n_photos = models.IntegerField(blank=True, null=True)
    visible = models.BooleanField()

    class Meta:
        """Meta."""

        managed = True
        db_table = 'map_aux_reports'


class StormDrain(models.Model):
    """Storm drains."""

    id = models.AutoField(primary_key=True)
    icon = models.IntegerField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    municipality = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    water = models.NullBooleanField(max_length=10, blank=True, null=True)
    sand = models.NullBooleanField(max_length=10, blank=True)
    treatment = models.NullBooleanField(max_length=10, blank=True)
    species2 = models.NullBooleanField(max_length=10, blank=True, null=True)
    species1 = models.NullBooleanField(max_length=10, blank=True, null=True)
    activity = models.NullBooleanField(max_length=10, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    original_lon = models.FloatField(blank=True, null=True)
    original_lat = models.FloatField(blank=True, null=True)
    size = models.CharField(max_length=5, blank=True, null=True)
    model = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        """Meta."""

        db_table = 'storm_drain'
        managed = True


class PredefinedNotificationManager(models.Manager):
    """PredefinedNotification manager. Ordering."""

    def get_queryset(self):
        """Just ordering province name."""
        return super(PredefinedNotificationManager,
                     self).get_queryset().order_by('user', 'title_es')


class PredefinedNotification(models.Model):
    """Predefined notifications."""

    id = models.AutoField(primary_key=True, help_text='Unique identifier of'
                          'the notification. Automatically generated by server'
                          'when notification created.')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body_html_es = models.TextField(help_text='Expert comment, expanded and'
                                    'allows html, in spanish')
    body_html_ca = models.TextField(help_text='Expert comment, expanded and'
                                    'allows html, in catalan', default=None,
                                    blank=True, null=True)
    body_html_en = models.TextField(help_text='Expert comment, expanded and'
                                    'allows html, in english', default=None,
                                    blank=True, null=True)
    title_es = models.TextField(help_text='Title of the comment, shown in'
                                'non-detail view, in spanish')
    title_ca = models.TextField(help_text='Title of the comment, shown in'
                                'non-detail view, in catalan', default=None,
                                blank=True, null=True)
    title_en = models.TextField(help_text='Title of the comment, shown in'
                                'non-detail view, in english', default=None,
                                blank=True, null=True)

    objects = PredefinedNotificationManager()

    def __str__(self):
        """Convert this object into a string."""
        return "(USER: %s) %s" % (str(self.user).upper(),
                                  self.title_es)

    class Meta:
        """Meta."""

        db_table = 'tigaserver_app_notificationpredefined'


class ObservationNotifications(models.Model):
    """Observation notifications."""

    report = models.ForeignKey(MapAuxReports, to_field='version_uuid',
                               on_delete=models.CASCADE)
    user_id = models.CharField(max_length=36, blank=False)
    expert = models.ForeignKey(User, on_delete=models.CASCADE)
    date_comment = models.DateTimeField(auto_now_add=True)
    expert_comment = models.TextField('Expert comment',
                                      help_text='Text message sent to user')
    expert_html = models.TextField('Expert comment, expanded and allows html',
                                   help_text='Expanded message information'
                                   'goes here. This field can contain HTML')
    public = models.BooleanField(default=False)
    notification_content = models.ForeignKey(NotificationContent,
                                             on_delete=models.CASCADE)
    preset_notification = models.ForeignKey(PredefinedNotification, null=True,
                                            blank=True, default=None,
                                            on_delete=models.CASCADE)

    class Meta:
        """Meta."""

        db_table = 'tigapublic_map_notification'


class StormDrainUserVersions(models.Model):
    """Storm drain user versions."""

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.IntegerField()
    published_date = models.DateTimeField(default=timezone.now)
    style_json = models.TextField()
    visible = models.BooleanField()
    title = models.CharField(max_length=50, blank=True)

    class Meta:
        """Meta."""

        db_table = 'tigapublic_storm_drain_user_version'
        managed = True


class Epidemiology(models.Model):
    """Epidemiolgy model."""

    id = models.CharField(max_length=15,
                          primary_key=True)
    year = models.IntegerField()
    lon = models.FloatField(null=False)
    lat = models.FloatField(null=False)
    health_center = models.CharField(max_length=225,
                                     blank=True,
                                     null=True)
    province = models.CharField(max_length=225,
                                blank=True,
                                null=True)
    age = models.IntegerField()
    country = models.CharField(max_length=225,
                               blank=True,
                               null=True)
    date_arribal = models.DateTimeField(blank=True,
                                        null=True,
                                        default=None)
    date_symptom = models.DateTimeField(blank=True,
                                        null=True,
                                        default=None)
    date_notification = models.DateTimeField(blank=True,
                                             null=True,
                                             default=None)
    patient_state = models.CharField(max_length=225,
                                     blank=True,
                                     null=True)
    comments = models.TextField(help_text='Extra comments for patients',
                                default=None,
                                blank=True,
                                null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        """Meta."""

        db_table = 'tigapublic_epidemiology'

class Irideon(models.Model):
    """Irideon traps model."""

    id = models.CharField(max_length=30,
                          primary_key=True)

    record_time = models.DateTimeField(blank=True,
                                       null=True,
                                       default=None)

    classification = models.CharField(max_length=255,
                                      blank=True,
                                      null=True)

    client_name = models.CharField(max_length=30,
                                   blank=True,
                                   null=True)

    client_type = models.CharField(max_length=20,
                                   blank=True,
                                   null=True)

    lon = models.FloatField(db_column='lng',)

    lat = models.FloatField()

    nice_name = models.CharField(max_length=255,
                                 blank=True,
                                 null=True)

    processed_time = models.DateTimeField(blank=True,
                                          null=True,
                                          default=None)
    class Meta:
        managed = False