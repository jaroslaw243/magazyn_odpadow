from django.http import FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as d_log_out
from django.contrib.auth.decorators import login_required, permission_required
from .models import Odpad, Pomiartlo, Pomiar, Izotop, Slownik, Osoby, Izotopy, Lokalizacja, Polka, Sprzet, \
    RoedigerPomiary, RoedigerZbiorniki
import datetime
import dateutil.relativedelta
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from .views_add_on import radioactivity_check, half_life_check, get_counter, check_calibration_validity, \
    waste_db_time_period, bck_rad_time_period, view_tanks_time_period
from reportlab.pdfgen import canvas
import io


def home_view(request):
    return render(request, 'home_page.html')


def log_in(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        messages.info(request, 'Zalogowano')
        return redirect('/waste/view_week')
    else:
        messages.info(request, 'Niepoprawny login i/lub hasło')
        return redirect('home')


def log_out(request):
    d_log_out(request)
    return redirect('home')


def index(request):
    return render(request, 'index.html')


@login_required
def add_form(request):
    isotope = Izotop.objects.filter(active=1)
    lab_name = Slownik.objects.filter(parent_id=1, active=1)
    waste_group = Slownik.objects.filter(parent_id=3, active=1)
    p_of_origin = Slownik.objects.filter(parent_id=5, active=1)
    gear_to_use = Sprzet.objects.filter(active=1)
    rooms = Polka.objects.all().values('pokoj').distinct().order_by('-pokoj')
    rooms = rooms.exclude(pokoj='UT')

    return render(request, 'add_form.html', {'isotope': isotope, 'lab_name': lab_name, 'waste_group': waste_group,
                                             'gear': gear_to_use, 'p_of_origin': p_of_origin, 'rooms': rooms})


def view_db_waste_week(request):
    return render(request, 'view_db_waste.html',
                  {'location': waste_db_time_period(request, datetime.timedelta(days=7))})


def view_db_waste_month(request):
    return render(request, 'view_db_waste.html',
                  {'location': waste_db_time_period(request, dateutil.relativedelta.relativedelta(months=1))})


def view_db_waste_quarter(request):
    return render(request, 'view_db_waste.html',
                  {'location': waste_db_time_period(request, dateutil.relativedelta.relativedelta(months=3))})


def view_db_waste_year(request):
    return render(request, 'view_db_waste.html',
                  {'location': waste_db_time_period(request, dateutil.relativedelta.relativedelta(years=1))})


def view_db_waste_all(request):
    location = Lokalizacja.objects.all()
    location = location.filter(biezacy=1).order_by('-data_umieszczenia')
    paginator = Paginator(location, 20)
    page_number = request.GET.get('page')
    location_page = paginator.get_page(page_number)
    return render(request, 'view_db_waste.html', {'location': location_page})


def view_db_monthly_report(request):
    report_year = request.POST.get('report_year')
    report_month = request.POST.get('report_month')

    if report_year is None:
        prior_month_year = datetime.datetime.now() - dateutil.relativedelta.relativedelta(months=1)
        report_year = prior_month_year.year
        report_month = prior_month_year.month

    years = Odpad.objects.datetimes('data_wydania', 'year', order='DESC')
    removed_waste = Odpad.objects.filter(data_wydania__year=report_year)
    removed_waste = removed_waste.filter(data_wydania__month=report_month)
    removed_waste = removed_waste.filter(active=0).order_by('-data_wydania')
    removed_waste_count = removed_waste.count()

    return render(request, 'view_monthly_report.html', {'removed_waste': removed_waste, 'years': years,
                                                        'report_year': report_year, 'report_month': report_month,
                                                        'removed_waste_count': removed_waste_count})


def view_by_date_search(request):
    date_from = request.POST.get('date_f')
    date_to = request.POST.get('date_t')
    try:
        location = Lokalizacja.objects.filter(data_umieszczenia__range=(date_from, date_to))
        location = location.filter(biezacy=1).order_by('-data_umieszczenia')
        paginator = Paginator(location, 20)
        page_number = request.GET.get('page')
        location_page = paginator.get_page(page_number)
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/view_search')

    return render(request, 'view_db_search_by_date.html', {'location': location_page})


def view_by_name_search(request):
    ref_num = request.GET.get('ref_num')
    try:
        if ref_num.isnumeric():
            waste_res = Odpad.objects.get(odpad_id=int(ref_num))
        else:
            waste_res = Odpad.objects.filter(nr_ewidencyjny__iexact=ref_num)[0]

    except IndexError:
        messages.info(request, 'Nie ma takiego numeru ewidencyjnego w bazie')
        return redirect('/waste/view_search')
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiego numeru ewidencyjnego w bazie')
        return redirect('/waste/view_search')

    location_res = Lokalizacja.objects.filter(id_odpadu=waste_res.odpad_id)
    if location_res.filter(biezacy=1).count() == 1:
        location_res = location_res.get(biezacy=1)
    else:
        location_res = location_res.order_by('-data_umieszczenia').first()

    isotopes_res = Izotopy.objects.filter(id_odpadu=waste_res.odpad_id)
    measurements = Pomiar.objects.filter(odpad_id=waste_res.odpad_id).order_by('-data')

    return render(request, 'view_db_search_by_name.html', {'waste': waste_res, 'location': location_res,
                                                           'isotopes': isotopes_res, 'measurements': measurements})


def search_form(request):
    return render(request, 'search.html')


@login_required
def remove_waste(request):
    waste_un_filtered = Odpad.objects.filter(active=1).order_by('data_przekazania_do')
    waste = []
    for u in waste_un_filtered:
        if radioactivity_check(u) or half_life_check(u):
            waste.append(u)

    gear_m = Sprzet.objects.filter(active=1)

    return render(request, 'remove_waste.html', {'waste': waste, 'gear': gear_m})


@permission_required(('waste.change_odpad', 'waste.change_lokalizacja', 'waste.add_lokalizacja', 'waste.add_pomiar'))
def remove_waste_submit(request):
    waste_id = request.POST.get('wasteSelect')
    try:
        waste_to_be_removed = Odpad.objects.get(odpad_id=waste_id)
    except ObjectDoesNotExist:
        messages.info(request, 'Należy wybrać odpad')
        return redirect('/waste/remove')

    person_giving_name = request.POST.get('person_g')
    person_receiving_name = request.POST.get('person_r')
    person_making_mes_name = request.POST.get('person_making_mes')
    remove_date = request.POST.get('remove_date')
    remove_time = request.POST.get('remove_time')

    dose = request.POST.get('dose')
    dose_unit = request.POST.get('dose_unit', 'uSv/h')
    mes_distance = request.POST.get('mes_distance', 1)
    gear_select = request.POST.get('gear_select')
    mes_date = request.POST.get('mes_date')
    mes_time = request.POST.get('mes_time')

    try:
        person_giving = Osoby.objects.filter(nazwa__iexact=person_giving_name)
        person_giving = person_giving.filter(active=1)[0]
        person_receiving = Osoby.objects.filter(nazwa__iexact=person_receiving_name)
        person_receiving = person_receiving.filter(active=1)[0]

        person_making_mes = Osoby.objects.filter(nazwa__iexact=person_making_mes_name)
        person_making_mes = person_making_mes.filter(active=1)[0]
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/remove')
    except IndexError:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/remove')

    waste_to_be_removed.data_usuniecia_pomiar = mes_date + ' ' + mes_time
    waste_to_be_removed.data_wydania = remove_date + ' ' + remove_time
    waste_to_be_removed.osoba_wydanie = person_giving
    waste_to_be_removed.osoba_odbior = person_receiving
    waste_to_be_removed.active = 0

    waste_to_be_removed.save()

    old_waste_location = Lokalizacja.objects.filter(id_odpadu=waste_id)
    old_waste_location = old_waste_location.get(biezacy=1)
    old_waste_location.biezacy = 0
    old_waste_location.save()

    try:
        new_waste_location = Lokalizacja(id_odpadu=Odpad(waste_id), id_polki=Polka(9999),
                                         data_umieszczenia=(remove_date + ' ' + remove_time),
                                         osoba=person_giving, biezacy=1)
        new_waste_location.save()

        remove_mes = Pomiar(odpad_id=Odpad(waste_id), sprzet_id_p=Sprzet(gear_select), wartosc=dose,
                            jednostka=dose_unit,
                            odleglosc=mes_distance, data=(mes_date + ' ' + mes_time), wykonal=person_making_mes,
                            waznosc_kal_sprz=check_calibration_validity(mes_date, gear_select))
        remove_mes.save()

    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/remove')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/remove')

    messages.info(request, 'Wyrzucono odpad')

    return redirect('/waste/remove')


