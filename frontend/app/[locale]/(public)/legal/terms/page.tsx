import type { Metadata } from 'next'
import PageContainer from '@/components/PageContainer'
import { Link } from '@/i18n/navigation'
import { fetchTemple } from '@/lib/server-api'
import { pageMetadata, templeAddress, templeLocation, templeName } from '@/lib/site'

export async function generateMetadata(): Promise<Metadata> {
  return pageMetadata('/legal/terms');
}

/**
 * Published in English only, deliberately - same reasoning as
 * /legal/privacy-policy: this is a compliance document, and an inaccurate
 * translation of a legal notice is worse than none.
 */
export default async function TermsPage() {
  const temple = await fetchTemple()
  const name = templeName(temple)
  const location = templeLocation(temple)
  const address = templeAddress(temple)
  const email = temple?.contact_email || 'the temple office'
  const phone = temple?.contact_phone
  const fullName = location ? `${name}, ${location}` : name

  return (
    <PageContainer>
      <h1 className="text-3xl font-serif font-semibold text-templeDark">Terms &amp; Conditions</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: 29 September 2026</p>
      <p className="mt-4 text-gray-700">
        Welcome to the official website of {fullName} (&quot;Temple&quot;, &quot;we&quot;, &quot;us&quot;, or
        &quot;our&quot;). This website is operated to provide devotees and visitors with information about
        the Temple, its timings, poojas and sevas, festivals, announcements, donations, and other
        temple-related services.
      </p>
      <p className="mt-2 text-gray-700">
        By accessing or using this website, creating an account, booking a seva, making a donation, or
        submitting information through the website, you agree to these Terms &amp; Conditions. If you do
        not agree with these terms, please do not use the website.
      </p>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">1. About the Website</h2>
        <p className="mt-2 text-gray-700">The website provides information and online services relating to the Temple, including, where available:</p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Temple timings and visiting information</li>
          <li>Poojas and seva information</li>
          <li>Online seva bookings</li>
          <li>Donation facilities</li>
          <li>Booking and donation confirmations</li>
          <li>Contact and enquiry services</li>
          <li>Temple announcements and festival information</li>
          <li>Gallery and other informational content</li>
        </ul>
        <p className="mt-2 text-gray-700">The Temple may add, modify, suspend, or discontinue any website feature or service when reasonably necessary.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">2. Temple Information</h2>
        <p className="mt-2 text-gray-700">
          We make reasonable efforts to keep information on the website accurate and current. However,
          temple timings, seva schedules, availability, festival arrangements, prices, procedures, and
          other information may change because of administrative decisions, religious occasions,
          festivals, government requirements, weather, safety considerations, or other circumstances.
        </p>
        <p className="mt-2 text-gray-700">
          The Temple reserves the right to make necessary changes to schedules or arrangements. Where
          reasonably possible, significant changes affecting an existing booking will be communicated to
          the devotee using the contact information provided during booking.
        </p>
        <p className="mt-2 text-gray-700">
          Information displayed on the website should not be treated as a guarantee that a particular
          seva, pooja, priest, facility, or temple activity will be available at all times.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">3. User Accounts</h2>
        <p className="mt-2 text-gray-700">Certain features may require you to create an account. When creating an account, you agree to:</p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Provide accurate and current information.</li>
          <li>Keep your login credentials confidential.</li>
          <li>Not share your password or account with another person.</li>
          <li>Notify the Temple if you believe your account has been accessed without authorization.</li>
          <li>Use your account only for lawful and legitimate purposes.</li>
        </ul>
        <p className="mt-2 text-gray-700">
          You are responsible for activities carried out through your account unless you have promptly
          notified us of unauthorized access. We store passwords using cryptographic hashing and do not
          store passwords in plain text.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">4. Seva Bookings</h2>
        <p className="mt-2 text-gray-700">
          Where online seva booking is available, devotees must provide accurate information required to
          complete the booking. A booking may require information such as:
        </p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Devotee name</li>
          <li>Mobile number</li>
          <li>Email address</li>
          <li>Selected seva</li>
          <li>Preferred date</li>
          <li>Number of devotees, where applicable</li>
          <li>Other information reasonably required to process the booking</li>
        </ul>
        <p className="mt-2 text-gray-700">
          An online booking is considered confirmed only when the website displays a successful
          confirmation and/or a confirmation message is sent to the registered contact details.
        </p>
        <p className="mt-2 text-gray-700">The Temple may decline, cancel, or modify a booking where:</p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>The selected seva is unavailable.</li>
          <li>The requested date or time is changed by the Temple.</li>
          <li>The booking contains materially incorrect or misleading information.</li>
          <li>Duplicate or suspicious bookings are detected.</li>
          <li>The Temple is required to make changes for administrative, religious, safety, or legal reasons.</li>
        </ul>
        <p className="mt-2 text-gray-700">
          Devotees should retain their booking confirmation or ticket and present it when requested by
          Temple staff. The Temple may require identification or other reasonable verification before
          allowing a devotee to participate in a booked seva.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">5. Cancellation and Refunds</h2>
        <p className="mt-2 text-gray-700">
          Cancellation and refund eligibility depends on the particular seva, donation, or service
          involved and any cancellation policy communicated at the time of booking.
        </p>
        <p className="mt-2 text-gray-700">
          Where a seva is cancelled by the Temple, or where the Temple is unable to provide the booked
          seva, the Temple will determine the appropriate remedy, which may include rescheduling or
          refund where applicable. Any refund, where applicable, will generally be made through the
          original payment method or another method determined by the Temple/payment service provider.
        </p>
        <p className="mt-2 text-gray-700">
          Certain donations may not be refundable once voluntarily made, subject to applicable law and
          the circumstances of the transaction. If a refund or cancellation policy specific to a
          particular seva is displayed during booking, that policy will apply to that booking.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">6. Donations</h2>
        <p className="mt-2 text-gray-700">
          The website may provide facilities for devotees to make voluntary donations to the Temple.
          Donors are responsible for providing accurate information required for donation records and
          receipts. Where applicable, the Temple may request information such as name, address, PAN,
          email address, and mobile number for accounting, tax, receipt, and statutory purposes.
        </p>
        <p className="mt-2 text-gray-700">
          Donation receipts will be issued based on the information provided by the donor and applicable
          requirements. A donation does not automatically create any right to a particular seva, service,
          facility, or personal benefit unless expressly stated by the Temple.
        </p>
        <p className="mt-2 text-gray-700">
          The Temple does not guarantee that a donation will qualify for a particular tax benefit. Donors
          should consult their own tax adviser regarding the tax treatment applicable to their
          circumstances.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">7. Online Payments</h2>
        <p className="mt-2 text-gray-700">
          Where online payment facilities are available, payments may be processed through a third-party
          payment gateway. Payment card, banking, UPI, or other payment credentials may be processed
          directly by the applicable payment service provider and may be subject to that provider&apos;s
          terms and privacy policy.
        </p>
        <p className="mt-2 text-gray-700">
          The Temple does not intentionally store complete card numbers, CVV numbers, UPI PINs, internet
          banking passwords, or other authentication credentials that should not be stored by the Temple.
          A payment may be considered successful only after confirmation is received from the payment
          service provider and/or the Temple&apos;s system.
        </p>
        <p className="mt-2 text-gray-700">
          If money is debited from your account but the booking or donation is not successfully recorded,
          please contact the Temple using the contact details provided on the website.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">8. Temple Rules and Devotee Conduct</h2>
        <p className="mt-2 text-gray-700">
          Visitors and devotees using the website or Temple services are expected to behave respectfully
          and comply with applicable Temple rules. Users must not:
        </p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Use the website for unlawful purposes.</li>
          <li>Submit false, misleading, or fraudulent information.</li>
          <li>Attempt to access another person&apos;s account.</li>
          <li>Attempt to bypass website security.</li>
          <li>Introduce malicious software, code, or harmful content.</li>
          <li>Interfere with the operation of the website.</li>
          <li>Create fraudulent, duplicate, or abusive bookings.</li>
          <li>Use automated systems to make excessive or unauthorized bookings.</li>
          <li>Use Temple content for misleading, defamatory, or unlawful purposes.</li>
        </ul>
        <p className="mt-2 text-gray-700">
          The Temple may restrict or suspend access where there is reasonable evidence of misuse, fraud,
          abuse, or security threats.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">9. Intellectual Property</h2>
        <p className="mt-2 text-gray-700">
          Unless otherwise stated, the content of this website, including Temple logos, text,
          photographs, graphics, page designs, documents, and other materials, is owned by or used with
          permission by the Temple. You may view and use website content for personal and non-commercial
          purposes.
        </p>
        <p className="mt-2 text-gray-700">
          You must not reproduce, modify, commercially exploit, distribute, or republish substantial
          portions of the website content without prior permission from the Temple, except where
          permitted by applicable law. Photographs and materials submitted to or published by the Temple
          may be subject to separate rights and permissions.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">10. Third-Party Services and Links</h2>
        <p className="mt-2 text-gray-700">
          The website may use or link to third-party services, including hosting providers, email
          providers, payment gateways, analytics or security services, and other external services
          necessary to operate the website. The Temple is not responsible for the availability, content,
          security, privacy practices, or terms of third-party websites or services that are outside the
          Temple&apos;s control. Third-party services may have their own terms and privacy policies,
          which users should review before using those services.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">11. Website Availability</h2>
        <p className="mt-2 text-gray-700">
          We aim to keep the website available and functioning properly, but uninterrupted availability
          cannot be guaranteed. The website may occasionally be unavailable because of:
        </p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Maintenance</li>
          <li>Software updates</li>
          <li>Hosting or network problems</li>
          <li>Security incidents</li>
          <li>Internet or telecommunications failures</li>
          <li>Third-party service interruptions</li>
          <li>Circumstances beyond the Temple&apos;s reasonable control</li>
        </ul>
        <p className="mt-2 text-gray-700">The Temple may perform maintenance or temporarily suspend services when necessary.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">12. Security</h2>
        <p className="mt-2 text-gray-700">
          The Temple takes reasonable technical and organizational measures to protect information
          submitted through the website. However, no internet-based service can be guaranteed to be
          completely secure.
        </p>
        <p className="mt-2 text-gray-700">
          Users should not share passwords, OTPs, UPI PINs, card PINs, or other authentication
          credentials with Temple staff or anyone claiming to represent the Temple. The Temple will not
          ask you to disclose your UPI PIN, ATM PIN, card CVV, or account password through email,
          telephone, or other unofficial communication.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">13. Privacy</h2>
        <p className="mt-2 text-gray-700">
          Your use of this website is also subject to our{' '}
          <Link href="/legal/privacy-policy" className="text-templeDark underline">Privacy Policy</Link>, which
          explains what personal information we collect, why we collect it, how it is used, and the
          rights available to you. Please review the Privacy Policy before creating an account, making a
          booking, or submitting personal information.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">14. Communications</h2>
        <p className="mt-2 text-gray-700">
          By providing your email address or mobile number while using the website, you agree that the
          Temple may use those details to communicate information relating to:
        </p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Your account</li>
          <li>Seva bookings</li>
          <li>Booking confirmations</li>
          <li>Payment or donation records</li>
          <li>Receipts</li>
          <li>Changes affecting your booking</li>
          <li>Responses to your enquiries</li>
          <li>Important service or security notices</li>
        </ul>
        <p className="mt-2 text-gray-700">
          The Temple will not use your personal information for unrelated promotional purposes except
          where permitted by applicable law and where the necessary consent or legal basis exists.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">15. Accuracy of Information Provided by Users</h2>
        <p className="mt-2 text-gray-700">
          You are responsible for ensuring that the information you provide through the website is
          accurate. If incorrect information results in a failed communication, incorrect booking
          information, inability to verify a transaction, or other issue, the Temple may not be able to
          correct the resulting problem in every circumstance. Please review your details carefully
          before submitting a booking, donation, or other form.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">16. Limitation of Liability</h2>
        <p className="mt-2 text-gray-700">
          To the extent permitted by applicable law, the Temple will not be responsible for indirect,
          incidental, special, or consequential losses arising from the use or inability to use the
          website or from circumstances outside the Temple&apos;s reasonable control. Nothing in these
          Terms is intended to exclude or limit any liability that cannot legally be excluded or limited
          under applicable law.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">17. Force Majeure</h2>
        <p className="mt-2 text-gray-700">
          The Temple will not be responsible for failure or delay in providing website services or
          fulfilling arrangements where the failure or delay results from circumstances beyond its
          reasonable control, including natural disasters, severe weather, government restrictions,
          public emergencies, technical infrastructure failures, security incidents, or other unforeseen
          circumstances.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">18. Suspension or Termination</h2>
        <p className="mt-2 text-gray-700">
          The Temple may suspend or terminate an account or restrict access to the website where
          reasonably necessary because of:
        </p>
        <ul className="mt-2 list-disc pl-6 text-gray-700">
          <li>Fraudulent activity</li>
          <li>Misuse of the website</li>
          <li>Violation of these Terms</li>
          <li>Security concerns</li>
          <li>Legal or regulatory requirements</li>
          <li>Repeated abusive or unauthorized activity</li>
        </ul>
        <p className="mt-2 text-gray-700">Where appropriate, the Temple may notify the affected user.</p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">19. Changes to These Terms</h2>
        <p className="mt-2 text-gray-700">
          The Temple may update these Terms &amp; Conditions from time to time. When material changes are
          made, the updated version will be published on this page and the &quot;Last updated&quot; date
          will be changed. Your continued use of the website after the updated terms are published
          constitutes acceptance of the updated Terms, to the extent permitted by applicable law.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">20. Governing Law and Jurisdiction</h2>
        <p className="mt-2 text-gray-700">
          These Terms &amp; Conditions are governed by the laws of India. Subject to applicable law,
          disputes relating to the use of this website or Temple services will be subject to the
          jurisdiction of the courts having appropriate jurisdiction over {location || 'the Temple’s location'}.
          Nothing in these Terms prevents a consumer or other person from exercising any mandatory rights
          or remedies available under applicable Indian law.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-semibold">21. Grievances and Contact</h2>
        <p className="mt-2 text-gray-700">
          If you have a question, complaint, booking issue, payment issue, or concern regarding these
          Terms or the website, please contact the Temple.
        </p>
        <p className="mt-2 text-gray-700">
          {name}
          {address && <><br />{address}</>}
          <br />Email: {email}
          {phone && <><br />Phone: {phone}</>}
        </p>
        <p className="mt-2 text-gray-700">
          For privacy-related matters, please refer to the contact and grievance information provided in
          our <Link href="/legal/privacy-policy" className="text-templeDark underline">Privacy Policy</Link>.
        </p>
      </section>
    </PageContainer>
  )
}
