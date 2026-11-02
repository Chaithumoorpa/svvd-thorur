"""The temple's HTML email layout.

Every email the site sends goes out as both plain text (for basic mail apps)
and this HTML version: the temple logo on a maroon banner, a saffron rule, a
white card on cream, and a footer with the temple's address and links. It is
built from the same plain-text body, so callers keep writing one message:

- a paragraph made only of "Label: value" lines becomes a details table;
- `code=` turns that code (an OTP, a username) into a large boxed code;
- `cta=(label, url)` turns the paragraph holding that link into a button;
- `tone="alert"` adds a red "Security notice" strip for account-security mail;
- `image="varasidhi"` shows Sri Varasidhi Vinayaka above greetings.

Table layout and inline styles only - what Gmail, Outlook and phone mail apps
all render the same way. All user text is HTML-escaped.
"""
import re
from html import escape
from typing import Literal, Optional, Tuple

from app.core.config import settings

TEMPLE_NAME = "Sri Varasidhi Vinayaka Swamy Temple"
TEMPLE_PLACE = "Thorur (V&P), Puttur (M), Tirupati (Dt) - 517583"
INVOCATION = "ఓం గం గణపతయే నమః"
NO_REPLY_TEXT = ("Please do not reply to this email - this mailbox is not monitored. For any help, use the "
                 "Contact page on our website or speak to the temple office.")

MAROON, MAROON_DARK, SAFFRON, GOLD_SOFT = "#7a1c1c", "#5a1010", "#d97a1f", "#f2d9a6"
CREAM, PAGE, RULE, INK, MUTED = "#fbf6ec", "#f3ebdc", "#e7c9a0", "#2b2b2b", "#6b6b6b"
ALERT = "#b91c1c"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

Tone = Literal["normal", "alert", "admin"]
IMAGES = {"varasidhi": ("email/varasidhi.png", "Sri Varasidhi Vinayaka Swamy", 180)}

_URL = re.compile(r"https?://[^\s<>\"]+[^\s<>\".,;:!?)\]]")
_KV = re.compile(r"^([A-Z][A-Za-z0-9 ./()&'-]{0,30}):\s+(.+)$")


def asset(path: str) -> str:
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/{path}"


def _inline(text: str) -> str:
    """Escaped text with links made clickable and line breaks kept."""
    out, last = [], 0
    for m in _URL.finditer(text):
        out.append(escape(text[last:m.start()]))
        url = m.group(0)
        out.append(f'<a href="{escape(url, quote=True)}" style="color:{MAROON};text-decoration:underline;'
                   f'word-break:break-all;">{escape(url)}</a>')
        last = m.end()
    out.append(escape(text[last:]))
    return "".join(out).replace("\n", "<br>")


def _p(html: str, style: str = "") -> str:
    return (f'<p style="margin:0 0 16px;font-family:{SANS};font-size:15px;line-height:1.6;color:{INK};{style}">'
            f"{html}</p>")


def _details(rows) -> str:
    cells = "".join(
        f'<tr><td style="padding:8px 12px;font-family:{SANS};font-size:13px;color:{MUTED};white-space:nowrap;'
        f'vertical-align:top;border-bottom:1px solid {RULE};">{escape(k)}</td>'
        f'<td style="padding:8px 12px;font-family:{SANS};font-size:14px;color:{INK};font-weight:600;'
        f'border-bottom:1px solid {RULE};">{_inline(v)}</td></tr>'
        for k, v in rows)
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 18px;'
            f'background:{CREAM};border:1px solid {RULE};border-radius:6px;border-collapse:separate;">{cells}</table>')


def _code_box(code: str) -> str:
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin:4px auto 20px;">'
            f'<tr><td style="padding:14px 26px;background:{CREAM};border:2px dashed {SAFFRON};border-radius:8px;'
            f'font-family:Consolas,Menlo,monospace;font-size:30px;font-weight:700;letter-spacing:6px;'
            f'color:{MAROON};text-align:center;">{escape(code)}</td></tr></table>')


def _button(label: str, url: str) -> str:
    href = escape(url, quote=True)
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:4px 0 10px;"><tr>'
            f'<td bgcolor="{MAROON}" style="border-radius:6px;background:{MAROON};">'
            f'<a href="{href}" style="display:inline-block;padding:12px 26px;font-family:{SANS};font-size:15px;'
            f'font-weight:700;color:#ffffff;text-decoration:none;border-radius:6px;">{escape(label)}</a>'
            f'</td></tr></table>'
            f'<p style="margin:0 0 18px;font-family:{SANS};font-size:12px;line-height:1.5;color:{MUTED};">'
            f'If the button doesn\'t work, open this link:<br>'
            f'<a href="{href}" style="color:{MAROON};word-break:break-all;">{escape(url)}</a></p>')


def _without(text: str, token: str) -> str:
    """The paragraph's text with a code / link taken out (it is shown as a block instead)."""
    return text.replace(token, "").rstrip(" :-\n")


def _body(body: str, code: Optional[str], cta: Optional[Tuple[str, str]]) -> str:
    parts = []
    for para in (p.strip("\n") for p in re.split(r"\n\s*\n", body.strip())):
        if not para.strip():
            continue
        if code and code in para:
            rest = _without(para, code)
            parts.append((_p(_inline(rest)) if rest else "") + _code_box(code))
            continue
        if cta and cta[1] in para:
            rest = _without(para, cta[1])
            parts.append((_p(_inline(rest)) if rest else "") + _button(*cta))
            continue
        lines = [l.strip() for l in para.splitlines() if l.strip()]
        pairs = [_KV.match(l) for l in lines]
        if len(lines) >= 2 and all(pairs):
            parts.append(_details([(m.group(1), m.group(2)) for m in pairs]))
        elif para.startswith(("Thank you,", "With gratitude,", "Regards,")):
            parts.append(_p(_inline(para), f"color:{MUTED};margin-top:8px;"))
        else:
            parts.append(_p(_inline(para)))
    return "".join(parts)


