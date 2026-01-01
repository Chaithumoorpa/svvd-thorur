'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Edit2, Trash2, X, Plus, Save, AlertCircle, Megaphone } from 'lucide-react';
import {
  Announcement,
  AnnouncementCreate,
  getAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement
} from '@/lib/api';



export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentAnnouncement, setCurrentAnnouncement] = useState<Partial<Announcement> | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [idToDelete, setIdToDelete] = useState<number | null>(null);

  const fetchAnnouncements = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAnnouncements(true); // show_all = true for admin
      setAnnouncements(data);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to fetch announcements';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const handleOpenModal = (announcement?: Announcement) => {
    if (announcement) {
      setCurrentAnnouncement({
        ...announcement,
      });
    } else {
      setCurrentAnnouncement({
        title: '',
        message: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCurrentAnnouncement(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentAnnouncement) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // Create clean payload matching backend schema
      const payload: AnnouncementCreate = {
        title: currentAnnouncement.title || '',
        message: currentAnnouncement.message || null,
        start_date: currentAnnouncement.start_date || null,
        end_date: currentAnnouncement.end_date || null,
      };

      console.log('Announcement operation:', currentAnnouncement.id ? 'UPDATE' : 'CREATE', payload);

      if (currentAnnouncement.id) {
        await updateAnnouncement(currentAnnouncement.id, payload);
        setSuccess('Announcement updated successfully');
      } else {
        await createAnnouncement(payload);
        setSuccess('Announcement created successfully');
      }
      handleCloseModal();
      fetchAnnouncements();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Announcement save error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });
      const message = err.response?.data?.detail || err.message || 'Failed to save announcement';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteClick = (id: number) => {
    setIdToDelete(id);
    setIsDeleting(true);
  };

  const confirmDelete = async () => {
    if (idToDelete === null) return;

    try {
      await deleteAnnouncement(idToDelete);
      setSuccess('Announcement deleted successfully');
      fetchAnnouncements();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to delete announcement';
      setError(message);
    } finally {
      setIsDeleting(false);
      setIdToDelete(null);
    }
  };

  return (
    <div className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Announcements</h1>
            <p className="text-gray-600 mt-1">Manage temple announcements and news</p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors font-medium shadow-sm"
          >
            <Plus className="w-5 h-5" />
            New Announcement
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800 animate-in fade-in duration-300">
            {success}
          </div>
        )}

        {/* Announcements List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-400">
              <div className="animate-pulse mb-2">Loading announcements...</div>
            </div>
          ) : announcements.length === 0 ? (
            <div className="p-12 text-center">
              <div className="inline-flex items-center justify-center p-4 bg-gray-50 rounded-full mb-4">
                <Megaphone className="w-8 h-8 text-gray-300" />
              </div>
              <p className="text-gray-500 font-medium">No announcements yet</p>
              <button
                onClick={() => handleOpenModal()}
                className="mt-4 text-slate-900 hover:underline font-semibold"
              >
                Create the first announcement
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Announcement</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Main Content</th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Visibility</th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {announcements.map((announcement) => (
                    <tr key={announcement.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4">
                        <p className="font-bold text-gray-900">{announcement.title}</p>
                        <p className="text-xs text-gray-400 mt-0.5">ID: #{announcement.id}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-gray-600 text-sm line-clamp-2 max-w-md">{announcement.message}</p>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col gap-1">
                          <span className="text-xs text-gray-500">
                            From: <span className="text-gray-900 font-medium">{announcement.start_date || 'Immediate'}</span>
                          </span>
                          <span className="text-xs text-gray-500">
                            To: <span className="text-gray-900 font-medium">{announcement.end_date || 'Permament'}</span>
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleOpenModal(announcement)}
                            className="p-2 text-gray-400 hover:text-slate-900 hover:bg-white border border-transparent hover:border-gray-200 rounded-lg transition-all shadow-sm"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteClick(announcement.id)}
                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-white border border-transparent hover:border-gray-200 rounded-lg transition-all shadow-sm"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal */}
        {isModalOpen && currentAnnouncement && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-in zoom-in duration-200">
              {/* Modal Header */}
              <div className="flex justify-between items-center p-6 border-b border-gray-100 sticky top-0 bg-white z-10">
                <h2 className="text-xl font-bold text-gray-900">
                  {currentAnnouncement.id ? 'Edit Announcement' : 'New Announcement'}
                </h2>
                <button
                  onClick={handleCloseModal}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-6 h-6 text-gray-400" />
                </button>
              </div>

              {/* Modal Form */}
              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {/* Title */}
                <div>
                  <label htmlFor="title" className="block text-sm font-semibold text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    id="title"
                    required
                    type="text"
                    value={currentAnnouncement.title || ''}
                    onChange={(e) => setCurrentAnnouncement({ ...currentAnnouncement, title: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none transition-all placeholder:text-gray-300"
                    placeholder="e.g., Annual Temple Festival"
                  />
                </div>

                {/* Content */}
                <div>
                  <label htmlFor="message" className="block text-sm font-semibold text-gray-700 mb-1">
                    Announcement Details *
                  </label>
                  <textarea
                    id="message"
                    required
                    value={currentAnnouncement.message || ''}
                    onChange={(e) => setCurrentAnnouncement({ ...currentAnnouncement, message: e.target.value })}
                    rows={5}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none transition-all resize-none placeholder:text-gray-300"
                    placeholder="Write the full announcement message here..."
                  />
                </div>

                {/* Dates */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="start_date" className="block text-sm font-semibold text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      id="start_date"
                      type="date"
                      value={currentAnnouncement.start_date || ''}
                      onChange={(e) => setCurrentAnnouncement({ ...currentAnnouncement, start_date: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none"
                    />
                    <p className="mt-1 text-xs text-gray-400 text-left">When the announcement appears</p>
                  </div>
                  <div>
                    <label htmlFor="end_date" className="block text-sm font-semibold text-gray-700 mb-1">
                      End Date
                    </label>
                    <input
                      id="end_date"
                      type="date"
                      value={currentAnnouncement.end_date || ''}
                      onChange={(e) => setCurrentAnnouncement({ ...currentAnnouncement, end_date: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-slate-900 focus:border-transparent outline-none"
                    />
                    <p className="mt-1 text-xs text-gray-400 text-left">When it automatically hides</p>
                  </div>
                </div>

                {/* Modal Actions */}
                <div className="flex gap-4 pt-6 border-t border-gray-100">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors font-semibold disabled:opacity-50 shadow-sm"
                  >
                    {isSubmitting ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Save className="w-5 h-5" />
                    )}
                    {isSubmitting ? 'Saving...' : currentAnnouncement.id ? 'Save Changes' : 'Create Announcement'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {isDeleting && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-[60] animate-in fade-in duration-200">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in duration-200">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <Trash2 className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Confirm Delete</h3>
                  <p className="text-gray-500 text-sm">Are you sure you want to remove this announcement? This action cannot be undone.</p>
                </div>
              </div>
              <div className="flex gap-3 mt-8">
                <button
                  onClick={() => setIsDeleting(false)}
                  className="flex-1 px-4 py-2 text-gray-700 font-semibold hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-semibold shadow-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