def bck_rad_week(request):
    return render(request, 'bck_rad.html', {'mes_bg': bck_rad_time_period(request, datetime.timedelta(days=7))})


def bck_rad_month(request):
    return render(request, 'bck_rad.html',
                  {'mes_bg': bck_rad_time_period(request, dateutil.relativedelta.relativedelta(months=1))})


def bck_rad_quarter(request):
    return render(request, 'bck_rad.html',
                  {'mes_bg': bck_rad_time_period(request, dateutil.relativedelta.relativedelta(months=3))})


def bck_rad_year(request):
    return render(request, 'bck_rad.html',
                  {'mes_bg': bck_rad_time_period(request, dateutil.relativedelta.relativedelta(years=1))})


def bck_rad_all(request):
    mes_bg = Pomiartlo.objects.all().order_by('-data_pomiaru')
    paginator = Paginator(mes_bg, 20)
    page_number = request.GET.get('page')
    mes_bg_page = paginator.get_page(page_number)
    return render(request, 'bck_rad.html', {'mes_bg': mes_bg_page})


def gear(request):
    gear_in = Sprzet.objects.filter(active=1)
    return render(request, 'gear.html', {'gear': gear_in})


@login_required
def calibrate(request):
    gear_c = Sprzet.objects.all()
    return render(request, 'calibrate_gear.html', {'gear_c': gear_c})


