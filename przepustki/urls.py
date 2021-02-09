from django.urls import path
from .views import przepustki_dzis,wystaw_przepustke,nowy_pracownik, edytuj_pracownik, usun_pracownik, przywroc_pracownik, wpisyPracownik, \
                    nowy_dzial, wpisyDzial, edytuj_dzial, usun_dzial, przywroc_dzial, login_request, logout_request, filtrowanie, upload_file_view


urlpatterns = [
    path('', przepustki_dzis, name='przepustki_dzis'),

    #= Nowy ===============================================
    path('wystaw_przepustke_form/', wystaw_przepustke, name='wystaw_przepustke'),
    path('pracownik_form/', nowy_pracownik, name='nowy_pracownik'),
    path('dzial_form/', nowy_dzial, name='nowy_dzial'),

    #= Edycja =============================================
    path('pracownikFormEdycja/<int:id>/', edytuj_pracownik, name='pracownikFormEdycja'),
    path('dzialFormEdycja/<int:id>/', edytuj_dzial, name='dzialFormEdycja'),

    #= Zestawienie ========================================
    path('pracownik/', wpisyPracownik, name='pracownik'),
    path('dzial/', wpisyDzial, name='dzial'),

    #= Kasowanie ==========================================
    path('pracownikUsun/<int:id>/', usun_pracownik, name='pracownikUsun'),
    path('dzialUsun/<int:id>/', usun_dzial, name='dzialUsun'),

    #= Przywracanie =======================================
    path('pracownikPrzywroc/<int:id>/', przywroc_pracownik, name='pracownikPrzywroc'),
    path('dzialPrzywroc/<int:id>/', przywroc_dzial, name='dzialPrzywroc'),

    #= Pozostałe ==========================================
    path('login/', login_request, name='login'),
    path('logout/', logout_request, name='logout'),
    path('eksport/', filtrowanie, name='filtrowanie'),
    path('upload/', upload_file_view, name='upload'),
]