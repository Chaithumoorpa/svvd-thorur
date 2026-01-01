-- Update existing users to have ADMIN role
-- Run this inside the PostgreSQL container

-- Update all existing users to be ADMINs (you can modify this as needed)
UPDATE users SET roles = ARRAY['ADMIN']::VARCHAR[];

-- If you want specific users to be SUPER_ADMIN:
-- UPDATE users SET roles = ARRAY['SUPER_ADMIN']::VARCHAR[] WHERE username = 'your_admin_username';

-- If you want users with multiple roles:
-- UPDATE users SET roles = ARRAY['ADMIN', 'TRUSTEE']::VARCHAR[] WHERE username = 'some_user';

-- Check the results:
SELECT id, username, roles FROM users;