@permission_required('waste.change_sprzet')
def calibrate_submit(request):
    gear_select = request.POST.get('gearSelect')
    new_date_c = request.POST.get('date_c')

    gear_to_calibrate = Sprzet.objects.get(sprzet_id=gear_select)
    gear_to_calibrate.data_kalibracji_exp = new_date_c
    gear_to_calibrate.save()
    messages.info(request, 'Zapisano nową datę wygaśnięcia kalibracji')

    return redirect('/waste/calibrate_gear')


@login_required
def add_new_mes_form(request):
    gear_m = Sprzet.objects.filter(active=1)
    person = request.user.last_name

    return render(request, 'add_new_waste_mes.html', {'gear': gear_m, 'person': person})


@login_required
def add_new_bg_mes_form(request):
    gear_m = Sprzet.objects.filter(active=1)
    return render(request, 'add_new_bg_mes.html', {'gear': gear_m})


@permission_required('waste.add_pomiar')
def add_mes_submit(request):
    try:
        waste_id = Odpad.objects.get(nr_ewidencyjny__iexact=request.POST.get('ref_num'))
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiego nr ewidencyjnego w bazie')
        return redirect('/waste/add_new_mes')

    dose = request.POST.get('dose')
    dose_unit = request.POST.get('dose_unit', 'uSv/h')
    mes_distance = request.POST.get('mes_distance', 1)
    gear_select = request.POST.get('gear_select')
    mes_date = request.POST.get('mes_date')
    mes_time = request.POST.get('mes_time')
    person_making_mes_name = request.POST.get('person_making_mes')

    try:
        person_making_mes = Osoby.objects.filter(nazwa__iexact=person_making_mes_name)
        person_making_mes = person_making_mes.filter(active=1)[0]
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/add_new_mes')
    except IndexError:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/add_new_mes')

    try:
        new_mes = Pomiar(odpad_id=waste_id, sprzet_id_p=Sprzet(gear_select), wartosc=dose, jednostka=dose_unit,
                         odleglosc=mes_distance, data=(mes_date + ' ' + mes_time), wykonal=person_making_mes,
                         waznosc_kal_sprz=check_calibration_validity(mes_date, gear_select))
        new_mes.save()
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add_new_mes')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add_new_mes')

    messages.info(request, 'Dodano pomiar')

    return redirect('/waste/add_new_mes')


