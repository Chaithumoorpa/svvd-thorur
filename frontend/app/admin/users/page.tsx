"use client";

import React, { useState, useEffect } from 'react';
import { UserPlus, Settings, Shield, User, RefreshCw, Info } from 'lucide-react';
import { api } from '@/lib/api';
import { isUserSuperAdmin } from '@/app/utils/auth';

interface UserItem {
    id: number;
    username: string;
    roles: string[];
    is_active: boolean;
    must_change_password: boolean;
}

export default function UserManagementPage() {
    const [users, setUsers] = useState<UserItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [showAddModal, setShowAddModal] = useState(false);

    // New user form
    const [newUsername, setNewUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newRoles, setNewRoles] = useState<string[]>(['TRUSTEE']);

    const [isSuperAdmin, setIsSuperAdmin] = useState(false);

    useEffect(() => {
        setIsSuperAdmin(isUserSuperAdmin());
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            setIsLoading(true);
            const response = await api.get<UserItem[]>('/auth/users');
            setUsers(response.data);
            setIsLoading(false);
        } catch (err: any) {
            console.error('Users fetch error:', {
                status: err.response?.status,
                data: err.response?.data,
                message: err.message
            });
            const message = err.response?.data?.detail || err.message || 'Failed to fetch users';
            setError(message);
            setIsLoading(false);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        const payload = {
            username: newUsername,
            password: newPassword,
            roles: newRoles
        };

        console.log('Creating user:', payload);

        try {
            await api.post('/auth/register', payload);
            setShowAddModal(false);
            setNewUsername('');
            setNewPassword('');
            setNewRoles(['TRUSTEE']);
            // Refresh list
            fetchUsers();
            alert('User created successfully. They will be asked to change their password on first login.');
        } catch (err: any) {
            console.error('User creation error:', {
                status: err.response?.status,
                data: err.response?.data,
                message: err.message
            });
            const message = err.response?.data?.detail || err.message || 'Failed to create user';
            setError(message);
            setIsLoading(false);
        }
    };

    if (!isSuperAdmin && !isLoading) {
        return (
            <div className="p-8 text-center">
                <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <h1 className="text-2xl font-bold">Access Denied</h1>
                <p className="text-gray-500 mt-2">Only Super Admins can manage users.</p>
            </div>
        );
    }

    return (
        <div className="p-4 md:p-8 max-w-6xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                        <Settings className="w-6 h-6" />
                        User Management
                    </h1>
                    <p className="text-gray-500 mt-1">Manage admin and trustee accounts</p>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={fetchUsers}
                        className="p-2 text-gray-500 hover:text-slate-900 border rounded-lg hover:bg-gray-50 transition-all focus:outline-none"
                        title="Refresh list"
                    >
                        <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-all shadow-md active:scale-95"
                    >
                        <UserPlus className="w-5 h-5" />
                        Add New User
                    </button>
                </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-8 flex gap-3 text-blue-800">
                <Info className="w-5 h-5 shrink-0" />
                <p className="text-sm">
                    <strong>Security Note:</strong> All new users are created with a temporary password and
                    will be forced to set their own password when they first log in.
                </p>
            </div>

            {/* User List Table */}
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
                {isLoading && users.length === 0 ? (
                    <div className="p-12 text-center text-gray-400">
                        <div className="w-8 h-8 border-4 border-slate-200 border-t-slate-900 rounded-full animate-spin mx-auto mb-4" />
                        <p>Loading users...</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-slate-50 border-b border-slate-100">
                                <tr>
                                    <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">User</th>
                                    <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Roles</th>
                                    <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Password</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                                {users.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center text-gray-400">
                                            No users found.
                                        </td>
                                    </tr>
                                ) : (
                                    users.map((user) => (
                                        <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                                                        <User className="w-4 h-4" />
                                                    </div>
                                                    <span className="font-medium text-slate-900">{user.username}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-wrap gap-1">
                                                    {user.roles.map(role => (
                                                        <span key={role} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-[10px] font-bold">
                                                            {role}
                                                        </span>
                                                    ))}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-sm">
                                                <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                    {user.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-sm">
                                                {user.must_change_password ? (
                                                    <span className="text-amber-600 font-medium flex items-center gap-1">
                                                        <RefreshCw className="w-3 h-3" /> Change Pending
                                                    </span>
                                                ) : (
                                                    <span className="text-green-600">Secure</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Add User Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
                        <h2 className="text-xl font-bold mb-4">Create New Account</h2>

                        <form onSubmit={handleCreateUser} className="space-y-4">
                            {error && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

                            <div>
                                <label className="block text-sm font-medium mb-1">Username</label>
                                <input
                                    type="text"
                                    value={newUsername}
                                    onChange={(e) => setNewUsername(e.target.value)}
                                    className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-slate-900"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Temporary Password</label>
                                <input
                                    type="text"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-slate-900"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Role</label>
                                <select
                                    value={newRoles[0]}
                                    onChange={(e) => setNewRoles([e.target.value])}
                                    className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-slate-900"
                                >
                                    <option value="TRUSTEE">Trustee (View Only)</option>
                                    <option value="ADMIN">Admin (Full Control)</option>
                                    <option value="SUPER_ADMIN">Super Admin (System Settings)</option>
                                </select>
                            </div>

                            <div className="flex gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="flex-1 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
                                >
                                    {isLoading ? 'Creating...' : 'Create User'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
