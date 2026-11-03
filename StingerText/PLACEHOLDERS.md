# Placeholders (clear when setup S1-S4 pass and A1 runs for real)
- fixtures/*.PLACEHOLDER.* : synthetic, built from the Brief's example payload. Finish: capture via capture_webhook.py, scrub, replace, update tests.
- Attachment download endpoint, exact payload fields, ADMIN_HANDLES format: TODO(SETUP) confirm from real capture.
- DRY_RUN=1 until setup done.
- Uncommitted stubs (C/B own): app/models.py, app/core/handler.py, app/data/*, requirements.txt (until C's lands).
- Send body CONFIRMED (S4 passed, 2 Nov): {chatGuid,tempGuid,message,method:apple-script}. Remove TODO(SETUP) markers in bluebubbles.py/send_test.py.
