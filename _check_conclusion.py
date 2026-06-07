h = open('dashboard/index.html', 'r').read()
i = h.find('id="conclusion"')
print(f'conclusion id= at {i}')
if i >= 0:
    print(h[i-30:i+100])
else:
    print('NOT FOUND - checking what comes between header and tab-nav')
    a = h.find('</div>')  # first closing div
    b = h.find('tab-nav')
    if a >= 0 and b >= 0:
        btwn = h[a:b]
        print(f'Between first </div> and tab-nav ({len(btwn)} chars):')
        print(repr(btwn[:200]))
