# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = ('content_type', 'codename')


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    def __str__(self):
        return self.username

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Izotop(models.Model):
    izotop_id = models.SmallIntegerField(primary_key=True)
    nazwa = models.CharField(max_length=10)
    t_polokres = models.FloatField(db_column='T_polokres', verbose_name='Okres połowicznego rozpadu w dniach')  # Field name made lowercase.
    active = models.IntegerField(verbose_name='aktywny', choices=[(1, 'Tak'), (0, 'Nie')])

    def __str__(self):
        return self.nazwa

    class Meta:
        managed = False
        verbose_name = 'Izotop'
        verbose_name_plural = 'Izotopy'
        ordering = ['nazwa']
        db_table = 'izotop'


class Izotopy(models.Model):
    id_odpadu = models.ForeignKey('Odpad', models.DO_NOTHING, db_column='id_odpadu')
    id_izotop = models.ForeignKey('Izotop', models.DO_NOTHING, db_column='id_izotop')
    id_izotopy = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.id_odpadu.odpad_id} - {self.id_izotop}'

    class Meta:
        managed = False
        verbose_name = 'Izotop w odpadzie'
        verbose_name_plural = 'Izotopy w odpadach'
        db_table = 'izotopy'
        unique_together = [['id_odpadu', 'id_izotop']]


class Liczniki(models.Model):
    licznik_id = models.AutoField(primary_key=True)
    wartosc = models.SmallIntegerField()
    rok = models.PositiveSmallIntegerField()
    opis = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'liczniki'


class Lokalizacja(models.Model):
    lokalizacja_id = models.BigAutoField(primary_key=True)
    id_odpadu = models.ForeignKey('Odpad', models.DO_NOTHING, db_column='id_odpadu')
    id_polki = models.ForeignKey('Polka', models.DO_NOTHING, db_column='id_polki')
    data_umieszczenia = models.DateTimeField()
    osoba = models.ForeignKey('Osoby', models.DO_NOTHING, db_column='osoba')
    biezacy = models.IntegerField()

    def __str__(self):
        return f'{self.id_odpadu} - {self.id_polki}'

    class Meta:
        managed = False
        verbose_name = 'Lokalizacja'
        verbose_name_plural = 'Lokalizacje'
        ordering = ['-data_umieszczenia']
        db_table = 'lokalizacja'


class Odpad(models.Model):
    odpad_id = models.BigAutoField(primary_key=True)
    nr_ewidencyjny = models.CharField(max_length=40)
    nazwa_pracowni = models.ForeignKey('Slownik', models.DO_NOTHING, db_column='nazwa_pracowni',
                                       related_name='nazwa_pracowni')
    postac_fiz = models.ForeignKey('Slownik', models.DO_NOTHING, db_column='postac_fiz', related_name='postac_fiz',
                                   verbose_name='Postać fizyczna')
    aktywnosc = models.FloatField(verbose_name='stężenie promieniotwórcze')
    ilosc = models.FloatField(verbose_name='objętość')
    wlasciwosc_komentarz = models.CharField(max_length=255)
    dodatkowe_informacje = models.CharField(max_length=255, blank=True, null=True)
    grupa_odpadow = models.ForeignKey('Slownik', models.DO_NOTHING, db_column='grupa_odpadow',
                                      related_name='grupa_odpadow')
    skazenie_zewnetrzne = models.IntegerField(choices=[(1, 'Tak'), (0, 'Nie')])
    rodzaj_opakowania = models.ForeignKey('Slownik', models.DO_NOTHING, db_column='rodzaj_opakowania',
                                          related_name='rodzaj_opakowania')
    data_przekazania_do = models.DateTimeField()
    osoba_przekazanie_do = models.ForeignKey('Osoby', models.DO_NOTHING, db_column='osoba_przekazanie_do',
                                             related_name='osoba_przekazanie_do',
                                             verbose_name='Osoba przekazująca do magazynu')
    osoba_przyjmujaca = models.ForeignKey('Osoby', models.DO_NOTHING, db_column='osoba_przyjmujaca',
                                          related_name='osoba_przyjmujaca')
    data_usuniecia_10t = models.DateTimeField(db_column='data_usuniecia_10T')
    data_usuniecia_pomiar = models.DateTimeField(blank=True, null=True,
                                                 verbose_name='Data pomiaru wykonanego przy wyrzucaniu')
    data_wydania = models.DateTimeField(blank=True, null=True)
    osoba_wydanie = models.ForeignKey('Osoby', models.DO_NOTHING, db_column='osoba_wydanie', blank=True, null=True,
                                      related_name='osoba_wydanie', verbose_name='Osoba wydająca')
    osoba_odbior = models.ForeignKey('Osoby', models.DO_NOTHING, db_column='osoba_odbior', blank=True, null=True,
                                     related_name='osoba_odbior', verbose_name='Osoba odbierająca')
    odpad_zwrot = models.IntegerField(verbose_name='Odpad zwrócony do magazynu', choices=[(1, 'Tak'), (0, 'Nie')])
    active = models.IntegerField(verbose_name='aktywny', choices=[(1, 'Tak'), (0, 'Nie')])

    def __str__(self):
        return self.nr_ewidencyjny

    class Meta:
        managed = False
        verbose_name = 'Odpad'
        verbose_name_plural = 'Odpady'
        ordering = ['-odpad_id']
        db_table = 'odpad'


