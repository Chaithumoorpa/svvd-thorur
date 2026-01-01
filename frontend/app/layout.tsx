import './globals.css'



export const metadata = {
  title: 'Sri Varasiddhi Vinayaka Swamy Temple',
  description: 'Thorur',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-templeWhite text-templeDark flex flex-col min-h-screen">
        {children}
      </body>
    </html>
  )
}
