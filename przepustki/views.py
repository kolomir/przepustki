from django.shortcuts import render, redirect, get_object_or_404
from .models import Przepustka, Pracownik, RodzajWpisu, Dzial, Lokalizacja, Autor, Csv
from django.contrib.auth.decorators import login_required
from .forms import PrzepustkaForm, SkasowacPrzepustka, PracownikForm, PrzepustkaEditForm, SkasowacPracownik, DzialForm, CsvModelForm, PracownikDetal
from datetime import datetime, date, time, timedelta
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import Group
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.db.models import Count, Sum, F
from projekt.settings import EMAIL_HOST_USER, EMAIL_RECIVE_USER
from django.core.mail import send_mail

# == INNE =====================================================================================
def get_author(user):
    qs = Autor.objects.filter(user=user)
    if qs.exists():
        return qs[0]
    return None


def przerobienie_daty(data,godzina):
   (rok1, miesiac1, dzien1) = data.split("-")
   (godzina1, minuta1) = godzina.split(":")
   return datetime(int(rok1),int(miesiac1),int(dzien1),int(godzina1),int(minuta1))


def czas_na_minuty(t):
    #podawany jest czas w formacie HH:MM
    h, m, s = map(int, t.split(':'))
    return h * 60 + m


def int_na_czas(i):
    #podawany jest czas jako liczba w minutach
    hours = i // 60
    czas = '%02d:%02d' % (hours, i % 60)
    return czas


# == PRZEPUSTKI ===============================================================================
def przepustki_dzis(request):

    przepustki_dzis = Przepustka.objects.filter(cofnieta=False, data_wyjscia=date.today()).order_by('-id')[:50]
    przepustki_wczoraj = Przepustka.objects.filter(cofnieta=False, data_wyjscia=date.today()-timedelta(1)).order_by('-id')[:50]
    przepustki_przyszle = Przepustka.objects.filter(cofnieta=False, data_wyjscia__gt=date.today()).order_by('-id')[:50]
    lokalizacja = Lokalizacja.objects.filter(aktywny=True).order_by('lokalizacja')
    przepustki_suma = Przepustka.objects.all().values('pracownik__lokalizacja__lokalizacja').annotate(licz=Count('pracownik__lokalizacja__lokalizacja'))
    print(przepustki_suma)
    czas_teraz = datetime.now()
    #czas = czas_teraz.strftime("%H:%M").time()
    #czas = datetime.strptime(czas, '%H:%M').time()
    #print(czas_teraz)
    #for czasy in przepustki_dzis:
    #    if str(czasy.godzina_przyjscia) > czas_teraz:
    #        print(czasy.godzina_przyjscia)

    context = {
        'przepustki_dzis': przepustki_dzis,
        'przepustki_wczoraj': przepustki_wczoraj,
        'przepustki_przyszle': przepustki_przyszle,
        'przepustki_suma': przepustki_suma,
        'czas': czas_teraz,
    }

    return render(request, 'przepustki/przepustki_dzis.html', context)


@login_required
def wystaw_przepustke(request):
    form_przepustka = PrzepustkaForm(request.POST or None, request.FILES or None)
    pracownik = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')
    rodzaj = RodzajWpisu.objects.filter(aktywny=True).order_by('rodzaj')
    lokalizacja = Lokalizacja.objects.filter(aktywny=True).order_by('lokalizacja')
    moja_Data = datetime.now()
    data_dodania = moja_Data.strftime("%Y-%m-%d")
    ile = Przepustka.objects.last()
    if ile == None:
        id = 1
    else:
        id = ile.id +1
    rok = datetime.now().strftime("%Y")

    liczy = 0
    zmiana_I_start = 6
    zmiana_II_start = 14
    zmiana_III_start = 22

    data_wyjscie = request.POST.get('data_wyjscia')
    godz_wyjscie = request.POST.get('godzina_wyjscia')
    data_przyjscie = request.POST.get('data_przyjscia')
    godz_przyjscie = request.POST.get('godzina_przyjscia')
    dat_dod = request.POST.get('data_dodania')
    wpis = request.POST.get('rodzaj_wpisu')
    pracownik_wpis = request.POST.get('pracownik')
    print("--> godzina powrotu: ", godz_przyjscie)
    print("--> data_dodania: ", data_dodania)
    print("--> dat_dod: ", dat_dod)

    if data_wyjscie:
        print("data_wyjscie: ", data_wyjscie)
        przerobiona_data_wyjscia = przerobienie_daty(data_wyjscie, godz_wyjscie)


    if godz_przyjscie == "":
        godzina_wyjscia = "%s%s" % (godz_wyjscie[0], godz_wyjscie[1])
        if int(godzina_wyjscia) >= zmiana_I_start and int(godzina_wyjscia) < zmiana_II_start:
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '14:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(data_przyjscie, godzina_przyjscie)
            liczy = 1
        elif int(godzina_wyjscia) >= zmiana_II_start and int(godzina_wyjscia) < zmiana_III_start:
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '22:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(data_przyjscie, godzina_przyjscie)
            liczy = 1
        elif (int(godzina_wyjscia) >= zmiana_III_start and int(godzina_wyjscia) <= 23):
            data_przyjscie = datetime.strptime(data_wyjscie, '%Y-%m-%d').date() + timedelta(days=1)
            godzina_przyjscie = '06:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(str(data_przyjscie), godzina_przyjscie)
            liczy = 1
        elif (int(godzina_wyjscia) >= 0 and int(godzina_wyjscia) < zmiana_I_start):
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '06:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(str(data_przyjscie), godzina_przyjscie)
            liczy = 1
        else:
            print("Godzina poza zakresem")
    else:
        godzina_przyjscie = godz_przyjscie
        print("godzina powrotu: ", godz_przyjscie)
        print("data_przyjscie: ", data_przyjscie)
        if data_przyjscie:
            przerobiona_data_przyjscia = przerobienie_daty(data_przyjscie, godzina_przyjscie)
            liczy = 1

    if liczy:
        print('przerobiona_data_wyjscia:', przerobiona_data_wyjscia)
        print('przerobiona_data_przyjscia', przerobiona_data_przyjscia)

        czas_r = przerobiona_data_przyjscia - przerobiona_data_wyjscia
        print('czas_r:', czas_r)
        czas_w_minutach = czas_na_minuty(str(czas_r))
        print('nr1 minęło dni: %s, godzin: %d, minut: %d' % (czas_r.days, czas_r.seconds / 3600, (czas_r.seconds % 3600) / 60))

    #===================================================================
    #print('data_dodania: ', data_dodania)
    #print('data_wyjscia: ', data_wyjscie)
    #print('godzina_wyjscia: ', godz_wyjscie)
    #print('data_przyjscia: ', data_przyjscie)
    #print('godzina_przyjscia: ', godz_przyjscie)
    #print('wpis: ', wpis)
    #rodzaj_w = RodzajWpisu.objects.get(id=wpis).rodzaj
    #print('rodzaj:', rodzaj_w)
    #print('pracownik_wpis: ', pracownik_wpis)
    #if data_przyjscie == "":
    #    print('puste')
    #else:
    #    print('z datą')
    #====================================================================


    if form_przepustka.is_valid():
        #czas = '00:00'
        czas = str(czas_r)
        czas = '0'+czas
        print(czas)
        id_pracownika = Pracownik.objects.get(id=pracownik_wpis).nr_pracownika
        #czas_w_minutach = 0
        autor = get_author(request.user)
        if godz_przyjscie == "":
            form_przepustka.instance.data_przyjscia = data_przyjscie
            form_przepustka.instance.godzina_przyjscia = godzina_przyjscie
        form_przepustka.instance.autor_wpisu = autor
        form_przepustka.instance.czas = czas
        form_przepustka.instance.czas_w_minutach = czas_w_minutach
        form_przepustka.instance.data_dodania = request.POST.get('data_dodania')
        form_przepustka.save()
        if request.method == 'POST':

            subject = '[' + Lokalizacja.objects.get(id=Pracownik.objects.get(id=pracownik_wpis).lokalizacja_id).lokalizacja + '] PRZEPUSTKA nr ' + str(id) + '/' + rok + ' - wystawiona w dniu: ' + data_dodania
            message = '**    ' + RodzajWpisu.objects.get(id=wpis).rodzaj + '    ************************\n\n'
            message +='Przepustka dla: ' + Pracownik.objects.get(id=pracownik_wpis).nazwisko + ' ' + Pracownik.objects.get(id=pracownik_wpis).imie + '\n'
            message += '***********************************************************\n\n'
            message +='Wyjście w dniu: ' + data_wyjscie + ' o godzinie: ' + godz_wyjscie + '\n'
            if (godz_przyjscie) == "":
                message += 'Bez powrotu do końca zmiany\n\n'
            else:
                message += 'Powrót: ' + data_przyjscie + ' o godzinie: ' + godz_przyjscie + '\n\n'
            message += '***********************************************************\n\n'
            recepient = EMAIL_RECIVE_USER
            send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently=False)
        return redirect(pracownik_szczegoly, id_pracownika)

    context = {
        'form_przepustka': form_przepustka,
        'pracownik': pracownik,
        'rodzaj':rodzaj,
        'data_dodania': data_dodania,
    }

    return render(request, 'przepustki/wystaw_przepustke_form.html', context)