class Osoby(models.Model):
    osoby_id = models.AutoField(primary_key=True)
    nazwa = models.CharField(max_length=30, verbose_name='Nazwisko')
    active = models.IntegerField(verbose_name='aktywny', choices=[(1, 'Tak'), (0, 'Nie')])

    def __str__(self):
        return self.nazwa

    class Meta:
        managed = False
        verbose_name = 'Osoba'
        verbose_name_plural = 'Osoby'
        ordering = ['nazwa']
        db_table = 'osoby'


class Polka(models.Model):
    polka_id = models.AutoField(primary_key=True)
    regal = models.CharField(max_length=4)
    polka = models.CharField(max_length=4)
    tag = models.CharField(max_length=8)
    budynek = models.CharField(max_length=4)
    pokoj = models.CharField(max_length=6)
    opis = models.CharField(max_length=64)

    def __str__(self):
        return f'{self.tag} p. {self.pokoj}'

    class Meta:
        managed = False
        verbose_name = 'Półka'
        verbose_name_plural = 'Półki'
        ordering = ['budynek', 'pokoj', 'regal', 'polka']
        db_table = 'polka'


class Pomiar(models.Model):
    pomiar_id = models.BigAutoField(primary_key=True)
    odpad_id = models.ForeignKey('Odpad', models.DO_NOTHING, db_column='odpad_id', verbose_name='odpad')
    sprzet_id_p = models.ForeignKey('Sprzet', models.DO_NOTHING, db_column='sprzet_id_p',
                                    verbose_name='urządzenie pomiarowe')
    wartosc = models.FloatField()
    jednostka = models.CharField(max_length=10)
    odleglosc = models.FloatField(verbose_name='odległość [cm]')
    data = models.DateTimeField(verbose_name='data pomiaru')
    wykonal = models.ForeignKey('Osoby', models.DO_NOTHING, db_column='wykonal')
    waznosc_kal_sprz = models.IntegerField(verbose_name='urządzenie pomiarowe z ważną kalibracją', choices=[(1, 'Tak'),
                                                                                                            (0, 'Nie')])

    class Meta:
        managed = False
        verbose_name = 'Pomiar odpadu'
        verbose_name_plural = 'Pomiary odpadów'
        ordering = ['-data']
        db_table = 'pomiar'