@permission_required('waste.add_pomiartlo')
def add_bg_mes_submit(request):
    dose = request.POST.get('dose')
    dose_unit = request.POST.get('dose_unit', 'uSv/h')
    gear_select = request.POST.get('gear_select')
    mes_date = request.POST.get('mes_date')
    mes_time = request.POST.get('mes_time')
    building = request.POST.get('building')

    try:
        new_bg_mes = Pomiartlo(wartosc=dose, jednostka=dose_unit, data_pomiaru=(mes_date + ' ' + mes_time),
                               sprzet_id=Sprzet(gear_select), budynek=building,
                               waznosc_kal_sprz=check_calibration_validity(mes_date, gear_select))
        new_bg_mes.save()
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add_new_bg_mes')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add_new_bg_mes')

    messages.info(request, 'Dodano pomiar tła')

    return redirect('/waste/add_new_bg_mes')


@permission_required(('waste.add_odpad', 'waste.add_lokalizacja', 'waste.add_pomiar'))
def add_to_db_submit(request):
    place_origin = request.POST.get('place_origin')
    lab_name = request.POST.get('lab_name')
    ph_form = request.POST.get('ph_form')
    act = request.POST.get('act')
    quantity = request.POST.get('quantity')
    properties_a = request.POST.get('properties_a', '')
    properties_b = request.POST.get('properties_b', '')
    additional_inf = request.POST.get('additional_inf', '')
    waste_group = request.POST.get('waste_group')
    container = request.POST.get('container')
    person_giving_name = request.POST.get('person_giving')
    person_receiving_name = request.POST.get('person_receiving')
    hand_on_date = request.POST.get('hand_on_date')
    hand_on_time = request.POST.get('hand_on_time')
    active = request.POST.get('active', 1)
    izotop = request.POST.getlist('isotopeSelect')
    current = request.POST.get('current', 1)
    shelf_tag_str = request.POST.get('shelf').upper()
    building = request.POST.get('building')
    room_nr = request.POST.get('room')
    returned = request.POST.get('returned', 0)

    dose = request.POST.get('dose')
    dose_unit = request.POST.get('dose_unit', 'uSv/h')
    mes_distance = request.POST.get('mes_distance', 1)
    contamination = request.POST.get('contaminationSelect')
    gear_select = request.POST.get('gear_select')
    mes_date = request.POST.get('mes_date')
    mes_time = request.POST.get('mes_time')
    person_making_mes_name = request.POST.get('person_making_mes')

    try:
        person_giving = Osoby.objects.filter(nazwa__iexact=person_giving_name)
        person_giving = person_giving.filter(active=1)[0]
        person_receiving = Osoby.objects.filter(nazwa__iexact=person_receiving_name)
        person_receiving = person_receiving.filter(active=1)[0]

    except ObjectDoesNotExist:
        messages.info(request, 'Przekazanie na magazyn: Nie ma takiej osoby w bazie')
        return redirect('/waste/add')
    except IndexError:
        messages.info(request, 'Przekazanie na magazyn: Nie ma takiej osoby w bazie')
        return redirect('/waste/add')

    shelf_tags = Polka.objects.filter(budynek=building)
    try:
        shelf_tags = shelf_tags.filter(tag=shelf_tag_str)
        shelf_tag = shelf_tags.get(pokoj=room_nr)
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej kombinacji tagu półki, pokoju i budynku')
        return redirect('/waste/add')

    decay_times = []
    for d in izotop:
        decay_times.append(Izotop.objects.get(izotop_id=d).t_polokres)

    try:
        isotope_decay = max(decay_times)
    except ValueError:
        messages.info(request, 'Odpad musi zawierać przynajmniej jeden izotop')
        return redirect('/waste/add')

    try:
        hand_on_datetime = datetime.datetime.strptime(hand_on_date + ' ' + hand_on_time, '%Y-%m-%d %H:%M')
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add')

    date_10t = hand_on_datetime + datetime.timedelta(days=isotope_decay * 10)

    if len(izotop) == 1:
        isotope_name = Izotop.objects.get(izotop_id=izotop[0]).nazwa
    else:
        isotope_name = 'mieszane'

    if place_origin == '33' or place_origin == '34':
        counter = get_counter(1)
    else:
        counter = get_counter(2)

    ref_num = f'{counter}/{isotope_name}/{Slownik.objects.get(slownik_id=place_origin).nazwa}/{hand_on_datetime.year}'

    properties = f'a.ciekłe: {properties_a}, b.stałe: {properties_b}'

    try:
        new_waste = Odpad(nr_ewidencyjny=ref_num, nazwa_pracowni=Slownik(lab_name), postac_fiz=Slownik(ph_form),
                          aktywnosc=act, ilosc=quantity, wlasciwosc_komentarz=properties,
                          dodatkowe_informacje=additional_inf,
                          grupa_odpadow=Slownik(waste_group), skazenie_zewnetrzne=contamination,
                          rodzaj_opakowania=Slownik(container), data_przekazania_do=hand_on_datetime,
                          osoba_przekazanie_do=person_giving, osoba_przyjmujaca=person_receiving,
                          data_usuniecia_10t=date_10t, odpad_zwrot=returned, active=active)
        new_waste.save()
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add')

    messages.info(request, 'Dodano odpad')

    for izo in izotop:
        new_waste_isotope = Izotopy(id_odpadu=new_waste, id_izotop=Izotop(izo))
        new_waste_isotope.save()

    new_waste_shelf = Lokalizacja(id_odpadu=new_waste, id_polki=shelf_tag,
                                  data_umieszczenia=hand_on_datetime, osoba=person_receiving,
                                  biezacy=current)
    new_waste_shelf.save()

    try:
        if dose != '':
            person_making_mes = Osoby.objects.filter(nazwa__iexact=person_making_mes_name)
            person_making_mes = person_making_mes.filter(active=1)[0]

            new_waste_mes = Pomiar(odpad_id=new_waste, sprzet_id_p=Sprzet(gear_select),
                                   wartosc=dose, jednostka=dose_unit,
                                   odleglosc=mes_distance, data=(mes_date + ' ' + mes_time),
                                   wykonal=person_making_mes,
                                   waznosc_kal_sprz=check_calibration_validity(mes_date, gear_select))
            new_waste_mes.save()
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/add')
    except IndexError:
        messages.info(request, 'Pomiary radiometryczne: Nie ma takiej osoby w bazie')
        return redirect('/waste/add')

    return redirect('/waste/add')