'''
def edytuj_przepustke(request, id):
    wpis = get_object_or_404(Przepustka, pk=id)
    wpisy = PrzepustkaForm(request.POST or None, request.FILES or None, instance=wpis)
    if wpisy.is_valid():
        wpisy.save()
        return redirect(przepustki_dzis)
    context = {
        'wpisy': wpisy
    }
    return render(request, 'przepustki/wystaw_przepustke_edycja_form.html', context)
'''
@login_required
def edytuj_przepustke(request, id):
    wpis = get_object_or_404(Przepustka, pk=id)

    wpisy = PrzepustkaEditForm(request.POST or None, request.FILES or None, instance=wpis)
    pracownicy = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')
    rodzaj = RodzajWpisu.objects.filter(aktywny=True).order_by('rodzaj')
    moja_Data = datetime.now()
    data_dodania = moja_Data.strftime("%Y-%m-%d")
    licz = 0

    pracownik_wpis = request.POST.get('pracownik')
    data_wyjscie = request.POST.get('data_wyjscia')
    godz_wyjscie = request.POST.get('godzina_wyjscia')
    data_przyjscie = request.POST.get('data_przyjscia')
    godz_przyjscie = request.POST.get('godzina_przyjscia')
    rodzaj_wpis = request.POST.get('rodzaj_wpisu')

    print('data_dodania:', data_dodania)
    print('data_dodania:', wpisy.instance.data_dodania)

    data_wyjscie_przed = wpis.data_wyjscia
    godz_wyjscie_przed = wpis.godzina_wyjscia
    data_przyjscie_przed = wpis.data_przyjscia
    godz_przyjscie_przed = wpis.godzina_przyjscia
    print('data_przyjscie_przed ',data_przyjscie_przed)
    print('godz_przyjscie_przed ',godz_przyjscie_przed)
    print('data_przyjscie ',data_przyjscie)
    print('godz_przyjscie ',godz_przyjscie)
    print('porownaj:',str(godz_przyjscie_przed)=="14:00:00")
    rok = wpis.data_dodania.strftime("%Y")
    print('rok ', rok)

    if data_przyjscie:
        przerobiona_data_wyjscia = przerobienie_daty(str(data_wyjscie), str(godz_wyjscie))
        przerobiona_data_przyjscia = przerobienie_daty(str(data_przyjscie), str(godz_przyjscie))
        czas_r = przerobiona_data_przyjscia - przerobiona_data_wyjscia

        print('czas_r:', czas_r)
        print('nr1 minęło dni: %s, godzin: %d, minut: %d' % (
        czas_r.days, czas_r.seconds / 3600, (czas_r.seconds % 3600) / 60))
        czas_w_minutach = czas_na_minuty(str(czas_r))
        licz = 1

    if wpisy.is_valid():
        id_pracownika = Pracownik.objects.get(id=pracownik_wpis).nr_pracownika
        if licz:
            czas = str(czas_r)
            #czas_w_minutach = 0
            wpisy.instance.czas = czas
            wpisy.instance.czas_w_minutach = czas_w_minutach
            wpisy.save()

        subject = '[' + Lokalizacja.objects.get(id=Pracownik.objects.get(id=pracownik_wpis).lokalizacja_id).lokalizacja + '] PRZEPUSTKA nr ' + str(id) + '/' + rok + ' - wystawiona w dniu: ' + data_dodania + ' - ZMIANA DANYCH!!!'
        message = '**    ' + RodzajWpisu.objects.get(id=rodzaj_wpis).rodzaj + '    ************************\n\n'
        message += 'Przepustka dla: ' + Pracownik.objects.get(id=pracownik_wpis).nazwisko + ' ' + Pracownik.objects.get(id=pracownik_wpis).imie + '\n'
        message += '***********************************************************\n\n'
        message += 'Treść przed zmianą\n'
        message += 'Wyjście w dniu: ' + str(data_wyjscie_przed) + ' o godzinie: ' + str(godz_wyjscie_przed) + '\n'
        if str(godz_przyjscie_przed) == "14:00:00" or str(godz_przyjscie_przed) == "06:00:00" or str(godz_przyjscie_przed) == "22:00:00":
            message += 'Bez powrotu do końca zmiany\n'
        else:
            message += 'Powrót: ' + str(data_przyjscie_przed) + ' o godzinie: ' + str(godz_przyjscie_przed) + '\n'
        message += '***********************************************************\n\n'
        message += 'Treść po zmianie\n'
        message += 'Wyjście w dniu: ' + data_wyjscie + ' o godzinie: ' + godz_wyjscie + '\n'
        if str(godz_przyjscie) == "14:00" or str(godz_przyjscie) == "06:00" or str(godz_przyjscie) == "22:00":
            message += 'Bez powrotu do końca zmiany\n'
        else:
            message += 'Powrót: ' + data_przyjscie + ' o godzinie: ' + godz_przyjscie + '\n'
        message += '***********************************************************\n\n'
        recepient = EMAIL_RECIVE_USER
        send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently=False)
        return redirect(pracownik_szczegoly, id_pracownika)

    context = {
        'wpisy': wpisy,
        'wpis': wpis,
        'pracownik': pracownicy,
        'rodzaj':rodzaj,
        'data_dodania': data_dodania
    }
    print('wpisy:', wpisy.instance.pracownik.imie)
    return render(request, 'przepustki/wystaw_przepustke_edycja_form.html', context)


