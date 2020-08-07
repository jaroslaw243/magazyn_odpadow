# Opis
Projekt składa się z jednej aplikacji która służy do zarządzania magazynem odpadów radioaktywnych. Obsługuje takie czynności jak dodawanie nowych odpadów, pomiarów i pomiarów tła.
Przechowywane są także informacje o tym jakie osoby wykonują pomiary, oddają odpady do magazynu, odbierają odpady itp. 
Na podstawie parametrów takich jak czas przechowywania odpadu i\lub jego radioaktywność (względem tła) staje się on dostępny do wyrzucenia.  
W produkcji serwerem aplikacji jest gunicorn, reverse proxy nginx a baza danych to mySQL/mariaDB. Dane takie jak klucz do hashowania, nazwa bazy danych itp. są podawane jako zmienne środowiskowe. Całość uruchamiana jest w kontenerze dockerowym we wspólnej sieci. Do stawiania kontenerów wykorzystywany jest docker-compose.    

# Struktura

aplikacja `waste`  
projekt `waste_storage`

# Użytkowanie  
Do działania aplikacja wymaga bazy danych mySQL/mariaDB oraz wygenerowania własnego pliku `settings.py`.  
Developerski serwer można postawić za pomocą polecenia `python manage.py runserver`.  

