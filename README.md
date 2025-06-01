# GROUP 8 FALL 2024 - Event Horizon

## Project Overview
Event Horizon is an astronomical viewing location platform that helps stargazers find optimal locations for celestial observations. The platform integrates real-time light pollution data, weather forecasts, moon phase information, and community reviews to provide comprehensive stargazing recommendations.

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
- Please install Django 5.1.3
- Check the current version of Django by running the command django-admin --version in the CLI of your virtual enviornment.
- This should be specified in the requirements.txt, so once you pip install -r the contents there, Django should be automatically installed.
- **GDAL is no longer required** - we've migrated to cloud-based tile services for better performance and reliability.

## How to Switch to a remote branch if it isn't showing up in your local environment:
Use the commands below:

    git branch -a                          # Get the name of the remote branch you want to switch to
    
    git fetch
    git checkout {branchname}
    
    git reset --hard origin/{branchname}   # removes staged and working directory changes

## Cloud-Based Light Pollution System
We have migrated from local GDAL processing to a modern cloud-based architecture for better performance and maintainability.

### Current Data Sources:
- **NASA VIIRS**: Real-time satellite light pollution data
- **NASA Black Marble**: Global nighttime lights visualization  
- **MapBox Geocoding**: Location-based light pollution estimation

### Managing Light Pollution Data:

1. Ensure the app is running correctly in your environment.

2. Log into the admin account with the credentials:
   - Username: group8
   - Password: A092320d@

3. Navigate to `/manage-light-pollution/` to access the data management interface.

4. Use the management interface to:
   - Refresh light pollution data cache
   - Update location data from NASA VIIRS
   - Monitor data source status

5. The map page now displays cloud-based light pollution overlays with:
   - Real-time NASA satellite data
   - Interactive dark sky visualization
   - Global coverage without local file storage

### Benefits of the New System:
- ✅ **No GDAL dependency issues**
- ✅ **Faster loading and better performance** 
- ✅ **Real-time data updates**
- ✅ **Reduced server storage requirements**
- ✅ **Cross-platform compatibility**

For detailed technical information about the migration, see `CLOUD_MIGRATION.md`.

## Core Features:
- **Interactive mapping** with light pollution overlays
- **Stargazing location discovery** and community reviews
- **Celestial event tracking** (meteor showers, eclipses, etc.)
- **Weather integration** for cloud cover forecasting
- **Moon phase and astronomical twilight calculations**
- **User favorites and location management**
- **Quality scoring** based on light pollution and elevation