@login_required
def usun_przepustke(request, id):
    wpis = get_object_or_404(Przepustka, pk=id)
    wpisy = SkasowacPrzepustka(request.POST or None, request.FILES or None, instance=wpis)

    data_wyjscie_przed = wpis.data_wyjscia
    godz_wyjscie_przed = wpis.godzina_wyjscia
    data_przyjscie_przed = wpis.data_przyjscia
    godz_przyjscie_przed = wpis.godzina_przyjscia

    moja_Data = datetime.now()
    data_dodania = moja_Data.strftime("%Y-%m-%d")
    rok = wpis.data_dodania.strftime("%Y")

    if wpisy.is_valid():
        id_pracownika = Pracownik.objects.get(id=Przepustka.objects.get(id=id).pracownik_id).nr_pracownika
        kasuj = wpisy.save(commit=False)
        kasuj.cofnieta = 1
        kasuj.save()

        subject = '[' + Lokalizacja.objects.get(id=Pracownik.objects.get(id=wpis.pracownik_id).lokalizacja_id).lokalizacja + '] PRZEPUSTKA nr ' + str(id) + '/' + rok + ' - WYCOFANA w dniu: ' + data_dodania
        message = '**    ' + RodzajWpisu.objects.get(id=wpis.rodzaj_wpisu_id).rodzaj + '    ************************\n\n'
        message += 'Przepustka dla: ' + Pracownik.objects.get(id=wpis.pracownik_id).nazwisko + ' ' + Pracownik.objects.get(id=wpis.pracownik_id).imie + '\n'
        message += '***********************************************************\n\n'
        message += 'Wyjście w dniu: ' + str(data_wyjscie_przed) + ' o godzinie: ' + str(godz_wyjscie_przed) + '\n'
        if str(godz_przyjscie_przed) == "14:00:00" or str(godz_przyjscie_przed) == "06:00:00" or str(godz_przyjscie_przed) == "22:00:00":
            message += 'Bez powrotu do końca zmiany\n\n'
        else:
            message += 'Powrót: ' + str(data_przyjscie_przed) + ' o godzinie: ' + str(godz_przyjscie_przed) + '\n\n'
        message += '***********************************************************\n\n'
        recepient = EMAIL_RECIVE_USER
        send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently=False)
        return redirect(pracownik_szczegoly, id_pracownika)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/potwierdz.html', context)


@login_required
def przywroc_przepustke(request, id):
    wpis = get_object_or_404(Przepustka, pk=id)
    wpisy = SkasowacPrzepustka(request.POST or None, request.FILES or None, instance=wpis)

    if wpisy.is_valid():
        id_pracownika = Pracownik.objects.get(id=Przepustka.objects.get(id=id).pracownik_id).nr_pracownika
        kasuj = wpisy.save(commit=False)
        kasuj.cofnieta = 0
        kasuj.save()
        return redirect(pracownik_szczegoly, id_pracownika)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/potwierdz.html', context)
# =============================================================================================


# == PRACOWNIK ================================================================================
@login_required
def nowy_pracownik(request):
    form_pracownik = PracownikForm(request.POST or None, request.FILES or None)
    dzial = Dzial.objects.filter(aktywny=True).order_by('dzial')
    lokalizacja = Lokalizacja.objects.filter(aktywny=True).order_by('lokalizacja')

    if form_pracownik.is_valid():
        form_pracownik.save()
        return redirect(wpisyPracownik)

    context = {
        'form_pracownik': form_pracownik,
        'dzial': dzial,
        'lokalizacja': lokalizacja,
    }

    return render(request, 'przepustki/pracownik_form.html', context)


@login_required
def edytuj_pracownik(request, id):
    wpis = get_object_or_404(Pracownik, pk=id)
    dzial = Dzial.objects.filter(aktywny=True).order_by('dzial')
    lokalizacja = Lokalizacja.objects.filter(aktywny=True).order_by('lokalizacja')
    form_pracownik = PracownikForm(request.POST or None, request.FILES or None, instance=wpis)

    if form_pracownik.is_valid():
        form_pracownik.save()
        return redirect(wpisyPracownik)

    context = {
        'form_pracownik': form_pracownik,
        'wpis': wpis,
        'dzial': dzial,
        'lokalizacja': lokalizacja,
    }

    return render(request, 'przepustki/pracownik_form_edycja.html', context)


@login_required
def usun_pracownik(request, id):
    wpis = get_object_or_404(Pracownik, pk=id)
    form_wpis = SkasowacPracownik(request.POST or None, request.FILES or None, instance=wpis)

    if form_wpis.is_valid():
        kasuj = form_wpis.save(commit=False)
        kasuj.zatrudniony = 0
        kasuj.save()
        return redirect(wpisyPracownik)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/pracownik_potwierdz.html', context)


@login_required
def przywroc_pracownik(request, id):
    wpis = get_object_or_404(Pracownik, pk=id)
    form_wpis = SkasowacPracownik(request.POST or None, request.FILES or None, instance=wpis)

    if form_wpis.is_valid():
        kasuj = form_wpis.save(commit=False)
        kasuj.zatrudniony = 1
        kasuj.save()
        return redirect(wpisyPracownik)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/pracownik_potwierdz.html', context)


def wpisyPracownik(request):
    pracownik = Pracownik.objects.all().order_by('nr_pracownika')

    context = {
        'pracownik': pracownik
    }
    return render(request,'przepustki/pracownik.html',context)
# =============================================================================================


# == DZIAL ====================================================================================
@login_required
def nowy_dzial(request):
    form_dzial = DzialForm(request.POST or None, request.FILES or None)

    if form_dzial.is_valid():
        form_dzial.save()
        return redirect(wpisyDzial)

    context = {
        'form_dzial': form_dzial,
    }

    return render(request, 'przepustki/dzial_form.html', context)


@login_required
def edytuj_dzial(request, id):
    wpis = get_object_or_404(Dzial, pk=id)
    form_dzial = DzialForm(request.POST or None, request.FILES or None, instance=wpis)

    if form_dzial.is_valid():
        form_dzial.save()
        return redirect(wpisyDzial)

    context = {
        'form_dzial': form_dzial,
        'wpis': wpis,
    }

    return render(request, 'przepustki/dzial_form_edycja.html', context)


