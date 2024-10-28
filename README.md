# GROUP 8 FALL 2024:

## Project Initial Setup
If you'd like to work in DevEDU, here are some instructions to get the project started and ready for development:

1. Navigate to DevEdu. Enter your container, make sure you click "Start" if it isn't started already.

2. Next, click "Editor" to access the VSCode environment.

3. Here are some preliminary tasks to do to get everything properly set up.
    - In the terminal, type `cd` so that way you are in your root directory...

    - Then type deactivate just in case there's other virtual environments currently running...
  ```
    cd && deactivate
  ```

4. You are now ready to clone the repo. Type the command 
```
git clone https://github.com/UCCS-CS4300-5300/Group8-fall2024.git
```
7. Once you have cloned the repo, cd into the main project directory.
```
cd Group8-fall2024
```

10. Once you are in the main project directory, create your own virtual environment. Here are the commands to do so:
    
Create the virtual env. with the name djvenv:
   ```
   python3 -m venv djvenv
   ```

Activate the venv:
    
   ```
    source djvenv/bin/activate
   ```

Download all necessary packages for the project:
    
   ```
   pip install -r requirements.txt
   ```

Additional notes:
    When you need to work on a different project with a different venv, be sure to deactivate this one

11. After this, go to django_project > settings.py and edit the file. You'll need to add your allowed host.
    
    For example, mine is:
    ```
    ALLOWED_HOSTS = ['app-adiazpar-5.devedu.io', "app-dbolding-5.devedu.io", ...]
    ```

12. Finally, cd into the main project file and run the command `
```
   python3 manage.py runserver 0.0.0.0:3000
```
11. Go to the DevEdu container menu and click on 'App'. You should see the main page of our app.

###### You have now successfully setup the project on DevEDU

KEY NOTES related to this section:
- If you're working on this project locally, please install and use Python 3.11.
- Check the current version of Python by running the command python3 --version in the CLI of your development environment.
- Please install Django 4.2
- Check the current version of Django by running the command django-admin --version in the CLI of your virtual enviornment.
- This should be specified in the requirements.txt, so once you pip install -r the contents there, Django 4.2 should be automatically installed.

## How to Switch to a remote branch if it isn't showing up in your local environment:
Use the commands below:

    git fetch
    git checkout {branchname}
    
    git reset --hard origin/{branchname}   # removes staged and working directory changes

## How to Upload a Tileset for GDAL parsing:
We have decided to excluded the /media/ directory from our repository since it ends up being a fairly large folder in size after GDAL parsing.

1. Be sure the app is running correctly in your environment. If you haven't done so already, be sure to follow the steps in the previous section to correctly set up the app.

2. Be sure to start the app and make sure it is running on a working server.

3. Log into the admin account. The credentials should be...
Username: group8
Password: A092320d@

4. Navigate to the app's '/upload' extension. Once there, you should see a button to upload a .tif file. I have provided a .tif file in our project's root directory downloaded from this link:

https://earthobservatory.nasa.gov/features/NightLights/page3.php
https://www.reddit.com/r/mapbox/comments/ufgst3/how_to_create_a_dark_sky_map/

5. Take a look at the command line tool where you are running the server. You should see activity there while the .tif is being uploaded and parsed into tiles.

6. Once this process is finished, you have successfully uploaded and processed the .tif data into a tiled mesh for our map.

7. Our 'map' page should now include a dark sky layer, where light pollution activity is clearly visible on all parts of the globe.
