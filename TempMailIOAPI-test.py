from TempMailIOAPI import TempMailIOAPI

# Random email
api = TempMailIOAPI()
result = api.generate_email()

# Custom email
api = TempMailIOAPI()
result = api.generate_custom_email("myname", "ozsaip.com")

# Or auto-select domain
result = api.generate_custom_email("myname")

# Wait for email
email = api.wait_for_email(timeout=120)
if email:
    full_email = api.get_email(email['id'])
    print(full_email['body_html'])

# Print inbox
api.print_inbox()