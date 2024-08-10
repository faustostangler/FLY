# selenium

# bin for executable
bin_folder = 'bin'

# webdriver wait
wait_time = 2

# Possible registry keys to check for Chrome version
registry_paths = [
    r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
    r'reg query "HKEY_LOCAL_MACHINE\Software\Google\Chrome\BLBeacon" /v version',
    r'reg query "HKEY_LOCAL_MACHINE\Software\WOW6432Node\Google\Chrome\BLBeacon" /v version'
]
