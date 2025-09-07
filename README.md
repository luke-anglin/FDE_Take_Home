# Creative Automation Pipeline for Social Campaigns

This project is a full-stack proof-of-concept for a creative automation pipeline. It allows a user to fill out a detailed campaign brief via a web interface, which then uses Google's Gemini Pro AI to generate multiple ad creatives based on the brief. The final assets are automatically uploaded to a structured folder system in Dropbox, and a gallery is available to view all past campaigns.

This application directly addresses key business pain points such as manual content creation overload, brand inconsistency, and slow approval cycles by automating the generation of localized and personalized ad variations at scale.

## Features

- **Dynamic Briefing UI:** A user-friendly web form built with FastAPI and Bulma CSS to capture all campaign requirements.
- **Advanced AI Image Generation:** Utilizes a multimodal Gemini Pro model to interpret complex creative briefs.
- **Multi-Base Image Support:** Users can upload up to two base images (e.g., a product shot and a logo), with descriptions, which are used as direct input for the AI generation.
- **In-Prompt Creative Control:** All creative requirements—including text overlay, brand color integration, and aspect ratio—are engineered into a single, powerful prompt, delegating the creative work to the AI.
- **Guaranteed Aspect Ratios:** Employs an advanced technique of providing a blank placeholder image to ensure the model strictly adheres to the required **1:1**, **9:16**, and **16:9** aspect ratios.
- **Automated Dropbox Integration:** All generated assets are automatically uploaded to a dedicated, unique folder on Dropbox.
- **Structured File Organization:** Creates a unique parent folder for each campaign, with subfolders for each aspect ratio, ensuring assets are always organized and easy to find.
- **Campaign Gallery:** A "View All Campaigns" page that queries Dropbox to display all previously generated assets, organized by campaign.
- **Downloadable Assets:** All images in the UI, on both the generation and gallery pages, feature a one-click download button.

## Tech Stack

- **Backend:** Python, FastAPI
- **AI Model:** Google Gemini Pro (via **google-generativeai**)
- **Cloud Storage:** Dropbox API V2
- **Frontend:** HTML, CSS (Bulma), JavaScript
- **Environment Management:** **python-dotenv**

---

## Setup and Installation

Follow these steps to get the application running locally.

### 1. Prerequisites

- Python 3.9+
- A Google Cloud account with the "AI Platform" APIs enabled.
- A Dropbox account.

### 2. Clone the Repository

```bash
git clone https://github.com/luke-anglin/FDE_Take_Home
cd FDE_Take_Home
```

### 3. Setup a Virtual Environment


For MacOS/Linux:

```bash
python3 -m venv env
source env/bin/activate
```

For Windows:

```bash
python -m venv env
.\env\Scripts\activate
```

### 4. Install Dependencies

```bash 
pip install -r requirements.txt
```

### 5. Configure Environment

```bash 
cp .env_template .env
```

Now, open the .env file and fill in the required values.

You will need: 

* A Google Cloud project and API key (`GOOGLE_API_KEY`)
* A choice image model `GEMINI_IMG_MODEL`
* A Dropbox account and app: 
    * Go to the Dropbox App Console and sign in.
    * Click "Create app".
    * Select "Scoped Access".
    * Choose the type of access: "App folder".
    * Give your app a unique name (e.g., FDE-Creative-Pipeline).

    *   In your new app's console, go to the "Permissions" tab.
    * Check the following boxes to grant permissions:
        * `files.content.write`
        * `sharing.write`
    * Click "Submit" at the bottom of the page.
    * Go back to the "Settings" tab.
    * Under the "OAuth 2" section, find the "Redirect URIs" field. Add http://localhost:8000 and click the "Add" button.