def print_choice(request):
    return render(request, 'print_form.html')


def print_waste_card(request):
    buffer = io.BytesIO()

    p = canvas.Canvas(buffer)

    p.drawString(150, 150, "Hello world.")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='hello.pdf')


@login_required
def move_waste(request):
    rooms = Polka.objects.all().values('pokoj').distinct().order_by('-pokoj')
    rooms = rooms.exclude(pokoj='UT')
    return render(request, 'move_waste_form.html', {'rooms': rooms})


@permission_required(('waste.add_lokalizacja', 'waste.change_lokalizacja'))
def move_waste_submit(request):
    try:
        waste = Odpad.objects.get(nr_ewidencyjny__iexact=request.POST.get('ref_num'))
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiego nr ewidencyjnego w bazie')
        return redirect('/waste/move_waste')

    current = request.POST.get('current', 1)
    shelf_tag_str = request.POST.get('shelf').upper()
    building = request.POST.get('building')
    room_nr = request.POST.get('room')
    hand_on_date = request.POST.get('hand_on_date')
    hand_on_time = request.POST.get('hand_on_time')
    person_receiving_name = request.POST.get('person_receiving')

    old_loc = Lokalizacja.objects.filter(id_odpadu=waste)
    if old_loc.filter(biezacy=1).count() == 1:
        old_loc = old_loc.get(biezacy=1)
    else:
        messages.info(request, 'Brak jednej bieżącej lokalizacji')
        return redirect('/waste/move_waste')

    old_loc.biezacy = 0
    old_loc.save()

    try:
        person_receiving = Osoby.objects.filter(nazwa__iexact=person_receiving_name)
        person_receiving = person_receiving.filter(active=1)[0]
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/move_waste')
    except IndexError:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/move_waste')

    shelf_tags = Polka.objects.filter(budynek=building)
    try:
        shelf_tags = shelf_tags.filter(tag=shelf_tag_str)
        shelf_tag = shelf_tags.get(pokoj=room_nr)

        new_loc = Lokalizacja(id_odpadu=waste, id_polki=shelf_tag,
                              data_umieszczenia=(hand_on_date + ' ' + hand_on_time), osoba=person_receiving,
                              biezacy=current)
        new_loc.save()

    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej kombinacji tagu półki, pokoju i budynku')
        return redirect('/waste/move_waste')
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/move_waste')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/move_waste')

    messages.info(request, 'Zapisano nową lokalizację')

    return redirect('/waste/move_waste')


