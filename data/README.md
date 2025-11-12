# Files 

- [Toronto 158 neighbourhoods](https://open.toronto.ca/dataset/neighbourhoods/) as GeoJSON file
- [TTC Bus Transit Data](https://open.toronto.ca/dataset/ttc-routes-and-schedules/)
- [Neighborhood crime rates](https://open.toronto.ca/dataset/neighbourhood-crime-rates/)
- [parks & recreational locations](https://open.toronto.ca/dataset/parks-and-recreation-facilities/)
- [active building permits](https://open.toronto.ca/dataset/building-permits-active-permits/)
- [green roof building permits](https://open.toronto.ca/dataset/building-permits-green-roofs/)
- [solar hot water building permits](https://open.toronto.ca/dataset/building-permits-solar-hot-water-heaters/)
- [cleared building permits](https://open.toronto.ca/dataset/building-permits-cleared-permits/)
- [target variable based on neighborhood region](https://trreb.ca/market-data/rental-market-report/rental-market-report-archive/)


We will be using PostgreSQL
- run into your terminal wtv you need to download that matches your os

brew install postgresql
brew install postgis
brew install --cask pgadmin4

PostGIS extends the capabilities of the PostgreSQL relational database by adding support for storing, indexing, and querying geospatial data.

CREATE USER myuser WITH PASSWORD 'mypassword';
ALTER ROLE myuser WITH SUPERUSER CREATEDB CREATEROLE LOGIN;

enable PostGIS on your database;
CREATE EXTENSION postgis;


brew services start postgresql
psql postgres
CREATE DATABASE toronto_housing;
\c toronto_housing
CREATE EXTENSION postgis;

you should be able to see - postgres=# to see that you are in. 

Once you’re inside pgAdmin:
In the left sidebar, right-click “Servers” → Create → Server...
Under the General tab:
Name: Local Postgres (or any name you like)
Under the Connection tab:
Host name/address: localhost
Port: 5432
Maintenance database: postgres
Username: myuser (the one you created earlier)
Password: your password (check “Save password” if you want)
Click Save.
If it connects successfully, you’ll see your server appear in the sidebar.



TO CHANGE THE PERMISSIONS OF THE IPS THAT CAN ACCESS 
brew info postgresql
once you find the right file prob (/usr/local/Cellar/postgresql/15.4_1) 
then usually the files are under <brew_path>/var/postgres/postgresql.conf
nano it and then you can change the listen adresses











