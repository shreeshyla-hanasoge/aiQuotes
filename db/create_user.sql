-- Drop the user if exists to ensure we start fresh with correct auth plugin
DROP USER IF EXISTS 'free_application_user'@'%';

-- Create the user with mysql_native_password to avoid SSL/caching_sha2_password issues
CREATE USER 'free_application_user'@'%' IDENTIFIED WITH mysql_native_password BY 'noquotesDevUse1!';

-- Grant privileges on the aiquotes database
GRANT ALL PRIVILEGES ON aiquotes.* TO 'free_application_user'@'%';

-- Apply changes
FLUSH PRIVILEGES;