@login_required
def return_waste(request):
    rooms = Polka.objects.all().values('pokoj').distinct().order_by('-pokoj')
    rooms = rooms.exclude(pokoj='UT')

    return render(request, 'return_waste_form.html', {'rooms': rooms})


@permission_required(('waste.change_odpad', 'waste.change_lokalizacja', 'waste.add_lokalizacja'))
def return_waste_submit(request):
    try:
        waste = Odpad.objects.get(nr_ewidencyjny__iexact=request.POST.get('ref_num'))

    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiego nr ewidencyjnego w bazie')
        return redirect('/waste/return_waste')

    current = request.POST.get('current', 1)
    shelf_tag_str = request.POST.get('shelf').upper()
    building = request.POST.get('building')
    room_nr = request.POST.get('room')
    hand_on_date = request.POST.get('hand_on_date')
    hand_on_time = request.POST.get('hand_on_time')
    person_receiving_name = request.POST.get('person_receiving')

    waste.odpad_zwrot = 1
    waste.active = 1
    waste.save()

    old_loc = Lokalizacja.objects.filter(id_odpadu=waste)
    if old_loc.filter(biezacy=1).count() == 1:
        old_loc = old_loc.get(biezacy=1)
    else:
        messages.info(request, 'Brak jednej bieżącej lokalizacji')
        return redirect('/waste/move_waste')

    old_loc.biezacy = 0
    old_loc.save()

    try:
        person_receiving = Osoby.objects.filter(nazwa__iexact=person_receiving_name)
        person_receiving = person_receiving.filter(active=1)[0]
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/return_waste')
    except IndexError:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/return_waste')

    shelf_tags = Polka.objects.filter(budynek=building)
    try:
        shelf_tags = shelf_tags.filter(tag=shelf_tag_str)
        shelf_tag = shelf_tags.get(pokoj=room_nr)

        new_loc = Lokalizacja(id_odpadu=waste, id_polki=shelf_tag,
                              data_umieszczenia=(hand_on_date + ' ' + hand_on_time), osoba=person_receiving,
                              biezacy=current)
        new_loc.save()
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej kombinacji tagu półki, pokoju i budynku')
        return redirect('/waste/return_waste')
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/return_waste')
    except ValueError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/return_waste')

    messages.info(request, 'Zwrócono odpad do bazy')

    return redirect('/waste/return_waste')


@login_required
def comment(request):
    return render(request, 'comment_form.html')


@permission_required('waste.change_odpad')
def comment_submit(request):
    try:
        waste = Odpad.objects.get(nr_ewidencyjny__iexact=request.POST.get('ref_num'))
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiego nr ewidencyjnego w bazie')
        return redirect('/waste/comment')

    if waste.dodatkowe_informacje != '':
        waste.dodatkowe_informacje += ', ' + request.POST.get('additional_inf')
    else:
        waste.dodatkowe_informacje += request.POST.get('additional_inf')
    waste.save()

    messages.info(request, 'Dodano komentarz')

    return redirect('/waste/comment')