@login_required
def usun_dzial(request, id):
    wpis = get_object_or_404(Dzial, pk=id)
    form_wpis = SkasowacPracownik(request.POST or None, request.FILES or None, instance=wpis)

    if form_wpis.is_valid():
        kasuj = form_wpis.save(commit=False)
        kasuj.aktywny = 0
        kasuj.save()
        return redirect(wpisyDzial)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/dzial_potwierdz.html', context)


@login_required
def przywroc_dzial(request, id):
    wpis = get_object_or_404(Dzial, pk=id)
    form_wpis = SkasowacPracownik(request.POST or None, request.FILES or None, instance=wpis)

    if form_wpis.is_valid():
        kasuj = form_wpis.save(commit=False)
        kasuj.aktywny = 1
        kasuj.save()
        return redirect(wpisyDzial)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/dzial_potwierdz.html', context)


def wpisyDzial(request):
    dzial = Dzial.objects.all().order_by('dzial')

    context = {
        'dzial': dzial
    }
    return render(request,'przepustki/dzial.html',context)
# =============================================================================================


# == LOGIN ====================================================================================
def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info( request, f"Witaj {username}! Właśnie się zalogowałeś.")
                return redirect("/")
            else:
                messages.error(request, f"Błędny login lub hasło")
        else:
            messages.error(request, f"- Błędny login lub hasło -")
    form = AuthenticationForm()

    context = {
        "form": form
    }
    return render(request, "przepustki/login.html", context)


def logout_request(request):
    logout(request)
    messages.info(request, "Właśnie się wylogowałeś")
    return redirect(przepustki_dzis)
# =============================================================================================


# == EKSPORT DANYCH ===========================================================================
def is_valid_queryparam(param):
    return param != '' and param is not None


@login_required
def filtrowanie(request):
    qs = Przepustka.objects.all()
    lokalizacja = Lokalizacja.objects.filter(aktywny=True).order_by('lokalizacja')
    pracownik = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')
    dzial = Dzial.objects.filter(aktywny=True).order_by('dzial')

    pracownik_contains_query = request.GET.get('pracownik_contains')
    lokalizacja_contains_query = request.GET.get('lokalizacja_contains')
    dzial_contains_query = request.GET.get('dzial_contains')
    data_od = request.GET.get('data_od')
    data_do = request.GET.get('data_do')
    eksport = request.GET.get('eksport')

    lokalizacja_contains_query2 = Lokalizacja.objects.get(id=1)
    print('pracownik_contains_query:',pracownik_contains_query)

    if is_valid_queryparam(pracownik_contains_query):
        qs = qs.filter(pracownik__exact=Pracownik.objects.get(id=int(pracownik_contains_query)))
    if is_valid_queryparam(data_od):
        qs = qs.filter(data_wyjscia__gte=data_od)
    if is_valid_queryparam(data_do):
        qs = qs.filter(data_wyjscia__lte=data_do)
    if is_valid_queryparam(lokalizacja_contains_query):
        qs = qs.filter(pracownik__lokalizacja__lokalizacja__icontains=Lokalizacja.objects.get(id=lokalizacja_contains_query))
    if is_valid_queryparam(dzial_contains_query):
        qs = qs.filter(pracownik__dzial__dzial__icontains=Dzial.objects.get(id=dzial_contains_query))

    if eksport == 'on':

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="eksport.csv"'
        response.write(u'\ufeff'.encode('utf8'))

        writer = csv.writer(response, dialect='excel', delimiter=';')
        writer.writerow(
            [
                'nr_pracownika',
                'pracownik',
                'data_wyjscia',
                'godzina_wyjscia',
                'data_przyjscia',
                'godzina_przyjscia',
                'czas',
                'rodzaj_wpisu',
                'autor_wpisu',
                'data_dodania',
                'cofnieta'
            ]
        )

        for obj in qs:
            dla_pracownika = "{} {}".format(obj.pracownik.nazwisko, obj.pracownik.imie)
            writer.writerow(
                [
                    obj.pracownik.nr_pracownika,
                    dla_pracownika,
                    obj.data_wyjscia,
                    obj.godzina_wyjscia,
                    obj.data_przyjscia,
                    obj.godzina_przyjscia,
                    obj.czas,
                    obj.rodzaj_wpisu,
                    obj.autor_wpisu,
                    obj.data_dodania,
                    obj.cofnieta
                ]
            )
        return response

    context = {
        'queryset': qs,
        'lokalizacja': lokalizacja,
        'pracownik': pracownik,
        'dzial': dzial,
    }
    return render(request, 'przepustki/eksport.html', context)


