import urllib.request

try:
    print("Testing HTTP connection to Supabase url...")
    res = urllib.request.urlopen("https://omfrvmbsazgfwhapsaur.supabase.co")
    print(f"Status: {res.status}")
    print(f"Body: {res.read()[:300]}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(f"Error body: {e.read()[:300]}")