def render_email(subject: str, body: str, *, heading: Optional[str] = None, code: Optional[str] = None,
                 cta: Optional[Tuple[str, str]] = None, tone: Tone = "normal", image: Optional[str] = None,
                 preheader: Optional[str] = None, attachments: Optional[list] = None) -> str:
    site = settings.FRONTEND_BASE_URL.rstrip("/")
    heading = heading or subject
    preheader = preheader or re.sub(r"\s+", " ", body.strip())[:110]

    strip = ""
    if tone == "alert":
        strip = (f'<tr><td style="background:#fdecec;border-left:4px solid {ALERT};padding:10px 32px;font-family:{SANS};'
                 f'font-size:13px;font-weight:700;color:{ALERT};letter-spacing:.3px;">SECURITY NOTICE</td></tr>')
    elif tone == "admin":
        strip = (f'<tr><td style="background:{CREAM};border-left:4px solid {SAFFRON};padding:10px 32px;'
                 f'font-family:{SANS};font-size:13px;font-weight:700;color:{MAROON};letter-spacing:.3px;">'
                 f'TEMPLE ADMIN NOTIFICATION</td></tr>')

    attached = ""
    if attachments:
        names = "".join(f'<div style="font-family:{SANS};font-size:14px;color:{INK};font-weight:600;padding:2px 0;">'
                        f'&#128206; {escape(n)}</div>' for n in attachments)
        attached = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 18px;">'
                    f'<tr><td style="padding:12px 14px;background:{CREAM};border:1px dashed {RULE};border-radius:6px;">'
                    f'<div style="font-family:{SANS};font-size:12px;color:{MUTED};margin-bottom:4px;">'
                    f'ATTACHED TO THIS EMAIL</div>{names}</td></tr></table>')

    picture = ""
    if image in IMAGES:
        path, alt, width = IMAGES[image]
        picture = (f'<div style="text-align:center;margin:0 0 12px;"><img src="{asset(path)}" width="{width}" '
                   f'alt="{escape(alt)}" style="display:inline-block;width:{width}px;max-width:60%;height:auto;'
                   f'border:0;"></div>')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">
<title>{escape(subject)}</title></head>
<body style="margin:0;padding:0;background:{PAGE};-webkit-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAGE};">{escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{PAGE}" style="background:{PAGE};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#ffffff;
border-radius:10px;overflow:hidden;border:1px solid {RULE};">
<tr><td bgcolor="{MAROON}" style="background:{MAROON};background-image:linear-gradient(135deg,{MAROON},{MAROON_DARK});padding:20px 28px;">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>
<td width="68" style="vertical-align:middle;padding-right:14px;">
<a href="{site}"><img src="{asset('email/logo.png')}" width="64" height="64" alt="Temple logo"
style="display:block;width:64px;height:64px;border:0;border-radius:50%;background:#ffffff;"></a></td>
<td style="vertical-align:middle;">
<div style="font-family:{SANS};font-size:12px;color:{GOLD_SOFT};letter-spacing:.5px;">{INVOCATION}</div>
<div style="font-family:{SERIF};font-size:21px;line-height:1.25;font-weight:700;color:#ffffff;">{TEMPLE_NAME}</div>
<div style="font-family:{SANS};font-size:12px;color:{GOLD_SOFT};margin-top:2px;">{escape(TEMPLE_PLACE)}</div>
</td></tr></table></td></tr>
<tr><td style="height:4px;line-height:4px;font-size:0;background:{SAFFRON};">&nbsp;</td></tr>
{strip}
<tr><td style="padding:28px 32px 12px;">
{picture}
<h1 style="margin:0 0 18px;font-family:{SERIF};font-size:22px;line-height:1.3;color:{MAROON};font-weight:700;">{escape(heading)}</h1>
{_body(body, code, cta)}
{attached}
</td></tr>
<tr><td style="padding:0 32px 24px;"><div style="border-top:1px solid {RULE};"></div></td></tr>
<tr><td style="padding:0 32px 14px;">
<div style="padding:10px 14px;background:{CREAM};border-radius:6px;font-family:{SANS};font-size:13px;line-height:1.5;color:{MAROON};">
<strong>Please do not reply to this email</strong> - this mailbox is not monitored. For any help, use the
<a href="{site}/contact" style="color:{MAROON};">Contact page</a> or speak to the temple office.</div></td></tr>
<tr><td style="padding:0 32px 26px;font-family:{SANS};font-size:12px;line-height:1.6;color:{MUTED};">
<strong style="color:{MAROON};">{TEMPLE_NAME}</strong><br>{escape(TEMPLE_PLACE)}<br>
<a href="{site}" style="color:{MAROON};">{escape(site.split('://')[-1])}</a> &middot;
<a href="{site}/contact" style="color:{MAROON};">Contact</a> &middot;
<a href="{site}/legal/privacy-policy" style="color:{MAROON};">Privacy policy</a><br>
This is an automated message from the temple's website. The temple will never ask you for a password,
a sign-in code or payment details by email.
</td></tr>
</table>
</td></tr></table>
</body></html>"""