@login_required
def change_tank_fill(request):
    tanks = RoedigerZbiorniki.objects.filter(active=1)
    number_of_tanks = tanks.count()
    return render(request, 'change_tank_fill.html', {'tanks': tanks, 'number_of_tanks': number_of_tanks})


@login_required
def change_tank_state(request):
    tanks = RoedigerZbiorniki.objects.filter(active=1)
    number_of_tanks = tanks.count()
    return render(request, 'change_tank_state.html', {'tanks': tanks, 'number_of_tanks': number_of_tanks})


@permission_required('waste.change_roedigerzbiorniki')
def change_tank_fill_submit(request):
    tank_nr = request.POST.get('tank_nr')
    new_fill = request.POST.get('fill')

    try:
        tank = RoedigerZbiorniki.objects.get(zbiornik_id=tank_nr)
    except ObjectDoesNotExist:
        messages.info(request, 'Należy wybrać zbiornik')
        return redirect('/waste/change_tank_fill')

    tank.zapelnienie = new_fill
    tank.save()

    messages.info(request, 'Zmieniono stan zapełnienia zbiornika')

    return redirect('/waste/change_tank_fill')


@permission_required('waste.change_roedigerzbiorniki')
def change_tank_state_submit(request):
    tank_nr = request.POST.get('tank_nr')
    new_state = request.POST.get('new_state')

    try:
        tank = RoedigerZbiorniki.objects.get(zbiornik_id=tank_nr)
    except ObjectDoesNotExist:
        messages.info(request, 'Należy wybrać zbiornik')
        return redirect('/waste/change_tank_state')

    tank.stan = new_state
    tank.save()

    messages.info(request, 'Zmieniono stan zbiornika')

    return redirect('/waste/change_tank_state')


@login_required
def tank_mes(request):
    tanks = RoedigerZbiorniki.objects.filter(active=1)
    person = request.user.last_name
    return render(request, 'tank_mes.html', {'tanks': tanks, 'person': person})


@permission_required('waste.add_roedigerpomiary')
def tank_mes_submit(request):
    tank_nr = request.POST.get('tank_nr')
    tank_mes_date = request.POST.get('tank_mes_date')
    tank_mes_time = request.POST.get('tank_mes_time')
    tank_mes_value = request.POST.get('tank_mes_value')
    tank_mes_unit = request.POST.get('tank_mes_unit', 'Bq/l')
    person_making_tank_mes_name = request.POST.get('person_making_tank_mes')

    try:
        person_making_tank_mes = Osoby.objects.filter(nazwa__iexact=person_making_tank_mes_name)
        person_making_tank_mes = person_making_tank_mes.filter(active=1)[0]
    except ObjectDoesNotExist:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/tank_mes')
    except IndexError:
        messages.info(request, 'Nie ma takiej osoby w bazie')
        return redirect('/waste/tank_mes')

    try:
        new_tank_mes = RoedigerPomiary(nr_zbiornika=RoedigerZbiorniki(tank_nr),
                                       data_pomiaru=tank_mes_date + ' ' + tank_mes_time, wartosc=tank_mes_value,
                                       jednostka=tank_mes_unit, wykonal=person_making_tank_mes)

        new_tank_mes.save()
    except ValidationError:
        messages.info(request, 'Nieprawidłowy format daty')
        return redirect('/waste/tank_mes')

    messages.info(request, 'Dodano pomiar')
    return redirect('/waste/tank_mes')


def view_tanks_month(request):
    return render(request, 'view_tanks.html',
                  {'tanks': view_tanks_time_period(request, dateutil.relativedelta.relativedelta(months=1))})


def view_tanks_all(request):
    tanks = RoedigerPomiary.objects.all().order_by('-data_pomiaru')
    paginator = Paginator(tanks, 20)
    page_number = request.GET.get('page')
    tanks_page = paginator.get_page(page_number)
    return render(request, 'view_tanks.html', {'tanks': tanks_page})
