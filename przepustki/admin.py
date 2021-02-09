from django.contrib import admin
from .models import Lokalizacja, Dzial, Pracownik, Autor, RodzajWpisu, Przepustka, Csv


@admin.register(Lokalizacja)
class LokalizacjaAdmin(admin.ModelAdmin):
    list_display = ('lokalizacja', 'aktywny')
    list_filter = ('aktywny',)
    search_fields = ('lokalizacja',)


@admin.register(Dzial)
class DzialAdmin(admin.ModelAdmin):
    list_display = ('dzial', 'lokalizacja', 'aktywny')
    list_filter = ('lokalizacja', 'aktywny',)
    search_fields = ('dzial', 'lokalizacja')


@admin.register(Pracownik)
class PracownikAdmin(admin.ModelAdmin):
    list_display = ('nr_pracownika','imie','nazwisko','dzial','zatrudniony')
    list_filter = ('dzial','zatrudniony')
    search_fields = ('nr_pracownika','nazwisko')


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('user',)


@admin.register(RodzajWpisu)
class RodzajWpisuAdmin(admin.ModelAdmin):
    list_display = ('rodzaj','aktywny')
    list_filter = ('aktywny',)
    search_fields = ('rodzaj',)


@admin.register(Przepustka)
class PrzepustkaAdmin(admin.ModelAdmin):
    list_display = ('pracownik','data_wyjscia','godzina_wyjscia','data_przyjscia','godzina_przyjscia','rodzaj_wpisu','cofnieta','autor_wpisu')
    list_filter = ('rodzaj_wpisu','cofnieta','autor_wpisu')
    search_fields = ('pracownik','data_wyjscia')


admin.site.register(Csv)