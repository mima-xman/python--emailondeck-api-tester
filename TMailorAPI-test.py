from TMailorAPI import TMailorAPI
import json

# Example 1: Generate new email and wait for message
print("=" * 60)
print("EXAMPLE 1: Generate New Email")
print("=" * 60)

api = TMailorAPI()
result = api.generate_email(level=0)

if result:
    # Check inbox
    api.print_inbox(level=0)
    
    # Wait for email
    new_email = api.wait_for_email(timeout=30, level=0)
    if new_email:
        # Get email content
        content = api.get_email(new_email['id'], new_email['email_id'], level=0)
        if content:
            print("\n" + "=" * 60)
            print("EMAIL CONTENT")
            print("=" * 60)
            print(f"From: {content['sender_name']} <{content['sender_email']}>")
            print(f"Subject: {content['subject']}")
            print(f"Subject: {content['subject']}")
            print(f"Body:\n{content['body']}")

# Example 2: Use existing token
print("\n" + "=" * 60)
print("EXAMPLE 2: Use Existing Token")
print("=" * 60)

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlIjoicHprS1pUOGxNM3lpTEhIMXBTRVZxeFcySTN5aUZ5QXdvMU9KTXlNNkZKcVpGYXl6Rm1XR3JSMUlJM3lqWjFjMkRhTUtNMFdVRVFTWlowODJFU0VLbko5WEFLeWtIUUliR0hnUnF5eURJbUFBRnlxYkdSYmtySGZsRUp5aUZ5QXdvM01KQXlNdUVKcVpGYXl6b21BSm5SamxCSnFKcXpjMkdJRVdaejVYREt5SnEyVzJwR1dXcXlNMm5hTUFGd1Mxb3hjZW5SMVlwS0FoRnhFMkRhcUZaU2NnSHdTT0hLT2VES01kcWFTWURLeWpyR3l3R0lPSkF5Y0laR3Vqb0t0MER4Z25DRD09In0.-NpUhgMjgqpTVR0pqrP1AQ5OIGcNlCtJY-QmbppPI2Q"

# Reuse existing instance
api.access_token = token
api.print_inbox(level=0)

# Get specific email content
inbox = api.get_inbox(level=0)
if inbox and inbox['emails']:
    first_email = inbox['emails'][0]
    content = api.get_email(first_email['id'], first_email['email_id'], level=0)
    
    if content:
        print("\n" + "=" * 60)
        print("EMAIL CONTENT")
        print("=" * 60)
        print(json.dumps(content, indent=2))

api.close()