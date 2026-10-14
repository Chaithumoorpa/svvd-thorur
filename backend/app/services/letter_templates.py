"""Starting text for each kind of letter. Words in [square brackets] are
placeholders the admin replaces; a letter cannot be sent for signatures while
any are left (see LetterService.send)."""
import re

from app.models.letter import LetterKind

PLACEHOLDER = re.compile(r"\[[^\[\]\n]{1,60}\]")

# Certificates have a centred title and no "To / Subject / Dear" block.
CERTIFICATE_TITLES = {
    LetterKind.MEMBERSHIP_CERTIFICATE: "MEMBERSHIP CERTIFICATE",
    LetterKind.SERVICE_CERTIFICATE: "SERVICE CERTIFICATE",
    LetterKind.TO_WHOM_IT_MAY_CONCERN: "TO WHOM IT MAY CONCERN",
    LetterKind.NOC: "NO OBJECTION CERTIFICATE",
}

LABELS = {
    LetterKind.GENERAL: "General letter",
    LetterKind.APPOINTMENT: "Appointment letter",
    LetterKind.MEMBERSHIP_CERTIFICATE: "Membership certificate",
    LetterKind.SERVICE_CERTIFICATE: "Service certificate",
    LetterKind.TO_WHOM_IT_MAY_CONCERN: "To whom it may concern",
    LetterKind.DONATION_ACKNOWLEDGEMENT: "Donation acknowledgement",
    LetterKind.NOC: "No objection certificate",
    LetterKind.INVITATION: "Invitation",
}

TEMPLATES: dict[LetterKind, dict[str, str]] = {
    LetterKind.GENERAL: {
        "subject": "[Subject]",
        "salutation": "Dear Sir/Madam,",
        "body": "[Write the letter here.]",
        "closing": "Yours sincerely,",
    },
    LetterKind.APPOINTMENT: {
        "subject": "Appointment as [Designation]",
        "salutation": "Dear [Name],",
        "body": (
            "On behalf of the Temple Committee, we are pleased to appoint you as [Designation] of "
            "{temple}, with effect from [Date].\n\n"
            "In this role you will be responsible for [Responsibilities]. You are requested to "
            "uphold the traditions and dignity of the temple and to serve the devotees with devotion "
            "and integrity.\n\n"
            "This appointment is made by the resolution of the Committee dated [Resolution date] and "
            "remains in force until [Term end or 'further orders'].\n\n"
            "May Sri Varasidhi Vinayaka Swamy bless you in this seva."
        ),
        "closing": "Yours sincerely,",
    },
    LetterKind.MEMBERSHIP_CERTIFICATE: {
        "subject": "Membership certificate - [Name]",
        "salutation": "",
        "body": (
            "This is to certify that Sri/Smt. [Name], son/daughter/wife of [Parent or spouse name], "
            "residing at [Address], is a [Life / Annual] Member of {temple} since [Date], with "
            "membership number [Membership number].\n\n"
            "This certificate is issued at the request of the member for [Purpose]."
        ),
        "closing": "",
    },
    LetterKind.SERVICE_CERTIFICATE: {
        "subject": "Service certificate - [Name]",
        "salutation": "",
        "body": (
            "This is to certify that Sri/Smt. [Name] has served {temple} as [Designation] from "
            "[Start date] to [End date / 'date'].\n\n"
            "During this period [he/she] discharged [his/her] duties with sincerity, devotion and "
            "honesty. [His/Her] conduct and character were good.\n\n"
            "We wish [him/her] all success in future endeavours."
        ),
        "closing": "",
    },
    LetterKind.TO_WHOM_IT_MAY_CONCERN: {
        "subject": "[Subject]",
        "salutation": "",
        "body": "This is to certify that [Statement].",
        "closing": "",
    },
    LetterKind.DONATION_ACKNOWLEDGEMENT: {
        "subject": "Acknowledgement of your generous donation",
        "salutation": "Dear [Name],",
        "body": (
            "On behalf of the Temple Committee and the devotees of {temple}, we gratefully "
            "acknowledge your generous donation of [Amount or item] received on [Date] towards "
            "[Purpose].\n\n"
            "Your contribution will be used for [Use] and will help the temple continue its "
            "services to devotees.\n\n"
            "May Sri Varasidhi Vinayaka Swamy shower His blessings on you and your family."
        ),
        "closing": "With gratitude,",
    },
    LetterKind.NOC: {
        "subject": "No objection certificate - [Purpose]",
        "salutation": "",
        "body": (
            "This is to certify that {temple} has no objection to [Name / organisation] "
            "[Purpose - e.g. conducting the event / using the premises / applying for ...] on "
            "[Date / period], subject to the following conditions:\n\n"
            "1. [Condition]\n"
            "2. The sanctity and customs of the temple shall be respected at all times.\n\n"
            "This certificate is valid until [Validity date]."
        ),
        "closing": "",
    },
    LetterKind.INVITATION: {
        "subject": "Invitation to [Festival / event]",
        "salutation": "Dear [Name],",
        "body": (
            "With the blessings of Sri Varasidhi Vinayaka Swamy, {temple} is celebrating "
            "[Festival / event] on [Date] from [Time].\n\n"
            "We cordially invite you and your family to attend and receive the blessings of the "
            "Lord.\n\n"
            "Programme: [Programme details]"
        ),
        "closing": "With regards,",
    },
}


def template_for(kind: LetterKind, temple_name: str) -> dict:
    t = TEMPLATES[kind]
    return {
        "kind": kind,
        "label": LABELS[kind],
        "certificate_title": CERTIFICATE_TITLES.get(kind),
        "subject": t["subject"],
        "salutation": t["salutation"],
        "body": t["body"].replace("{temple}", temple_name),
        "closing": t["closing"],
    }
