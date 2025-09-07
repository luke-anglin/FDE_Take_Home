# Table of Contents

- [Creative Automation Pipeline for Social Campaigns](#creative-automation-pipeline-for-social-campaigns)
    - [Features](#features)
    - [Tech Stack](#tech-stack)
    - [Setup and Installation](#setup-and-installation)
        - [1. Prerequisites](#1-prerequisites)
        - [2. Clone the Repository](#2-clone-the-repository)
        - [3. Setup a Virtual Environment](#3-setup-a-virtual-environment)
        - [4. Install Dependencies](#4-install-dependencies)
        - [5. Configure Environment](#5-configure-environment)
    - [How to Run](#how-to-run)
    - [Project Structure](#project-structure)
    - [How the Creative Automation Pipeline Works](#how-the-creative-automation-pipeline-works)
        - [High-Level Overview](#high-level-overview)
        - [The Core Components](#the-core-components)
        - [The Journey of a Request: A Step-by-Step Flow](#the-journey-of-a-request-a-step-by-step-flow)
        - [The Campaign Gallery Flow](#the-campaign-gallery-flow)
        - [The AI-Powered Monitoring Agent](#the-ai-powered-monitoring-agent)

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
    * On the "Settings" tab, you will see your App key and App secret.
    * Copy these values into your .env file for DROPBOX_APP_KEY and DROPBOX_APP_SECRET.
    * Run `python dropbox_helper.py` and follow the steps to have your token in `.env` replaced.
    * Your browser will open to a Dropbox authorization page. Click "Allow".
    * You will be redirected to a "Site not found" page at localhost:8000. This is expected and correct.
    * Copy the code value from the URL in your browser's address bar.
    * Paste this code back into your terminal and press Enter.

Your `.env` file should now be complete.

# How to Run 

```bash
python -m uvicorn main:app --reload
```

## Project Structure 

Important files/directories listed below:

```bash
.
├── agent.py # logic for the alerts AI agent
├── alerts # generated alerts 
│   ├── <generated alerts here>
├── creative_generator.py # pipeline code for generating graphics
├── dropbox_helper.py # connects to dropbox API/manages storage 
├── frontend # Web UI
│   ├── gallery.html
│   ├── gallery.js
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── logs 
│   ├── <generated logs here>
├── main.py # fastAPI 
├── README.md

10 directories, 23 files


```

# How the Creative Automation Pipeline Works

This document provides a high-level overview of the application's architecture, data flow, and the core concepts behind its operation.

## High-Level Overview

The application is built on a modern client-server architecture. A user interacts with a web-based **Frontend**, which communicates with a **Backend** server. The backend serves as an orchestrator, taking the user's creative brief and managing a complex workflow involving a powerful external **AI Generation Service** (Google Gemini) and a **Cloud Storage Service** (Dropbox).

The core principle of this pipeline is **delegation**. Instead of performing manual steps like overlaying text or checking for brand colors in our own code, we engineer a highly specific, multimodal prompt that instructs the AI to perform all these creative tasks in a single step, resulting in a cleaner workflow and more sophisticated output.

---

## The Core Components

-   **1. The Frontend (Web UI):** Built with HTML, CSS (Bulma), and vanilla JavaScript, this is the user's entry point. Its primary responsibilities are to present a clear and intuitive form for the campaign brief, package all the user's input (text, images, descriptions), send it to the backend, and elegantly display the final generated assets or any errors.

-   **2. The Backend (FastAPI Server):** A Python server that acts as the brain of the operation. It exposes API endpoints that the frontend can call. Its responsibilities are to receive and validate user requests, manage the step-by-step generation process, handle authentication with external services, and organize the final assets for storage.

-   **3. The AI Generation Service (Creative Generator):** A specialized Python class that is responsible for all communication with the Google Gemini model. It takes the raw brief from the backend and performs the critical task of "prompt engineering"—translating the business requirements into a detailed, multimodal set of instructions that the AI can understand and execute.

-   **4. The Cloud Storage Service (Dropbox Helper):** A dedicated Python class for all interactions with the Dropbox API. It handles the complexities of OAuth 2.0 authentication (using a permanent refresh token), checks for existing folders, uploads the final image assets into a structured folder system, and generates the shareable links needed by the frontend.

---

## The Journey of a Request: A Step-by-Step Flow

This is the end-to-end journey of a user's request to generate new ad creatives, broken down into five phases.

### Phase 1: The User's Action (Frontend)

1.  **Briefing:** The user fills out the comprehensive form on the main webpage, providing all campaign details, product information, and optional base images with their required descriptions.
2.  **Submission:** The user clicks the "Generate & Upload" button.
3.  **Packaging:** The browser's JavaScript gathers all the text fields and image files into a single package (**FormData**) ready to be sent to the server.

### Phase 2: The Server's Initial Role (Backend)

4.  **API Call:** The frontend sends all the data to the backend's **/process-brief** API endpoint.
5.  **Validation:** The server receives the data and immediately checks with Dropbox to ensure the campaign name is unique. If a campaign with that name already exists, it sends an error back to the user.
6.  **Delegation:** Assuming the campaign is new, the server passes the entire brief (all text and image data) to the Creative Generator module to begin the core work.

### Phase 3: The Creative Core (AI Generation)

7.  **Prompt Engineering:** For each creative to be generated (for every product and every aspect ratio), the Creative Generator constructs a highly detailed, multimodal prompt. This is the "secret sauce" of the application, instructing the AI on exactly what to do.
8.  **AI Communication:** The generator sends a complete package to the Google Gemini API. This package includes the text prompt, any user-uploaded images, and a crucial blank placeholder image correctly sized for the desired aspect ratio.
9.  **Image Creation:** The Gemini model processes all inputs and generates a single, finished creative asset that includes the overlaid text, brand colors, and correct dimensions. It sends this image back to our server as data.

### Phase 4: Finalization and Storage (Backend)

10. **File Handling:** The backend receives the generated image data, saves it as a temporary file, and then immediately uploads it to the correct, structured folder on Dropbox (e.g., **/Summer_Campaign/9:16/**).
11. **Link Creation:** After each successful upload, the backend requests a permanent, shareable link from Dropbox for the newly uploaded file.
12. **Response:** Once all images are generated and uploaded, the backend gathers all the shareable links into a list.

### Phase 5: Displaying the Result (Frontend)

13. **Success:** The backend sends the list of image links back to the user's browser in a final success message.
14. **Display:** The JavaScript on the main page receives this list and dynamically builds the image cards, allowing the user to see and download their new creatives instantly.

---

## The Campaign Gallery Flow

The process for viewing past campaigns is simpler but follows a similar pattern:

1.  **User Navigates:** The user clicks the "View All Campaigns" button, which opens the **gallery.html** page.
2.  **Frontend Requests Data:** The gallery's JavaScript immediately sends a request to the backend's **/list-campaigns** API endpoint.
3.  **Backend Queries Dropbox:** The backend uses the **Dropbox Helper** to recursively scan the entire Dropbox app folder. It finds all files, organizes them by their parent campaign folder, and gets a shareable link for each one.
4.  **Backend Responds:** The backend sends the organized data—a JSON object where keys are campaign names and values are lists of their image assets—back to the frontend.
5.  **Frontend Renders Gallery:** The JavaScript receives the data and dynamically builds the gallery page, creating a new section for each campaign and filling it with the corresponding image cards.

---

## The AI-Powered Monitoring Agent

To provide intelligent oversight and quality control for the pipeline, the system includes a lightweight, AI-driven monitoring agent. It is designed to be database-free, using a simple and transparent file-based logging system.

### Purpose

The agent's primary role is to automatically audit the outcome of every campaign generation task. It ensures that the pipeline is performing as expected and creates clear, human-readable alerts when it detects a problem, such as a partial failure in generating creatives.

### How It Works

The agent's workflow is triggered automatically after every campaign is processed:

1.  **Audit & Log:** Immediately after a campaign's assets are uploaded, the agent runs. It creates a permanent, detailed log file for the campaign in the **`/logs`** directory. This log records the full brief, the final status (e.g., `SUCCESS` or `FLAGGED`), and the metrics (e.g., `Expected: 6, Generated: 3`).

2.  **Detect Issues:** The agent's core logic compares the number of expected assets against the number that were actually generated and uploaded.

3.  **Trigger AI Alert:** If a discrepancy is found, the agent triggers its alert mechanism.

### The Role of the Gemini AI

The agent's logic is written in Python; the **Gemini AI acts as its specialized communication tool**.

-   The Python agent detects the problem and compiles the cold, hard facts into a structured JSON object (this is the "Model Context Protocol").
-   This JSON object is then passed to the Gemini text model with a specific prompt: "You are a production assistant. Translate this data into a clear email alert."
-   The AI's sole task is to translate this structured data into a well-written, human-readable message.

This creates a powerful division of labor: **the Python agent handles the logic, and the AI handles the nuanced communication**. The final alert is saved as a `.txt` file in the **`/alerts`** directory.

### How to See it in Action

-   **On a successful run,** a new file will appear in the **`/logs`** directory with a `SUCCESS` status.
-   **To test the alerting,** submit a brief with content designed to be blocked by safety filters (e.g., a product description depicting a dangerous act). This will cause a partial failure.
-   The agent will then create a `FLAGGED` log in **`/logs`** and a new, AI-generated alert file will appear in the **`/alerts`** directory.