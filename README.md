## Museum RecSys - Web App

### Installation 
Hopefully, this guide will take you from having nothing installed to having the entire web app 
up and running...

I know that you have `conda` and `homebrew` installed, so we'll skip that step. Don't clone this repo until we've got to a certain point.

**MySQL** 

In your terminal, write the follow commands to install MySQL and start the service:
```bash
$ brew install mysql
$ brew services start mysql
```

To set the MySQL installation up properly, run the following command in your terminal window and follow the on-screen prompts:

```bash
$ mysql_secure_installation
```

I would set the password policy to `medium`, then enter a `root` (the master user) password of your choice, remove anonymous users, disable remote login, it's up to you if you want to keep the `test` database but I would reload the privilege tables.

You now have MySQL installed. We now need to setup a database and custom user for the Web App to use which is consistent on both my end and yours. Run the following commands to do so

```bash
$ mysql -u root -p
```

*Ask me via iMessage for the password! (don't want to put it on github)*

**You already have MySQL installed, so start from this point**

We should probably delete the old database created when you first went through this tutorial. To do so, follow these commands (make sure you're logged into your MySQL instance):
```bash
mysql> drop database muse_recsys_db;
mysql> drop user 'muse_recsys_user'@'localhost';
```

The above will have deleted both the original database and the user. To check it's worked, run the following (`muse_recsys_db` should have disappeared):
```bash
mysql> show databases;
```

Now we can create a new database and user for the web app to work from:

```bash
mysql> create database museum_recsys_db;
mysql> create user 'museum_db_user'@'localhost' identified with mysql_native_password by 'password';
mysql> grant all privileges on * . * to 'muse_recsys_user'@'localhost';
mysql> flush privileges;
mysql> \q
```

The commands above should have created a new database, a new user with admin privileges, and then quit out of the `mysql` console. You can check that it's worked by doing the following (the password is what I said in the iMessage):

```bash
$ mysql -u museum_db_user -p
```

If you're able to access MySQL using that user, then we're good to go (use `\q` to get out of the MySQL console).

**Clone the Repo**

Now we have successfully setup MySQL, you can clone the repository to wherever you want on your machine.

```bash
$ git clone https://github.com/JonoCX/museum_recsys.git
```

**Environment Setup**

Make sure that you're in the directory you've cloned at this point otherwise the commands won't work!

Let's delete the previous environment from your conda installation, to free up space:

```bash
$ conda remove --name museum_recsys --all
```

Now, we can create a new environment (I've used python 3.7 to get the latest Django features):

```bash
$ conda create -n museum_webapp python=3.7 -y
$ conda activate museum_webapp
(museum_webapp) $ conda install --file requirements.txt -y 
```

You should now have the environment setup and ready to go. To test that `django` is installed, you can do the following (the `get_version()` should print '3.1.1'):

```bash
(museum_webapp) $ python 
>>> import django
>>> django.get_version()
>>> exit()
```

As we're using environment variables to make sure that access is private, you'll need to create a file called `.env` in the main project directory (where the .gitignore is). Create that file and add the following two lines to it:

```
DB_USER="museum_db_user"
DB_PW="<the password from before>"
SECRET_KEY="l5il)#1h#d&_sbt+*svpu&6wkz$dz(gz93&)ew3l2u=tyjz*a-"
DEBUG=True
```

**Setting up the Database**

In this step, we'll tell Django to migrate the various models that it uses as well as the models that we've defined in the project. Whenever we make changes to the model structure (something that we should talk about before doing) we'll need to go through this step (plus an additional `makemigrations` step beforehand). Run the following:

```bash
(museum_recsys) $ python manage.py migrate
```

If you get output similar to the following, then it's worked!

```bash
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, muse_recsys, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying muse_recsys.0001_initial... OK
  Applying sessions.0001_initial... OK
 ```

**Running the Server**

Once the database has been setup, you'll be able to run the web server (it's extremely basic at the moment). Use the following command:

```bash
(museum_webapp) $ python manage.py runserver
```
then navigate in your web browser to: http://127.0.0.1:8000/ you should be greeted with a consent + demographic questionnaire.