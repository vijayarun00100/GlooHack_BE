import email
from email import policy
from email.parser import Parser
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedEmail:
    message_id: str
    thread_id: str
    in_reply_to: Optional[str]
    sender_email: str
    sender_name: str
    subject: str
    date_str: str
    body_text: str
    body_html: str
    is_cancellation: bool = False

class EmailIngestionService:
    """
    Parses raw MIME email strings or email payloads using Python standard email library.
    Adapted from legacy email assistant architecture.
    """

    def parse_mime_email(self, raw_mime_str: str) -> ParsedEmail:
        msg = email.message_from_string(raw_mime_str, policy=policy.default)
        
        # 1. Header extraction
        message_id = str(msg.get("Message-ID", "")).strip("<>")
        in_reply_to = str(msg.get("In-Reply-To", "")).strip("<>") or None
        references = str(msg.get("References", ""))
        
        # Thread ID heuristics
        thread_id = in_reply_to or (references.split()[0].strip("<>") if references else message_id)

        # Sender details
        from_header = str(msg.get("From", ""))
        sender_email, sender_name = self._parse_address(from_header)

        subject = str(msg.get("Subject", "")).strip()
        date_str = str(msg.get("Date", "")).strip()

        # 2. Body extraction
        body_text = ""
        body_html = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    body_text += part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                elif content_type == "text/html":
                    body_html += part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
        else:
            body_text = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")

        # Cancellation intent heuristic
        lower_body = (subject + " " + body_text).lower()
        is_cancellation = any(kw in lower_body for kw in ["cancel", "ignore previous", "available after all", "please disregard", "nevermind"])

        return ParsedEmail(
            message_id=message_id,
            thread_id=thread_id,
            in_reply_to=in_reply_to,
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            date_str=date_str,
            body_text=body_text.strip(),
            body_html=body_html.strip(),
            is_cancellation=is_cancellation,
        )

    def _parse_address(self, address_str: str) -> tuple[str, str]:
        if "<" in address_str and ">" in address_str:
            name_part = address_str.split("<")[0].strip("\"' ")
            email_part = address_str.split("<")[1].split(">")[0].strip()
            return email_part, name_part or email_part.split("@")[0]
        return address_str.strip(), address_str.split("@")[0] if "@" in address_str else address_str
