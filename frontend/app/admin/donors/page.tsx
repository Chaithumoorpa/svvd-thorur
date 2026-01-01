"use client"

import React, { useMemo, useState, useEffect } from "react"
import { api } from "@/lib/api"
import { Plus, Edit, Trash2, X, Save, AlertCircle, FileDown } from "lucide-react"
import { getDonorReceipt, generateDonorReceipt } from "@/lib/api"

type Donor = {
  id: number
  name: string
  phone: string | null
  email: string | null
  donated_for: string | null
  amount: number
  donated_on: string // ISO date string
}

type DonorResponse = {
  id: number
  name: string
  phone: string | null
  email: string | null
  donated_for: string | null
  amount: number
  donated_on: string
  is_active: boolean
  created_at: string
  updated_at: string
}

function formatAmount(a: number) {
  return `₹${a.toLocaleString()}`
}

export default function AdminDonorsPage() {
  const [donors, setDonors] = useState<Donor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Filter states
  const [fromDate, setFromDate] = useState<string>("")
  const [toDate, setToDate] = useState<string>("")

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [currentDonor, setCurrentDonor] = useState<Partial<Donor> | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [donorToDelete, setDonorToDelete] = useState<number | null>(null)

  const fetchDonors = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get<DonorResponse[]>("/donors")
      const mappedDonors: Donor[] = response.data.map((d) => ({
        id: d.id,
        name: d.name,
        phone: d.phone,
        email: d.email,
        donated_for: d.donated_for,
        amount: d.amount,
        donated_on: d.donated_on,
      }))
      setDonors(mappedDonors)
    } catch (err: any) {
      console.error('Donors fetch error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });

      if (err.response?.status === 403) {
        setError('Permission denied. You need TRUSTEE, ADMIN, or SUPER_ADMIN role to view donors.');
      } else {
        const message = err.response?.data?.detail || err.message || "Failed to fetch donors";
        setError(message);
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDonors()
  }, [])

  const handleOpenModal = (donor?: Donor) => {
    if (donor) {
      setCurrentDonor({
        ...donor,
        donated_on: donor.donated_on.split('T')[0] // Format for date input
      })
    } else {
      setCurrentDonor({
        name: "",
        phone: "",
        email: "",
        donated_for: "general",
        amount: 0,
        donated_on: new Date().toISOString().split('T')[0]
      })
    }
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setCurrentDonor(null)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentDonor) return

    setIsSubmitting(true)
    setError(null)

    try {
      console.log('Donor operation:', currentDonor.id ? 'UPDATE' : 'CREATE', currentDonor);

      if (currentDonor.id) {
        // Update
        await api.put(`/donors/${currentDonor.id}`, currentDonor)
        setSuccess("Donor updated successfully")
      } else {
        // Create
        await api.post("/donors", currentDonor)
        setSuccess("Donor added successfully")
      }
      handleCloseModal()
      fetchDonors()
      // Clear success after 3 seconds
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      console.error('Donor save error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });

      if (err.response?.status === 403) {
        setError('Permission denied. You need ADMIN or SUPER_ADMIN role to modify donors.');
      } else {
        const message = err.response?.data?.detail || err.message || "Failed to save donor";
        setError(message);
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    setDonorToDelete(id)
    setIsDeleting(true)
  }

  const confirmDelete = async () => {
    if (!donorToDelete) return

    try {
      console.log('Deleting donor:', donorToDelete);
      await api.delete(`/donors/${donorToDelete}`)
      setSuccess("Donor deleted successfully")
      fetchDonors()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      console.error('Donor delete error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });

      if (err.response?.status === 403) {
        setError('Permission denied. You need ADMIN or SUPER_ADMIN role to delete donors.');
      } else {
        const message = err.response?.data?.detail || err.message || "Failed to delete donor";
        setError(message);
      }
    } finally {
      setIsDeleting(false)
      setDonorToDelete(null)
    }
  }

  const handleDownloadReceipt = async (id: number) => {
    try {
      // First ensure receipt is generated
      await generateDonorReceipt(id)
      // Then download
      const blob = await getDonorReceipt(id)
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `receipt_${id}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err: any) {
      alert("Failed to download receipt")
    }
  }

  const filtered = useMemo(() => {
    const from = fromDate ? new Date(fromDate) : null
    const to = toDate ? new Date(toDate) : null

    return donors.filter((d) => {
      const dt = new Date(d.donated_on)
      if (from && dt < from) return false
      if (to && dt > to) return false
      return true
    })
  }, [fromDate, toDate, donors])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Donors & Contributions</h1>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Donor</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 text-sm text-green-800">
          {success}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-6">
        <div className="flex flex-col md:flex-row md:items-end md:space-x-4 gap-3">
          <div className="flex-1 max-w-xs">
            <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">From Date</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none"
            />
          </div>

          <div className="flex-1 max-w-xs">
            <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wider">To Date</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none"
            />
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => { setFromDate(""); setToDate("") }}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
            >
              Clear Filters
            </button>
            <div className="text-sm text-gray-400">
              Showing <span className="text-gray-900 font-semibold">{filtered.length}</span> donor(s)
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          <div className="animate-pulse mb-2">Loading donors...</div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Donor Details</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Purpose</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-50">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                      No donors found matching your criteria.
                    </td>
                  </tr>
                ) : (
                  filtered.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">{d.name}</div>
                        <div className="text-xs text-gray-500">{d.phone || d.email || "No contact info"}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <span className="px-2 py-1 bg-gray-100 rounded text-xs capitalize">{d.donated_for || "general"}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 text-right">
                        {formatAmount(d.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(d.donated_on).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex justify-end space-x-2">
                          <button
                            onClick={() => handleDownloadReceipt(d.id)}
                            className="p-1.5 text-blue-400 hover:text-blue-600 transition-colors rounded-md hover:bg-white border border-transparent hover:border-gray-200"
                            title="Download Receipt"
                          >
                            <FileDown className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleOpenModal(d)}
                            className="p-1.5 text-gray-400 hover:text-slate-900 transition-colors rounded-md hover:bg-white border border-transparent hover:border-gray-200"
                            title="Edit Donor"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(d.id)}
                            className="p-1.5 text-gray-400 hover:text-red-600 transition-colors rounded-md hover:bg-white border border-transparent hover:border-gray-200"
                            title="Delete Donor"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {isModalOpen && currentDonor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-bold text-gray-900">{currentDonor.id ? "Edit Donor" : "Add New Donor"}</h2>
              <button onClick={handleCloseModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    required
                    type="text"
                    value={currentDonor.name || ""}
                    onChange={(e) => setCurrentDonor({ ...currentDonor, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 outline-none"
                    placeholder="Enter donor name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    value={currentDonor.phone || ""}
                    onChange={(e) => setCurrentDonor({ ...currentDonor, phone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 outline-none"
                    placeholder="+91..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email (Optional)</label>
                  <input
                    type="email"
                    value={currentDonor.email || ""}
                    onChange={(e) => setCurrentDonor({ ...currentDonor, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 outline-none"
                    placeholder="email@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Donation Amount (₹)</label>
                  <input
                    required
                    type="number"
                    value={currentDonor.amount || ""}
                    onChange={(e) => setCurrentDonor({ ...currentDonor, amount: Number(e.target.value) })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 outline-none"
                    placeholder="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                  <input
                    required
                    type="date"
                    value={currentDonor.donated_on || ""}
                    onChange={(e) => setCurrentDonor({ ...currentDonor, donated_on: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 outline-none"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Donated For</label>
                  <select
                    value={currentDonor.donated_for || "general"}
                    onChange={(e) => setCurrentDonor({ ...currentDonor, donated_for: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 outline-none"
                  >
                    <option value="general">General Donation</option>
                    <option value="annadanam">Annadanam</option>
                    <option value="pooja">Special Pooja</option>
                    <option value="festival">Festival</option>
                    <option value="construction">Construction</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t mt-6">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-6 py-2 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center space-x-2 px-6 py-2 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{isSubmitting ? "Saving..." : "Save Donor"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6">
              <div className="flex items-center space-x-4 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <Trash2 className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Delete Donor</h2>
                  <p className="text-sm text-gray-500">Are you sure you want to delete this donor record? This action cannot be undone.</p>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-8">
                <button
                  onClick={() => setIsDeleting(false)}
                  className="px-6 py-2 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-6 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
