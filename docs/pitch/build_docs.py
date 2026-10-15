"""Builds the three pitch documents (SRS, TRD, Budget) as .docx. Run: python build_docs.py"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

MAROON = RGBColor(0x7B, 0x1A, 0x1A)
TITLE = "Temple Platform"
SUB = "Based on the Sri Varasidhi Vinayaka Swamy Devasthanam, Thorur reference implementation"


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:fill"), hexcolor)
    tcPr.append(s)


class Doc:
    def __init__(self, title, subtitle, version="1.0 (Draft)"):
        self.d = Document()
        sec = self.d.sections[0]
        sec.left_margin = sec.right_margin = Cm(2.2)
        st = self.d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
        for n in ("Heading 1", "Heading 2", "Heading 3"):
            h = self.d.styles[n]; h.font.name = "Georgia"; h.font.color.rgb = MAROON
        p = self.d.add_paragraph(); p.paragraph_format.space_before = Pt(120)
        r = p.add_run(TITLE); r.font.size = Pt(16); r.font.color.rgb = RGBColor(0xC8, 0x7A, 0x1E); r.bold = True
        p = self.d.add_paragraph(); r = p.add_run(title); r.font.size = Pt(30); r.bold = True; r.font.color.rgb = MAROON; r.font.name = "Georgia"
        p = self.d.add_paragraph(); r = p.add_run(subtitle); r.font.size = Pt(13)
        p = self.d.add_paragraph(); r = p.add_run(SUB); r.italic = True
        self.table([["Document version", version], ["Date", "15 October 2026"],
                    ["Prepared by", "Chaithanya M — Vriksha Studio"], ["Status", "For client presentation"]],
                   widths=[4, 10], header=False)
        self.d.add_page_break()

    def h(self, text, lvl=1): self.d.add_heading(text, lvl)

    def p(self, text, bold=False, italic=False):
        para = self.d.add_paragraph(); r = para.add_run(text); r.bold = bold; r.italic = italic
        return para

    def ul(self, items):
        for i in items: self.d.add_paragraph(i, style="List Bullet")

    def table(self, rows, widths=None, header=True):
        t = self.d.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                c = t.cell(i, j); c.text = ""
                run = c.paragraphs[0].add_run(str(v)); run.font.size = Pt(9.5)
                if header and i == 0:
                    run.bold = True; run.font.color.rgb = RGBColor(255, 255, 255); shade(c, "7B1A1A")
                elif not header and j == 0:
                    run.bold = True; shade(c, "F5EFE6")
                if widths: c.width = Cm(widths[j])
        self.d.add_paragraph()

    def save(self, name): self.d.save(name); print("wrote", name)


# ============================== SRS ==============================
def srs():
    D = Doc("Software Requirements Specification", "Temple website & management platform")
    D.h("1. Introduction")
    D.h("1.1 Purpose", 2)
    D.p("This document specifies the functional and non-functional requirements of a reusable temple website and "
        "management platform. It is derived from the working system built for Sri Varasidhi Vinayaka Swamy "
        "Devasthanam, Thorur (Andhra Pradesh), and is intended as the baseline for delivering the same platform "
        "to future temples.")
    D.h("1.2 Scope", 2)
    D.p("The platform has two parts: (a) a public, multilingual website for devotees, and (b) a secure admin panel "
        "for temple staff and trustees. It covers temple information, darshan timings, poojas/sevas, festivals, "
        "announcements, gallery, online seva booking, donation records, finance ledger, member directory and audit trail.")
    D.h("1.3 Definitions", 2)
    D.table([["Term", "Meaning"],
             ["Seva / Pooja", "A ritual offering a devotee can book or sponsor"],
             ["Darshan", "Public viewing hours of the deity"],
             ["Trustee", "Temple committee member with read-only oversight"],
             ["OTP", "One-time password sent by email"],
             ["RBAC", "Role-based access control"],
             ["DPDPA", "India's Digital Personal Data Protection Act, 2023"]], widths=[4, 12])
    D.h("1.4 Stakeholders and users", 2)
    D.table([["Role", "Description", "Access"],
             ["Visitor / Devotee", "Anyone browsing; may register to track bookings", "Public site; My Bookings"],
             ["Staff", "Temple office / counter staff", "Content, messages, seva tickets, scanning"],
             ["Trustee", "Committee oversight", "Read-only dashboards, donors, finance"],
             ["Admin", "Temple administrator", "All content, donors, finance, members"],
             ["Super Admin", "Technical/chief administrator", "Everything incl. user management & audit log"]],
            widths=[3.5, 7, 5.5])

    D.h("2. Overall description")
    D.h("2.1 Product perspective", 2)
    D.p("A web application (Next.js frontend + FastAPI backend + PostgreSQL) delivered per temple as an isolated "
        "deployment with its own domain, database and branding. No dependency between temples' data.")
    D.h("2.2 Assumptions and constraints", 2)
    D.ul(["Most devotees use mobile phones on average networks; the site must be mobile-first and lightweight.",
          "Temple staff have limited technical skill; the admin panel must be self-explanatory.",
          "Languages needed vary per temple; the reference build supports English, Telugu, Tamil, Kannada and Hindi.",
          "Online payment gateway is NOT in the reference build (paid sevas are booked online and paid at the counter). "
          "It is offered as an optional add-on.",
          "Personal data is handled per DPDPA; a privacy policy is shown on the site, in emails and on tickets."])

    D.h("3. Functional requirements")
    D.h("3.1 Public website", 2)
    D.table([["ID", "Requirement", "Priority"],
             ["FR-PUB-01", "Home page with deity carousel, darshan timing strip and latest announcements", "Must"],
             ["FR-PUB-02", "Darshan timings page; timings editable by staff without developer help", "Must"],
             ["FR-PUB-03", "Poojas & Sevas listing filtered by Daily / Special / Festival sevas", "Must"],
             ["FR-PUB-04", "Festivals calendar incl. Sankashti Chaturthi dates; auto-generated festival announcements", "Should"],
             ["FR-PUB-05", "Announcements feed", "Must"],
             ["FR-PUB-06", "Photo gallery and media page", "Should"],
             ["FR-PUB-07", "About / history, committee (publicly shown members) and information pages", "Must"],
             ["FR-PUB-08", "Contact form with auto-reply; spam/bot protection", "Must"],
             ["FR-PUB-09", "Donation information page and historical donor records archive", "Should"],
             ["FR-PUB-10", "Legal pages: privacy policy, terms, refund policy; help desk and feedback", "Must"],
             ["FR-PUB-11", "Language switcher; all public text translatable per locale", "Must"],
             ["FR-PUB-12", "SEO: per-locale canonical/hreflang, sitemap.xml, robots.txt, JSON-LD", "Must"],
             ["FR-PUB-13", "Installable look: favicon, home-screen icons, web manifest", "Could"]], widths=[2.4, 11.2, 2.4])
    D.h("3.2 Seva booking and devotee accounts", 2)
    D.table([["ID", "Requirement", "Priority"],
             ["FR-BK-01", "Guest booking of a seva, verified by email OTP (no account needed)", "Must"],
             ["FR-BK-02", "Booking confirmation by email with ticket; QR code on ticket", "Must"],
             ["FR-BK-03", "Free sevas auto-confirm; paid sevas can be booked online and paid at counter (status PENDING)", "Must"],
             ["FR-BK-04", "Devotee self-registration, login, password reset by emailed link", "Should"],
             ["FR-BK-05", "'My Bookings' lists a signed-in devotee's tickets", "Should"],
             ["FR-BK-06", "Self-service account deletion; existing tickets unlinked, not orphaned", "Should"],
             ["FR-BK-07", "Optional occasion tag (birthday, anniversary) triggers a blessing email once paid", "Could"],
             ["FR-BK-08", "Devotees emailed when darshan timings change or an announcement is posted", "Could"]], widths=[2.4, 11.2, 2.4])
    D.h("3.3 Admin panel", 2)
    D.table([["ID", "Requirement", "Priority"],
             ["FR-AD-01", "Dashboard with key statistics", "Must"],
             ["FR-AD-02", "CRUD for announcements, festivals, poojas/sevas, gallery, timings, temple profile", "Must"],
             ["FR-AD-03", "Contact-message inbox with status workflow (Open → Resolved/Closed) and reply", "Must"],
             ["FR-AD-04", "Seva tickets: counter sales, QR scan check-in; scan refuses tickets with payment pending; collect payment at scan", "Must"],
             ["FR-AD-05", "Donor and donation records; PDF receipt generation; receipt-issued records locked from edit/delete", "Must"],
             ["FR-AD-06", "Finance ledger auto-posted from paid tickets and donations; manual entries by Admin only; reports", "Should"],
             ["FR-AD-07", "Member/committee directory with photo upload and public-visibility flag", "Should"],
             ["FR-AD-08", "User management (create, role-assign, deactivate, delete) by Super Admin; forced password change on first login", "Must"],
             ["FR-AD-09", "Append-only audit log of every mutating action", "Must"],
             ["FR-AD-10", "Email alerts to admins for new bookings, donations, contact messages", "Could"]], widths=[2.4, 11.2, 2.4])
    D.h("3.4 Security-related functions", 2)
    D.table([["ID", "Requirement", "Priority"],
             ["FR-SEC-01", "Role-based permissions enforced server-side on every endpoint", "Must"],
             ["FR-SEC-02", "Email-OTP two-factor login for accounts with an email on file", "Should"],
             ["FR-SEC-03", "30-minute idle session timeout with activity-based silent refresh", "Must"],
             ["FR-SEC-04", "Rate limiting on public endpoints; bot challenge on forms", "Must"],
             ["FR-SEC-05", "Alert Super Admins on bursts of repeated deletions by one actor", "Could"]], widths=[2.4, 11.2, 2.4])
    D.h("3.5 Future / optional modules (not in reference build)", 2)
    D.ul(["Online payment gateway for sevas and donations (UPI / cards) with reconciliation.",
          "WhatsApp / SMS notifications.",
          "Live darshan / video streaming embed.",
          "Annadanam and accommodation booking.",
          "Native mobile app."])

    D.h("4. Non-functional requirements")
    D.table([["ID", "Category", "Requirement"],
             ["NFR-01", "Performance", "Public pages server-rendered; target Largest Contentful Paint < 2.5 s on 4G; content cached"],
             ["NFR-02", "Availability", "Target 99.5% monthly (single-server deployment); daily DB backups"],
             ["NFR-03", "Scalability", "Sized for ~1–2k devotees/day; vertical scale or move DB to managed service beyond that"],
             ["NFR-04", "Security", "HTTPS everywhere (Let's Encrypt), hashed passwords, JWT sessions, parameterised queries, secrets via env/IAM role"],
             ["NFR-05", "Privacy", "DPDPA-aligned: privacy policy, consent-aware emails, personal data not written to audit log"],
             ["NFR-06", "Usability", "Mobile-first responsive layout; admin panel usable after ≤ 2 hours of training"],
             ["NFR-07", "Accessibility", "Semantic HTML, sufficient contrast, keyboard navigable forms (target WCAG 2.1 AA)"],
             ["NFR-08", "Localisation", "Unicode, Indic fonts, per-locale URLs; additional languages added by JSON translation file"],
             ["NFR-09", "Maintainability", "Automated tests gate every deploy; versioned DB migrations; documented architecture"],
             ["NFR-10", "Portability", "Fully containerised; deployable to any Docker host (AWS, Railway, VPS)"]], widths=[2, 3, 11])

    D.h("5. External interfaces")
    D.table([["Interface", "Purpose"],
             ["AWS SES", "Transactional email (OTP, confirmations, resets, alerts)"],
             ["AWS S3", "Gallery, member photos, ticket/receipt PDFs"],
             ["Cloudflare Turnstile", "Bot protection on public forms"],
             ["Browser", "Chrome, Edge, Safari, Firefox — last 2 major versions; Android & iOS"],
             ["Payment gateway (optional)", "Razorpay / PayU etc., if the add-on is purchased"]], widths=[5, 11])

    D.h("6. Acceptance criteria")
    D.ul(["All 'Must' requirements for the purchased package demonstrated on the client's staging site.",
          "Automated backend and frontend test suites pass; typecheck and lint clean.",
          "Admin staff complete: add announcement, change timings, sell a counter ticket, scan a ticket, issue a receipt.",
          "Site served over HTTPS on the client's domain; backup restore tested once.",
          "Training session held and handover document delivered."])
    D.h("7. Requirements by package")
    D.table([["Area", "Essential", "Standard", "Complete"],
             ["Public site (FR-PUB)", "Yes (2 languages)", "Yes (5 languages)", "Yes (5 languages)"],
             ["Admin CMS (FR-AD-01/02/03/08)", "Yes", "Yes", "Yes"],
             ["Seva booking & devotee accounts", "—", "Yes", "Yes"],
             ["Donors, receipts (FR-AD-05)", "—", "Yes", "Yes"],
             ["Finance, members, audit, 2FA, QR scan", "—", "—", "Yes"],
             ["Online payment gateway", "—", "Add-on", "Add-on"]], widths=[6, 3.4, 3.3, 3.3])
    D.save("SRS_Temple_Platform.docx")


# ============================== TRD ==============================
def trd():
    D = Doc("Technical Requirements Document", "Architecture, stack, infrastructure and delivery")
    D.h("1. Purpose")
    D.p("Defines how the platform specified in the SRS is built, deployed, secured and operated. Everything marked "
        "'as built' is taken from the running reference implementation.")
    D.h("2. Technology stack (as built)")
    D.table([["Layer", "Technology", "Notes"],
             ["Frontend", "Next.js 15.5 (App Router), React 19, TypeScript", "Server-rendered public site; client admin panel"],
             ["Styling", "Tailwind CSS 3", "Maroon/saffron theme, Georgia serif headings"],
             ["i18n", "next-intl 4", "en, te, ta, kn, hi — one JSON per locale"],
             ["Backend", "FastAPI (Python 3.11), Pydantic", "~52 REST endpoints under /api/v1; auto docs at /docs"],
             ["ORM / migrations", "SQLAlchemy + Alembic", "21 versioned migrations; startup migration validator"],
             ["Database", "PostgreSQL", "Numeric types for money; query indexes"],
             ["Storage", "AWS S3", "Presigned direct-from-browser uploads"],
             ["Email", "AWS SES", "Best-effort; failure never blocks the action"],
             ["Bot protection", "Cloudflare Turnstile", "Public forms"],
             ["Containers", "Docker + Docker Compose", "postgres, backend, frontend, nginx"],
             ["Reverse proxy / TLS", "Nginx + Let's Encrypt (Certbot)", "Auto-renewing certificates"],
             ["CI/CD", "GitHub Actions", "Tests gate deploy; dependency-audit workflow"],
             ["Testing", "pytest (backend), Vitest + tsc + ESLint (frontend)", "~40 backend test modules"]], widths=[3.2, 6.3, 6.5])

    D.h("3. Architecture")
    D.p("Browser → Nginx (TLS) → Next.js frontend (SSR) → FastAPI backend → PostgreSQL. The frontend proxies "
        "/api/v1 to the backend; the browser never reaches the database. Files go browser → S3 via presigned URLs. "
        "Email goes backend → SES. One daily cron job runs the festival-announcement generator; there is no task queue.")
    D.h("3.1 Backend layering", 2)
    D.ul(["Routers (thin): validate request, call one service, write audit entry, shape response.",
          "Services: business rules (e.g. a PENDING ticket cannot be scanned; issued receipts are immutable).",
          "Repositories: data access per aggregate.",
          "Models / Schemas: SQLAlchemy tables and Pydantic validation (mobile format, money bounds, safe URLs).",
          "Core: config (dev vs prod guards), RBAC table, DB session, middleware, rate limiter."])
    D.h("3.2 Multi-temple strategy", 2)
    D.p("Recommended: one isolated deployment per temple (own domain, DB, S3 bucket, SES identity, branding). "
        "Chosen over a shared multi-tenant system because it gives each temple full data isolation, independent "
        "release timing, and zero blast radius — at a hosting cost of roughly ₹1,000/month per temple. "
        "Branding (name, logo, deity carousel, colours, translations) is configuration plus content, not code forks; "
        "feature differences are controlled by package.")
    D.p("Work required once to productise: move hard-coded temple strings/colours to a per-temple config, and "
        "script new-temple provisioning (see Budget, 'Platform productisation').", italic=True)

    D.h("4. Data model (summary)")
    D.table([["Entity", "Purpose"],
             ["User", "Login identity; roles list; optional email/phone"],
             ["Member", "Committee member shown publicly; optionally linked to a User"],
             ["Temple, TempleTiming", "Profile and darshan schedule"],
             ["Pooja, Festival, Announcement, Gallery", "Public content"],
             ["SevaTicket", "Booking; payment_status FREE / PENDING / PAID; QR token; booked_by_user_id"],
             ["Donor, Donation", "Contributions; receipt PDF key"],
             ["FinanceEntry", "Ledger; auto-posted from tickets/donations"],
             ["ContactMessage", "Inbox with status workflow"],
             ["EmailOtp, PasswordReset", "Booking verification, login 2FA, reset tokens"],
             ["AuditLog", "Append-only; actor survives user deletion"],
             ["Visitor", "Aggregate visit counts"]], widths=[5.5, 10.5])

    D.h("5. Security design")
    D.table([["Control", "Implementation"],
             ["Authorisation", "RBAC permission table; require_permission() on every route; Finance write narrower than content write"],
             ["Authentication", "JWT, 30-min expiry with activity refresh; email-OTP 2FA; forced change of initial password"],
             ["Transport", "HTTPS only (Let's Encrypt); HSTS at Nginx"],
             ["Abuse", "Rate limit 120 req/min default, spoof-resistant client IP; Turnstile on forms"],
             ["Data", "Passwords hashed; secrets via env / EC2 IAM role (no AWS keys in app); PII excluded from audit values"],
             ["Production guards", "Config refuses unsafe settings in production; migration validator at startup"],
             ["Supply chain", "Dependency-audit workflow; lockfiles; pinned core versions"],
             ["Compliance", "DPDPA-aligned privacy policy linked from emails and printed on tickets"]], widths=[3.5, 12.5])

    D.h("6. Infrastructure requirements")
    D.table([["Item", "Minimum (≤ 2k users)", "Recommended (growth)"],
             ["Compute", "AWS EC2 t4g.micro/t3.micro (1 vCPU, 1 GB) + swap", "t4g.small (2 GB)"],
             ["Storage", "20–30 GB gp3", "50 GB + snapshots"],
             ["Database", "Postgres in Docker on same host", "Managed RDS if > 5k users or HA required"],
             ["Object store", "S3 bucket, public-read gallery prefix, private tickets", "+ CloudFront CDN"],
             ["Backups", "Daily pg_dump to S3, 14-day retention", "EBS snapshots + PITR (RDS)"],
             ["DNS / domain", "Client-owned .org/.in domain", "—"],
             ["Monitoring", "Uptime check + container logs", "CloudWatch alarms"]], widths=[3, 6.5, 6.5])

    D.h("7. Delivery and operations")
    D.h("7.1 Environments", 2)
    D.p("development → staging (per temple, for client review) → production. Branch model: feature branches merge "
        "to `development`; production deploys from the production branch via GitHub Actions after tests pass.")
    D.h("7.2 Per-temple onboarding checklist", 2)
    D.ul(["Collect: temple name, deities, logo, history text, timings, poojas/sevas list with fees, festival list, committee, gallery photos.",
          "Provision AWS (EC2, S3, IAM role, SES identity) and DNS; run setup script; issue TLS certificate.",
          "Apply branding/config; load content; translate to required languages (client or paid translation).",
          "Create Super Admin and staff accounts; force password change.",
          "UAT on staging; training; go-live; 30-day hypercare."])
    D.h("7.3 Testing", 2)
    D.ul(["Backend: pytest suites per feature (auth, RBAC, booking OTP, receipts, finance, 2FA, privacy, query counts).",
          "Frontend: typecheck, ESLint (zero warnings), Vitest.",
          "CI gate: deploy blocked on any failure. Manual UAT checklist per temple."])
    D.h("7.4 Support model", 2)
    D.table([["Level", "Scope", "Response"],
             ["Critical", "Site down / data loss / security", "4 business hours"],
             ["High", "Booking or admin function broken", "1 business day"],
             ["Normal", "Content help, small changes", "3 business days"]], widths=[3, 8, 5])
    D.h("8. Known gaps and risks")
    D.table([["Item", "Impact", "Mitigation"],
             ["No payment gateway", "Paid sevas settled at counter", "Optional add-on; PENDING flow already built"],
             ["Single-server deployment", "Downtime during host failure", "Daily backups; documented rebuild; upgrade to RDS/HA if required"],
             ["Admin panel English-only", "Harder for non-English staff", "Add admin i18n as optional work"],
             ["Frontend/back types synced by hand", "Drift risk", "Generate TS types from OpenAPI (planned)"],
             ["Temple-specific strings in code", "Slows new-temple setup", "Productisation phase (see Budget)"],
             ["Content readiness", "Empty site at launch (timings, poojas)", "Content collection checklist; client sign-off before go-live"]], widths=[4.5, 5, 6.5])
    D.save("TRD_Temple_Platform.docx")


# ============================== BUDGET ==============================
def inr(n): return f"₹{n:,.0f}"


def budget():
    D = Doc("Budget Proposal", "Cost estimate for future temple websites")
    D.h("1. Summary")
    D.p("Three packages, all built from one proven platform. Prices are estimates in Indian Rupees (INR), exclusive of "
        "GST (18%), and based on the assumptions in section 6. They are a starting point for discussion, not a final quotation.")
    pk = {"Essential": (55000, 4, "Information website"),
          "Standard": (140000, 8, "Website + seva booking + donations"),
          "Complete": (260000, 12, "Full temple management")}
    D.table([["", "Essential", "Standard", "Complete"],
             ["Best for", "Small temple needing an online presence", "Temple taking seva bookings & recording donations", "Temple needing full accounts & governance"],
             ["Languages", "2", "5", "5"],
             ["Public website", "Yes", "Yes", "Yes"],
             ["Admin CMS & user roles", "Yes", "Yes", "Yes"],
             ["Seva booking, devotee accounts", "—", "Yes", "Yes"],
             ["Donors, receipts (PDF)", "—", "Yes", "Yes"],
             ["Finance, members, audit, 2FA, QR scan", "—", "—", "Yes"],
             ["One-time build fee", inr(pk["Essential"][0]), inr(pk["Standard"][0]), inr(pk["Complete"][0])],
             ["Timeline", "3–4 weeks", "6–8 weeks", "10–12 weeks"]], widths=[4.6, 3.8, 3.8, 3.8])

    D.h("2. One-time costs (per temple)")
    D.table([["Item", "Essential", "Standard", "Complete"],
             ["Requirements & content collection", "₹5,000", "₹10,000", "₹15,000"],
             ["Branding & theme configuration", "₹8,000", "₹12,000", "₹15,000"],
             ["Public website setup", "₹18,000", "₹30,000", "₹30,000"],
             ["Admin panel & roles", "₹10,000", "₹20,000", "₹25,000"],
             ["Seva booking, OTP, devotee accounts", "—", "₹35,000", "₹35,000"],
             ["Donors, donations, receipts", "—", "₹15,000", "₹20,000"],
             ["Finance, members, audit, 2FA, QR scan", "—", "—", "₹70,000"],
             ["Cloud setup, domain, TLS, email, backups", "₹6,000", "₹8,000", "₹10,000"],
             ["Testing, UAT, data load", "₹4,000", "₹8,000", "₹25,000"],
             ["Training & handover", "₹4,000", "₹2,000", "₹15,000"],
             ["Total (excl. GST)", inr(55000), inr(140000), inr(260000)]], widths=[7, 3, 3, 3])
    D.p("Check: Essential 5+8+18+10+6+4+4 = ₹55,000; Standard 10+12+30+20+35+15+8+8+2 = ₹140,000; "
        "Complete 15+15+30+25+35+20+70+10+25+15 = ₹260,000 (₹ thousands).", italic=True)

    D.h("3. Optional add-ons")
    D.table([["Add-on", "Price (one-time)", "Note"],
             ["Online payment gateway (UPI/cards) for sevas & donations", "₹35,000", "Gateway charges (~2% + GST) paid by temple/devotee; KYC by temple. Not in reference build."],
             ["Extra language (translation + QA)", "₹6,000 each", "Per language, for public site text"],
             ["Admin panel in a local language", "₹25,000", "Translate admin UI"],
             ["WhatsApp / SMS notifications", "₹20,000 + usage", "Provider fees extra"],
             ["Content entry & photo digitisation", "₹8,000–20,000", "Depends on volume"],
             ["Professional photography / drone video", "At actuals", "Third party"],
             ["Live darshan embed", "₹8,000", "Streaming costs separate"],
             ["Annual DPDPA/legal text review", "₹6,000", "By legal advisor; optional"]], widths=[6.5, 3, 6.5])

    D.h("4. Recurring costs (per temple, per year)")
    D.table([["Item", "Essential", "Standard", "Complete", "Basis"],
             ["Cloud hosting (EC2 + storage + transfer)", "₹10,000", "₹10,000", "₹14,000", "~$8–11/mo (t4g.micro), t4g.small for Complete; free tier in year 1 if new AWS account"],
             ["S3 storage & requests", "₹600", "₹1,200", "₹2,500", "Gallery and PDFs; cents per GB"],
             ["Email (SES)", "₹300", "₹1,500", "₹3,000", "$0.10 per 1,000 emails"],
             ["Domain (.org / .in)", "₹1,200", "₹1,200", "₹1,200", "Registrar renewal"],
             ["Backups & monitoring", "₹1,500", "₹2,000", "₹3,000", "S3 backups, uptime checks"],
             ["Infrastructure subtotal", inr(13600), inr(15900), inr(23700), ""],
             ["Maintenance & support retainer", "₹24,000", "₹48,000", "₹84,000", "₹2,000 / ₹4,000 / ₹7,000 per month"],
             ["Total recurring (excl. GST)", inr(37600), inr(63900), inr(107700), ""]],
            widths=[5, 2.2, 2.2, 2.2, 4.4])
    D.p("Maintenance covers security patches, dependency upgrades, monitoring, backup verification, content-help requests "
        "(up to 2 / 4 / 8 hours a month) and the support SLA in the TRD. Feature work is quoted separately.")

    D.h("5. Total cost of ownership")
    D.table([["", "Essential", "Standard", "Complete"],
             ["Year 1 (build + recurring)", inr(55000 + 37600), inr(140000 + 63900), inr(260000 + 107700)],
             ["Year 2", inr(37600), inr(63900), inr(107700)],
             ["Year 3", inr(37600), inr(63900), inr(107700)],
             ["3-year total (excl. GST)", inr(55000 + 3 * 37600), inr(140000 + 3 * 63900), inr(260000 + 3 * 107700)],
             ["Average per month", inr((55000 + 3 * 37600) / 36), inr((140000 + 3 * 63900) / 36), inr((260000 + 3 * 107700) / 36)]],
            widths=[5.5, 3.5, 3.5, 3.5])

    D.h("6. Multi-temple programme pricing")
    D.p("Because the platform already exists, the first project in a group of temples funds productisation and later "
        "temples are much cheaper to deliver.")
    D.table([["Item", "Cost", "Notes"],
             ["Platform productisation (one-time, shared)", "₹90,000", "Move temple-specific strings/colours into config, new-temple provisioning script, onboarding guide, generate API types"],
             ["2nd–5th temple", "25% off build fee", "Same package; content and translation still per temple"],
             ["6th temple onward", "35% off build fee", "—"],
             ["Shared maintenance across temples", "10% off retainer from 3rd temple", "Single release process"]], widths=[5.5, 4, 6.5])
    D.p("Illustration — 5 temples on the Standard package:", bold=True)
    std = 140000
    total = 90000 + std + 4 * std * 0.75
    rec = 5 * 63900
    D.table([["Line", "Amount"],
             ["Productisation (once)", inr(90000)],
             ["Temple 1 build", inr(std)],
             ["Temples 2–5 build (25% off)", inr(4 * std * 0.75)],
             ["One-time total", inr(total)],
             ["Recurring per year (5 × Standard)", inr(rec)],
             ["Year-1 total (excl. GST)", inr(total + rec)],
             ["Without programme pricing (5 × full build + recurring)", inr(5 * std + rec)]], widths=[10, 6])

    D.h("7. Assumptions and exclusions")
    D.ul(["Prices exclude GST (18%), third-party fees (payment gateway, SMS/WhatsApp, domain premium names) and temple-side translation effort.",
          "Hosting figures use AWS list prices at an assumed ₹85 = US$1; AWS free tier assumed for the first 12 months of a new account (not deducted above — treat as upside).",
          "Client supplies content (text, logo, photographs, timings, sevas, fees, committee) within the timeline; delays move go-live.",
          "Traffic up to ~2,000 devotees/day on a single server; beyond that, hosting is re-quoted (managed database, CDN).",
          "Two rounds of revisions on design/content are included; additional rounds billed at ₹1,000/hour.",
          "Client owns the domain, AWS account (or we operate it on their behalf at pass-through cost) and all content and data.",
          "Source-code licence: temple receives a perpetual right to use the deployed software; ownership of the reusable platform code remains with the developer unless otherwise agreed.",
          "Figures are estimates from the reference project's stack and are subject to a signed quotation after requirements are confirmed."])
    D.h("8. Payment schedule (suggested)")
    D.table([["Milestone", "Share"],
             ["On signing / content kickoff", "40%"],
             ["Staging site ready for review", "30%"],
             ["Go-live and handover", "30%"],
             ["Maintenance retainer", "Billed quarterly in advance"]], widths=[9, 7])
    D.save("Budget_Temple_Platform.docx")


if __name__ == "__main__":
    srs(); trd(); budget()
