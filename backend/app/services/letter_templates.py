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
    LetterKind.POWER_OF_ATTORNEY: "POWER OF ATTORNEY",
    LetterKind.RESOLUTION: "EXTRACT OF RESOLUTION",
}

# Who the second group of signatories are, as printed above them.
ATTESTOR_HEADINGS = {LetterKind.POWER_OF_ATTORNEY: "WITNESSES"}

LABELS = {
    LetterKind.GENERAL: "General letter",
    LetterKind.APPOINTMENT: "Appointment letter",
    LetterKind.MEMBERSHIP_CERTIFICATE: "Membership certificate",
    LetterKind.SERVICE_CERTIFICATE: "Service certificate",
    LetterKind.TO_WHOM_IT_MAY_CONCERN: "To whom it may concern",
    LetterKind.DONATION_ACKNOWLEDGEMENT: "Donation acknowledgement",
    LetterKind.NOC: "No objection certificate",
    LetterKind.INVITATION: "Invitation",
    LetterKind.POWER_OF_ATTORNEY: "Power of attorney (authorised signatory)",
    LetterKind.RESOLUTION: "Resolution (authorised signatory)",
    LetterKind.AUTHORISATION: "Letter of authorisation",
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
    LetterKind.POWER_OF_ATTORNEY: {
        "subject": "Power of attorney - authorised signatory for [Organisation]",
        "salutation": "",
        "body": (
            "KNOW ALL MEN BY THESE PRESENTS that {temple}, a [Trust / Society] registered under "
            "[Act] with registration number [Registration number], having its office at "
            "[Temple address] (hereinafter called \"the Trust\"), acting through its "
            "[Board of Trustees / Temple Committee] in pursuance of the resolution passed on "
            "[Resolution date], does hereby nominate, constitute and appoint Sri/Smt. [Attorney name], "
            "[Designation] of the Trust, son/daughter/wife of [Parent or spouse name], aged [Age] years, "
            "residing at [Attorney address], holding PAN [Attorney PAN] (hereinafter called "
            "\"the Attorney\"), as its true and lawful Attorney and Authorised Signatory, to do the "
            "following acts, deeds and things for and on behalf of the Trust in relation to its "
            "account with [Organisation, e.g. Razorpay Software Private Limited]:\n\n"
            "1. To apply for, open, operate and manage the Trust's account, and to accept the "
            "applicable terms and conditions on behalf of the Trust.\n"
            "2. To sign, execute and submit all applications, agreements, KYC documents, "
            "declarations, forms and correspondence required for the account.\n"
            "3. To furnish and update the Trust's bank account, business and contact details, and to "
            "receive all communications on its behalf.\n"
            "4. To raise and resolve queries, settlements, refunds and disputes relating to the account.\n"
            "5. To do all other lawful acts, deeds and things incidental to the above.\n\n"
            "The Trust hereby agrees to ratify and confirm all acts lawfully done by the Attorney "
            "under this Power of Attorney. This Power of Attorney shall remain in force until "
            "[Validity date / revoked in writing].\n\n"
            "IN WITNESS WHEREOF the Trust has executed this Power of Attorney on the date mentioned "
            "above at [Place].\n\n"
            "Specimen signature of the Attorney: ______________________ ([Attorney name])"
        ),
        "closing": "",
    },
    LetterKind.RESOLUTION: {
        "subject": "Resolution - authorised signatory for [Organisation]",
        "salutation": "",
        "body": (
            "CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE MEETING OF THE "
            "[BOARD OF TRUSTEES / TEMPLE COMMITTEE] OF {temple_upper} HELD ON [Meeting date] AT "
            "[Venue], WITH [Number] MEMBERS PRESENT.\n\n"
            "RESOLVED THAT Sri/Smt. [Name], [Designation] of the Trust, be and is hereby authorised "
            "to act as the Authorised Signatory of the Trust for [Purpose, e.g. its Razorpay account], "
            "and to sign, execute and submit all applications, agreements, KYC documents, "
            "declarations and other papers required for the same, on behalf of the Trust.\n\n"
            "RESOLVED FURTHER THAT [Organisation] be requested to act on instructions signed by the "
            "said Authorised Signatory, whose specimen signature is given below, until the Trust "
            "revokes this authority in writing.\n\n"
            "RESOLVED FURTHER THAT a copy of this resolution, certified by the President and the "
            "Secretary, be furnished to [Organisation] and to any other authority as required.\n\n"
            "Specimen signature of the Authorised Signatory: ______________________ ([Name])\n\n"
            "Certified true copy."
        ),
        "closing": "",
    },
    LetterKind.AUTHORISATION: {
        "subject": "Letter of authorisation - [Purpose]",
        "salutation": "Dear Sir/Madam,",
        "body": (
            "{temple}, a [Trust / Society] registered with registration number "
            "[Registration number], hereby authorises Sri/Smt. [Name], [Designation] of the Trust, "
            "to act as our Authorised Signatory for [Purpose, e.g. our Razorpay merchant account].\n\n"
            "Sri/Smt. [Name] is authorised to sign agreements, KYC documents, declarations and "
            "correspondence, to submit and receive documents, and to represent the Trust in all "
            "matters relating to the above. This authorisation is given in pursuance of the "
            "resolution of the [Board of Trustees / Temple Committee] dated [Resolution date].\n\n"
            "Specimen signature of the Authorised Signatory: ______________________ ([Name])\n\n"
            "Kindly take this letter on record and act on instructions given by the Authorised "
            "Signatory until this authority is revoked by us in writing."
        ),
        "closing": "Yours faithfully,",
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
        "body": t["body"].replace("{temple_upper}", temple_name.upper()).replace("{temple}", temple_name),
        "closing": t["closing"],
    }
