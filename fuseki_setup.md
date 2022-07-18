# Get the data
Create a folder called "fuseki" and save a version of the DNB data there. The ETH library uses "authorities-person_lds_20201013.ttl".

# Set up the Fuseki Server
This is so that you can easily query the data. (These setup instructions were originally posted here: https://gist.github.com/nichtich/113ecc2831d01eb4ae91508b88c0217c)

## Install Java

```shell
$ sudo apt-get install default-jre
```

## Download and install Fuseki with a dedicated user account

```shell
sudo adduser --disabled-password fuseki
cd /home/fuseki
sudo -u fuseki bash
wget http://mirrors.ae-online.de/apache/jena/binaries/apache-jena-fuseki-2.4.1.tar.gz
tar xzf apache-jena-fuseki-2.4.1.tar.gz
ln -s apache-jena-fuseki-2.4.1 fuseki
cd fuseki
```
Fuseki will in `/home/fuseki/fuseki`. Call `./fuseki-server` for testing.

## Setup Fuseki as service

```shell
$ sudo vim /etc/default/fuseki # edit file
$ cat /etc/default/fuseki
FUSEKI_HOME=/home/fuseki/fuseki
FUSEKI_BASE=/etc/fuseki
$ sudo mkdir /etc/fuseki
$ sudo chown fuseki /etc/fuseki
$ sudo cp /home/fuseki/fuseki/fuseki /etc/init.d/
$ sudo update-rc.d fuseki defaults
```

Restrict access to localhost only:

    $ sudo -u fuseki vim  /etc/fuseki/shiro.ini

Install nginx and configure as reverse proxy. Make sure the administration can not be accessed publically.

    $ sudo apt-get install nginx
    $ sudo vim /etc/nginx/sites-enabled/default

## Configure Fuseki

See <https://github.com/NatLibFi/Skosmos/wiki/InstallFusekiJenaText>


# (optional) Create an Index
This step is marked as "optional", as we found out that the field the ETH library indexed "variantNameForThePerson" is not a good choice. In our code, we query "preferredNameForThePerson" instead. (To not artificially boost our system's performance, we changed the query for the rule-based system as well and ran it like that.)

They used this "tutorial" to set the index up:
https://medium.com/@rrichajalota234/how-to-apache-jena-fuseki-3-x-x-1304dd810f09
in addition to this page for further information:
https://jena.apache.org/documentation/query/text-query.html#working-with-fuseki

# Putting it all together
If the setup worked, you can simply git clone https://github.com/rashitig/nla/ from the GR branch, and follow the workflow description in: https://github.com/rashitig/nla/blob/GR/configs/commandline/worflow%20description . The models are not available on github, as they are too big. But the models are only used for tagging and our project is only concerned with linking, so it should work fine for the intended purpose.

If anything is missing at all, or something does not work correctly, don't hesistate to contact me: rashitig@student.ethz.ch, I'm happy to help!
