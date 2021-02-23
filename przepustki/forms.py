from django.forms import ModelForm
from django import forms
from .models import Lokalizacja, Dzial, Pracownik, RodzajWpisu, Przepustka, Csv


#= Lokalizacja =======================================================
class LokalizacjaForm(ModelForm):
    class Meta:
        model = Lokalizacja
        fields = ['lokalizacja','aktywny']


class SkasowacLokalizacja(ModelForm):
    class Meta:
        model = Lokalizacja
        fields = [
            'aktywny',
        ]


#= Dzial =======================================================
class DzialForm(ModelForm):
    class Meta:
        model = Dzial
        fields = ['dzial','lokalizacja','aktywny']


class SkasowacDzial(ModelForm):
    class Meta:
        model = Dzial
        fields = [
            'aktywny',
        ]


#= Pracownik =======================================================
class PracownikForm(ModelForm):
    class Meta:
        model = Pracownik
        fields = ['nr_pracownika','imie','nazwisko','dzial','zatrudniony']


class SkasowacPracownik(ModelForm):
    class Meta:
        model = Pracownik
        fields = [
            'zatrudniony',
        ]


#= RodzajWpisu =======================================================
class RodzajWpisuForm(ModelForm):
    class Meta:
        model = RodzajWpisu
        fields = ['rodzaj','aktywny']


class SkasowacRodzajWpisu(ModelForm):
    class Meta:
        model = RodzajWpisu
        fields = [
            'aktywny',
        ]


#= Przepustka =======================================================
class PrzepustkaForm(ModelForm):
    class Meta:
        model = Przepustka
        fields = ['pracownik','data_wyjscia','godzina_wyjscia','data_przyjscia','godzina_przyjscia','rodzaj_wpisu','cofnieta']


class SkasowacPrzepustka(ModelForm):
    class Meta:
        model = Przepustka
        fields = [
            'cofnieta',
        ]


#= IMPORT =======================================================
class CsvModelForm(forms.ModelForm):
    class Meta:
        model = Csv
        fields = ('file_name',)
