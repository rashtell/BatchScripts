@echo off
setlocal

rem Check if openssl is installed
where openssl >nul 2>&1
if %errorlevel% neq 0 (
    echo OpenSSL is not installed. Please install it from https://www.openssl.org/
    exit /b 1
)

rem Set variables
set CERTIFICATE_DAYS=365
set COUNTRY=US
set STATE=California
set LOCALITY=SanFrancisco
set ORGANIZATION=YourOrganization
set ORGANIZATIONAL_UNIT=YourUnit
set COMMON_NAME=localhost
set EMAIL=your-email@example.com

rem Generate private key
openssl genrsa -out localhost.key 2048
if %errorlevel% neq 0 (
    echo Failed to generate private key.
    exit /b 1
)

rem Create a configuration file for the extensions
(
echo [req]
echo default_bits = 2048
echo prompt = no
echo default_md = sha256
echo req_extensions = req_ext
echo distinguished_name = dn

echo [dn]
echo C=%COUNTRY%
echo ST=%STATE%
echo L=%LOCALITY%
echo O=%ORGANIZATION%
echo OU=%ORGANIZATIONAL_UNIT%
echo CN=%COMMON_NAME%
echo emailAddress=%EMAIL%

echo [req_ext]
echo subjectAltName = @alt_names

echo [alt_names]
echo DNS.1 = localhost
echo IP.1 = 127.0.0.1
) > localhost.cnf

rem Generate Certificate Signing Request (CSR)
openssl req -new -key localhost.key -out localhost.csr -config localhost.cnf
if %errorlevel% neq 0 (
    echo Failed to generate CSR.
    exit /b 1
)

rem Generate Self-Signed Certificate
openssl x509 -req -days %CERTIFICATE_DAYS% -in localhost.csr -signkey localhost.key -out localhost.crt -extensions req_ext -extfile localhost.cnf
if %errorlevel% neq 0 (
    echo Failed to generate self-signed certificate.
    exit /b 1
)

echo SSL certificate for localhost generated successfully.

endlocal
