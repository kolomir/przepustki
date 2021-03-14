from django.shortcuts import render, redirect, get_object_or_404
from .models import Przepustka, Pracownik, RodzajWpisu, Dzial, Lokalizacja, Autor, Csv
from django.contrib.auth.decorators import login_required
from .forms import PrzepustkaForm, SkasowacPrzepustka, PracownikForm, PrzepustkaEditForm, SkasowacPracownik, DzialForm, CsvModelForm
from datetime import datetime, date, time, timedelta
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.db.models import Count, Sum
from projekt.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

# == INNE =====================================================================================
def get_author(user):
    qs = Autor.objects.filter(user=user)
    if qs.exists():
        return qs[0]
    return None


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


    if godz_przyjscie == "":
        godzina_wyjscia = "%s%s" % (godz_wyjscie[0], godz_wyjscie[1])
        if int(godzina_wyjscia) >= zmiana_I_start and int(godzina_wyjscia) < zmiana_II_start:
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '14:00'
        elif int(godzina_wyjscia) >= zmiana_II_start and int(godzina_wyjscia) < zmiana_III_start:
            data_przyjscie = data_wyjscie
            godzina_przyjscie = '22:00'
        elif (int(godzina_wyjscia) >= zmiana_III_start and int(godzina_wyjscia) <= 23) or (
                int(godzina_wyjscia) >= 0 and int(godzina_wyjscia) < zmiana_I_start):
            data_przyjscie = datetime.strptime(data_wyjscie, '%Y-%m-%d').date() + timedelta(days=1)
            godzina_przyjscie = '06:00'
        else:
            print("Godzina poza zakresem")
    else:
        print("godzina powrotu: ", godz_przyjscie)

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
        autor = get_author(request.user)
        if godz_przyjscie == "":
            form_przepustka.instance.data_przyjscia = data_przyjscie
            form_przepustka.instance.godzina_przyjscia = godzina_przyjscie
        form_przepustka.instance.autor_wpisu = autor
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
            recepient = 'mirek.kolczynski@gmail.com'
            send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently=False)
        return redirect(przepustki_dzis)

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

    if wpisy.is_valid():
        wpisy.save()

        subject = '[' + Pracownik.objects.get(id=pracownik_wpis).lokalizacja + '] PRZEPUSTKA nr ' + str(id) + '/' + rok + ' - wystawiona w dniu: ' + data_dodania + ' - ZMIANA DANYCH!!!'
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
        recepient = 'mirek.kolczynski@gmail.com'
        send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently=False)

        return redirect(przepustki_dzis)

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

    pracownik_wpis = request.POST.get('pracownik')
    data_wyjscie_przed = wpis.data_wyjscia
    godz_wyjscie_przed = wpis.godzina_wyjscia
    data_przyjscie_przed = wpis.data_przyjscia
    godz_przyjscie_przed = wpis.godzina_przyjscia

    moja_Data = datetime.now()
    data_dodania = moja_Data.strftime("%Y-%m-%d")
    rok = wpis.data_dodania.strftime("%Y")
    print('rok ', rok)

    if wpisy.is_valid():
        kasuj = wpisy.save(commit=False)
        kasuj.cofnieta = 1
        kasuj.save()

        subject = '[' + Pracownik.objects.get(id=pracownik_wpis).lokalizacja + '] PRZEPUSTKA nr ' + str(id) + '/' + rok + ' - WYCOFANA w dniu: ' + data_dodania
        message = '**    ' + RodzajWpisu.objects.get(id=wpis).rodzaj + '    ************************\n\n'
        message += 'Przepustka dla: ' + Pracownik.objects.get(id=pracownik_wpis).nazwisko + ' ' + Pracownik.objects.get(id=pracownik_wpis).imie + '\n'
        message += '***********************************************************\n\n'
        message += 'Wyjście w dniu: ' + data_wyjscie_przed + ' o godzinie: ' + godz_wyjscie_przed + '\n'
        if str(godz_przyjscie_przed) == "14:00:00" or str(godz_przyjscie_przed) == "06:00:00" or str(godz_przyjscie_przed) == "22:00:00":
            message += 'Bez powrotu do końca zmiany\n\n'
        else:
            message += 'Powrót: ' + data_przyjscie_przed + ' o godzinie: ' + godz_przyjscie_przed + '\n\n'
        message += '***********************************************************\n\n'
        recepient = 'mirek.kolczynski@gmail.com'
        send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently=False)

        return redirect(przepustki_dzis)

    context = {
        'wpis': wpis
    }
    return render(request, 'przepustki/potwierdz.html', context)


@login_required
def przywroc_przepustke(request, id):
    wpis = get_object_or_404(Przepustka, pk=id)
    wpisy = SkasowacPrzepustka(request.POST or None, request.FILES or None, instance=wpis)

    if wpisy.is_valid():
        kasuj = wpisy.save(commit=False)
        kasuj.cofnieta = 0
        kasuj.save()
        return redirect(przepustki_dzis)

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
    print(pracownik_contains_query)

    if is_valid_queryparam(pracownik_contains_query):
        qs = qs.filter(pracownik__icontains=Pracownik.objects.get(pk=pracownik_contains_query))
    if is_valid_queryparam(data_od):
        qs = qs.filter(data_wyjscia__gte=data_od)
    if is_valid_queryparam(data_do):
        qs = qs.filter(data_wyjscia__lte=data_do)
    if is_valid_queryparam(lokalizacja_contains_query):
        qs = qs.filter(pracownik__lokalizacja__lokalizacja__icontains=Lokalizacja.objects.get(id=lokalizacja_contains_query))
    if is_valid_queryparam(dzial_contains_query):
        qs = qs.filter(pracownik__dzial__dzial__icontains=dzial_contains_query)

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
                    obj.pracownik,
                    dla_pracownika,
                    obj.data_wyjscia,
                    obj.godzina_wyjscia,
                    obj.data_przyjscia,
                    obj.godzina_przyjscia,
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
    #pracownik = Pracownik.objects.all()
    qs = Przepustka.objects.all()

    data_od = request.GET.get('data_od')
    data_do = request.GET.get('data_do')
    eksport = request.GET.get('eksport')
    print('data_od:', data_od)
    print('data_do:', data_do)

    przepustki_suma = Przepustka.objects.filter(data_wyjscia__gte=data_od).filter(data_wyjscia__lte=data_do).values('pracownik__imie').annotate(licz=Sum('autor_wpisu_id'))
    print('pracownik__imie')
    print(przepustki_suma.pracownik__imie)

    print("=================")
    #for obj in przepustki_suma:
        #print(obj.pracownik__imie['imie'])

    print(przepustki_suma)

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

    '''    
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


def pomoc(request):
    context = {}
    return render(request, 'przepustki/pomoc.html', context)