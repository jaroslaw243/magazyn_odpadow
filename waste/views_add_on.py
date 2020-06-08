import dateutil
import datetime
from .models import Pomiartlo, Pomiar, Lokalizacja, Liczniki, Sprzet, RoedigerPomiary
from django.core.paginator import Paginator


def nearest(items, pivot):
    pivot = pivot.data
    items_dates = []
    for i in items:
        items_dates.append(i.data_pomiaru)

    try:
        nearest_date = min(items_dates, key=lambda x: abs(x - pivot))
    except ValueError:
        return []

    for j in items:
        if j.data_pomiaru == nearest_date:
            return j


def measurement_value_check(waste_object):
    try:
        measurement = Pomiar.objects.filter(odpad_id=waste_object.odpad_id).order_by('-data')[0]
    except IndexError:
        return False
    loc = Lokalizacja.objects.filter(id_odpadu=waste_object.odpad_id).order_by('-data_umieszczenia')[0]
    loc_building = loc.id_polki.budynek

    bg_measurements = Pomiartlo.objects.filter(budynek=loc_building)
    bg_measurements = bg_measurements.filter(
        data_pomiaru__gte=measurement.data - dateutil.relativedelta.relativedelta(days=7),
        data_pomiaru__lte=measurement.data + dateutil.relativedelta.relativedelta(days=7))

    try:
        if nearest(bg_measurements, measurement).wartosc >= measurement.wartosc:
            return True
        else:
            return False
    except AttributeError:
        return False


def measurement_time_check(waste_object2):
    if waste_object2.data_usuniecia_10t <= datetime.datetime.now():
        return True
    else:
        return False


def get_counter(category):
    counter = Liczniki.objects.get(licznik_id=category)
    year_now = datetime.datetime.now().year
    if counter.rok == year_now:
        if counter.wartosc == 99999:
            counter.wartosc = 0
    else:
        counter.wartosc = 0
        counter.rok = year_now

    counter.wartosc += 1
    counter.save()

    return counter.wartosc


def check_calibration_validity(date, gear):
    gear_cal_date = Sprzet.objects.get(sprzet_id=gear).data_kalibracji_exp
    if datetime.datetime.strptime(date, '%Y-%m-%d').date() > gear_cal_date:
        return 0
    else:
        return 1


def waste_db_time_period(request, delta):
    date_now = datetime.datetime.now()
    location = Lokalizacja.objects.filter(data_umieszczenia__gte=date_now - delta,
                                          data_umieszczenia__lte=date_now)
    location = location.filter(biezacy=1).order_by('-data_umieszczenia')
    paginator = Paginator(location, 20)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def bck_rad_time_period(request, delta):
    date_now = datetime.datetime.now()
    mes_bg = Pomiartlo.objects.filter(data_pomiaru__gte=date_now - delta,
                                      data_pomiaru__lte=date_now).order_by('-data_pomiaru')
    paginator = Paginator(mes_bg, 20)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def view_tanks_time_period(request, delta):
    date_now = datetime.datetime.now()
    tanks = RoedigerPomiary.objects.filter(data_pomiaru__gte=date_now - delta,
                                           data_pomiaru__lte=date_now).order_by('-data_pomiaru')
    paginator = Paginator(tanks, 20)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
