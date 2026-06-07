h = open('dashboard/index.html', 'r').read()
i = h.find('(function(){')
while i >= 0:
    j = h.find('})();', i)
    if j > i and j - i < 5000:
        snippet = h[i:j+5]
        if 'KESIMPULAN' in snippet or 'exitCount=0' in snippet:
            print("=== CONCLUSION IIFE ===")
            print(snippet)
            # Try to parse it
            try:
                compile(snippet, 'conclusion.js', 'exec')
                print("=== JS SYNTAX OK ===")
            except SyntaxError as e:
                print(f"=== JS SYNTAX ERROR: {e} ===")
            break
    i = h.find('(function(){', i + 1)
