# Optional email delivery (planned)

Email delivery is a post-build feature, not part of EPUB generation. It is not implemented yet. A successful build must leave a usable local EPUB even when email is unavailable or delivery fails.

## Proposed provider and inputs

Prefer Resend for programmatic delivery: its Send Email API supports Base64 attachments, including EPUB files. The sender must belong to a verified domain. Gmail or Outlook connectors may be an alternative for occasional personal delivery only after verifying that the connected account can attach local EPUB files and use the intended sender identity.

Ask the user for:

- recipient address, including a Kindle Personal Document address when applicable;
- a sender address on a verified domain, or a connected mail account with permission to use that sender;
- delivery policy: confirm every send, or explicitly configured automatic delivery;
- optional subject, body template, and display language.

For Kindle delivery, the sender address must be on Amazon's Approved Personal Document Email List before sending.

## Proposed command boundary

Add separate, opt-in arguments such as:

```text
--email-provider resend
--email-to reader@example.com
--email-from books@example.org
--email-subject "Lex Fridman Podcast — EPUB"
--send-email
```

Never infer a recipient or send because `--email-to` is present. Require `--send-email` as the final explicit opt-in. Validate that the EPUB exists, is readable, and fits the provider's attachment limit before sending. Never send a partial EPUB.

## Credentials, observability, and failure behavior

Use a connected service or a securely configured runtime secret. Never write API keys, OAuth tokens, recipient lists, or email bodies to the skill files, output directory, transcript cache, or version control.

After a send attempt, retain the EPUB and report only the necessary provider result (for example, a message ID or an actionable error). Do not automatically retry ambiguous failures or claim delivery from an API acceptance response. A retry must be explicitly requested or covered by the user's stated automated-delivery policy.

Official references: [Resend Send Email API](https://resend.com/docs/api-reference/emails/send-email), [Resend verified domains](https://resend.com/docs/dashboard/domains/introduction), and [Amazon Send to Kindle](https://digprjsurvey.amazon.co.uk/csad/help/node/G7NECT4B4ZWHQ8WV).