class Pomiartlo(models.Model):
    pomiartlo_id = models.AutoField(db_column='pomiarTlo_id', primary_key=True)  # Field name made lowercase.
    wartosc = models.FloatField()
    jednostka = models.CharField(max_length=6)
    data_pomiaru = models.DateTimeField()
    sprzet_id = models.ForeignKey('Sprzet', models.DO_NOTHING, db_column='sprzet_id',
                                  verbose_name='urządzenie pomiarowe')
    budynek = models.CharField(max_length=5, choices=[('SB', 'Stary budynek'), ('NB', 'Nowy budynek')])
    waznosc_kal_sprz = models.IntegerField(verbose_name='urządzenie pomiarowe z ważną kalibracją', choices=[(1, 'Tak'),
                                                                                                            (0, 'Nie')])

    class Meta:
        managed = False
        verbose_name = 'Pomiar tła'
        verbose_name_plural = 'Pomiary tła'
        ordering = ['-data_pomiaru', 'budynek']
        db_table = 'pomiartlo'


class RoedigerPomiary(models.Model):
    pomiar_zbiornika_id = models.AutoField(primary_key=True)
    nr_zbiornika = models.ForeignKey('RoedigerZbiorniki', models.DO_NOTHING, db_column='nr_zbiornika')
    data_pomiaru = models.DateTimeField()
    wartosc = models.FloatField()
    jednostka = models.CharField(max_length=10)
    wykonal = models.ForeignKey(Osoby, models.DO_NOTHING, db_column='wykonal')

    class Meta:
        managed = False
        ordering = ['nr_zbiornika', '-data_pomiaru']
        verbose_name = 'Pomiar zbiornika roediger'
        verbose_name_plural = 'Pomiary zbiorników roediger'
        db_table = 'roediger_pomiary'


class RoedigerZbiorniki(models.Model):
    zbiornik_id = models.SmallIntegerField(primary_key=True)
    stan = models.CharField(max_length=1, choices=[('O', 'Otwarty'), ('Z', 'Zamknięty'), ('D', 'Dekontaminacja')])
    zapelnienie = models.IntegerField()
    active = models.IntegerField(verbose_name='w użyciu', choices=[(1, 'Tak'), (0, 'Nie')])

    def __str__(self):
        return str(self.zbiornik_id)

    class Meta:
        managed = False
        ordering = ['zbiornik_id']
        verbose_name = 'Zbiornik roediger'
        verbose_name_plural = 'Zbiorniki roediger'
        db_table = 'roediger_zbiorniki'


class Settings(models.Model):
    settings_id = models.AutoField(primary_key=True)
    opis = models.CharField(max_length=25)
    wartosc = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'settings'


class Slownik(models.Model):
    slownik_id = models.SmallIntegerField(primary_key=True)
    parent_id = models.SmallIntegerField(verbose_name='grupa', choices=[(1, 'nazwa pracowni'), (2, 'postać fizyczna'),
                                                                        (3, 'grupa odpadów'), (4, 'rodzaj opakowania'),
                                                                        (5, 'miejsce powstania')])
    nazwa = models.CharField(max_length=128)
    active = models.IntegerField(verbose_name='aktywny', choices=[(1, 'Tak'), (0, 'Nie')])

    def __str__(self):
        return self.nazwa

    class Meta:
        managed = False
        ordering = ['parent_id']
        verbose_name = 'Słownik'
        verbose_name_plural = 'Słowniki'
        db_table = 'slownik'


class Sprzet(models.Model):
    sprzet_id = models.SmallIntegerField(primary_key=True)
    nazwa = models.CharField(max_length=40)
    data_kalibracji_exp = models.DateField(verbose_name='data wygaśnięcia kalibracji')
    active = models.IntegerField(verbose_name='aktywny', choices=[(1, 'Tak'), (0, 'Nie')])

    def __str__(self):
        return self.nazwa

    class Meta:
        managed = False
        verbose_name = 'Urządzenie pomiarowe'
        verbose_name_plural = 'Urządzenia pomiarowe'
        db_table = 'sprzet'


class Users(models.Model):
    users_id = models.AutoField(primary_key=True)
    nazwisko = models.CharField(max_length=50)
    imie = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=35)
    mail = models.CharField(max_length=50)
    utype = models.IntegerField()
    active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'users'