@login_required
def zestawienie(request):
    qs = Przepustka.objects.all()
    pracownik = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')

    lista_zestawienie = {}

    data_od = request.GET.get('data_od')
    data_do = request.GET.get('data_do')
    eksport = request.GET.get('eksport')
    print('data_od:', data_od)
    print('data_do:', data_do)


    if data_od == None:
        data_od = '1900-01-01'
        data_do = '1900-02-01'
    przepustki_suma = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    ilosc_przepustek = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=1).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    ilosc_odpracowan = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=2).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    ilosc_sluzbowych = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=0).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    czas_przepustki = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=1).values('pracownik__nr_pracownika').annotate(czas_licz=Sum('czas_w_minutach'))
    czas_odpracowania = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=2).values('pracownik__nr_pracownika').annotate(czas_licz=Sum('czas_w_minutach'))
    czas_sluzbowych = Przepustka.objects.filter(cofnieta=0).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=0).values('pracownik__nr_pracownika').annotate(czas_licz=Sum('czas_w_minutach'))
    #czas_licznik_2 = Przepustka.objects.filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).values('czas').annotate(Count("id")).order_by()

    #print("=================")
    #print('///////////////////////////////////////////////////')
    #print('/// PRZEPUSTKI CZAS ///////////////////////////////')
    #print('///////////////////////////////////////////////////')

    #print('czas_przepustki:',czas_przepustki)
    for tm in czas_przepustki:
        my_czas = tm['czas_licz']
        czasy = int_na_czas(my_czas)
        lista_zestawienie[tm['pracownik__nr_pracownika']] = {
            'czas_przepustki':czasy,
            'czas_odpracowania':0,
            'czas_sluzbowych':0,
            'ilosc_przepusustek':0,
            'ilosc_wyjsc_prywatnych': 0,
            'ilosc_odpracowan':0,
            'ilosc_wyjsc_sluzbowych':0
        }

        #print(tm['pracownik__nr_pracownika'],' ',Pracownik.objects.get(nr_pracownika__exact=tm['pracownik__nr_pracownika']),' ',tm['czas_licz'],' ',czasy)
        #print(Pracownik.objects.get(nr_pracownika__exact=tm['pracownik__nr_pracownika']))

    #print()
    #print('///////////////////////////////////////////////////')
    #print('/// ODPRACOWANIE CZAS /////////////////////////////')
    #print('///////////////////////////////////////////////////')
    #print('czas_odpracowania:',czas_odpracowania)
    for tm in czas_odpracowania:
        my_czas = tm['czas_licz']
        czasy = int_na_czas(my_czas)

        if tm['pracownik__nr_pracownika'] in lista_zestawienie:
            #print('JEST --->>',lista_zestawienie[tm['pracownik__nr_pracownika']]['czas_przepustki'])

            lista_zestawienie[tm['pracownik__nr_pracownika']] = {
                'czas_przepustki':lista_zestawienie[tm['pracownik__nr_pracownika']]['czas_przepustki'],
                'czas_odpracowania':czasy,
                'czas_sluzbowych':0,
                'ilosc_przepusustek':0,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan':0,
                'ilosc_wyjsc_sluzbowych':0
            }
        else:
            #print('NIE MA --->>')
            lista_zestawienie[tm['pracownik__nr_pracownika']] = {
                'czas_przepustki': 0,
                'czas_odpracowania': czasy,
                'czas_sluzbowych':0,
                'ilosc_przepusustek': 0,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': 0
            }

        #print(tm['pracownik__nr_pracownika'],' ',Pracownik.objects.get(nr_pracownika__exact=tm['pracownik__nr_pracownika']),' ',tm['czas_licz'],' ',czasy)
        #print(Pracownik.objects.get(nr_pracownika__exact=tm['pracownik__nr_pracownika']))
        #print('-----------------------------------------------')

    #print()
    #print('///////////////////////////////////////////////////')
    #print('/// SLUZBOWY CZAS /////////////////////////////')
    #print('///////////////////////////////////////////////////')
    #print('czas_odpracowania:',czas_odpracowania)
    for tm in czas_sluzbowych:
        my_czas = tm['czas_licz']
        czasy = int_na_czas(my_czas)

        if tm['pracownik__nr_pracownika'] in lista_zestawienie:
            #print('JEST --->>',lista_zestawienie[tm['pracownik__nr_pracownika']]['czas_przepustki'])

            lista_zestawienie[tm['pracownik__nr_pracownika']] = {
                'czas_przepustki':lista_zestawienie[tm['pracownik__nr_pracownika']]['czas_przepustki'],
                'czas_odpracowania':lista_zestawienie[tm['pracownik__nr_pracownika']]['czas_odpracowania'],
                'czas_sluzbowych':czasy,
                'ilosc_przepusustek':0,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan':0,
                'ilosc_wyjsc_sluzbowych':0
            }
        else:
            #print('NIE MA --->>')
            lista_zestawienie[tm['pracownik__nr_pracownika']] = {
                'czas_przepustki': 0,
                'czas_odpracowania': 0,
                'czas_sluzbowych': czasy,
                'ilosc_przepusustek': 0,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': 0
            }

        #print(tm['pracownik__nr_pracownika'],' ',Pracownik.objects.get(nr_pracownika__exact=tm['pracownik__nr_pracownika']),' ',tm['czas_licz'],' ',czasy)
        #print(Pracownik.objects.get(nr_pracownika__exact=tm['pracownik__nr_pracownika']))
        #print('-----------------------------------------------')
    #print()
    #print('///////////////////////////////////////////////////')
    #print('/// ILOSC WPISÓW //////////////////////////////////')
    #print('///////////////////////////////////////////////////')

    #print('przepustki_suma',przepustki_suma)
    for obj in przepustki_suma:
        ilosc = obj['licz']
        if obj['pracownik__nr_pracownika'] in lista_zestawienie:
            #print('JEST', ilosc)
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_przepustki'],
                'czas_odpracowania': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_odpracowania'],
                'czas_sluzbowych':lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_sluzbowych'],
                'ilosc_przepusustek': ilosc,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': 0
            }
        else:
            #print('NIE MA')
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': 0,
                'czas_odpracowania': 0,
                'czas_sluzbowych':0,
                'ilosc_przepusustek': ilosc,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': 0
            }
        #print(obj['pracownik__nr_pracownika'], ' ',Pracownik.objects.get(nr_pracownika__exact=obj['pracownik__nr_pracownika']),' ', ilosc)
        #print(Pracownik.objects.get(nr_pracownika__exact=obj['pracownik__nr_pracownika']))

    #print()
    #print('///////////////////////////////////////////////////')
    #print('/// PRZEPUSTKI ILOSC //////////////////////////////')
    #print('///////////////////////////////////////////////////')
    for obj in ilosc_przepustek:
        ilosc = obj['licz']
        if obj['pracownik__nr_pracownika'] in lista_zestawienie:
            #print('JEST', ilosc)
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_przepustki'],
                'czas_odpracowania': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_odpracowania'],
                'czas_sluzbowych': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_sluzbowych'],
                'ilosc_przepusustek': lista_zestawienie[obj['pracownik__nr_pracownika']]['ilosc_przepusustek'],
                'ilosc_wyjsc_prywatnych': ilosc,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': 0
            }
        else:
            #print('NIE MA')
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': 0,
                'czas_odpracowania': 0,
                'czas_sluzbowych':0,
                'ilosc_przepusustek': 0,
                'ilosc_wyjsc_prywatnych': ilosc,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': 0
            }
        #print(obj['pracownik__nr_pracownika'], ' ',Pracownik.objects.get(nr_pracownika__exact=obj['pracownik__nr_pracownika']),' ', ilosc)

    #print()
    #print('///////////////////////////////////////////////////')
    #print('/// ODPRACOWANIE ILOSC ////////////////////////////')
    #print('///////////////////////////////////////////////////')
    for obj in ilosc_odpracowan:
        ilosc = obj['licz']
        if obj['pracownik__nr_pracownika'] in lista_zestawienie:
            #print('JEST', ilosc)
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_przepustki'],
                'czas_odpracowania': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_odpracowania'],
                'czas_sluzbowych': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_sluzbowych'],
                'ilosc_przepusustek': lista_zestawienie[obj['pracownik__nr_pracownika']]['ilosc_przepusustek'],
                'ilosc_wyjsc_prywatnych': lista_zestawienie[obj['pracownik__nr_pracownika']]['ilosc_wyjsc_prywatnych'],
                'ilosc_odpracowan': ilosc,
                'ilosc_wyjsc_sluzbowych': 0
            }
        else:
            #print('NIE MA')
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': 0,
                'czas_odpracowania': 0,
                'czas_sluzbowych': 0,
                'ilosc_przepusustek': 0,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan': ilosc,
                'ilosc_wyjsc_sluzbowych': 0
            }
        #print(obj['pracownik__nr_pracownika'], ' ',Pracownik.objects.get(nr_pracownika__exact=obj['pracownik__nr_pracownika']),' ', ilosc)

    #print()
    #print('///////////////////////////////////////////////////')
    #print('/// SLUZBOWE ILOSC ////////////////////////////////')
    #print('///////////////////////////////////////////////////')
    for obj in ilosc_sluzbowych:
        ilosc = obj['licz']
        if obj['pracownik__nr_pracownika'] in lista_zestawienie:
            #print('JEST', ilosc)
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_przepustki'],
                'czas_odpracowania': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_odpracowania'],
                'czas_sluzbowych': lista_zestawienie[obj['pracownik__nr_pracownika']]['czas_sluzbowych'],
                'ilosc_przepusustek': lista_zestawienie[obj['pracownik__nr_pracownika']]['ilosc_przepusustek'],
                'ilosc_wyjsc_prywatnych': lista_zestawienie[obj['pracownik__nr_pracownika']]['ilosc_wyjsc_prywatnych'],
                'ilosc_odpracowan': lista_zestawienie[obj['pracownik__nr_pracownika']]['ilosc_odpracowan'],
                'ilosc_wyjsc_sluzbowych': ilosc
            }
        else:
            #print('NIE MA')
            lista_zestawienie[obj['pracownik__nr_pracownika']] = {
                'czas_przepustki': 0,
                'czas_odpracowania': 0,
                'czas_sluzbowych': 0,
                'ilosc_przepusustek': 0,
                'ilosc_wyjsc_prywatnych': 0,
                'ilosc_odpracowan': 0,
                'ilosc_wyjsc_sluzbowych': ilosc
            }
        #print(obj['pracownik__nr_pracownika'], ' ',Pracownik.objects.get(nr_pracownika__exact=obj['pracownik__nr_pracownika']),' ', ilosc)

    print()
    print('///////////////////////////////////////////////////')
    print('/// GOTOWE ZESTAWIENIE ////////////////////////////')
    print('///////////////////////////////////////////////////')

    for obj in lista_zestawienie:
        print(obj,'; ',lista_zestawienie[obj])

    #print('-----------------------------------------------')

    if eksport == 'on':

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="zestawienie.csv"'
        response.write(u'\ufeff'.encode('utf8'))

        writer = csv.writer(response, dialect='excel', delimiter=';')
        writer.writerow(
            [
                'nr_pracownika',
                'pracownik',
                'ilosc_przepusustek',
                'ilosc_wyjsc_prywatnych',
                'ilosc_odpracowan',
                'ilosc_wyjsc_sluzbowych',
                'czas_przepustki',
                'czas_odpracowania',
                'czas_sluzbowych'
            ]
        )

        for obj in lista_zestawienie:
            #dla_pracownika = "{} {}".format(obj.pracownik.nazwisko, obj.pracownik.imie)
            #print(obj,' ',Pracownik.objects.get(nr_pracownika__exact=obj),' ',lista_zestawienie[obj]['czas_przepustki'])

            writer.writerow(
                [
                    obj,
                    Pracownik.objects.get(nr_pracownika__exact=obj),
                    lista_zestawienie[obj]['ilosc_przepusustek'],
                    lista_zestawienie[obj]['ilosc_wyjsc_prywatnych'],
                    lista_zestawienie[obj]['ilosc_odpracowan'],
                    lista_zestawienie[obj]['ilosc_wyjsc_sluzbowych'],
                    lista_zestawienie[obj]['czas_przepustki'],
                    lista_zestawienie[obj]['czas_odpracowania'],
                    lista_zestawienie[obj]['czas_sluzbowych']
                ]
            )

        return response

    '''
    if is_valid_queryparam(data_od):
        qs = qs.filter(data_wyjscia__gte=data_od)
    if is_valid_queryparam(data_do):
        qs = qs.filter(data_wyjscia__lte=data_do)
    #if is_valid_queryparam(data_do):
    #    qs = qs.values('pracownik__imie').annotate(licz=Sum('autor_wpisu_id'))

    print(qs)
    if eksport == 'on':
        for obj in przepustki_suma:
            a=1
            #dla_pracownika = "{} {}".format(obj.pracownik.nazwisko, obj.pracownik.imie)
            #print(obj.pracownik_id + ' - ' + Sum)
        print('jestem')

 
    qs = Przepustka.objects.all()

    data_od = request.GET.get('data_od')
    data_do = request.GET.get('data_do')
    eksport = request.GET.get('eksport')

    if is_valid_queryparam(data_od):
        qs = qs.filter(data_dodania__gte=data_od + ' 00:00:00')
    if is_valid_queryparam(data_do):
        qs = qs.filter(data_dodania__lt=data_do + ' 23:59:59')

    if eksport == 'on':
        for obj in qs:
            print('data_wyjscia_od:', obj.pracownik.imie)
            #print('data_wyjscia_do:', obj.pracownik)
    '''

    context = {
        'queryset': qs,
    }
    return render(request, 'przepustki/zestawienie.html', context)
