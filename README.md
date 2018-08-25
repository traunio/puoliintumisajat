# Puoliintumisajat

Tässä repossa on koodi Flaskillä toteutettuun nettiappiin, jossa voi tarkistaa eri isotooppien puoliintumisaikoja.

Tämän pienen projektin tavoitteena oli tehdä nettisivu, josta voi helposti tarkistaa eri isotooppien puoliintumisajat ja hajoamistavat. Alun perin ainoana "selaustapana" oli kirjoittaa isotooppi osoitekenttään suoraan (esim. /Cs-137), mutta lopulta lisäsin myös helpon etsintä-palkin.

Haastavinta projektissa oli esittää hajoamistiedot selkeästi ja siististi. 

## Tekninen toteutus 

### Lähtötiedot 

Kaikki esitetävät tiedot perustuvat **ENDF/B-VII.0**-tiedostossa esitettyihin tietoihin. Koska kyseisen tiedoston rakenne on melko kryptinen, luettiin sieltä halutut tiedot suoraan *sqlite3*-tietokantaa helpommin käytettävään formaattiin. Tietokantaan luettiin myös suomenkielisestä Wikipediasta alkuaineiden suomenkieliset nimet. Muutamisessa käytettiin sellaista Haskelilla tehtyä purkkaviritelmää (ei sisälly tähän repoon). Sqlite3-tietokanta löytyy /static-hakemistosta. 

### Muu tavara

Nettiappi pyörii Flask-frameworkilla. Bootsrappia käytettiin nettisivujen saattamiseksi nätiksi.


