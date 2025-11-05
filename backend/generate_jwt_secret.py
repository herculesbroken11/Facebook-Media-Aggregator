"""
Generate a secure JWT secret key for use in .env file
"""
import secrets

if __name__ == '__main__':
    # Generate a secure random secret (32 bytes = 256 bits)
    jwt_secret = secrets.token_urlsafe(32)
    print("=" * 60)
    print("Generated JWT Secret Key")
    print("=" * 60)
    print(f"\nJWT_SECRET={jwt_secret}\n")
    print("=" * 60)
    print("IMPORTANT: Copy this to your .env file!")
    print("Keep this secret secure and never commit it to git.")
    print("=" * 60)

