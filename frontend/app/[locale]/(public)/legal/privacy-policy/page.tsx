import type { Metadata } from 'next'
import PageContainer from '@/components/PageContainer'
import { fetchTemple } from '@/lib/server-api'
import { localizedAlternates, templeAddress, templeName } from '@/lib/site'

export async function generateMetadata(): Promise<Metadata> {
  return { alternates: await localizedAlternates('/legal/privacy-policy') }
}

/**
 * Published in English only, deliberately - this is a compliance document
 * (India's Digital Personal Data Protection Act, 2023) and an inaccurate
 * translation of a legal notice is worse than none. Every other page on the
 * site is translated; this one and /legal/terms and /legal/refund-policy
 * are the exceptions.
 */
export default async function PrivacyPolicyPage() {
  const temple = await fetchTemple()
  const name = templeName(temple)
  const address = templeAddress(temple)
  const email = temple?.contact_email || 'the temple office'
  const phone = temple?.contact_phone

  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Privacy Policy</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: 24 September 2026</p>
      <p className="mt-4 text-gray-700">
        {name} (&quot;the temple&quot;, &quot;we&quot;, &quot;us&quot;) operates svvdthorur.org for devotees to look up
        temple information, book sevas, make donations and get in touch with the temple office. This
        policy explains what personal data we collect through the website, why, and the rights you have
        over it under India&apos;s Digital Personal Data Protection Act, 2023 (DPDPA) and the Information
        Technology Act, 2000 and its rules. As a charitable religious institution registered in Andhra
        Pradesh, we hold this data to the same standard we&apos;d want applied to our own family&apos;s
        information.
      </p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">1. What we collect</h2>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li><strong>Account registration:</strong> username, email address, mobile number, and your password (stored as a one-way hash - we cannot see or recover it).</li>
          <li><strong>Seva bookings:</strong> devotee name, mobile number, email address, and the seva/date booked. Online bookings verify the email with a one-time code before the booking is created.</li>
          <li><strong>Donations:</strong> donor name, phone, email, postal address, and PAN (only when provided, to issue an 80G tax receipt).</li>
          <li><strong>Contact form:</strong> name, email address, and your message.</li>
          <li><strong>Site visits:</strong> an anonymized, one-way hash of your IP address plus the date, used only to show a visitor count - never a raw IP, and never linked to any account.</li>
        </ul>
        <p className="mt-2 text-gray-700">We do not use advertising or third-party tracking cookies. Staying signed in relies on a token your browser stores locally, not a tracking cookie.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">2. Why we collect it</h2>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>To create and manage your devotee account, and to let you view your own booking history.</li>
          <li>To process and confirm seva bookings, and to let temple staff verify a ticket at the counter.</li>
          <li>To record donations and issue tax receipts where applicable.</li>
          <li>To respond to messages sent through the contact form.</li>
          <li>To meet our legal and tax record-keeping obligations as a religious/charitable institution.</li>
          <li>To keep the site secure - for example, detecting unusual account activity.</li>
        </ul>
        <p className="mt-2 text-gray-700">Our basis for processing is your consent (given when you register, book, or donate), the need to perform the service you asked for, and, for tax records, our legal obligations.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">3. Who we share it with</h2>
        <p className="mt-2 text-gray-700">
          We do not sell, rent, or trade your personal data. It is shared only with service providers who
          process it on our behalf, strictly to run the site:
        </p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Amazon Web Services (AWS), for hosting and file storage, and Amazon SES, to deliver booking/verification/receipt emails.</li>
          <li>Once online payment is enabled, a payment gateway - only for the transaction it's processing, and only the details that transaction needs.</li>
        </ul>
        <p className="mt-2 text-gray-700">We disclose personal data to government or law enforcement only where legally required to do so.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">4. How long we keep it</h2>
        <p className="mt-2 text-gray-700">
          We keep personal data only as long as needed for the purpose it was collected for, and as long as
          applicable tax and charity-accounting rules require donation and receipt records to be kept.
          Devotee account data is kept until you delete your account (see below) or ask us to.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">5. Your rights</h2>
        <p className="mt-2 text-gray-700">As a Data Principal under the DPDPA, you have the right to:</p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li><strong>Access</strong> a summary of the personal data we hold about you.</li>
          <li><strong>Correct or update</strong> inaccurate or incomplete data.</li>
          <li><strong>Erase</strong> your data once it's no longer needed for the purpose you gave it for.</li>
          <li><strong>Withdraw consent</strong> at any time, as easily as you gave it.</li>
          <li><strong>Nominate</strong> another individual to exercise these rights on your behalf if you become unable to (e.g. in the event of death or incapacity).</li>
          <li><strong>Grievance redressal</strong> - raise a complaint with us, and if unsatisfied, with the Data Protection Board of India.</li>
        </ul>
        <p className="mt-2 text-gray-700">
          If you have a devotee account, you can delete it yourself at any time from your account page -
          this removes your registration details immediately. For anything else (correcting a booking,
          a donation record, or a question about what we hold), contact us using the details below.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">6. Children</h2>
        <p className="mt-2 text-gray-700">
          This site is not directed at children. We do not knowingly collect personal data from anyone
          under 18 without a parent or guardian booking or registering on their behalf.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">7. Keeping your data secure</h2>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>All traffic to the site is encrypted (HTTPS).</li>
          <li>Passwords are never stored in plain text - only a one-way cryptographic hash.</li>
          <li>Access to donor, booking and account data is restricted to authorized temple staff and administrators, and every sensitive action they take is logged.</li>
          <li>Sign-in sessions expire automatically after a period of inactivity.</li>
        </ul>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">8. Changes to this policy</h2>
        <p className="mt-2 text-gray-700">
          If we make a material change to how we handle personal data, we&apos;ll update this page and
          change the date at the top.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">9. Grievance Officer / Contact us</h2>
        <p className="mt-2 text-gray-700">
          For any question about this policy, or to exercise a right described above, contact:
        </p>
        <p className="mt-2 text-gray-700">
          {name}
          {address && <><br />{address}</>}
          <br />Email: {email}
          {phone && <><br />Phone: {phone}</>}
        </p>
        <p className="mt-2 text-gray-700">We aim to respond to any privacy request within 30 days.</p>
      </section>
    </PageContainer>
  )
}
