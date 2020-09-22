from django.contrib import admin
from django.template.response import TemplateResponse
from .models import Izotop, Slownik, Sprzet, Polka, Odpad, Osoby, RoedigerZbiorniki, RoedigerPomiary, Pomiartlo, Pomiar, \
    Izotopy, Liczniki
from django.urls import path
from django.shortcuts import render, redirect
import datetime


def deactivate(modeladmin, request, queryset):
    rows_deactivated = queryset.update(active=0)
    if rows_deactivated == 1:
        message_bit = "1 wartość została oznaczona"
    elif 2 <= rows_deactivated <= 4:
        message_bit = "%s wartości zostały oznaczone" % rows_deactivated
    else:
        message_bit = "%s wartości zostało oznaczonych" % rows_deactivated
    modeladmin.message_user(request, "%s jako nieaktywne." % message_bit)


def activate(modeladmin, request, queryset):
    rows_activated = queryset.update(active=1)
    if rows_activated == 1:
        message_bit = "1 wartość została oznaczona"
    elif 2 <= rows_activated <= 4:
        message_bit = "%s wartości zostały oznaczone" % rows_activated
    else:
        message_bit = "%s wartości zostało oznaczonych" % rows_activated
    modeladmin.message_user(request, "%s jako aktywne." % message_bit)


def active2bool(obj):
    return bool(obj.active)


deactivate.short_description = 'Oznacz wybrane wartości jako nieaktywne'
activate.short_description = 'Oznacz wybrane wartości jako aktywne'
active2bool.short_description = 'Aktywny'
active2bool.boolean = True


class IzotopAdmin(admin.ModelAdmin):
    exclude = ['izotop_id']
    list_filter = ['active']
    list_display = ['nazwa', active2bool]
    actions = [activate, deactivate]

    def has_delete_permission(self, request, obj=None):
        return False


class SlownikAdmin(admin.ModelAdmin):
    exclude = ['slownik_id']
    list_filter = ['parent_id', 'active']
    list_display = ['nazwa', 'parent_name', active2bool]
    actions = [activate, deactivate]

    def parent_name(self, obj):
        return obj.parent_id

    parent_name.short_description = 'Grupa'

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return Slownik.objects.exclude(parent_id=0)


class SprzetAdmin(admin.ModelAdmin):
    exclude = ['sprzet_id']
    list_filter = ['active']
    list_display = ['nazwa', 'active2bool_gear']
    actions = [activate, deactivate]

    def active2bool_gear(self, obj):
        return bool(obj.active)

    active2bool_gear.short_description = 'W użyciu'
    active2bool_gear.boolean = True

    def has_delete_permission(self, request, obj=None):
        return False


class PolkaAdmin(admin.ModelAdmin):
    exclude = ['polka_id']
    list_filter = ['budynek', 'pokoj']
    list_display = ['polka_id', 'tag', 'pokoj', 'opis']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return Polka.objects.exclude(polka_id=9999)


