### How to run

Recommended python version: `Python 3.11.4`

#### Install dependencies

At root directory, where requirements.txt locates, run:

```bash
pip install -r requirements.txt
```

### Start backend server (run before frontend)

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

If it says does not recognize python. Try using `python3 manage.py [command]` instead.

### running the scheduler.

  - This runs the technician bookings cleanup (1s intervals) for pending bookings older than 1 day.

```bash
python.exe .\manage.py scheduler
```

### Create an `admin` user
> #### creating user
>   ```bash
>   python.exe manage.py createsuperuser
>   ```
>   enter the usernam email and password as requested in cli

> #### Give admin role
> - open `http://localhost:8000/admin` in browser and log with previously craeted admin user
> - go to users
> - change role to `Admin`
> - add a phone number
> - save

How you can log with this admin account in UI

### Features