# =============================================================================================


# == IMPORT DANYCH ===========================================================================
def upload_file_view(request):
    form = CsvModelForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        form = CsvModelForm()
        obj = Csv.objects.get(activated = False)
        with open(obj.file_name.path, 'r',encoding='utf-8') as f:
            reader = csv.reader(f)

            for i, row in enumerate(reader):
                if i==0:
                    pass
                else:
                    row = "".join(row)
                    row = row.replace(";", " ")
                    row = row.split()
                    # - PRACOWNICY ------------------------------
                    r_dzial = Dzial.objects.get(id=row[3])
                    r_lokalizacja = Lokalizacja.objects.get(id=row[4])

                    Pracownik.objects.create(
                        nr_pracownika=int(row[0]),
                        imie=row[2],
                        nazwisko=row[1],
                        dzial_id=int(row[3]),
                        zatrudniony=1,
                        lokalizacja_id=int(row[4]),
                    )
                    #nr_pracownika = int(row[0])
                    #imie=row[2]
                    #nazwisko=row[1]
                    #dzial=row[3]
                    #zatrudniony=1
                    #lokalizacja=row[4]
                    #print('nr:',nr_pracownika,'; imie:',imie,'; nazwisko:',nazwisko,'; dzial:',dzial,'; zatru:',zatrudniony,'; lokalizacja:',lokalizacja)
                    # - KONIEC PRACOWNICY ------------------------------
                    # =================================================
                    # - KLIENCI ------------------------------
                    #r_dzial = Dzial.objects.get(id=row[3])

                    #Klient.objects.create(
                    #    nazwa_klienta = row[1],
                    #    aktywny = 1,
                    #)
                    #print(row[1])
                    # - KONIEC KLIENCI ------------------------------
                    # =================================================
                    # - WIAZKI ------------------------------
                    #r_klient = Klient.objects.get(id=row[1])

                    #Wiazka.objects.create(
                    #    nazwa_wiazki = row[0],
                    #    nazwa_klienta = r_klient,
                    #    aktywny = 1,
                    #)
                    #print(row[0], row[1], " | ", r_klient)
                    #print(row[0]," || ", row[1]," || ", row[3])
                    # - KONIEC WIAZKI ------------------------------
                    # =================================================
            obj.activated = True
            obj.save()
    context = {
        "form": form
    }
    return render(request, 'przepustki/form_upload.html', context)


