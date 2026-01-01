import React from 'react'

type Props = {
  children: React.ReactNode
}

export default function PageContainer({ children }: Props) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="prose prose-lg max-w-none text-gray-800">{children}</div>
    </div>
  )
}
