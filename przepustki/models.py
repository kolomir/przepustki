from django.db import models
from django.contrib.auth.models import User


class Lokalizacja(models.Model):
    lokalizacja = models.CharField(max_length=30, unique=True)
    aktywny = models.BooleanField(default=True)

    def __str__(self):
        return self.lokalizacja


class Dzial(models.Model):
    dzial = models.CharField(max_length=20, unique=False)
    lokalizacja = models.ForeignKey(Lokalizacja, on_delete=models.CASCADE)
    aktywny = models.BooleanField(default=True)

    def __str__(self):
        return self.dzial


class Pracownik(models.Model):
    nr_pracownika = models.DecimalField(max_digits=4, decimal_places=0, unique=True)
    imie = models.CharField(max_length=20)
    nazwisko = models.CharField(max_length=40)
    dzial = models.ForeignKey(Dzial, on_delete=models.CASCADE)
    zatrudniony = models.BooleanField(default=True)

    def __str__(self):
        return str(self.nr_pracownika)


class Autor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return self.user.username


class RodzajWpisu(models.Model):
    rodzaj = models.CharField(max_length=60, unique=True)
    aktywny = models.BooleanField(default=True)

    def __str__(self):
        return self.rodzaj


#id wpisu będzie wraz z rokiem numerem kolejnym przepustki
class Przepustka(models.Model):
    pracownik = models.ForeignKey(Pracownik, on_delete=models.CASCADE, default=1)
    data_wyjscia = models.DateField('data wyjscia')
    godzina_wyjscia = models.TimeField('godzina wyjscia')
    data_przyjscia = models.DateField('data przyjscia', blank=True, null=True)
    godzina_przyjscia = models.TimeField('godzina przyjscia', blank=True, null=True)
    rodzaj_wpisu = models.ForeignKey(RodzajWpisu, on_delete=models.CASCADE, default=1)
    autor_wpisu = models.ForeignKey(Autor, on_delete=models.CASCADE)
    data_dodania = models.DateTimeField('data dodania', blank=True, null=True)
    cofnieta = models.BooleanField(default=False)

    def przepustki(self):
        return str(self.pracownik) + "(" +str(self.data_wyjscia) + ")"

    def __str__(self):
        return self.przepustki()


class Csv(models.Model):
    file_name = models.FileField(upload_to='csvs')
    uploaded = models.DateTimeField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f"File id: {self.id}"