class OdpadAdmin(admin.ModelAdmin):
    exclude = ['odpad_id']
    date_hierarchy = 'data_przekazania_do'
    list_filter = ['active']
    list_display = ['odpad_id', 'nr_ewidencyjny', 'data_przekazania_do']
    search_fields = ['nr_ewidencyjny']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class IzotopyAdmin(admin.ModelAdmin):
    exclude = ['izotopy_id']
    list_display = ['isotopes']

    def new_isotopes_submit(self, request):
        waste = request.POST.get('waste')
        isotopes = request.POST.getlist('isotopeSelect')

        if len(isotopes) == 0:
            return redirect('/admin/waste/izotopy/')

        Izotopy.objects.filter(id_odpadu=waste).delete()

        decay_times = []
        for d in isotopes:
            decay_times.append(Izotop.objects.get(izotop_id=d).t_polokres)
        isotope_decay = max(decay_times)

        if len(isotopes) == 1:
            isotope_name = Izotop.objects.get(izotop_id=isotopes[0]).nazwa
        else:
            isotope_name = 'mieszane'

        old_waste = Odpad.objects.get(odpad_id=waste)
        old_waste.data_usuniecia_10t = old_waste.data_przekazania_do + datetime.timedelta(days=isotope_decay * 10)

        old_ref_num = old_waste.nr_ewidencyjny.split('/')
        old_waste.nr_ewidencyjny = f'{old_ref_num[0]}/{isotope_name}/{old_ref_num[2]}/{old_ref_num[3]}'

        old_waste.save()

        for iso_id in isotopes:
            new_isos = Izotopy(id_odpadu=Odpad(waste), id_izotop=Izotop(iso_id))
            new_isos.save()
        return redirect('/admin/waste/izotopy/')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def isotopes(self, obj):
        return f'{obj.id_odpadu.nr_ewidencyjny} - {obj.id_izotop.nazwa}'
    isotopes.short_description = 'Izotopy w odpadach'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('my_view/', self.new_isotopes_submit),
        ]
        return my_urls + urls

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        all_isotopes = Izotop.objects.filter(active=1)
        context = {'all_isotopes': all_isotopes,
                   'ob': obj.id_odpadu,
                   'opts': self.model._meta,
                   'change': True,
                   'add': False,
                   'is_popup': False,
                   'save_as': False,
                   'has_delete_permission': False,
                   'has_add_permission': False,
                   'has_change_permission': True,
                   'has_view_permission': True,
                   'has_editable_inline_admin_formsets': True}
        return TemplateResponse(request, "admin/change_isotopes.html", context)


class OsobyAdmin(admin.ModelAdmin):
    exclude = ['osoby_id']
    list_display = ['nazwa', active2bool]
    list_filter = ['active']
    search_fields = ['nazwa']
    actions = [activate, deactivate]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return Osoby.objects.exclude(osoby_id__in=(31, 73))


class PomiartloAdmin(admin.ModelAdmin):
    exclude = ['pomiarTlo_id']
    date_hierarchy = 'data_pomiaru'
    list_display = ['wartosc', 'jednostka', 'data_pomiaru', 'budynek']
    list_filter = ['budynek']


class PomiarAdmin(admin.ModelAdmin):
    exclude = ['pomiar_id']
    date_hierarchy = 'data'
    list_display = ['wartosc', 'jednostka', 'pomiar_odpad', 'data', 'pomiar_wykonal']
    search_fields = ['wykonal__nazwa', 'odpad_id__nr_ewidencyjny']

    def pomiar_odpad(self, obj):
        return obj.odpad_id

    pomiar_odpad.short_description = 'Odpad'

    def pomiar_wykonal(self, obj):
        return obj.wykonal

    pomiar_wykonal.short_description = 'Wykonał'


class RoedigerZbiornikiAdmin(admin.ModelAdmin):
    exclude = ['zbiornik_id']
    list_display = ['zbiornik_id', 'stan', 'zapelnienie', 'active2bool_tank']
    list_filter = ['active']
    actions = [activate, deactivate]

    def active2bool_tank(self, obj):
        return bool(obj.active)

    active2bool_tank.short_description = 'w użyciu'
    active2bool_tank.boolean = True

    def has_delete_permission(self, request, obj=None):
        return False


class RoedigerPomiaryAdmin(admin.ModelAdmin):
    exclude = ['pomiar_zbiornika_id']
    date_hierarchy = 'data_pomiaru'
    list_display = ['data_pomiaru', 'nr_zbiornika', 'wykonal']
    list_filter = ['nr_zbiornika']
    search_fields = ['wykonal__nazwa']


class LicznikiAdmin(admin.ModelAdmin):
    exclude = ['licznik_id']
    list_display = ['opis', 'wartosc', 'rok']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Odpad, OdpadAdmin)
admin.site.register(Sprzet, SprzetAdmin)
admin.site.register(Slownik, SlownikAdmin)
admin.site.register(Izotop, IzotopAdmin)
admin.site.register(Polka, PolkaAdmin)
admin.site.register(Osoby, OsobyAdmin)
admin.site.register(Pomiartlo, PomiartloAdmin)
admin.site.register(Pomiar, PomiarAdmin)
admin.site.register(RoedigerZbiorniki, RoedigerZbiornikiAdmin)
admin.site.register(RoedigerPomiary, RoedigerPomiaryAdmin)
admin.site.register(Izotopy, IzotopyAdmin)
admin.site.register(Liczniki, LicznikiAdmin)
