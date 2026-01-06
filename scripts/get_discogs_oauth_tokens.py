#!/usr/bin/env python3
"""
Script to obtain Discogs OAuth 1.0a access tokens.

This is a one-time setup script. Once you have the tokens, they don't expire
(unless you revoke access), so you can store them in your .env file.

Requirements:
- DISCOGS_KEY (consumer key)
- DISCOGS_SECRET (consumer secret)

The script will guide you through the OAuth flow and output the tokens.
"""

import os
import sys
from oauthlib.oauth1 import Client as OAuthClient, SIGNATURE_TYPE_AUTH_HEADER
import requests
from urllib.parse import parse_qs

# Discogs OAuth URLs
REQUEST_TOKEN_URL = "https://api.discogs.com/oauth/request_token"
AUTHORIZE_URL = "https://www.discogs.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.discogs.com/oauth/access_token"

# User agent is required by Discogs
USER_AGENT = "MyCousinVinyl/1.0 +http://github.com/yourusername/mycousinvinyl"


def get_request_token(consumer_key: str, consumer_secret: str) -> tuple[str, str]:
    """
    Step 1: Get request token from Discogs.

    Returns:
        (oauth_token, oauth_token_secret)
    """
    print("\n[Step 1] Getting request token from Discogs...")

    oauth_client = OAuthClient(
        consumer_key,
        client_secret=consumer_secret,
        signature_type=SIGNATURE_TYPE_AUTH_HEADER,
    )

    uri, headers, body = oauth_client.sign(
        REQUEST_TOKEN_URL,
        http_method="GET",
    )

    headers["User-Agent"] = USER_AGENT

    response = requests.get(uri, headers=headers)
    response.raise_for_status()

    credentials = parse_qs(response.text)
    request_token = credentials.get('oauth_token', [None])[0]
    request_token_secret = credentials.get('oauth_token_secret', [None])[0]

    if not request_token or not request_token_secret:
        raise ValueError("Failed to get request token from Discogs")

    print(f"[OK] Request token obtained: {request_token[:20]}...")
    return request_token, request_token_secret


def authorize_app(request_token: str) -> str:
    """
    Step 2: User authorizes the app.

    Returns:
        oauth_verifier code from user
    """
    print("\n[Step 2] Authorizing application...")
    authorize_url = f"{AUTHORIZE_URL}?oauth_token={request_token}"

    print("\n" + "=" * 70)
    print("AUTHORIZATION REQUIRED")
    print("=" * 70)
    print(f"\nPlease visit this URL in your browser:\n\n{authorize_url}\n")
    print("After authorizing the application, you will see a confirmation page")
    print("with a verification code (or you'll be redirected with oauth_verifier).")
    print("=" * 70 + "\n")

    verifier = input("Enter the verification code: ").strip()

    if not verifier:
        raise ValueError("Verification code is required")

    print(f"[OK] Verification code received: {verifier[:10]}...")
    return verifier


def get_access_token(
    consumer_key: str,
    consumer_secret: str,
    request_token: str,
    request_token_secret: str,
    verifier: str
) -> tuple[str, str]:
    """
    Step 3: Exchange request token + verifier for access token.

    Returns:
        (oauth_token, oauth_token_secret)
    """
    print("\n[Step 3] Getting access token...")

    oauth_client = OAuthClient(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=request_token,
        resource_owner_secret=request_token_secret,
        verifier=verifier,
        signature_type=SIGNATURE_TYPE_AUTH_HEADER,
    )

    uri, headers, body = oauth_client.sign(
        ACCESS_TOKEN_URL,
        http_method="POST",
    )

    headers["User-Agent"] = USER_AGENT

    response = requests.post(uri, headers=headers)
    response.raise_for_status()

    credentials = parse_qs(response.text)
    access_token = credentials.get('oauth_token', [None])[0]
    access_token_secret = credentials.get('oauth_token_secret', [None])[0]

    if not access_token or not access_token_secret:
        raise ValueError("Failed to get access token from Discogs")

    print(f"[OK] Access token obtained: {access_token[:20]}...")
    return access_token, access_token_secret


def main():
    """Run the OAuth flow."""
    print("\n" + "=" * 70)
    print("DISCOGS OAUTH 1.0A TOKEN GENERATOR")
    print("=" * 70)

    # Get consumer credentials from environment or prompt
    consumer_key = os.getenv("DISCOGS_KEY")
    consumer_secret = os.getenv("DISCOGS_SECRET")

    if not consumer_key:
        consumer_key = input("\nEnter your Discogs Consumer Key: ").strip()
    else:
        print(f"\n[OK] Using consumer key from environment: {consumer_key[:20]}...")

    if not consumer_secret:
        consumer_secret = input("Enter your Discogs Consumer Secret: ").strip()
    else:
        print(f"[OK] Using consumer secret from environment: {consumer_secret[:10]}...")

    if not consumer_key or not consumer_secret:
        print("\n[ERROR] Consumer key and secret are required")
        print("\nYou can get these from: https://www.discogs.com/settings/developers")
        sys.exit(1)

    try:
        # Step 1: Get request token
        request_token, request_token_secret = get_request_token(consumer_key, consumer_secret)

        # Step 2: User authorizes the app
        verifier = authorize_app(request_token)

        # Step 3: Get access token
        access_token, access_token_secret = get_access_token(
            consumer_key,
            consumer_secret,
            request_token,
            request_token_secret,
            verifier
        )

        # Success! Display the tokens
        print("\n" + "=" * 70)
        print("SUCCESS! OAuth tokens obtained")
        print("=" * 70)
        print("\nAdd these to your .env file:\n")
        print(f"DISCOGS_OAUTH_TOKEN={access_token}")
        print(f"DISCOGS_OAUTH_TOKEN_SECRET={access_token_secret}")
        print("\nThese tokens do not expire unless you revoke access.")
        print("Keep them secure and never commit them to version control!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
