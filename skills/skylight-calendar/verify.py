import os
import json
import urllib.request
import urllib.error
import base64

def authenticate(email, password):
    url = "https://app.ourskylight.com/api/sessions"
    data = json.dumps({
        "session": {
            "email": email,
            "password": password
        }
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    req.add_header("Accept", "application/json, text/plain, */*")
    req.add_header("Origin", "https://app.ourskylight.com")
    req.add_header("Referer", "https://app.ourskylight.com/")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result
    except urllib.error.HTTPError as e:
        print(f"Authentication failed: {e.code} - {e.read().decode()}")
        return None

def fetch_frames(user_id, token):
    url = f"https://app.ourskylight.com/api/users/{user_id}/claims"
    
    auth_str = f"{user_id}:{token}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    req.add_header("Accept", "application/json, text/plain, */*")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch frames: {e.code} - {e.read().decode()}")
        return None

if __name__ == "__main__":
    print("--- Skylight Verification Script ---")
    email = os.environ.get("SKYLIGHT_EMAIL")
    password = os.environ.get("SKYLIGHT_PASSWORD")
    
    if not email or not password:
        print("Please set the SKYLIGHT_EMAIL and SKYLIGHT_PASSWORD environment variables.")
        print("Example:")
        print("  export SKYLIGHT_EMAIL='your@email.com'")
        print("  export SKYLIGHT_PASSWORD='yourpassword'")
        print("  python3 verify.py")
        exit(1)
        
    print("Authenticating...")
    auth_res = authenticate(email, password)
    
    if not auth_res:
        exit(1)
        
    user_id = auth_res.get("id")
    token = auth_res.get("token")
    
    print(f"Successfully authenticated! User ID: {user_id}")
    
    print("Fetching available frames...")
    claims = fetch_frames(user_id, token)
    if claims:
        print("\nYour Frames:")
        for claim in claims:
            frame = claim.get("device", claim.get("frame", {})) # The API might return it under 'device' or 'frame'
            frame_id = claim.get("device_id", claim.get("frame_id", "Unknown"))
            print(f"- {frame.get('name', 'Unknown Name')} (ID: {frame_id})")
            
    print("\nVerification Complete!")
