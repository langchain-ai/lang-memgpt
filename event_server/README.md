# Discord Bot Deployment Guide

This guide will walk you through deploying a Discord bot to Google Cloud Run.

## Prerequisites

1. [Google Cloud Account](https://cloud.google.com/)
2. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. [Discord Developer Account](https://discord.com/developers/applications)
4. [Docker](https://docs.docker.com/get-docker/) (for local testing)

## Step-by-Step Deployment Guide

### 1. Clone this repo

1. Clone this repository:
   ```bash
   git clone https://github.com/langchain-ai/lang-memgpt.git
   cd lang-memgpt/event_server
   ```

### 2. Set Up Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under the "Token" section, click "Copy" to copy your bot token
5. In the "General Information" tab, copy the "Public Key"
6. Create a `.env` file in your project directory and add:
   ```
   DISCORD_TOKEN=your_copied_token_here
   DISCORD_PUBLIC_KEY=your_copied_public_key_here
   ```
   Note: You can add any additional environment variables your bot might need to this file.


### 3. Set Up Google Cloud Project

1. Create a new Google Cloud project or select an existing one:

   To create a new one:
   ```bash
   # To create a new project:
   PROJECT_ID="your-project-id"
   gcloud projects create $PROJECT_ID
   ```
   _Note: Project ID must be globally unique and contain only lowercase letters, numbers, or hyphens._

   Or if you have an existing one:
   ```bash
   PROJECT_ID="your-existing-project-id"

   # Set the current project
   gcloud config set project $PROJECT_ID
   ```

   Or if you already have it configured:
   ```bash
   PROJECT_ID=$(gcloud config get-value project)
   ```

2. Enable necessary APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
   ```

3. Set up permissions for the Cloud Build service account:
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
     --role=roles/run.admin

   gcloud iam service-accounts add-iam-policy-binding \
     $PROJECT_NUMBER-compute@developer.gserviceaccount.com \
     --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
     --role=roles/iam.serviceAccountUser
   ```


### 4. Deploy to Cloud Run

1. Submit the build to Cloud Build:
   ```bash
    sh deploy_server.sh
   ```
   This reads the DISCORD_TOKEN and DISCORD_PUBLIC_KEY from your local `.env` file.

2. After deployment, get your Cloud Run URL:
   ```bash
   gcloud run services describe discord-bot --platform managed --region us-central1 --format 'value(status.url)'
   ```

### 5. Add Bot to Your Server

1. In the Discord Developer Portal, go to the "OAuth2" tab
2. In the "Scopes" section, select "bot"
3. In the "Bot Permissions" section, select the permissions your bot needs
4. Copy the generated URL and open it in a new tab
5. Select the server you want to add the bot to and click "Authorize"

## Troubleshooting

If you encounter any issues:

1. Check the Cloud Build logs:
   ```bash
   gcloud builds list --limit=1 --format='value(id)' | xargs gcloud builds log
   ```

2. Check the Cloud Run logs:
   ```bash
   gcloud run logs read discord-bot --region us-central1
   ```

If you still face issues, please open an issue in this repository with the error details.

## Contributing

If you'd like to contribute to this project, please fork the repository and create a pull request, or open an issue for discussion.

## License

[MIT License](../LICENSE)