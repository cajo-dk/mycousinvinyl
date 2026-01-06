# Scripts

## Getting Discogs OAuth 1.0a Tokens

This script helps you obtain OAuth 1.0a access tokens from Discogs for use with the pricing worker.

### Prerequisites

1. **Discogs Developer Application**: Create one at https://www.discogs.com/settings/developers
   - Note your **Consumer Key** and **Consumer Secret**

2. **Python Dependencies**:
   ```bash
   pip install requests oauthlib
   ```

### Usage

1. **Run the script**:
   ```bash
   python scripts/get_discogs_oauth_tokens.py
   ```

2. **Follow the prompts**:
   - Enter your Consumer Key and Secret (or set them in .env first)
   - Visit the authorization URL in your browser
   - Authorize the application
   - Copy the verification code and paste it back into the script

3. **Update your .env file**:
   The script will output two lines to add to your `.env` file:
   ```
   DISCOGS_OAUTH_TOKEN=your_access_token_here
   DISCOGS_OAUTH_TOKEN_SECRET=your_access_token_secret_here
   ```

4. **Restart your services**:
   ```bash
   docker compose restart pricing-worker discogs-service
   ```

### Notes

- OAuth tokens **do not expire** unless you revoke access
- This is a **one-time setup** - you only need to run this script once
- Keep your tokens secure and never commit them to version control
- The tokens provide access to marketplace endpoints and user-specific data

### Switching from Personal Access Token

If you're currently using a Personal Access Token, you can switch to OAuth 1.0a by:

1. Running this script to get OAuth tokens
2. Updating your `.env` file with both `DISCOGS_OAUTH_TOKEN` and `DISCOGS_OAUTH_TOKEN_SECRET`
3. Restarting the services

The code will automatically detect OAuth credentials (token + secret) and use OAuth 1.0a authentication instead of Personal Access Token.
