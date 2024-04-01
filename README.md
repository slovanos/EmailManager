# Email Manager 

**It automatically checks your emails and drafts replies, storing them in the respective folder for your review.!**

## Prerequisites
To get started, ensure you have the following:

- Gmail account
- Access to Gmail API. Follow [these instructions](./readme_gmail_API.md) to set it up. 
- OpenAI API Key. Get it from OpenAi and paste it on the .env file.
- Python V3.10 or higher installed on your system
- The python3-venv module for creating virtual environments.

## Getting Started

### Installation

1. Clone the repository or download the code:

```shell
git clone https://github.com/slovanos/emailmanager
cd emailmanager
```
2. Create and activate a virtual environment:

```shell
python3 -m venv .myvenv
source .myvenv/bin/activate
```
3. Install the required dependencies:
```shell
pip3 install -r requirements.txt
```

### Usage

1. Configure the parameters.py file with your preferences, instructions, and personal data.

2. To run Email Manager, execute the following command:

```shell
(.myvenv)$ python3 email-replier.py
```
This will fetch your emails and draft replies based on your instructions or guidelines. The responses will be pushed to your draft folder, allowing you to check, edit, and verify them before sending.

For checking emails without replying, use the following command:

```shell
(.myvenv)$ python3 email-replier.py --check
```
Logs for fetched and replied emails can be found under the logs folder.

**ENJOY!**

**Note:** The first time you launch it, you'll need to authorize the app via a browser logged into your Gmail account. This will download a token.json file to your local project folder. For subsequent uses, this file enables access without further authorization (~week). Should you encounter any authorization issues later, simply remove token.json and authorize again.

## License

[GPLv3](./LICENSE)
