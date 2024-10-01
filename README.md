GROUP 8 FALL 2024:

If you'd like to work in DevEDU, here are some instructions to get the project started and ready for development:

1. Navigate to DevEdu. Enter your container, make sure you click "Start" if it isn't started already.

2. Next, click "Editor" to access the VSCode environment.

3. Here are some preliminary tasks to do to get everything properly set up.
    - In the terminal, type `cd` so that way you are in your root directory...
    - Then type ```deactivate``` just in case there's other virtual environments currently running...

4. You are now ready to clone the repo. Type the command `git clone https://github.com/UCCS-CS4300-5300/Group8-fall2024.git`

5. Once you have cloned the repo, cd into the main project directory. `cd Group8-fall2024`

6. Once you are in the main project directory, create your own virtual environment. Here are the commands to do so:
    
    Create the virtual env. with the name djvenv:
    - `python3 -m venv djvenv`
    
    Activate the venv:
    - `source djvenv/bin/activate`

    Download all necessary packages for the project:
    - `pip install -r requirements.txt`

    Additional notes:
    When you need to work on a different project with a different venv, be sure to deactivate this one

7. After this, go to django_project > settings.py and edit the file. You'll need to add your allowed host.
    
    - For example, mine is:
    `ALLOWED_HOSTS = ['app-adiazpar-5.devedu.io', "app-dbolding-5.devedu.io", ...]`

8. Finally, cd into the main project file and run the command `python3 manage.py runserver 0.0.0.0:3000`

9. Go to the DevEdu container menu and click on 'App'. You should see the main page of our app.

OTHER NOTES:

If you're working on this project locally, please install and use Python 3.11.
- Check the current version of Python by running the command python3 --version in the CLI of your development environment.
 
Please install Django 4.2
- Check the current version of Django by running the command django-admin --version in the CLI of your virtual enviornment.
- This should be specified in the requirements.txt, so once you pip install -r the contents there, Django 4.2 should be automatically installed.