def pomoc_haslo(request):
    context = {}
    return render(request, 'przepustki/pomoc_haslo.html', context)


def pomoc_o_programie(request):
    context = {}
    return render(request, 'przepustki/pomoc_o_programie.html', context)


def pomoc_przepustka(request):
    context = {}
    return render(request, 'przepustki/pomoc_przepustka.html', context)


def pomoc_pracownik(request):
    context = {}
    return render(request, 'przepustki/pomoc_pracownik.html', context)


def pracownik_szczegoly_form(request):
    form_pracownik_detal = PracownikDetal(request.POST or None, request.FILES or None)
    pracownik = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')
    pracownik_wpis = request.POST.get('pracownik')
    if pracownik_wpis == None:
        print('puste')
    else:
        id_pracownika = Pracownik.objects.get(id=pracownik_wpis).nr_pracownika
        print('wybrane:',pracownik_wpis)
        return redirect(pracownik_szczegoly, id_pracownika)


    context = {
        'pracownik': pracownik
    }

    return render(request, 'przepustki/szczegoly_form.html', context)


def pracownik_szczegoly(request, id):
    #wpis = get_object_or_404(Pracownik, pk=id)
    szczegoly = Pracownik.objects.filter(nr_pracownika__exact=id)

    data_miesiac = datetime.now().strftime("%m")
    data_rok = datetime.now().strftime("%Y")
    print('miesiac:',data_miesiac)
    print('rok:',data_rok)

    if data_miesiac > '00' and data_miesiac < '07':
        print('pierwsza połowa')
        okres = 'I półrocze'
        data_od = data_rok+'-01-01'
        data_do = data_rok+'-06-30'


    elif data_miesiac > '06' and data_miesiac < '13':
        print('druga połowa')
        okres = 'II półrocze'
        data_od = data_rok+'-07-01'
        data_do = data_rok+'-12-31'


    else:
        print('Coś poszło nie tak z datą!!!')

    przepustki_suma = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    ilosc_przepustek = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=1).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    ilosc_odpracowan = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=2).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    ilosc_sluzbowych = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=0).values('pracownik__nr_pracownika').annotate(licz=Count('czas'))
    czas_przepustki = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=1).values('pracownik__nr_pracownika').annotate(czas_licz=Sum('czas_w_minutach'))
    czas_odpracowania = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=2).values('pracownik__nr_pracownika').annotate(czas_licz=Sum('czas_w_minutach'))
    czas_sluzbowych = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(rodzaj_wpisu__czas__exact=0).values('pracownik__nr_pracownika').annotate(czas_licz=Sum('czas_w_minutach'))

    wpisy = Przepustka.objects.filter(pracownik__nr_pracownika__exact=id).filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).filter(cofnieta=False).order_by('-id')


    lista_zestawienie = {
        'przepustek':0,
        'wyjscia_prywatne':0,
        'odpracowania':0,
        'sluzbowe':0,
        'czas_przepustek':0,
        'czas_odpracowanych':0,
        'czas_sluzbowych':0
    }

    lista_zestawienie['rok'] =data_rok
    lista_zestawienie['okres'] = okres
    czas_przep = 0
    czas_odpr = 0

    for ob in szczegoly:
        lista_zestawienie['id'] = ob.nr_pracownika
        lista_zestawienie['nazwisko'] = ob.nazwisko
        lista_zestawienie['imie'] = ob.imie

    for ob in przepustki_suma:
        lista_zestawienie['przepustek'] = ob['licz']

    for ob in ilosc_przepustek:
        lista_zestawienie['wyjscia_prywatne'] = ob['licz']

    for ob in ilosc_sluzbowych:
        lista_zestawienie['sluzbowe'] = ob['licz']

    for ob in ilosc_odpracowan:
        lista_zestawienie['odpracowania'] = ob['licz']

    for ob in czas_przepustki:
        czasy = int_na_czas(ob['czas_licz'])
        czas_przep = ob['czas_licz']
        lista_zestawienie['czas_przepustek'] = czasy

    for ob in czas_odpracowania:
        czasy = int_na_czas(ob['czas_licz'])
        czas_odpr = ob['czas_licz']
        lista_zestawienie['czas_odpracowanych'] = czasy

    for ob in czas_sluzbowych:
        czasy = int_na_czas(ob['czas_licz'])
        lista_zestawienie['czas_sluzbowych'] = czasy

    if czas_przep < czas_odpr:
        czas2 = czas_odpr - czas_przep
        lista_zestawienie['prezwaga'] = 1
        lista_zestawienie['ile_prezwaga'] = int_na_czas(czas2)
    elif czas_przep > czas_odpr:
        czas2 = czas_przep - czas_odpr
        lista_zestawienie['prezwaga'] = 2
        lista_zestawienie['ile_prezwaga'] = int_na_czas(czas2)
    else:
        print('czas na 0')
        lista_zestawienie['prezwaga'] = 0
        lista_zestawienie['ile_prezwaga'] = 0

    print(
        'Id:', lista_zestawienie['id'],
        '; Imie:',lista_zestawienie['imie'],'Nazwisko:',lista_zestawienie['nazwisko'],
        '; Przepustek:',lista_zestawienie['przepustek'],
        '; Wyjsc prywatnych:',lista_zestawienie['wyjscia_prywatne'],
        '; Odpracowania:',lista_zestawienie['odpracowania'],
        '; Sluzbowe:',lista_zestawienie['sluzbowe'],
        '; Czas przepustek:',lista_zestawienie['czas_przepustek'],
        '; Czas odpracowanych:',lista_zestawienie['czas_odpracowanych'],
        '; Czas sluzbowych:',lista_zestawienie['czas_sluzbowych']
    )

    context = {
        'lista': lista_zestawienie,
        'wpisy': wpisy
    }
    return render(request, 'przepustki/szczegoly.html', context)


# -- TYMCZASOWE ROZWIĄZANIA --------------------------------------------------------------------------

