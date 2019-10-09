# Occupations catalog using PostgreSQL

Occupations catalog provides a list of Occupations and every Occupation has its items as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items

# Tech

Occupations catalog uses a number of tools to work properly:

* [Python](https://www.python.org/) - an interpreted, high-level, general-purpose programming language.
* [PostgreSQL](https://www.postgresql.org) -  free and open-source relational database management system
* [Oracle VirtualBox](https://www.virtualbox.org/) -free and open-source hosted hypervisor for x86 virtualization.

Occupations catalog requires [Vagrant](https://www.vagrantup.com/) to run the virtual machine and [Git Bash](https://git-scm.com/downloads) to execute commands.

# Design description
* define Database connection .
* define Login method.
* define User functions.
* define Categories functions (CRUD).
* define Items functions (CRUD).
* JSON API.

# Project Overview
The Project consists of:
* Main page: contains all categories and the latest items had been created.
* Login page: contains Facebook sign in button.
* Items page: contains all the items for a specific category.
* Description page: contains the description for a specific item.

# Important Notices:
* Without "signing in" in the website the user cannot use (Create,Update,Delete) for the categories or the items. I'd created two test users (Abigail Seligsteinstein, Jennifer Chengsen) and their details located in the file: (TestUsers.txt). The database contains allready some categories and items which belongs to user (Abigail).

* If the user is not the owner of the category then he will not see the (Create,Update,Delete) buttons.

* The project has an Authorization mechanism for the users so even the (Create,Update,Delete) buttons exist in the website the Authorization will prevent the user to Create,Update or Delete if he is not the owner of the category.


# JSON Endpoints

| Endpoint | URL |
| ------ | ------ |
| All categories with their items | [/categories.JSON](https://localhost:80/categories.JSON) |
|  Show a specific item | [categories/<int:category_id>/items/<int:item_id>/JSON](https://localhost:80/categories/<int:category_id>/items/<int:item_id>/JSON) |


# Run the Server
> /catalog: contains Occupations catalog

```sh
$ cd /vagrant/catalog
$ python application.py

Now go to your web browser and visit this URL: https://localhost:80/
```




