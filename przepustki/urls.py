from django.urls import path
from .views import przepustki_dzis,wystaw_przepustke,edytuj_przepustke, usun_przepustke, przywroc_przepustke, \
                   nowy_pracownik, edytuj_pracownik, usun_pracownik, przywroc_pracownik, wpisyPracownik, \
                   nowy_dzial, wpisyDzial, edytuj_dzial, usun_dzial, przywroc_dzial, login_request, logout_request, \
                   zestawienie, filtrowanie, upload_file_view, pomoc_haslo, pomoc_o_programie, pomoc_przepustka, pomoc_pracownik, \
                   wystaw_przepustke_temp, edytuj_przepustke_temp


urlpatterns = [
    path('', przepustki_dzis, name='przepustki_dzis'),

    #= Nowy ===============================================
    path('wystaw_przepustke_form/', wystaw_przepustke, name='wystaw_przepustke'),
    path('pracownik_form/', nowy_pracownik, name='nowy_pracownik'),
    path('dzial_form/', nowy_dzial, name='nowy_dzial'),

    #= Edycja =============================================
    path('pracownikFormEdycja/<int:id>/', edytuj_pracownik, name='pracownikFormEdycja'),
    path('dzialFormEdycja/<int:id>/', edytuj_dzial, name='dzialFormEdycja'),
    path('wystaw_przepustke_edycja_form/<int:id>/', edytuj_przepustke, name='wystaw_przepustke_edycja'),

    #= Zestawienie ========================================
    path('pracownik/', wpisyPracownik, name='pracownik'),
    path('dzial/', wpisyDzial, name='dzial'),

    #= Kasowanie ==========================================
    path('pracownikUsun/<int:id>/', usun_pracownik, name='pracownikUsun'),
    path('dzialUsun/<int:id>/', usun_dzial, name='dzialUsun'),
    path('usun_przepustke/<int:id>/', usun_przepustke, name='usun_przepustke'),

    #= Przywracanie =======================================
    path('pracownikPrzywroc/<int:id>/', przywroc_pracownik, name='pracownikPrzywroc'),
    path('dzialPrzywroc/<int:id>/', przywroc_dzial, name='dzialPrzywroc'),
    path('przywroc_przepustke/<int:id>/', przywroc_przepustke, name='przywroc_przepustke'),

    #= Pozostałe ==========================================
    path('login/', login_request, name='login'),
    path('logout/', logout_request, name='logout'),
    path('eksport/', filtrowanie, name='filtrowanie'),
    path('upload/', upload_file_view, name='upload'),
    path('zestawienie/', zestawienie, name='zestawienie'),
    path('pomoc_haslo/', pomoc_haslo, name='pomoc_haslo'),
    path('pomoc_o_programie/', pomoc_o_programie, name='pomoc_o_programie'),
    path('pomoc_przepustka/', pomoc_przepustka, name='pomoc_przepustka'),
    path('pomoc_pracownik/', pomoc_pracownik, name='pomoc_pracownik'),

    #= Tymczasowe ==========================================
    path('wystaw_temp/', wystaw_przepustke_temp, name='wystaw_temp'),
    path('edytuj_temp/', edytuj_przepustke_temp, name='edytuj_temp'),
]