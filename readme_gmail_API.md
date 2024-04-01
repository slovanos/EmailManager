# Create Google Cloud Project on Google Workspace and enable API

Follow the instructions on the following links:

## Create Google Cloud Project
https://developers.google.com/workspace/guides/create-project

## Set up environment
https://developers.google.com/gmail/api/quickstart/python

**Includes the following steps**
- Enable the API
- Configure the OAuth consent screen
- Authorize credentials for a desktop application

### Credentials
Enter the cloud console
https://console.cloud.google.com/apis/credentials/consent?project=your_project_name

And on the left menu select the area and follow these steps:

- -> Credentials
  - Create credential
  - Create OAth client ID
  - Application type: Desktop app
  - Download json file to credentials.json on the project folder

- -> OAuth consent screen
  - Add yourself (your gmail account) as a test user

## Further API References
https://developers.google.com/gmail/api/reference/rest