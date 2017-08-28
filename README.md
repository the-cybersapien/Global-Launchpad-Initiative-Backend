# Global Launchpad Initiative Backend

This is the backend for the [Global Launchpad Initiative](https://github.com/the-dagger/Global-Launchpad-Initiative). 

## Environment Requirements
1. Python 3.6
2. PostgreSQL
3. Python packages:

```text
psycopg2>=2.7.1
psutil>=5.0.1
SQLAlchemy>=1.1.13
oauth>=1.0.1
oauth2client>=4.1.2
Flask>=0.12.2
Flask-BasicAuth>=0.2.0
Flask-Login>=0.4.0
Flask-SQLAlchemy>=2.2
httplib2>=0.9.2
html5lib=0.9
Jinja2>=2.9.6
Werkzeug>=0.12.2
requests>=2.10.0
SecretStorage>=2.3.1
simplejson>=3.10.0
```

## Setting up the environment:
1. Clone this repo
2. Create a Google Cloud Project and enable sign in auth.
3. Download and copy the client_secret.json file in the root directory
4. run the app.py file using
```
$ python3 app.py
```

### TODO:
- Add delete functionality
- Add bookmarks functionality
- Add profile edit option
- Add Auth with mobile