@login_required
def wystaw_przepustke_temp(request):
    form_przepustka = PrzepustkaForm(request.POST or None, request.FILES or None)
    pracownik = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')
    rodzaj = RodzajWpisu.objects.filter(aktywny=True).order_by('rodzaj')
    moja_Data = datetime.now()
    data_dodania = moja_Data.strftime("%Y-%m-%d")

    liczy = 0
    zmiana_I_start = 6
    zmiana_II_start = 14
    zmiana_III_start = 22

    data_wyjscie = request.POST.get('data_wyjscia')
    godz_wyjscie = request.POST.get('godzina_wyjscia')
    data_przyjscie = request.POST.get('data_przyjscia')
    godz_przyjscie = request.POST.get('godzina_przyjscia')
    dat_dod = request.POST.get('data_dodania')
    wpis = request.POST.get('rodzaj_wpisu')
    pracownik_wpis = request.POST.get('pracownik')

    if data_wyjscie:
        przerobiona_data_wyjscia = przerobienie_daty(data_wyjscie, godz_wyjscie)


    if godz_przyjscie == "":
        godzina_wyjscia = "%s%s" % (godz_wyjscie[0], godz_wyjscie[1])
        if int(godzina_wyjscia) >= zmiana_I_start and int(godzina_wyjscia) < zmiana_II_start:
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '14:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(data_przyjscie, godzina_przyjscie)
            liczy = 1
        elif int(godzina_wyjscia) >= zmiana_II_start and int(godzina_wyjscia) < zmiana_III_start:
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '22:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(data_przyjscie, godzina_przyjscie)
            liczy = 1
        elif (int(godzina_wyjscia) >= zmiana_III_start and int(godzina_wyjscia) <= 23):
            data_przyjscie = datetime.strptime(data_wyjscie, '%Y-%m-%d').date() + timedelta(days=1)
            godzina_przyjscie = '06:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(str(data_przyjscie), godzina_przyjscie)
            liczy = 1
        elif (int(godzina_wyjscia) >= 0 and int(godzina_wyjscia) < zmiana_I_start):
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '06:00'
            print("data_przyjscie: ", data_przyjscie)
            przerobiona_data_przyjscia = przerobienie_daty(str(data_przyjscie), godzina_przyjscie)
            liczy = 1
        else:
            print("Godzina poza zakresem")
    else:
        godzina_przyjscie = godz_przyjscie
        if data_przyjscie:
            przerobiona_data_przyjscia = przerobienie_daty(data_przyjscie, godzina_przyjscie)
            liczy = 1

    if liczy:
        czas_r = przerobiona_data_przyjscia - przerobiona_data_wyjscia
        czas_w_minutach = czas_na_minuty(str(czas_r))
        print('nr1 minęło dni: %s, godzin: %d, minut: %d' % (czas_r.days, czas_r.seconds / 3600, (czas_r.seconds % 3600) / 60))


    if form_przepustka.is_valid():
        czas = str(czas_r)
        czas = '0'+czas
        autor = get_author(request.user)
        if godz_przyjscie == "":
            form_przepustka.instance.data_przyjscia = data_przyjscie
            form_przepustka.instance.godzina_przyjscia = godzina_przyjscie
        form_przepustka.instance.autor_wpisu = autor
        form_przepustka.instance.czas = czas
        form_przepustka.instance.czas_w_minutach = czas_w_minutach
        form_przepustka.instance.data_dodania = request.POST.get('data_dodania')
        form_przepustka.save()
        return redirect(przepustki_dzis_temp)

    context = {
        'form_przepustka': form_przepustka,
        'pracownik': pracownik,
        'rodzaj':rodzaj,
        'data_dodania': data_dodania,
    }

    return render(request, 'przepustki/temp_form.html', context)


@login_required
def edytuj_przepustke_temp(request, id):
    wpis = get_object_or_404(Przepustka, pk=id)

    wpisy = PrzepustkaEditForm(request.POST or None, request.FILES or None, instance=wpis)
    pracownicy = Pracownik.objects.filter(zatrudniony=True).order_by('nr_pracownika')
    rodzaj = RodzajWpisu.objects.filter(aktywny=True).order_by('rodzaj')
    moja_Data = datetime.now()
    data_dodania = moja_Data.strftime("%Y-%m-%d")
    licz = 0

    pracownik_wpis = request.POST.get('pracownik')
    data_wyjscie = request.POST.get('data_wyjscia')
    godz_wyjscie = request.POST.get('godzina_wyjscia')
    data_przyjscie = request.POST.get('data_przyjscia')
    godz_przyjscie = request.POST.get('godzina_przyjscia')
    rodzaj_wpis = request.POST.get('rodzaj_wpisu')

    data_wyjscie_przed = wpis.data_wyjscia
    godz_wyjscie_przed = wpis.godzina_wyjscia
    data_przyjscie_przed = wpis.data_przyjscia
    godz_przyjscie_przed = wpis.godzina_przyjscia
    print('data_przyjscie_przed ',data_przyjscie_przed)
    print('godz_przyjscie_przed ',godz_przyjscie_przed)
    print('data_przyjscie ',data_przyjscie)
    print('godz_przyjscie ',godz_przyjscie)
    print('porownaj:',str(godz_przyjscie_przed)=="14:00:00")
    rok = wpis.data_dodania.strftime("%Y")
    print('rok ', rok)

    if data_przyjscie:
        przerobiona_data_wyjscia = przerobienie_daty(str(data_wyjscie), str(godz_wyjscie))
        przerobiona_data_przyjscia = przerobienie_daty(str(data_przyjscie), str(godz_przyjscie))
        czas_r = przerobiona_data_przyjscia - przerobiona_data_wyjscia

        print('nr1 minęło dni: %s, godzin: %d, minut: %d' % (czas_r.days, czas_r.seconds / 3600, (czas_r.seconds % 3600) / 60))
        czas_w_minutach = czas_na_minuty(str(czas_r))
        licz = 1

    if wpisy.is_valid():
        if licz:
            czas = str(czas_r)
            wpisy.instance.czas = czas
            wpisy.instance.czas_w_minutach = czas_w_minutach
            wpisy.save()

        return redirect(przepustki_dzis_temp)

    context = {
        'wpisy': wpisy,
        'wpis': wpis,
        'pracownik': pracownicy,
        'rodzaj':rodzaj,
        'data_dodania': data_dodania
    }
    print('wpisy:', wpisy.instance.pracownik.imie)
    return render(request, 'przepustki/temp_edycja_form.html', context)


def przepustki_dzis_temp(request):

    przepustki_dzis = Przepustka.objects.filter(cofnieta=False, data_dodania=date.today()).order_by('-id')[:50]
    przepustki_wczoraj = Przepustka.objects.filter(cofnieta=False, data_dodania__lt=date.today(), data_dodania__gt=date.today()-timedelta(7)).order_by('-id')[:50]
    przepustki_przyszle = Przepustka.objects.filter(cofnieta=False, data_wyjscia__gt=date.today()).order_by('-id')[:50]
    lokalizacja = Lokalizacja.objects.filter(aktywny=True).order_by('lokalizacja')
    przepustki_suma = Przepustka.objects.all().values('pracownik__lokalizacja__lokalizacja').annotate(licz=Count('pracownik__lokalizacja__lokalizacja'))
    print(przepustki_suma)
    czas_teraz = datetime.now()
    #czas = czas_teraz.strftime("%H:%M").time()
    #czas = datetime.strptime(czas, '%H:%M').time()
    #print(czas_teraz)
    #for czasy in przepustki_dzis:
    #    if str(czasy.godzina_przyjscia) > czas_teraz:
    #        print(czasy.godzina_przyjscia)

    context = {
        'przepustki_dzis': przepustki_dzis,
        'przepustki_wczoraj': przepustki_wczoraj,
        'przepustki_przyszle': przepustki_przyszle,
        'przepustki_suma': przepustki_suma,
        'czas': czas_teraz,
    }

    return render(request, 'przepustki/temp_przepustki_dzis.html', context)

